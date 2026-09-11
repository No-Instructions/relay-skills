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

- Obsidian desktop 1.12.4 or later, with the command line interface enabled under Settings, General, Advanced.
- The [Relay](https://relay.md) plugin installed and enabled in the vault.
- Obsidian running with the vault open. The skills talk to the running app through the [Obsidian CLI](https://help.obsidian.md/cli).

## Skills

| Skill                          | Description                                                                                                                                    |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| [relay](skills/relay)                                  | What Relay is, and where the documentation, releases, source, and support live                                                                 |
| [relay-obsidian-plugin](skills/relay-obsidian-plugin)  | Inspect Relay sync status and resolve sync conflicts in shared folders from the terminal, without opening notes, using the Obsidian CLI        |
| [relay-comments](skills/relay-comments)                | Review notes, suggest edits, and work comment threads through Relay Comments, which stores review state in the note as CriticMarkup           |

For general vault operations from the terminal, pair these with the [obsidian-cli](https://github.com/kepano/obsidian-skills/tree/main/skills/obsidian-cli) skill from [obsidian-skills](https://github.com/kepano/obsidian-skills).
