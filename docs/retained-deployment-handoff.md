# Retained YouTrack deployment handoff

**Purpose:** Minimal configuration and current status for the authorised retained
deployment.

## Implementation status

Verified on 2026-09-18:

| Item | Retained environment |
| --- | --- |
| Host | Proxmox VM `devtools`, Ubuntu 24.04, 4 vCPU, 8 GiB RAM, 64 GB disk |
| Network | Static/reserved `192.168.14.136`; public DNS A record `dev-tools.helix-onprem.net` resolves to that private address |
| Container runtime | Docker Engine 29.8.1 and Compose 5.5.1 from Docker's official Ubuntu repository |
| Deployment | [`deploy/retained`](../deploy/retained): pinned YouTrack plus pinned Caddy with Route53 DNS-01 |
| Host preparation | Patched and rebooted; Docker verified; persistent directories created; Caddy image built and configuration validated |
| Not started | YouTrack, certificate issuance, and the configuration wizard |

The remaining start blockers are a dedicated root-only Route53 credential and the
human decision to start empty or restore the accepted trial backup.

## Known-good baseline

| Item | Retained configuration |
| --- | --- |
| Image | Pin `jetbrains/youtrack:2026.2.18991`; do not use `latest` |
| Service | One YouTrack container with `restart: unless-stopped` |
| Storage | Separate persistent host directories mapped to `/opt/youtrack/data`, `/opt/youtrack/conf`, `/opt/youtrack/logs`, and `/opt/youtrack/backups` |
| Ownership | Host directories accessible to container user/group `13001:13001` |
| Database | Use YouTrack's bundled database on local durable storage; do not put its live data directory on NFS |
| State | `TO DO`, `IN PROGRESS`, `IN REVIEW`, `DONE` with the seven transitions recorded in the trial |
| Readiness | Public single-value enum `Agent Readiness`: `Pending Review`, `Approved`; default `Pending Review` |
| Enforcement | Import and attach [`workflows/adoption-readiness`](../workflows/adoption-readiness) to each intended project |

The image and storage model follow YouTrack's supported
[Docker installation](https://www.jetbrains.com/help/youtrack/server/youtrack-docker-installation.html).

## Identities and permissions

- Keep at least one separately held human administrator account for installation,
  backup, restore, identity, project, and workflow administration.
- Give each automation consumer its own non-admin identity and permanent token. Grant
  only the project/article issue operations it needs.
- Do not grant agent identities Low-level Admin Write, user administration, workflow
  administration, backup administration, or deletion unless a concrete retained use
  requires it.
- Store tokens in the consuming environment's secret mechanism, never in Git or the
  Compose file. Define rotation and revocation ownership.
- Verify with the retained agent identity: project read; issue/article create/read/
  update; attachment/comment operations if required; allowed and denied transitions;
  and `403` for backup administration.

**Human decisions required:** administrator owners; agent identities; exact project
roles and groups; token storage, rotation interval, and emergency revocation owner.

## Supported interfaces

- Native YouTrack MCP: normal issue, comment, relationship, and article CRUD.
- REST command endpoint: state-machine transitions for REST clients.
- Native MCP `update_issue`: State updates are allowed only with the attached guard
  workflow active.
- REST article and attachment endpoints: publishing and file upload.
- Browser UI: human work, workflow/field administration, and occasional article
  ordering.

Do not use direct REST State-field assignment; for a state-machine field it returned
HTTP `200` without changing either an allowed or forbidden value. Do not integrate
with the private article-ordering request observed behind the UI.

## Backup and recovery

Enable YouTrack's built-in regular backup after the human supplies:

- **Human decision:** schedule/cron and time zone.
- **Human decision:** number of local backup files to retain.
- **Human decision:** off-host destination, credentials, encryption, retention, and
  who can restore from it.
- **Human decision:** administrators who receive backup-failure notifications and the
  notification channel configuration.
- **Human decision:** restore-rehearsal cadence and recovery objectives.

Use `TAR.GZ` unless there is a reason to choose ZIP; YouTrack notes a 2 GB ZIP limit.
Schedule outside normal working hours. Copy each completed archive from the mounted
backup directory to separately protected off-host storage, then verify transfer and
archive integrity. A backup left only beside the live deployment is not sufficient.

YouTrack supports a cron schedule, local rotation, and administrator failure
notifications in its
[database backup settings](https://www.jetbrains.com/help/youtrack/server/back-up-the-database.html).
The accepted trial proved a manual built-in backup and clean restore, but did not
configure automation, off-host copying, or alerts.

### Restore outline

1. Select a verified archive and a YouTrack image at the same version or a compatible
   later version.
2. Stop the affected service and preserve the failed directories for investigation.
3. Provision empty `data` and `conf` directories plus persistent `logs` and `backups`;
   make the selected archive readable by `13001:13001`.
4. Start the pinned container with all four mounts and a controlled temporary port.
5. In the Configuration Wizard choose Upgrade and select the archive as the source.
6. Verify administrator and restricted-agent authentication, representative issues,
   articles, attachments, hierarchy, State guard, readiness reset, and configured base
   URL before cutover.
7. Keep the prior service stopped and recoverable until the restored instance is
   accepted.

Follow the official
[Docker restore procedure](https://www.jetbrains.com/help/youtrack/server/restore-docker-image-installation.html).
The trial's exact recovery evidence remains in
[`trial-results.md`](trial-results.md); repeating it was intentionally out of scope for
this follow-up.

## Documentation publication

- Git Markdown and assets are authoritative; articles are derived browser-readable
  copies.
- Record repository, path, and commit in every published article.
- Keep a stable source-to-article-ID mapping and update in place.
- Store the last-published exact body SHA-256. Before each update, GET the article and
  compare its body hash. Stop and report any mismatch rather than overwriting.
- Reconcile approved human edits into Git, then republish. Do not build bidirectional
  synchronisation.
- Keep article ordering manual in the UI unless YouTrack publishes a supported API.

## Network and TLS

Use `https://dev-tools.helix-onprem.net` through Caddy. Only ports 80 and 443 are
published; YouTrack port 8080 stays on the Compose network. Caddy obtains a dedicated
Let's Encrypt certificate with the same Route53 DNS-01 pattern observed in the
Kubernetes cluster. Its Route53 module and Caddy version are pinned and built from the
documented Docker builder image.

The AWS identity is restricted to listing records and changing only TXT record
`_acme-challenge.dev-tools.helix-onprem.net` in hosted zone
`Z0684996186NCRQKGH7CM`. Store its access key in the root-only file documented under
[`deploy/retained`](../deploy/retained). Caddy creates and removes challenge values;
do not add a permanent TXT record.

The A record deliberately publishes a private RFC1918 address, so clients still need
routing to the internal network. Remove stale hosts-file overrides for the former
trial address before browser acceptance.

## Before starting the application

- Confirm whether the retained service starts empty or from an authorised backup.
- Install the dedicated Route53 credential without copying or reusing the Kubernetes
  credential.
- Confirm project names, human admins, restricted identities, and notification users.
- Review the workflow code and publish sources through the normal PR workflow.
- Plan one post-deployment acceptance run; do not repeat the whole exploratory trial.
