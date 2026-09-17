# YouTrack trial handoff

**Status:** YouTrack container running; browser setup pending
**Updated:** 2026-09-17 for `/home/ai/Development/devtools-trial`

## Purpose

Run a small, development-only trial of self-hosted YouTrack. The question is whether
it gives humans and coding agents a clearer, faster way to manage development work
than the current Jira/Rovo interaction, while also providing a readable development
Knowledge Base.

This is an evaluation, not a production rollout. Prefer learning quickly over
perfecting infrastructure.

## Current environment

Verified on 2026-09-17:

| Item | Observation |
| --- | --- |
| Workspace | `/home/ai/Development/devtools-trial` on ext4 |
| Git | Repository on `trial/youtrack-evaluation`; no remote |
| Workstation VM | Ubuntu 26.04.1 LTS, x86_64, at `10.37.129.10` in Parallels |
| Docker client | 29.8.1 with Compose 5.5.1 |
| Docker target | `helix-runtime` over SSH: Ubuntu 24.04.4 LTS, x86_64, at `10.37.129.20` |
| Docker server | 29.6.2 |
| Runtime port 8080 | YouTrack published on `10.37.129.20:8080` |
| Trial hostname | `dev-tools.helix-onprem.net`; hosts entries configured on the Mac and workstation VM |

The `.10` workstation runs the development tools; Compose commands use the remote
Docker engine on the `.20` runtime VM. Docker-published ports therefore belong to
`.20`, as do bind-mounted runtime paths. Recheck port availability there before
deployment.

## Smallest useful trial

- One Docker Compose service using pinned image `jetbrains/youtrack:2026.2.18991`.
- Persistent mounts for `/opt/youtrack/data`, `/opt/youtrack/conf`,
  `/opt/youtrack/logs`, and `/opt/youtrack/backups`.
- Publish port 8080 on the runtime VM's `10.37.129.20` interface and use restart
  policy `unless-stopped`.
- One trial project, one human administrator, and one restricted agent identity.
- One representative issue and one small Git-controlled documentation fixture.
- HTTP is acceptable for this bounded trial if it stays on a trusted local, office,
  or VPN path. Add TLS only if the client requires it or the trial is retained.

For this trial, add the following entry to `/etc/hosts` on both the Mac and workstation
VM:

```text
10.37.129.20 dev-tools.helix-onprem.net
```

This gives the Mac browser and workstation agent the same HTTP URL without introducing
DNS or TLS:

```text
http://dev-tools.helix-onprem.net:8080
```

Confirm Mac-to-runtime reachability after YouTrack starts. Route53 remains deferred;
it is useful only if clients outside this Mac/VM environment need the hostname.

## Required behaviour

Use one state field:

- `TO DO` (initial)
- `IN PROGRESS`
- `IN REVIEW`
- `DONE` (resolved)

Allowed transitions:

```text
TO DO       -> IN PROGRESS
IN PROGRESS -> TO DO | IN REVIEW
IN REVIEW   -> TO DO | IN PROGRESS | DONE
DONE        -> TO DO
```

Use YouTrack's visual Workflow Constructor if it expresses this cleanly. Prove at
least one denied transition, preferably `TO DO -> DONE`.

For agent access, use a disposable permanent token belonging to a minimally
privileged, non-admin user. Prove a small authenticated REST read first, then use the
native `/mcp` endpoint from the actual target client. Authentication, authorization,
network, and client-compatibility failures should be distinguished before adding
components.

## Documentation authority

Git-controlled Markdown, screenshots, and diagram sources are authoritative.
YouTrack articles are derived copies for human reading and review. Apply corrections
to Git first, then update YouTrack. Do not build a publisher for this trial.

A sufficient fixture is:

```text
docs/
├── trial-guide.md
├── images/trial-screen.png
└── diagrams/trial-flow.mmd
```

The article should identify its repository, branch, commit, and source path. Create
and update it directly through supported UI, REST, or MCP operations. Include one
screenshot and either a rendered Mermaid diagram or a Git-controlled rendered image.

## Practical path

The sequence may adapt to what the environment reveals:

1. Confirm runtime port 8080 is free and verify the URL from the Mac browser and
   workstation agent.
2. Create the one-service Compose definition and keep runtime data and secrets out of
   Git.
3. Start YouTrack and complete its normal first-run setup without reproducing setup
   tokens in files, chat, or committed output.
4. Configure the project, workflow, and restricted agent account.
5. Exercise REST, MCP, issue workflow, comments, and the Knowledge Base.
6. Recreate the container without deleting persistent data and verify the trial data
   remains.
7. Produce one supported backup artifact outside the live data directory.
8. Record what passed, failed, was blocked, or was not run.

Stop when the trial question has enough evidence. A blocked optional network or DNS
step should not invalidate useful local findings; record the limitation plainly.

## Evidence of success

The trial should demonstrate:

- A normal human can sign in and work with the project.
- The restricted token can perform an allowed REST operation but not an administrative
  one.
- The actual agent client can discover and use the required MCP issue and article
  operations.
- Every allowed state transition works and an unlisted transition is denied.
- An agent can create or update an issue and add and retrieve a comment.
- A human can comfortably read an article containing text, a screenshot, and a
  diagram, while the Git source remains unchanged by publication.
- Project and Knowledge Base data survive non-destructive container recreation.
- A supported backup artifact exists.
- The participants can make an evidence-based judgment about speed, cost, and
  ambiguity compared with Jira/Rovo; invented timing precision is unnecessary.

Record the tested image version, Compose/Git revision, host architecture, client,
transport, and any material limitation. Do not report an unrun or failed journey as
passed.

## Deliberately deferred

Unless evidence from the trial requires one, do not add a reverse proxy, TLS
automation, Kubernetes, an external database, SSO/OAuth, monitoring infrastructure,
multiple agent identities, Jira import, Confluence publication, a custom MCP server,
or a documentation publishing framework.

## Working rules

- Apply `KISS.md`: each added component or abstraction must solve a current trial
  need.
- Never expose setup tokens, bearer tokens, private keys, or cloud credentials.
- Keep secrets and runtime state out of Git.
- Work on a non-protected branch. If a remote is added later, merge through a pull
  request rather than pushing to `main` or `master`.
- Prefer supported YouTrack and Docker behaviour over custom code.
- Test complete human and agent journeys, including one denial and persistence, rather
  than treating a running container as success.

## References

- [YouTrack Docker installation](https://www.jetbrains.com/help/youtrack/server/youtrack-docker-installation.html)
- [YouTrack MCP server](https://www.jetbrains.com/help/youtrack/server/model-context-protocol-server.html)
- [Permanent tokens](https://www.jetbrains.com/help/youtrack/server/manage-permanent-token.html)
- [REST API introduction](https://www.jetbrains.com/help/youtrack/devportal/api-getting-started.html)
- [Workflow state machines](https://www.jetbrains.com/help/youtrack/server/workflow-constructor-state-machines.html)
- [Backup and installation topics](https://www.jetbrains.com/help/youtrack/server/installation-and-upgrade.html)

Verify version-specific details in current official documentation when they become
necessary.
