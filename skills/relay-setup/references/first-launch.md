# Automatic first launch

Obsidian stores the community-plugin permission in its local app storage,
separately from the vault's enabled-plugin list. Copying `community-plugins.json`
alone does not disable Restricted mode. Apply both parts during setup.

The editable [local-storage defaults](../assets/defaults/local-storage.json)
set `enable-plugin` to the string `"true"`. The activation helper applies it
to the selected vault's `enable-plugin-<appId>` key in the running profile.
It never copies another profile's storage. This permission is local to the
device/profile: repeat activation when setting up another device.

## Open and activate

If the Obsidian CLI is already available, use the skill's `plugins:restrict off`
and `plugin:enable` commands and verify loading. Otherwise use the CDP helper,
which needs Node.js 22 or later and no npm packages:

1. Finish the bundle installation while the target vault is closed.
2. For a new folder, register it while Obsidian is stopped:

   ```sh
   python3 scripts/register_vault.py --vault "/absolute/path/My Vault" --profile "/path/to/Obsidian/profile"
   ```

   Locate the profile actually used by the installed app. Common desktop
   locations are `~/.config/obsidian` on Linux,
   `~/Library/Application Support/obsidian` on macOS, and `%APPDATA%/obsidian`
   on Windows; a `--user-data-dir` argument overrides the location. The helper
   merges the vault into `obsidian.json`, marks it to open at startup, preserves
   other vaults and preferences, and backs up an existing registry. Do not run
   it against a live profile that could overwrite the registry from memory.
3. Start the installed **desktop application executable** with
   `--remote-debugging-address=127.0.0.1 --remote-debugging-port=9222`. The
   registered vault opens at startup. For an already registered vault, the
   [open URI](https://help.obsidian.md/uri) can select it explicitly. Choose
   an unused local port if necessary. On Linux, resolve the desktop executable
   or AppImage; a command named `obsidian` may be only a CLI wrapper. On macOS,
   use the executable inside `Obsidian.app`; on Windows use `Obsidian.exe`.
   Use the user's intended profile so the permission persists where they work.
   If Obsidian is already running without CDP, close/restart it normally after
   allowing pending edits to save; a second launch may forward to the existing
   process without enabling debugging. Never terminate unrelated processes.
4. From this skill's directory, run:

   ```sh
   node scripts/activate_plugins.mjs --vault "/absolute/path/My Vault" --port 9222
   ```

The helper waits for the exact vault path, applies the permission, reloads the
window, and verifies every requested plugin has a loaded version. It does not
require the user to click the trust prompt or enable a plugin. It fails if no
matching vault opens or a requested plugin fails to load. Investigate failures;
do not replace verification with instructions for the user to finish setup.

Use `--plugins-file PATH` with the same enablement list used for installation.
Use `--storage-file PATH` for a one-vault local-storage override, or edit the
bundled defaults when asked to change future setups. `--timeout SECONDS`
controls the bounded startup wait (60 seconds by default).

## Verify persistence

Close Obsidian normally and reopen the same vault and profile. Then run the
helper in observation-only mode:

```sh
node scripts/activate_plugins.mjs --vault "/absolute/path/My Vault" --port 9222 --check
```

`--check` never changes storage or reloads the window. Success confirms the
permission and loaded plugin versions survived a restart. Report plugin setup
complete only after this check passes. Account sign-in and connecting shared
folders are separate from plugin activation.
