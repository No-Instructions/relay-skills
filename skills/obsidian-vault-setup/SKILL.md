---
name: obsidian-vault-setup
description: Create an Obsidian vault, apply useful editor and core-plugin settings, or update the reusable vault defaults stored with this skill. Use for new vault setup and requests to change default Obsidian settings.
metadata:
  version: "0.1.0"
---

# Set up an Obsidian vault

Prepare a folder and its vault-local configuration. The settings live in
[assets/defaults](assets/defaults), separately from these instructions and the
helper. Use Python 3.9 or later for the helper; Obsidian need not be installed or
running to prepare the files.

## Set up or configure a vault

1. Resolve the vault's absolute path from the request or workspace. Inspect any
   existing configuration first. Use the vault's actual configuration folder;
   `.obsidian` is the default, but users can override it in Files and links.
   For a running vault with the CLI enabled, inspect it with:

   ```sh
   obsidian vault="My Vault" eval code='({path:app.vault.adapter.basePath,configDir:app.vault.configDir})'
   ```

2. Read [references/defaults.md](references/defaults.md) and the JSON assets.
   Honor preferences already given by the user. Close the target vault before
   writing its configuration files, so Obsidian cannot overwrite them from
   memory. Close only that vault; do not terminate unrelated windows.

3. Run the helper from this skill's directory (or use its absolute path):

   ```sh
   python3 scripts/configure_vault.py --vault "/absolute/path/My Vault" --dry-run
   python3 scripts/configure_vault.py --vault "/absolute/path/My Vault"
   ```

   It creates missing directories, fills missing settings, and preserves
   existing values. It backs up changed files inside the configuration folder
   and leaves notes, community plugins, and other configuration files alone.
   Repeating a successful application makes no further changes.

   Use `--config-dir .obsidian-work` for a custom configuration folder. Use
   `--overwrite` only when applying the supplied values to existing settings
   is part of the request. For a narrow change, supply a temporary directory
   containing just the desired file and keys with `--defaults-dir PATH`;
   `--overwrite` then changes only those keys.

4. Open the prepared folder through **Manage vaults → Open folder as vault**.
   This registers it with Obsidian without replacing the application's vault
   registry. Check Files and links, Editor, and Core plugins against the files
   applied. If the CLI is enabled, use `plugins:enabled filter=core` and
   `eval` with `app.vault.getConfig("settingName")` to verify relevant settings.
   Report the path, changed settings, and whether the vault was opened and
   verified, or just prepared on disk.

For a request that also includes Relay, continue with `relay-setup` when
available. Independently, Relay can be installed from **Settings → Community
plugins → Browse → Relay → Install → Enable**. Vault defaults alone do not
install or enable community plugins.

## Change the reusable defaults

When the user asks to update defaults for future vaults, edit the relevant JSON
asset, keeping it valid JSON. Update the rationale in
[references/defaults.md](references/defaults.md) if the behavior changes. Run
the helper against a temporary vault and inspect the generated configuration.
Keep preferences in assets; do not duplicate them as constants in the helper.

Changing the assets does not change existing vaults. Apply to a named vault as
well when requested, using a patch containing only the requested settings.
For a one-vault customization, leave the reusable assets unchanged.

## Sources

- [Vault creation and registration](https://help.obsidian.md/manage-vaults)
- [Configuration folder overrides](https://help.obsidian.md/configuration-folder)
- [Obsidian CLI](https://help.obsidian.md/cli)
