---
name: relay-comments
description: Collaborate on Obsidian notes through Relay Comments, the plugin that stores comments and suggested edits in the note as CriticMarkup. Use when asked to review a note, suggest edits, open or reply to a comment thread, resolve feedback, or accept and reject suggestions in a vault that uses Relay Comments.
metadata:
  version: "0.1.0"
---

# Relay Comments

Relay Comments is System 3's review plugin for Obsidian, plugin id `relay-comments`. It keeps comments, suggested edits, and highlights inside the note as plain [CriticMarkup](https://github.com/CriticMarkup/CriticMarkup-toolkit), so review state needs no server, syncs with anything that syncs text, and stays readable in any editor. People work in a review sidebar and hover previews; an agent works by editing the markup directly.

- Plugin listing: https://community.obsidian.md/plugins/relay-comments
- Source: https://github.com/No-Instructions/Relay-Comments

## Choose the role

Infer the role from the request and combine roles when needed:

- **Author**: create or revise the note itself.
- **Reviewer**: preserve the source text and propose changes with CriticMarkup.
- **Thread participant**: investigate, reply, challenge, clarify, or resolve feedback.

A request only to review or assess is read-only: report findings and wait for authorization before writing annotations. Never silently replace clean source text during a review.

## The marks

| Mark | Syntax |
|---|---|
| Addition | `{++inserted text++}` |
| Deletion | `{--removed text--}` |
| Replacement | `{~~old~>new~~}` |
| Highlight | `{==marked text==}` |
| Comment | `{>>comment text<<}` |

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

If you are writing on behalf of the user, always use their relay ID and author setting. If you are collaborating with the user using your own identity, then you may want to create an identity so every message you leave is attributable and consistent across sessions.

To create an identity, pick a random alphanumeric 15 digit id. pocketbase compatible.

Local identities can be registered in the plugin's settings file, `.obsidian/plugins/relay-comments/data.json` inside the vault, under `identities`. With the user's permission you may add the entry yourself.

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

Only `id` and `name` are required. `picture` is any image URL; use Relay's avatar service at `https://avatars.relay.md/?seed=<id>` for a stable avatar seeded with your URL-encoded id. The plugin reloads its settings when the file changes on disk; if the sidebar still shows the plain name, reload the plugin.

This directory lives in the vault's local plugin settings and does not travel through Relay, so it resolves your identity only on that machine. Other collaborators see your `author` name, which is why the name must stand on its own.

## Review as a peer

1. Read the complete note and whatever evidence its claims rest on. Review the argument, not only the prose.
2. Prioritize incorrect or unsupported claims, missing implications, unclear decisions, and stale status over style.
3. Use the narrowest mark that communicates the change: a replacement for a local rewrite, separate addition and deletion marks only when the changes belong in different places.
4. Open a comment when the author must answer a question, decide something, supply evidence, or act. Highlight the passage so the anchor is unambiguous.
5. Attach a comment to a suggestion only when its reasoning matters. Do not restate the visible diff.
6. Preserve the author's voice and intent unless the review explicitly challenges them.
7. Do not nest CriticMarkup, split a Markdown delimiter, or annotate inside an existing mark. Reply to the existing thread instead.

## Respond and resolve

When a collaborator has changed the note, read the whole note and every thread before acting, not just the changed lines. Treat every contribution as peer input, not automatically as truth.

- Answer a question in the note when the answer belongs in the durable text. Remove the thread only after the note carries the answer.
- Complete a requested action before resolving its thread. Do not resolve by restating the request.
- Resolving a highlight thread keeps the highlighted text and removes the highlight delimiters plus every attached comment.
- Resolving a standalone comment thread removes the whole comment run.
- Accepting or rejecting a suggestion applies that outcome and removes its attached comments. To close only the discussion, remove the comments and keep the suggestion mark.
- The plugin's `Finalize for publish` command accepts every remaining suggestion at once; use it only when the author has asked for that.
- Re-read the clean note afterward for contradictions, unsupported claims, and stale status.

## Respond quickly to owned notes

When a collaboration is live, watch the notes you own, the ones you authored or were asked to follow, and act as soon as their review marks change instead of waiting to be prompted. Ordinary typing in the note is not a signal; a new comment, a reply, a resolved thread, or a suggested edit is.

`scripts/review_watch.py` in this skill's directory does that filtering. It watches the notes' parent directories with inotify on Linux, with nothing to install, and polls every half second where inotify is unavailable. It ignores edits that leave the CriticMarkup unchanged, prints one JSON line when a mark is added or removed, and exits. It needs only Python 3.8.

```sh
python3 scripts/review_watch.py path/to/note.md [more notes...] [--timeout SECONDS]
```

Wait for the `ready` line before telling the user the note is being watched. A `changed` line names the note and lists the added and removed marks with their kind, line, and text, which is enough to decide whether the change is addressed to you. Then read the whole note and every thread, respond and resolve as above, and run the watcher again to re-arm it. Use `--timeout` only when the user asked for a bounded window, and `--any-change` if they want you to react to every edit. Do not create sidecar or registry files in the vault to track state.

## Keep discussion and artifact separate

CriticMarkup is the temporary collaboration surface. A finished note carries no reviewer dialogue, agent replies, or task narration. Report workflow status in the conversation, not in the note, unless status is the note's subject.
