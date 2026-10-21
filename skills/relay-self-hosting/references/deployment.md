# Docker deployment on a private network

This Compose layout adapts the public
[Docker and private-VPN guide](https://github.com/No-Instructions/relay-server-template/blob/main/guides/docker-s3-custom.md).
It runs the published image with `/app/relay.toml` mounted read-only and exposes
port 8080 on the host's loopback interface. The host supplies private networking
and HTTPS; the container does not join a VPN itself.

## Prepare the files

Choose a deployment directory outside the vault. Copy the assets using the
filename mapping in the skill. Preserve existing files and review changes when
adapting a deployment. Set permissions on the credentials file before filling
it, for example `chmod 600 auth.env` on Unix. Use the user's credential manager
or a local edit, and do not print the populated file.

Configure these values:

- `.env`: the published Relay Server image, host binding, and host port.
- `relay.toml`: the URL clients will use, public auth keys, and storage block.
- `auth.env`: credentials scoped to the selected storage bucket.

Use the current key set from the public
[configuration example](https://github.com/No-Instructions/relay-server-template/blob/main/relay.toml.example).
Do not generate replacement signing keys: the server verifies tokens issued
by Relay's Control Plane. Keep the advertised URL consistent with registration.

The default storage block uses AWS S3. Set the existing bucket's name and
region, and choose a stable prefix dedicated to this deployment. For R2,
replace that block with [store-r2.toml.example](../assets/deployment/store-r2.toml.example)
and fill the account and bucket identifiers. Both use the AWS credential
variable names in `auth.env`. Read the public
[R2 guide](https://github.com/No-Instructions/relay-server-template/blob/main/guides/docker-r2-custom.md)
when configuring the provider. Other S3-compatible providers have their own
blocks in the public example; use the one matching the chosen image.

For a document-only evaluation, use
[store-local.toml.example](../assets/deployment/store-local.toml.example).
The Compose volume persists `/app/data` across container recreation. Local
storage does not provide attachment storage; use S3-compatible persistence for
attachments and production. Keep an empty `auth.env` file for the local option.

Clients must also reach the object-storage URLs used for attachments. For a
private S3-compatible service, its advertised endpoint must resolve and be
reachable from every collaborating device, not just the server container.
Verify provider CORS requirements when testing uploads and downloads. Keep the
bucket private; making objects public is not a connectivity fix.

## Private HTTPS

With Tailscale already configured on the host and client devices, inspect the
host's existing Serve configuration before adding a route:

```sh
tailscale serve status
tailscale serve --bg http://127.0.0.1:8080
tailscale serve status
```

Use the HTTPS hostname reported by Serve as `[server].url`. If the chosen host
port differs, update the proxy target as well. Keep existing services intact
when choosing a port or route. Tailscale Serve provides tailnet access; Funnel
publishes services to the internet and is not the deployment path here. Follow
the [Tailscale Serve reference](https://tailscale.com/docs/reference/tailscale-cli/serve)
for prerequisites and access rules.

For a corporate VPN, use its private DNS name and existing HTTPS reverse
proxy. The proxy must handle WebSocket upgrades and preserve request paths.
All collaborators must trust the certificate. Keep the loopback binding when
the proxy runs on the same host. A remote proxy needs an explicit private
interface binding and firewall rules allowing that proxy. Do not change the
binding to all interfaces merely to resolve connectivity.

## Validate and start

Replace every `YOUR-...` placeholder before starting. Parse `relay.toml` with a
TOML parser; check there is one storage block and the current public auth keys.
With Python 3.11 or later, a syntax check without displaying settings is:

```sh
python3 -c 'import pathlib,tomllib; tomllib.loads(pathlib.Path("relay.toml").read_text())'
docker compose config --quiet
```

Do not paste expanded `docker compose config` or container environment output
into chat: it can contain credentials. Resolve the published image before a
persistent deployment:

```sh
docker compose pull relay
docker image inspect docker.system3.md/relay-server:latest --format '{{json .RepoDigests}}'
```

If `.env` names a different published tag, inspect that tag. Set
`RELAY_SERVER_IMAGE` to the selected `docker.system3.md/relay-server@sha256:...`
digest in `.env`, then validate again. Retain the digest when recreating the
deployment; changing it is an upgrade.

Start the configured service within the requested deployment scope:

```sh
docker compose up -d relay
docker compose ps
curl --fail --silent --show-error http://127.0.0.1:8080/ready
```

Use the configured host port. From an intended client on the VPN, repeat the
check against the private HTTPS URL, for example:

```sh
curl --fail --silent --show-error https://relay.YOUR-TAILNET.ts.net/ready
```

The [server API](https://github.com/No-Instructions/relay-server/blob/main/openapi.yaml)
defines `/ready` as an HTTP health check. It does not exercise object storage.
Complete server registration and a collaboration/attachment check in Obsidian
as described in the skill. If a check fails, inspect bounded server logs,
the proxy route, advertised URL, auth keys, and storage configuration for that
failure. Report relevant error messages with credentials and signed URLs removed.

## Persistence and recovery

Back up the configuration and record the image digest. Keep credentials in the
user's secret store. For S3-compatible storage, use the provider's backup or
versioning facilities for the deployment's bucket/prefix. For local storage,
stop the service before taking a consistent volume backup and restart it
afterward. A restart is not a persistence test; verify content from a fresh
client or another existing client after the server returns.

Do not delete the volume or change the bucket/prefix during routine updates.
Keep the prior image and a restorable data backup before upgrading. Check
upstream compatibility guidance before rolling an image back against data
written by another version. Restoring shared data can affect every collaborator;
coordinate the recovery and stop writers before restoring it.
