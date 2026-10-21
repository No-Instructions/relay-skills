---
name: relay-self-hosting
description: Set up a self-hosted Relay Server on a private network, configure persistent storage and HTTPS, register it in Obsidian, and verify collaboration. Use for Relay server deployment, self-hosted connection troubleshooting, or changes to the reusable deployment templates.
metadata:
  version: "0.1.0"
---

# Self-host Relay

Use the public [Relay Server template](https://github.com/No-Instructions/relay-server-template)
as the deployment reference. The [server source](https://github.com/No-Instructions/relay-server)
and [hosting guide](https://docs.relay.md/guides/choose-how-to-host-relay/)
explain the supported architecture. Recheck these when deploying: image
releases, configuration fields, and the public signing-key set can change.

Self-hosting runs the content server and storage on infrastructure the user
controls. Relay's hosted Control Plane still supplies accounts and permissions.
It is not an air-gapped installation. Keep the content server on the user's
private network or VPN; this network boundary is part of Relay's privacy model.
See [what Relay can see](https://docs.relay.md/how-relay-works/what-relay-can-see/).

## Establish the deployment

Use the host, VPN, storage provider, and server URL already specified by the
user. Inspect an existing deployment before changing it. Ask only for missing
choices that affect the result; prepare configuration while access or answers
are pending. A request to create deployment files does not also request cloud
resource creation, server registration, or sharing existing notes.

For a new Docker deployment, read [references/deployment.md](references/deployment.md).
The bundled configuration uses a loopback listener, a private HTTPS proxy on
the host, and S3 persistence. Tailscale Serve is one supported proxy option.
An existing corporate VPN and HTTPS proxy can use the same server configuration.
For Fly.io, Kubernetes, or a VPN inside the container, follow the corresponding
guide in the public server-template repository instead of assuming this Compose
layout applies.

Prepare a separate deployment directory outside the vault. Copy the relevant
files from [assets/deployment](assets/deployment) without overwriting existing
configuration:

| Asset | Deployment file | Purpose |
| --- | --- | --- |
| `compose.yaml` | `compose.yaml` | Container, network binding, config mount, and local data volume |
| `env.example` | `.env` | Image reference, bind address, and host port |
| `auth.env.example` | `auth.env` | Storage credentials, filled only in the deployment directory |
| `relay.toml.example` | `relay.toml` | Advertised URL, public verification keys, and storage backend |
| `store-r2.toml.example` | Merge into `relay.toml` | Alternative R2 storage block |
| `store-local.toml.example` | Merge into `relay.toml` | Local document persistence for an evaluation |
| `gitignore.example` | `.gitignore` | Excludes credentials and local state |

For a storage alternative, replace the existing `[store]` block; do not append
a second block. Keep reusable assets free of actual domains, credentials,
bucket names, and account-specific identifiers. The bundled signing keys are
public verification keys, not secrets; compare them with upstream before use.

## Configure, deploy, and register

Follow the deployment reference to resolve the image, validate configuration,
start the service within the user's authorized scope, and test the URL from
a client on the VPN. The URL advertised by `[server].url` must match the URL
used by clients, including HTTPS and any nonstandard port. A container address
or `localhost` is not a usable advertised address for other devices.

In the user's target vault, install and enable Relay if necessary using
`relay-setup` when available, or Obsidian's community-plugin browser. Sign in,
then run **Relay: Register self-hosted Relay Server** from the command palette.
Enter the same server URL. This registers a server with the Control Plane;
it does not replace the plugin's global endpoints or authenticate by copying
another vault's `data.json`.

If driving Obsidian through the CLI, discover the installed command id with
`obsidian vault="My Vault" commands filter=system3-relay`, then run the
matching registration command. Complete its dialog in the UI. Do not invent
a debug API call or guess a command id.

Select this server when sharing the folder the user requested. Registering a
new server does not migrate existing shared folders to it. Treat migration
as separate work: preserve the original until transfer and collaboration have
been verified. Never change a populated storage prefix as a migration shortcut.

## Verify and hand off

Check the server responds at `/ready` from an intended client, then verify
registration and a test shared folder in Obsidian. When authorized, edit a
disposable note from two connected devices/vaults and confirm both directions.
For attachment storage, transfer a small file inside that shared folder and
open it from the other device. A passing `/ready` check only proves HTTP
reachability, not authentication, persistence, WebSockets, or attachment access.

Report the deployment directory, image reference, server URL, storage backend,
and what was verified. Identify unfinished access, sign-in, or second-device
checks without reporting successful collaboration prematurely. Omit secrets
and signed attachment URLs from the report.

## Maintain defaults and deployments

Edit the assets for requested reusable-default changes. Keep per-deployment
values in that deployment's files. Validate Compose and TOML after edits.
For an upgrade, retain the prior image reference and a restorable storage
backup, consult the image's release guidance, and repeat the connection and
sync checks. Keep storage volumes and bucket prefixes intact during ordinary
restarts and upgrades; do not use `docker compose down --volumes`.
