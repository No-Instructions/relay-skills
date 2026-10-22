#!/usr/bin/env python3
"""Register a prepared vault in a stopped Obsidian profile, preserving other entries."""

import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import tempfile
import time


DEFAULTS = Path(__file__).resolve().parent.parent / "assets/defaults/profile.json"


def register(vault, profile, defaults_file):
    vault = vault.expanduser().resolve()
    profile = profile.expanduser()
    if not vault.is_dir():
        raise ValueError(f"Vault directory does not exist: {vault}")
    registry = profile / "obsidian.json"
    if profile.is_symlink() or registry.is_symlink():
        raise ValueError("Profile and registry must not be symlinks")
    data = json.loads(registry.read_text(encoding="utf-8")) if registry.exists() else {}
    if not isinstance(data, dict) or not isinstance(data.get("vaults", {}), dict):
        raise ValueError("Expected an Obsidian registry object with a vaults object")
    defaults = json.loads(defaults_file.read_text(encoding="utf-8"))
    if not isinstance(defaults, dict) or set(defaults) != {"cli"} or not isinstance(defaults["cli"], bool):
        raise ValueError("Profile defaults must contain only a boolean cli setting")
    settings_changed = any(data.get(key) != value for key, value in defaults.items())
    data.update(defaults)
    entries = data.setdefault("vaults", {})
    for key, entry in entries.items():
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError(f"Invalid vault registry entry: {key}")
    key = next((key for key, entry in entries.items() if Path(entry["path"]).resolve() == vault), None)
    if key is not None and entries[key].get("open") is True and not settings_changed:
        return key
    if key is None:
        key = secrets.token_hex(8)
        while key in entries:
            key = secrets.token_hex(8)
        entries[key] = {"path": str(vault)}
    entries[key].update(open=True, ts=int(time.time() * 1000))
    profile.mkdir(parents=True, exist_ok=True)
    if registry.exists():
        with tempfile.NamedTemporaryFile(prefix="vault-registry-backup-", suffix=".json", dir=profile, delete=False) as stream:
            backup = Path(stream.name)
        shutil.copy2(registry, backup)
        print(f"Registry backup: {backup}")
    with tempfile.NamedTemporaryFile(dir=profile, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write((json.dumps(data, indent=2) + "\n").encode("utf-8"))
            stream.close()
            if registry.exists():
                shutil.copymode(registry, temporary)
            os.replace(temporary, registry)
        finally:
            temporary.unlink(missing_ok=True)
    return key


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path, help="Obsidian application data directory; app must be stopped")
    parser.add_argument("--defaults-file", type=Path, default=DEFAULTS)
    args = parser.parse_args()
    try:
        print(f"Vault id: {register(args.vault, args.profile, args.defaults_file.expanduser())}")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
