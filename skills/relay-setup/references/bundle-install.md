# Install a published Relay bundle

Use this path to prepare a closed vault, including before its first launch.
The helper needs Python 3.9 or later. It copies release files and merges plugin
enablement without changing the vault's notes or existing Relay settings.

## Obtain the release

Download from [No-Instructions/Relay releases](https://github.com/No-Instructions/Relay/releases).
Use a separate temporary directory. Resolve a single release tag first, so
all files come from the same release. With GitHub CLI available:

```sh
RELAY_BUNDLE_DIR=$(mktemp -d)
RELAY_RELEASE_TAG=$(gh release view --repo No-Instructions/Relay --json tagName --jq .tagName)
gh release download "$RELAY_RELEASE_TAG" --repo No-Instructions/Relay \
  --pattern main.js --pattern manifest.json --pattern styles.css \
  --dir "$RELAY_BUNDLE_DIR"
```

If the user specified a tag, use it in place of the lookup. A beta or a
downgrade needs to be part of the user's request. Without `gh`, use the public
GitHub Releases API at
`https://api.github.com/repos/No-Instructions/Relay/releases/latest` (or
`/releases/tags/<tag>`), then download those three named assets using their
`browser_download_url` fields. Check HTTP success for every file.

These are plugin release assets, not the repository's source archive. Never
copy a personal plugin directory or a settings file along with them. Check
the manifest's `minAppVersion` against the installed Obsidian version before
loading the plugin. For an offline preparation, report that compatibility
and loading still need verification.

## Install into the closed vault

Close the target vault before copying files. From this skill's directory:

```sh
python3 scripts/install_bundle.py --vault "/absolute/path/My Vault" \
  --bundle "$RELAY_BUNDLE_DIR" --dry-run
python3 scripts/install_bundle.py --vault "/absolute/path/My Vault" \
  --bundle "$RELAY_BUNDLE_DIR"
```

Use `--config-dir .obsidian-work` when that is the vault's configured folder.
The vault folder must already exist. The helper validates the manifest id,
checks all three files are nonempty, and writes:

```text
<config-dir>/plugins/system3-relay/main.js
<config-dir>/plugins/system3-relay/manifest.json
<config-dir>/plugins/system3-relay/styles.css
<config-dir>/community-plugins.json
```

It adds the ids in [community-plugins.json](../assets/defaults/community-plugins.json)
to the enabled list without removing existing entries. Any extra ids in the
defaults must have matching installed manifests and `main.js` files already.
Use `--plugins-file PATH` for a one-vault enablement list without editing the
reusable defaults.

An identical bundle is a no-op. To replace differing installed files for a
requested update or reinstall, add `--replace`. Before any replacements, the
helper backs up changed existing files under
`<config-dir>/setup-backups/<unique-run>/`, preserving their relative paths.
Close the vault and restore those files to undo a replacement. It never
copies or changes `data.json`, authentication state, or shared-folder records.

## Finish in Obsidian

Open the vault, turn on community plugins if Restricted mode is enabled, and
confirm Relay is enabled and loaded. An enabled-plugin JSON file is not proof
that the app allowed or loaded the plugin. Use the CLI verification in the
skill, or inspect **Settings → Community plugins → Relay**. Then complete the
sign-in and folder setup requested by the user.
