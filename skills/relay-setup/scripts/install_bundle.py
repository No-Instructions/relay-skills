#!/usr/bin/env python3
"""Install a published Relay bundle into a closed Obsidian vault."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile


PLUGIN_ID = "system3-relay"
BUNDLE_FILES = ("main.js", "manifest.json", "styles.css")
PLUGINS_FILE = Path(__file__).resolve().parent.parent / "assets" / "defaults" / "community-plugins.json"


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path} at line {exc.lineno}") from exc


def plugin_ids(value, path):
    if not isinstance(value, list) or not all(
        isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9_-]+", item) for item in value
    ):
        raise ValueError(f"Expected a JSON array of plugin ids in {path}")
    return value


def check_target(config, relative):
    target = config
    for part in relative.parts:
        target = target / part
        if target.is_symlink():
            raise ValueError(f"Installation path is a symlink: {target}")
    return target


def plan(vault, config_name, bundle, plugins_file, replace):
    if not vault.is_dir():
        raise ValueError(f"Create the vault directory first: {vault}")
    if not config_name.startswith(".") or config_name in (".", "..") or any(
        char in config_name for char in ("/", "\\")
    ):
        raise ValueError("--config-dir must be a single folder name starting with a dot")
    config = vault / config_name
    if config.is_symlink() or (config.exists() and not config.is_dir()):
        raise ValueError(f"Configuration path must be a directory, not a symlink: {config}")
    payloads = {}
    for name in BUNDLE_FILES:
        source = bundle / name
        data = source.read_bytes()
        if not data.strip():
            raise ValueError(f"Empty release file: {source}")
        payloads[Path("plugins") / PLUGIN_ID / name] = data
    manifest = read_json(bundle / "manifest.json")
    if not isinstance(manifest, dict) or manifest.get("id") != PLUGIN_ID:
        raise ValueError(f"Bundle manifest must identify {PLUGIN_ID}")
    if not isinstance(manifest.get("version"), str) or not manifest["version"]:
        raise ValueError("Bundle manifest must include a version")
    requested = plugin_ids(read_json(plugins_file), plugins_file)
    for plugin_id in requested:
        if plugin_id == PLUGIN_ID:
            continue
        relative = Path("plugins") / plugin_id
        other_manifest = read_json(check_target(config, relative / "manifest.json"))
        if not isinstance(other_manifest, dict) or other_manifest.get("id") != plugin_id:
            raise ValueError(f"Installed manifest does not match {plugin_id}")
        if not check_target(config, relative / "main.js").is_file():
            raise ValueError(f"Install {plugin_id} before enabling it")
    enabled_path = check_target(config, Path("community-plugins.json"))
    enabled = plugin_ids(read_json(enabled_path), enabled_path) if enabled_path.exists() else []
    merged = list(enabled)
    merged.extend(item for item in requested if item not in merged)
    if not enabled_path.exists() or merged != enabled:
        payloads[Path("community-plugins.json")] = (json.dumps(merged, indent=2) + "\n").encode("utf-8")
    changes = []
    for relative, data in payloads.items():
        target = check_target(config, relative)
        if target.exists():
            if target.read_bytes() == data:
                continue
            if relative.name in BUNDLE_FILES and not replace:
                raise ValueError(f"Installed bundle differs at {relative}; use --replace for an intended update")
        changes.append((relative, data))
    return config, manifest["version"], changes


def apply(config, changes):
    if not changes:
        return None
    config.mkdir(parents=True, exist_ok=True)
    existing = [relative for relative, _ in changes if (config / relative).exists()]
    backup = None
    if existing:
        backup_root = check_target(config, Path("setup-backups"))
        backup_root.mkdir(exist_ok=True)
        backup = Path(tempfile.mkdtemp(prefix="relay-", dir=backup_root))
        for relative in existing:
            (backup / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(config / relative, backup / relative)
    for relative, data in changes:
        target = config / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            try:
                stream.write(data)
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
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--config-dir", default=".obsidian")
    parser.add_argument("--plugins-file", type=Path, default=PLUGINS_FILE)
    parser.add_argument("--replace", action="store_true", help="Replace differing installed release files")
    parser.add_argument("--dry-run", action="store_true", help="Validate and list changes without writing")
    args = parser.parse_args()
    try:
        config, version, changes = plan(
            args.vault.expanduser().resolve(), args.config_dir, args.bundle.expanduser(),
            args.plugins_file.expanduser(), args.replace,
        )
        for relative, _ in changes:
            print(f"{'Would write' if args.dry_run else 'Write'} {config / relative}")
        if not args.dry_run:
            backup = apply(config, changes)
            if backup:
                print(f"Backups: {backup}")
        if not changes:
            print("Bundle and enabled plugins already match; no changes.")
        print(f"Relay {version}: {'validated' if args.dry_run else 'prepared on disk'}; complete automatic first-launch activation before reporting setup complete.")
        return 0
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
