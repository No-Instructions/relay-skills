---
name: relay-setup
description: Install and enable the Relay community plugin in an Obsidian vault, prepare a vault with a published Relay bundle, and guide sign-in and shared-folder setup. Use when setting up a vault with Relay or changing the plugin enablement defaults.
metadata:
  version: "0.1.0"
---

# Set up Relay

Relay's Obsidian plugin id is `system3-relay`. Install the public stable release
unless the user requests a particular release. A local vault, an installed
plugin, a signed-in account, and a connected shared folder are separate setup
steps; report which have been verified.

## Prepare the vault

Resolve the target vault path and its configuration folder (`.obsidian` unless
overridden). If a new vault is requested, create the folder and use
`obsidian-vault-setup` when available for the editable settings profile. Without
that skill, create the folder, then use **Manage vaults → Open folder as vault**
in Obsidian. Do not replace an existing vault or its application registry.

For shared notes, set new attachments to a subfolder beside the current note
when configuring defaults: **Files and links → Default location for new
attachments → In subfolder under current folder → Attachments**. This keeps
attachments inside the shared folder. Preserve an existing preference unless
the request includes changing it. See [attachment placement](https://docs.relay.md/guides/set-attachment-location/).

## Install in a running vault

Prefer the [Obsidian CLI](https://help.obsidian.md/cli) when available. It needs
a supported desktop installer and **Settings → General → Command line
interface** enabled. Target the vault explicitly; use its id if names collide:

```sh
obsidian vault="My Vault" eval code='({path:app.vault.adapter.basePath,configDir:app.vault.configDir})'
obsidian vault="My Vault" plugin id=system3-relay
obsidian vault="My Vault" plugins:restrict
```

Check the reported path before changing anything. If community plugins are
restricted, enabling them is part of a request to install and enable Relay:

```sh
obsidian vault="My Vault" plugins:restrict off
```

Read [assets/defaults/community-plugins.json](assets/defaults/community-plugins.json)
for the desired plugin ids. For each missing id, install and enable it; for an
installed id, enable it without reinstalling. With the bundled defaults:

```sh
# When Relay is missing:
obsidian vault="My Vault" plugin:install id=system3-relay enable
# When Relay is already installed:
obsidian vault="My Vault" plugin:enable id=system3-relay filter=community
```

Keep other installed and enabled plugins intact. Inspect command output for
errors, then verify the enabled list and loaded Relay version:

```sh
obsidian vault="My Vault" plugins:enabled filter=community versions
obsidian vault="My Vault" eval code='app.plugins.plugins["system3-relay"]?.manifest.version ?? "Relay is not loaded"'
```

An exit code alone does not establish success. If the CLI is unavailable, use
**Settings → Community plugins → Turn on community plugins → Browse → Relay →
Install → Enable**. The [official installation guide](https://docs.relay.md/guides/install-relay-for-obsidian/)
describes this path. For preparing files before the first launch, or installing
a specific published release, use [references/bundle-install.md](references/bundle-install.md).

## Sign in and connect a folder

For hosting the content server on the user's own infrastructure, use
`relay-self-hosting` when available, or the public
[server template](https://github.com/No-Instructions/relay-server-template).
Registration of a self-hosted server is separate from installing the plugin.

Open Relay settings and let the user complete the provider's sign-in flow.
Keep credentials, share keys, account ids, and folder registrations out of
reusable settings. Preserve the installed plugin's `data.json`.

Use the server and folder named by the user. For a fresh account, look for its
starter Relay Server before creating another one. Join an invitation or share
a local folder only when that action is included in the request; do not infer
which existing notes should become shared from a plugin-install request. Use
the UI and current public guides for [server setup](https://docs.relay.md/guides/create-a-relay-server/)
and [sharing a folder](https://docs.relay.md/guides/share-a-folder/).

Verify the account appears in Relay settings and, when folder connection was
requested, that the selected folder appears connected. The
`relay-obsidian-plugin` skill can inspect sync status when available. Report
the vault path, plugin version, and any remaining sign-in or folder-selection
step. Do not describe a bundle copied to disk as a working sync connection.

## Change plugin defaults

Edit [assets/defaults/community-plugins.json](assets/defaults/community-plugins.json)
when the user asks to change the enabled community-plugin defaults. Keep it
an array of plugin ids. Adding an id to this file does not download a plugin:
the CLI workflow installs missing entries; the bundle helper requires other
listed plugins to be installed already. Changes apply to future setup runs;
apply them to a particular vault as well only when requested.

Relay uses its own shipped settings for a new installation. Do not distribute
a copied `data.json`, feature-flag profile, or endpoint configuration as a
default. Account and shared-folder setup belongs to each vault.
