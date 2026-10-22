"""Exercise setup helpers against disposable vaults without launching Obsidian."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIGURE = ROOT / "skills/obsidian-vault-setup/scripts/configure_vault.py"
INSTALL = ROOT / "skills/relay-setup/scripts/install_bundle.py"
REGISTER = ROOT / "skills/relay-setup/scripts/register_vault.py"


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.vault = self.root / "Vault with spaces"
        self.config = self.vault / ".obsidian"
        self.bundle = self.root / "release"
        self.bundle.mkdir()
        self.write_json(self.bundle / "manifest.json", {
            "id": "system3-relay", "version": "1.0.0", "minAppVersion": "1.6.6",
        })
        (self.bundle / "main.js").write_text("// Test bundle; never executed.\n")
        (self.bundle / "styles.css").write_text(".relay {}\n")

    def write_json(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def read_json(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def run_helper(self, script, *args, success=True):
        result = subprocess.run(
            [sys.executable, str(script), "--vault", str(self.vault), *map(str, args)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def install(self, *args, **kwargs):
        return self.run_helper(INSTALL, "--bundle", self.bundle, *args, **kwargs)

    def snapshot(self):
        if not self.vault.exists():
            return {}
        return {str(p.relative_to(self.vault)): p.read_bytes() for p in self.vault.rglob("*") if p.is_file()}

    def test_fresh_vault_and_repeat_are_idempotent(self):
        self.run_helper(CONFIGURE, "--dry-run")
        self.assertFalse(self.vault.exists())
        self.run_helper(CONFIGURE)
        app = self.read_json(self.config / "app.json")
        self.assertEqual(app["attachmentFolderPath"], "./Attachments")
        self.assertTrue(app["alwaysUpdateLinks"])
        self.assertTrue(self.read_json(self.config / "core-plugins.json")["file-recovery"])
        self.assertFalse((self.config / "community-plugins.json").exists())
        initial = self.snapshot()
        self.run_helper(CONFIGURE)
        self.assertEqual(self.snapshot(), initial)

    def test_existing_preferences_notes_and_plugins_survive(self):
        app = {"alwaysUpdateLinks": False, "attachmentFolderPath": "Media", "custom": {"x": 1}}
        self.write_json(self.config / "app.json", app)
        original = (self.config / "app.json").read_bytes()
        self.write_json(self.config / "core-plugins.json", {"graph": False, "sync": True, "other": True})
        self.write_json(self.config / "community-plugins.json", ["other-plugin"])
        (self.vault / "Note.md").write_text("Keep this note.\n")
        self.run_helper(CONFIGURE)
        result = self.read_json(self.config / "app.json")
        for key, value in app.items():
            self.assertEqual(result[key], value)
        core = self.read_json(self.config / "core-plugins.json")
        self.assertFalse(core["graph"])
        self.assertTrue(core["sync"])
        self.assertTrue(core["other"])
        self.assertEqual(self.read_json(self.config / "community-plugins.json"), ["other-plugin"])
        self.assertEqual((self.vault / "Note.md").read_text(), "Keep this note.\n")
        backups = list((self.config / "setup-backups").glob("*/app.json"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)

    def test_targeted_profile_overwrites_only_supplied_keys(self):
        self.write_json(self.config / "app.json", {"alwaysUpdateLinks": False, "custom": {"a": 1, "b": 2}})
        profile = self.root / "profile"
        self.write_json(profile / "app.json", {"alwaysUpdateLinks": True, "custom": {"a": 3}})
        self.run_helper(CONFIGURE, "--defaults-dir", profile, "--overwrite")
        self.assertEqual(self.read_json(self.config / "app.json"), {
            "alwaysUpdateLinks": True, "custom": {"a": 3, "b": 2},
        })
        self.assertFalse((self.config / "appearance.json").exists())

    def test_core_array_preserves_disabled_plugins_until_overwrite(self):
        self.write_json(self.config / "core-plugins.json", ["sync", "custom-core"])
        self.run_helper(CONFIGURE)
        self.assertEqual(self.read_json(self.config / "core-plugins.json"), ["sync", "custom-core"])
        profile = self.root / "profile"
        self.write_json(profile / "core-plugins.json", {"sync": False, "file-recovery": True})
        self.run_helper(CONFIGURE, "--defaults-dir", profile, "--overwrite")
        self.assertEqual(self.read_json(self.config / "core-plugins.json"), ["custom-core", "file-recovery"])

    def test_malformed_later_file_leaves_all_configuration_untouched(self):
        self.write_json(self.config / "app.json", {"custom": True})
        (self.config / "core-plugins.json").write_text("{invalid")
        initial = self.snapshot()
        self.run_helper(CONFIGURE, success=False)
        self.assertEqual(self.snapshot(), initial)

    def test_both_helpers_support_custom_config_folder(self):
        self.run_helper(CONFIGURE, "--config-dir", ".obsidian-work")
        self.install("--config-dir", ".obsidian-work")
        self.assertFalse(self.config.exists())
        custom = self.vault / ".obsidian-work"
        self.assertTrue((custom / "app.json").is_file())
        self.assertEqual(self.read_json(custom / "community-plugins.json"), ["system3-relay"])

    def test_install_preserves_enabled_plugins_and_local_data(self):
        self.write_json(self.config / "community-plugins.json", ["other-plugin"])
        data_path = self.config / "plugins/system3-relay/data.json"
        self.write_json(data_path, {"sharedFolders": [{"path": "Team"}], "custom": True})
        original_data = data_path.read_bytes()
        self.write_json(self.bundle / "data.json", {"mustNotBeCopied": True})
        before = self.snapshot()
        self.install("--dry-run")
        self.assertEqual(self.snapshot(), before)
        self.install()
        self.assertEqual(self.read_json(self.config / "community-plugins.json"), ["other-plugin", "system3-relay"])
        self.assertEqual(data_path.read_bytes(), original_data)
        for name in ("main.js", "manifest.json", "styles.css"):
            self.assertEqual((self.config / "plugins/system3-relay" / name).read_bytes(), (self.bundle / name).read_bytes())
        after = self.snapshot()
        self.install()
        self.assertEqual(self.snapshot(), after)

    def test_bundle_replacement_is_explicit_and_backed_up(self):
        self.vault.mkdir()
        self.install()
        installed_main = self.config / "plugins/system3-relay/main.js"
        original_main = installed_main.read_bytes()
        (self.bundle / "main.js").write_text("// Replacement bundle\n")
        before = self.snapshot()
        self.install(success=False)
        self.assertEqual(self.snapshot(), before)
        self.install("--replace")
        self.assertEqual(installed_main.read_bytes(), (self.bundle / "main.js").read_bytes())
        backups = list((self.config / "setup-backups").glob("*/plugins/system3-relay/main.js"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original_main)

    def test_invalid_bundle_does_not_modify_vault(self):
        self.vault.mkdir()
        for invalid in ({"id": "wrong", "version": "1.0.0"}, {"id": "system3-relay"}):
            with self.subTest(manifest=invalid):
                self.write_json(self.bundle / "manifest.json", invalid)
                self.install(success=False)
                self.assertEqual(self.snapshot(), {})
        self.write_json(self.bundle / "manifest.json", {"id": "system3-relay", "version": "1.0.0"})
        (self.bundle / "main.js").write_text("")
        self.install(success=False)
        self.assertEqual(self.snapshot(), {})

    def test_invalid_enabled_list_is_not_replaced(self):
        self.write_json(self.config / "community-plugins.json", {"other-plugin": True})
        before = self.snapshot()
        self.install(success=False)
        self.assertEqual(self.snapshot(), before)

    def test_extra_default_plugin_must_be_installed(self):
        self.vault.mkdir()
        plugins = self.root / "plugins.json"
        self.write_json(plugins, ["system3-relay", "extra-plugin"])
        self.install("--plugins-file", plugins, success=False)
        self.assertFalse(self.config.exists())
        self.write_json(self.config / "plugins/extra-plugin/manifest.json", {"id": "extra-plugin"})
        (self.config / "plugins/extra-plugin/main.js").write_text("// Existing plugin\n")
        self.install("--plugins-file", plugins)
        self.assertEqual(self.read_json(self.config / "community-plugins.json"), ["system3-relay", "extra-plugin"])

    def test_config_path_cannot_escape_vault(self):
        self.vault.mkdir()
        self.run_helper(CONFIGURE, "--config-dir", "../outside", success=False)
        self.install("--config-dir", "../outside", success=False)
        outside = self.root / "outside"
        outside.mkdir()
        self.config.symlink_to(outside, target_is_directory=True)
        self.run_helper(CONFIGURE, success=False)
        self.install(success=False)
        self.assertEqual(list(outside.iterdir()), [])

    def test_register_new_vault_is_idempotent(self):
        self.vault.mkdir()
        profile = self.root / "profile"
        self.run_helper(REGISTER, "--profile", profile)
        registry = profile / "obsidian.json"
        original = registry.read_bytes()
        self.assertTrue(self.read_json(registry)["cli"])
        entry = next(iter(self.read_json(registry)["vaults"].values()))
        self.assertEqual(entry["path"], str(self.vault))
        self.assertTrue(entry["open"])
        self.run_helper(REGISTER, "--profile", profile)
        self.assertEqual(registry.read_bytes(), original)
        self.assertEqual(list(profile.glob("vault-registry-backup-*")), [])

    def test_register_preserves_existing_vaults_preferences_and_id(self):
        self.vault.mkdir()
        profile = self.root / "profile"
        registry = profile / "obsidian.json"
        other = {"path": str(self.root / "Other"), "open": True, "ts": 12}
        self.write_json(registry, {
            "vaults": {"existing": {"path": str(self.vault), "open": False, "custom": 42}, "other": other},
            "customPreference": "keep", "cli": False,
        })
        original = registry.read_bytes()
        self.run_helper(REGISTER, "--profile", profile)
        result = self.read_json(registry)
        self.assertEqual(set(result["vaults"]), {"existing", "other"})
        self.assertTrue(result["vaults"]["existing"]["open"])
        self.assertEqual(result["vaults"]["existing"]["custom"], 42)
        self.assertEqual(result["vaults"]["other"], other)
        self.assertEqual(result["customPreference"], "keep")
        self.assertTrue(result["cli"])
        backups = list(profile.glob("vault-registry-backup-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)

    def test_invalid_registry_is_not_changed(self):
        self.vault.mkdir()
        profile = self.root / "profile"
        registry = profile / "obsidian.json"
        self.write_json(registry, {"vaults": {"invalid": None}})
        original = registry.read_bytes()
        self.run_helper(REGISTER, "--profile", profile, success=False)
        self.assertEqual(registry.read_bytes(), original)
        self.assertEqual(list(profile.glob("vault-registry-backup-*")), [])

    def test_register_enables_cli_for_already_open_vault(self):
        self.vault.mkdir()
        profile = self.root / "profile"
        registry = profile / "obsidian.json"
        self.write_json(registry, {
            "vaults": {"existing": {"path": str(self.vault), "open": True}},
            "cli": False,
        })
        self.run_helper(REGISTER, "--profile", profile)
        self.assertTrue(self.read_json(registry)["cli"])
        self.assertEqual(set(self.read_json(registry)["vaults"]), {"existing"})


if __name__ == "__main__":
    unittest.main()
