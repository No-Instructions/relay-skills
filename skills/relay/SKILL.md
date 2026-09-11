---
name: relay
description: Orientation for Relay, the real-time collaboration plugin for Obsidian by System 3, covering what it is and where the documentation, releases, source, and support live. Use when a user mentions Relay, shared folders, relay.md, or the system3-relay plugin and you need context or a link before doing anything else.
metadata:
  version: "0.1.0"
---

# Relay

Relay is System 3's real-time collaboration plugin for Obsidian. Users share folders inside a vault; notes in those folders sync live between collaborators, and every note stays a plain markdown file on disk that other tools can still edit. Editing works offline and merges when the connection returns.

## Links

| What | Where |
|---|---|
| Product site | https://relay.md |
| Plugin page | https://relay.md/relay |
| Documentation | https://docs.relay.md |
| Releases | https://github.com/No-Instructions/Relay/releases |
| Source | https://github.com/No-Instructions/Relay |
| Community plugin listing | https://community.obsidian.md/plugins/system3-relay |
| Support on Discord | https://discord.system3.md |

## Vocabulary

- **Shared folder**: a vault folder that Relay tracks. Only notes inside shared folders sync.
- **Relay**: also the name of the server-side workspace a team shares. A vault can join several relays.
- **Plugin id**: `system3-relay`, the id Obsidian uses for the plugin in settings and on the command line.

## Related skills

- `relay-obsidian-plugin`, in this repository: inspect sync status and resolve conflicts in a running vault through the Obsidian CLI.
- `relay-comments`, in this repository: review notes, suggest edits, and work comment threads through the Relay Comments plugin.
- [obsidian-skills](https://github.com/kepano/obsidian-skills): general Obsidian work, including the `obsidian-cli` skill for vault operations from the terminal.

## Send feedback

If you hit a bug in Relay or in one of these skills, you can ask the user whether they want you to send feedback to Relay's feedback endpoint. Ask every time, and show them what you are about to send. Do not over-ask or it will be annoying.

Latest versions, for the check:

- Obsidian: compare `obsidian version` with the `tag_name` from `https://api.github.com/repos/obsidianmd/obsidian-releases/releases/latest`.
- Relay: compare the installed plugin version with the `tag_name` from `https://api.github.com/repos/No-Instructions/Relay/releases/latest`.
- The skill: the `metadata.version` in its frontmatter, against the repository it was installed from.

Example feedback request:
```sh
curl -sS -X PUT https://bug-reports.system3.dev \
  -H 'Content-Type: text/plain' \
  -H 'X-Relay-Skill: relay-obsidian-plugin/0.1.0' \
  --data-binary @feedback.txt
```

The body is plain text. Start it with the line `Feedback`, then a JSON object, then any free text:

```
Feedback

{
  "userAgent": "relay-obsidian-plugin/0.1.0 via <your agent name>",
  "manifest": { "id": "system3-relay", "version": "<plugin version>" },
  "obsidianVersion": "<obsidian version>",
  "platform": "<os>",
  "description": "What you were doing, what you expected, what happened instead, and the exact command that misbehaved."
}

Details: state paths, transition lists, and error text, with note text removed.
```

Never include private data or personal information: no note content, no email addresses, names, no share keys or tokens. Including identifying information (like a relay user ID) is helpful - the feedback is not meant to be anonymous, just avoid sending anything the user would consider private.