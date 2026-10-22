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

Use an ordinary running Obsidian desktop app with CLI support. No debug port,
special launch arguments, or control over the app's launcher is required.
The activation helper connects to Obsidian's normal local CLI socket, uses
`eval`, and checks the exact vault path before changing anything. It needs
Node.js 18 or later and no npm packages. The installed `obsidian` CLI can also
run the commands in the skill; the helper does not require it on `PATH`.

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
   other vaults and preferences, and backs up an existing registry. It also
   applies [profile.json](../assets/defaults/profile.json), whose `"cli": true`
   enables the app's CLI preference. Use `--defaults-file PATH` for an override.
   Do not edit a live profile that could overwrite the registry from memory.
3. Use the app as it is normally opened. The registered vault opens at startup;
   an already running instance with CLI enabled needs no relaunch. The helper
   does not launch Obsidian or alter its startup arguments. If CLI support is
   disabled, its socket rejects `eval` too: apply the profile defaults while
   the app is closed, then use its next normal launch. Do not claim a disabled
   CLI can be enabled through that same gated socket.
4. From this skill's directory, run:

   ```sh
   node scripts/activate_plugins.mjs --vault "/absolute/path/My Vault"
   ```

The helper waits for the exact vault path, applies the permission, reloads only
that vault window, and verifies every requested plugin has a loaded version. It does not
require the user to click the trust prompt or enable a plugin. It fails if no
matching vault opens or a requested plugin fails to load. Investigate failures;
do not replace verification with instructions for the user to finish setup.

It discovers the normal per-user socket on Linux and macOS or named pipe on
Windows. Use `--socket PATH` only when the running app uses another endpoint.
Do not start a separate instance or overwrite the user's socket to make a
connection succeed. Socket protocol details are version-dependent; surface
an unsupported-client error rather than falling back to a debugging port.

Use `--plugins-file PATH` with the same enablement list used for installation.
Use `--storage-file PATH` for a one-vault local-storage override, or edit the
bundled defaults when asked to change future setups. `--timeout SECONDS`
controls the bounded startup wait (60 seconds by default).

## Verify persistence

Run the helper in observation-only mode to check the existing instance:

```sh
node scripts/activate_plugins.mjs --vault "/absolute/path/My Vault" --check
```

`--check` never changes storage or reloads the window. Report plugin setup
complete only after this check passes. When validating setup defaults, also
close and reopen a disposable profile normally and repeat `--check` to verify
persistence. Account sign-in and connecting shared folders are separate from
plugin activation.
