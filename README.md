Agent Skills for use with [Relay](https://relay.md), the real-time collaboration plugin for Obsidian.

## Installation

### Marketplace

```
/plugin marketplace add No-Instructions/relay-skills
/plugin install relay@relay-skills
```

### npx skills

```
npx skills add git@github.com:No-Instructions/relay-skills.git
```

Instead of ssh, if you prefer to use https:

```
npx skills add https://github.com/No-Instructions/relay-skills
```

### Manually

#### Claude Code

Add the contents of this repo to a `/.claude` folder in the root of your Obsidian vault (or whichever folder you're using with Claude Code). See more in the [official Claude Skills documentation](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).

#### Codex

Copy the `skills/` directory into your Codex skills path (typically `~/.codex/skills`). See the [Agent Skills specification](https://agentskills.io/specification) for the standard skill format.

## Requirements

The setup skills can prepare files before Obsidian is running. Their helpers
require Python 3.9 or later; installing through the Obsidian UI is also supported.
For the sync-status, conflict-resolution, and comment skills:

- Obsidian desktop 1.12.4 or later, with the command line interface enabled under Settings, General, Advanced.
- The [Relay](https://relay.md) plugin installed and enabled in the vault.
- Obsidian running with the vault open. The skills talk to the running app through the [Obsidian CLI](https://help.obsidian.md/cli).

## Skills

| Skill                          | Description                                                                                                                                    |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| [relay](skills/relay)                                  | What Relay is, and where the documentation, releases, source, and support live                                                                 |
| [obsidian-vault-setup](skills/obsidian-vault-setup)      | Create or configure a vault with editable JSON defaults for the editor, files, appearance, and core plugins                                     |
| [relay-setup](skills/relay-setup)                       | Install and enable Relay through Obsidian or from a published bundle, then complete account and shared-folder setup                              |
| [relay-self-hosting](skills/relay-self-hosting)         | Deploy a Relay Server on a private network with editable Compose and storage templates, then register it in Obsidian                            |
| [relay-obsidian-plugin](skills/relay-obsidian-plugin)  | Inspect Relay sync status and resolve sync conflicts in shared folders from the terminal, without opening notes, using the Obsidian CLI        |
| [relay-comments](skills/relay-comments)                | Review notes, suggest edits, and work comment threads through Relay Comments, using its Obsidian CLI commands                                    |

Vault settings live in [obsidian-vault-setup/assets/defaults](skills/obsidian-vault-setup/assets/defaults).
Community-plugin enablement lives in [relay-setup/assets/defaults](skills/relay-setup/assets/defaults).
Server deployment templates live in [relay-self-hosting/assets/deployment](skills/relay-self-hosting/assets/deployment).
Ask to update these defaults for future vaults, or apply a specific change to an
existing vault. Setup preserves existing settings unless overwriting them is
requested, and backs up files it changes.

## Versions

`main` describes the latest release of each plugin, and an agent that finds an older plugin upgrades it through the Obsidian CLI first. A skill for an older client line is frozen on a branch named after it, such as `relay-comments-0.4`, as a last resort for a plugin that cannot be upgraded. Each skill's own `Versions` section lists the branches.

For general vault operations from the terminal, pair these with the [obsidian-cli](https://github.com/kepano/obsidian-skills/tree/main/skills/obsidian-cli) skill from [obsidian-skills](https://github.com/kepano/obsidian-skills).

## Checking setup helpers

Run the setup checks against temporary vaults without launching Obsidian:

```sh
python3 -m unittest discover -s tests -v
```
