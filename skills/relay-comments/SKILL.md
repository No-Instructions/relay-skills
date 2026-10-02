---
name: relay-comments
description: Collaborate on Obsidian notes through Relay Comments, the plugin that stores comments and suggested edits in the note as CriticMarkup. Use when asked to review a note, suggest edits, open or reply to a comment thread, resolve feedback, or accept and reject suggestions in a vault that uses Relay Comments.
metadata:
  version: "0.3.0"
---

# Relay Comments

Relay Comments is System 3's review plugin for Obsidian, plugin id `relay-comments`. It keeps comments, suggested edits, and highlights inside the note as plain [CriticMarkup](https://github.com/CriticMarkup/CriticMarkup-toolkit), so review state needs no server, syncs with anything that syncs text, and stays readable in any editor. People work in a review sidebar and hover previews; an agent works through the plugin's commands on the [Obsidian CLI](https://help.obsidian.md/cli), and falls back to editing the markup directly when the CLI is not available.

- Plugin listing: https://community.obsidian.md/plugins/relay-comments
- Source: https://github.com/No-Instructions/Relay-Comments

## Versions

This skill describes Relay Comments 0.5.0 and later. If the plugin is out of date, update it.
In order to upgrade Relay Comments, follow the procedure below:
```sh
obsidian vault=<name> eval code="(async () => { await app.plugins.checkForUpdates(); const u = app.plugins.updates['relay-comments']; if (!u) return 'up to date'; await app.plugins.installPlugin(u.repo, u.version, u.manifest); return 'installed ' + u.version; })()"
obsidian vault=<name> plugin:reload id=relay-comments
obsidian vault=<name> comments --json
```

Confirm the version in the last answer and tell the user the plugin was upgraded. If you are unable to upgrade, or the user has pinned the version, then you can find old documentation by reading the relay-skills repo's branches and selecting the appropriate version (e.g. `relay-comments-0.4`).

## Choose your role

Infer the role from the request and combine roles when needed:

- **Author**: create or revise the note itself.
- **Reviewer**: preserve the source text and propose changes with CriticMarkup.
- **Thread participant**: investigate, reply, challenge, clarify, or resolve feedback.

## Reach the plugin from the terminal

The plugin registers a `comments` command family with the Obsidian CLI. It needs Obsidian desktop 1.12.4 or later with the command line interface enabled under Settings, General, Advanced, and Obsidian running with the vault open. The same commands work on Windows, macOS, and Linux; only the shell quoting differs.

Always pass the vault first, then the command, then `key=value` parameters. Add `--json` for machine output. The CLI exits 0 whatever happened, so read `ok` in the JSON envelope; a failure carries `code` and `message`.

Use the top level `--help` command to discover usage information. The CLI is self-documenting.

```sh
obsidian vault=<name> comments --help
```

## The marks

When the CLI is unavailable you edit the markup directly. The commands write exactly these forms.

| Mark | Syntax |
|---|---|
| Addition | `{++inserted text++}` |
| Deletion | `{--removed text--}` |
| Replacement | `{~~old~>new~~}` |
| Highlight | `{==marked text==}` |
| Comment | `{>>comment text<<}` |

A highlight or comment anchors to text, never to a line's block syntax. Write `## {==Heading==}` and `- {==item==}`, not `{==## Heading==}`: a mark around the hashes or bullet turns the line into a paragraph, and Obsidian's own `==highlight==` parser can then run a highlight down the rest of it.

A comment attached to a native highlight is written immediately after it without converting it.

A comment can carry identity metadata:

```text
{==the passage==}{{authorId="service-user-id" author="Bongo Cat" date="2026-07-13T07:01:55.123Z">>Can we ground this sooner?<<}}
```

`authorId` is an opaque id from the identity provider (typically relay), `author` is the display name, and `date` is an ISO-8601 timestamp. When only a name is available, store it in `author` and omit `authorId`.

## Threads

An anchor followed by adjacent comments is one ordered thread. The anchor may be a highlight, a suggestion, or a comment. Marks written back to back belong together; a single line break between them still parses as one thread; text or a blank line ends it.

```text
{==passage==}{{authorId="user-id" author="Reviewer" date="2026-07-13T07:01:55.123Z">>question<<}}{{author="Claude" date="2026-07-13T07:10:00.000Z">>reply<<}}
```

- Read every message in order. Later replies may correct or narrow the opening comment.
- Preserve existing comment bodies, attribution, dates, and ordering while the thread stays open.
- Append a reply after the final message, not after the anchor. Use your product name as `author`, add the current UTC timestamp as `date`, and omit `authorId` unless you hold a real identity from the provider. Never copy or invent a human's `authorId`.
- Keep replies concise and free of nested CriticMarkup. Use single quotes inside metadata values and avoid `<<}` in comment text.
- Reply when useful even if you did not author the note: supply evidence, disagree, ask a narrower question, or offer an authorized action.

## Agent identity

If you are writing on behalf of the user, always use their relay ID and author setting; that is what the CLI does by default. If you are collaborating with the user using your own identity, create an identity so every message you leave is attributable and consistent across sessions, then pass its id or name as `author=` on every write.

To create an identity, pick a random alphanumeric 15 digit id. pocketbase compatible.

Local identities are registered in the plugin's settings file, `.obsidian/plugins/relay-comments/data.json` inside the vault, under `identities`. Add the entry yourself and mention it.

```json
{
  "identities": [
    {
      "id": "mqvxlopr0ocsmgv",
      "name": "Claude",
      "picture": "https://avatars.relay.md/?seed=mqvxlopr0ocsmgv",
      "color": "#7c3aed",
      "colorLight": "#7c3aed33"
    }
  ]
}
```

Only `id` and `name` are required. `picture` is any image URL; use Relay's avatar service at `https://avatars.relay.md/?seed=<id>` for a stable avatar seeded with your URL-encoded id. The plugin reloads its settings when the file changes on disk.

This directory lives in the vault's local plugin settings and does not travel through Relay, so it resolves your identity only on that machine. Other collaborators see your `author` name, which is why the name must stand on its own.

## Review as a peer

1. Read the complete note and whatever evidence its claims rest on. Review the argument, not only the prose.
2. Prioritize incorrect or unsupported claims, missing implications, unclear decisions, and stale status over style.
3. Use the narrowest mark that communicates the change: `suggest ... replace=` for a local rewrite, `--delete` or `insert=` only when the change is one-sided.
4. Open a comment when the author must answer a question, decide something, supply evidence, or act. Quote the passage so the anchor is unambiguous.
5. Attach a comment to a suggestion only when its reasoning matters. Do not restate the visible diff.
6. Preserve the author's voice and intent unless the review explicitly challenges them.
7. Do not nest CriticMarkup, split a Markdown delimiter, or annotate inside an existing mark. Reply to the existing thread instead.

## Respond and resolve

When a collaborator has changed the note, read the whole note and every thread before acting, not just the changed lines. Treat every contribution as peer input, not automatically as truth.

- Answer a question in the note when the answer belongs in the durable text. Resolve the thread only after the note carries the answer.
- Complete a requested action before resolving its thread. Do not resolve by restating the request.
- Resolving a highlight thread keeps the highlighted text and removes the highlight delimiters plus every attached comment.
- Resolving a standalone comment thread removes the whole comment run.
- Accepting or rejecting a suggestion applies that outcome and removes its attached comments. To close only the discussion, resolve the thread and the suggestion mark stays.
- The plugin's `Finalize for publish` command accepts every remaining suggestion at once; use it only when the author has asked for that.
- Re-read the clean note afterward for contradictions, unsupported claims, and stale status.

## Respond quickly to owned notes

When a collaboration is live, watch the notes you own, the ones you authored or were asked to follow, and act as soon as their review marks change instead of waiting to be prompted. Ordinary typing in the note is not a signal; a new comment, a reply, a resolved thread, or a suggested edit is.

`comments:watch` blocks until the next such change in its `path=` (a note, a canvas, or a folder) and prints it with a cursor. On a canvas, a comment thread is a `pin` mark with the node id and whether it is resolved, and each message in it is a `comment` mark; resolving a pin shows as the open pin removed and the resolved pin added. Watch the narrowest scope that covers your notes: the plugin only reads and parses notes inside watched scopes. Pass your own author name as `ignore-author=` so your replies do not wake you, and `kind=` if only some marks matter.

```sh
obsidian vault=<name> comments:watch path="Projects/plan.md" ignore-author=Claude since=<cursor> timeout=590 --json
```

Take the first cursor from `comments --json`. Each call returns once, so run it again with the cursor it printed; anything that happened in between comes back on the next call. Where your harness can run a command in the background and wake you when it exits, as Claude Code can, start `watch` that way and do nothing until it returns. Otherwise run it in the foreground with a `timeout=` under your harness's limit on a command. Do not wrap it in a shell loop.

Each event names the note and the marks added and removed with kind, line, readable text, and author. Then read the whole note and every thread, respond and resolve as above, and watch again. `timedOut: true` with no events means the window passed quietly; watch again with the same cursor. `gap: true` means events older than your cursor were dropped, so list the threads to catch up.

When Obsidian is not running or the plugin predates the CLI, `scripts/review_watch.py` in this skill's directory does the same filtering against the files: inotify on Linux, polling elsewhere, one JSON line when a mark changes, then it exits. It needs only Python 3.8.

```sh
python3 scripts/review_watch.py path/to/note.md [more notes...] [--timeout SECONDS]
```

Wait for its `ready` line before telling the user the note is being watched, and run it again to re-arm it. Do not create sidecar or registry files in the vault to track state.

## Keep discussion and artifact separate

CriticMarkup is the temporary collaboration surface. A finished note carries no reviewer dialogue, agent replies, or task narration. Report workflow status in the conversation, not in the note, unless status is the note's subject.
