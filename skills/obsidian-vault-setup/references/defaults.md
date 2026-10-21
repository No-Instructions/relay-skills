# Vault defaults

The JSON files in [assets/defaults](../assets/defaults) are the source of truth.
Their names match the destination files in the vault's configuration folder.
Settings not listed there use Obsidian's own defaults.

| File | Purpose |
| --- | --- |
| `app.json` | Editor behavior, file placement, links, deletion, and settings window |
| `appearance.json` | Inline note titles and the ribbon |
| `core-plugins.json` | Built-in plugin enablement, as a map of plugin ids to booleans |

The profile uses Live Preview, readable lines, line numbers, folding, and
spellcheck. New notes stay in the current folder. Wikilinks update when files
are renamed. Settings open within the vault window. Deletion asks for
confirmation and moves files to the vault's `.trash` folder.

Attachments go into `./Attachments`, a subfolder beside the current note.
Keeping attachments inside the same shared folder as the note makes them
available to Relay; attachment sync also requires storage on the Relay server.
This setting only affects new attachments and does not move existing files.
See [Relay's attachment guidance](https://docs.relay.md/guides/set-attachment-location/).

Core plugins cover navigation, search, links, daily notes, templates, Canvas,
Bases, properties, and file recovery. Publish and Obsidian Sync start disabled
in a fresh vault. Existing choices remain intact unless an overwrite is
requested. Daily notes and templates retain their own default paths; the
profile does not impose a folder hierarchy. File recovery and trash are local
recovery aids, not a backup of a shared folder's remote history.

## Applying settings

The helper accepts these three filenames, including a subset for targeted
updates. Each supplied file must be a JSON object. Core-plugin values must be
booleans. Object settings merge recursively: existing values win by default;
`--overwrite` makes supplied values win. Unspecified keys remain untouched.

An existing core-plugin array is also supported. Its absent ids are disabled,
so the helper preserves the array by default. With `--overwrite`, it applies
only the enable/disable choices named in the supplied profile, retaining other
ids. Malformed configuration causes an error before any files are written.

`--dry-run` lists filenames that would change without creating the vault or
backups. Changed existing files are copied into
`<config-dir>/setup-backups/<unique-run>/` before replacement. To restore them,
close the vault and copy the needed files back to their original names. Newly
created files have no previous copy. The helper does not register the vault,
change application-wide settings, or open Obsidian.

For settings meanings, see [Obsidian settings](https://help.obsidian.md/settings)
and [core plugins](https://help.obsidian.md/plugins). JSON keys are Obsidian's
on-disk format; verify unfamiliar keys in the installed app when extending the
profile.
