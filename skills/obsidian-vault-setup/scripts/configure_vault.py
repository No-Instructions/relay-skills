#!/usr/bin/env python3
"""Apply a small JSON settings profile to a closed Obsidian vault."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


FILENAMES = ("app.json", "appearance.json", "core-plugins.json")
DEFAULTS = Path(__file__).resolve().parent.parent / "assets" / "defaults"


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path} at line {exc.lineno}") from exc


def merge(current, supplied, overwrite):
    result = dict(current)
    for key, value in supplied.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge(result[key], value, overwrite)
        elif overwrite or key not in result:
            result[key] = value
    return result


def validate_core(value, path):
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return
    if isinstance(value, dict) and all(isinstance(item, bool) for item in value.values()):
        return
    raise ValueError(f"Expected plugin boolean map or id array in {path}")


def plan(vault, config_name, defaults, overwrite):
    if not config_name.startswith(".") or config_name in (".", "..") or any(
        char in config_name for char in ("/", "\\")
    ):
        raise ValueError("--config-dir must be a single folder name starting with a dot")
    if vault.exists() and not vault.is_dir():
        raise ValueError(f"Vault path is not a directory: {vault}")
    config = vault / config_name
    if config.is_symlink():
        raise ValueError(f"Configuration folder is a symlink: {config}")
    if config.exists() and not config.is_dir():
        raise ValueError(f"Configuration path is not a directory: {config}")
    if not defaults.is_dir():
        raise ValueError(f"Defaults directory does not exist: {defaults}")
    unknown = {p.name for p in defaults.glob("*.json")} - set(FILENAMES)
    if unknown:
        raise ValueError(f"Unsupported defaults files: {', '.join(sorted(unknown))}")
    changes = []
    found = False
    for name in FILENAMES:
        source = defaults / name
        if not source.exists():
            continue
        found = True
        supplied = read_json(source)
        if not isinstance(supplied, dict):
            raise ValueError(f"Defaults must be a JSON object: {source}")
        if name == "core-plugins.json":
            validate_core(supplied, source)
        target = config / name
        if target.is_symlink():
            raise ValueError(f"Configuration file is a symlink: {target}")
        current = read_json(target) if target.exists() else {}
        if name == "core-plugins.json":
            validate_core(current, target)
        elif not isinstance(current, dict):
            raise ValueError(f"Expected a JSON object in {target}")
        if isinstance(current, list):
            result = list(current)
            if overwrite:
                result = [item for item in result if supplied.get(item) is not False]
                result.extend(key for key, value in supplied.items() if value and key not in result)
        else:
            result = merge(current, supplied, overwrite)
        if not target.exists() or result != current:
            changes.append((target, result))
    if not found:
        raise ValueError(f"No supported defaults files in {defaults}")
    return config, changes


def apply(config, changes):
    if not changes:
        return None
    config.mkdir(parents=True, exist_ok=True)
    backup = None
    existing = [target for target, _ in changes if target.exists()]
    if existing:
        backup_root = config / "setup-backups"
        if backup_root.is_symlink():
            raise ValueError(f"Backup folder is a symlink: {backup_root}")
        backup_root.mkdir(exist_ok=True)
        backup = Path(tempfile.mkdtemp(prefix="settings-", dir=backup_root))
        for target in existing:
            shutil.copy2(target, backup / target.name)
    for target, value in changes:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=config, delete=False) as stream:
            temporary = Path(stream.name)
            try:
                stream.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
                stream.close()
                if target.exists():
                    shutil.copymode(target, temporary)
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--config-dir", default=".obsidian")
    parser.add_argument("--defaults-dir", type=Path, default=DEFAULTS)
    parser.add_argument("--overwrite", action="store_true", help="Apply supplied values to existing keys")
    parser.add_argument("--dry-run", action="store_true", help="List changes without writing files")
    args = parser.parse_args()
    try:
        vault = args.vault.expanduser().resolve()
        config, changes = plan(vault, args.config_dir, args.defaults_dir.expanduser(), args.overwrite)
        for target, _ in changes:
            print(f"{'Would write' if args.dry_run else 'Write'} {target}")
        if not args.dry_run:
            backup = apply(config, changes)
            if backup:
                print(f"Backups: {backup}")
        if not changes:
            print("Settings already match; no changes.")
        print(f"Vault: {vault}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
