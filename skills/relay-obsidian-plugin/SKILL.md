---
name: relay-obsidian-plugin
description: Inspect Relay sync status and resolve Relay sync conflicts from a terminal through the Obsidian CLI, without opening notes. Use when a user asks about Relay sync state, about shared notes that are stuck or conflicted, or wants an agent to resolve conflicts on their behalf.
metadata:
  version: "0.1.1"
---

# Relay from the terminal

Relay keeps shared folders converged through a per-note sync machine, and it exposes that machine on a debug object in the vault window. The Obsidian CLI can evaluate JavaScript inside a running vault, so an agent can read sync state and resolve conflicts from a shell without touching the editor.

## Reaching the vault

- **Obsidian desktop 1.12.4 or later**, 1.12.7 or later preferred. Check with `obsidian version`. There is no mobile path.
- **Enable the CLI** in Settings, General, Advanced, "Command line interface". That toggle also installs the `obsidian` command. Every command answers with a fixed message until it is on.
- **Obsidian must be running** with the vault open. Always pass the vault as the first argument, `vault=<name>`, where the name is the vault folder name. Without it the CLI picks the vault containing the working directory, or the last active one.
- **Invocation shape**:

  ```sh
  obsidian vault=<name> eval code='<one JavaScript expression>'
  ```

  Single-quote the code and use double quotes inside it. A returned Promise is awaited. Top-level `await` is not available, so wrap sequences in `(async()=>{ ... })()`.
- **Reading output**. Objects print as JSON after a `=> ` prefix, strings print verbatim after the same prefix, `undefined` prints `(no output)`, and a thrown error prints `Error: <message>`. The exit code is always 0, so parse the text and never trust `$?`.
- **Empty output on a slow call** means the shell is using the Electron shim instead of the native client. The client installed by the settings toggle is native. A hand-made symlink to the app binary is not.
- **Confirm Relay is loaded** before anything else:

  ```sh
  obsidian vault=<name> eval code='app.plugins.plugins["system3-relay"].manifest.version'
  ```

## Debug API discovery

The debug object is `window.__relayDebug`. Explore when a documented call is missing, throws "is not a function", or returns a shape the workflow does not expect, and report any such difference to the user together with the plugin version.

- **List functions with their parameter counts**:

  ```sh
  obsidian vault=<name> eval code='Object.entries(window.__relayDebug).filter(([k,v])=>typeof v==="function").map(([k,v])=>k+"/"+v.length).join(" ")'
  ```

- **Paths** are vault-level with a leading slash and include the shared folder, for example `/Home/beeps/note.md`.
- **Read-only calls**, safe to run at will: `listSyncPanelStatus`, `getSyncPanelStatus`, `getFolderSyncStatus`, `getFolderSyncErrors`, `getFolderConflicts`, `listAllConflicts`, `getConflictInfo`, `getHsmStateSnapshot`, `getIdbContent`, `getIdbHistory`, `getIdbFork`, `awaitHsmState`, `lookupDocument`, `lookupFolder`, `getSessionLogs`. Two of them reach the network and attach the note server-side, so call them deliberately rather than in loops: `getDocumentContent` and `getCanvasContent`.
- **Mutating calls** the workflow uses, each on one note the user has asked about: `resolveHunk`, `resolveConflict`.
- **Never call** the rest without a full reference to the relay source code (read and understood) and an explicit instruction from the user. `clearLca`, `setEditorContent`, `closeEditor`, `createRelay`, `renameRelay`, `deleteRelay`, `acceptRelayShareKey`, and the recording functions change state that is not the user's conflict.
- **Raw snapshots are large.** `getHsmStateSnapshot` carries three full copies of the note text and `getConflictInfo` carries base, ours, and theirs in full. Project the fields you need inside the expression instead of printing whole objects.

## Writing expressions

- Alias the debug object at the start of longer expressions: `(()=>{const rd=window.__relayDebug; ...})()`.
- Objects and arrays print as indented JSON, which is readable but long. Wrap the result in `JSON.stringify(...)` when you only need to parse it, since strings print on one line.
- Project inside the expression. Return the two or three fields you will act on, not the whole snapshot.
- **Repeated operations.** If you will run the same shape of call many times, register your own small helpers once per Obsidian session on `window.__helper`, as thin projections over the debug object, and call those instead. They cost one install and vanish when Obsidian restarts, so keep them to what the session needs.

## Workflow: resolving conflicts

Replace `P` with the quoted note path throughout.

1. **Find the work.** Folder status as the sync pane shows it, then the flat list of conflicted notes:

   ```sh
   obsidian vault=<name> eval code='JSON.stringify(window.__relayDebug.listSyncPanelStatus().map(p=>[p.folderPath,p.snapshot.label,p.queue.total,p.actionableFiles.map(f=>[f.category,f.path,f.label])]))'
   obsidian vault=<name> eval code='JSON.stringify(window.__relayDebug.listAllConflicts().map(c=>c.path))'
   ```

   The actionable rows are conflicts and errors, each with the label the user would see.

2. **Read one conflict.**

   ```sh
   obsidian vault=<name> eval code='window.__relayDebug.getConflictInfo(P).then(i=>JSON.stringify({state:i.statePath,ours:i.oursLabel,theirs:i.theirsLabel,resolved:i.resolvedHunkCount+"/"+i.hunkCount,hunks:i.hunks.map(h=>[h.id,h.resolved,h.oursContent,h.theirsContent])}))'
   ```

   Example answer:

   ```json
   {"state":"idle.conflict","ours":"Local","theirs":"Local file","resolved":"0/1","hunks":[["16",false,"","\n\nfasdf no double coverage"]]}
   ```

   Read the labels before choosing a side. `theirs` is always the file on disk. `ours` is the note's collaborative copy, labelled "Local" when the conflict is between disk and the local copy, and "Remote" when it is between disk and what other people wrote. A three-way conflict also carries a shared `base`; a two-way one has none. Hunk ids are stable strings, so pass them back exactly as printed. On a long note, slice the hunk text in the projection for triage, then fetch the full hunk before deciding.

3. **Decide, then resolve per hunk, through the editor.** Open the note first, so the resolution runs through the editor's conflict view rather than the closed-note path; on plugin versions up to 0.8.12 the closed-note path can silently revert a resolution when the conflict came from an edit made while the folder was disconnected. The editor path holds on every version.

   ```sh
   obsidian vault=<name> eval code='(async()=>{const rd=window.__relayDebug;const h=await rd.openEditor(P);await rd.awaitHsmState(P,"active.conflict.bannerShown",15000);await rd.openDiffView(P);const state=await rd.resolveHunk(P,"16","theirs");await rd.closeEditor(h.handle);return JSON.stringify({state})})()'
   ```

   `ours` keeps the collaborative copy, `theirs` keeps the disk text, `both` keeps ours then theirs, `neither` drops the region. When the wanted result is neither side verbatim, compose the text and call `resolveConflict(P, contents)` in place of `resolveHunk` in the same sequence. The state after a resolve starts with `active.`; closing the editor settles it to `idle.`. A note that is already open in the user's editor needs only the diff view and the resolve; do not close their tab.

4. **Verify.** State, conflict flag, merge base, and whether disk matches the local store:

   ```sh
   obsidian vault=<name> eval code='window.__relayDebug.getHsmStateSnapshot(P).then(s=>JSON.stringify([s.statePath,s.hasConflict,s.hasLCA,s.diskMatchesIdb]))'
   ```

   Expect `["idle.synced",false,true,true]` once the last hunk is resolved. While hunks remain the state stays `idle.conflict`; go back to step 2. Then read the note back and compare it to the side you chose, not just to the server: a reverted resolution leaves disk, store, and server agreeing with each other on the unresolved text.

   ```sh
   obsidian vault=<name> eval code='window.__relayDebug.getDocumentContent(P).then(d=>JSON.stringify({disk:d.disk&&d.disk.content}))'
   ```

   To confirm the server copy as well, at the cost of one download:

   ```sh
   obsidian vault=<name> eval code='window.__relayDebug.getDocumentContent(P).then(d=>JSON.stringify({serverMatchesDisk:!!d.server&&!!d.disk&&d.server.content===d.disk.content}))'
   ```

   A resolution made while the note is closed can leave the server copy behind until the note next connects, even though local status already reads synced. If the server check says false, ask the folder to converge the note, then run the server check again:

   ```sh
   obsidian vault=<name> eval code='(()=>{const l=window.__relayDebug.lookupDocument(P);return l.folder.backgroundSync.enqueueSync(l.doc)})()'
   ```

5. **Report back** with the path, the side chosen per hunk and why, and the final state. Leave any note whose hunks you cannot judge unresolved and say so.
