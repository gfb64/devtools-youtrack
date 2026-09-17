# YouTrack trial result

**Decision:** Successful

**Accepted:** 2026-09-17

**Version:** YouTrack Server `2026.2.18991`

**Scope:** Local development trial in Parallels; not a production rollout

## Outcome

Self-hosted YouTrack met the trial need. Humans can use the issue and Knowledge Base
interfaces comfortably, while Codex can perform the representative work quickly through
YouTrack's native MCP and REST interfaces. The containerised, file-backed deployment is
simple, survived recreation, and was recovered successfully from a supported backup.

The trial is accepted with HTTP and no TLS requirement while it remains on the trusted
local network. Git-controlled Markdown, images, and diagram sources remain authoritative;
Knowledge Base articles are readable derived copies.

## Environment delivered

| Item | Result |
| --- | --- |
| Workstation | Ubuntu 26.04.1 LTS at `10.37.129.10` |
| Runtime | Ubuntu 24.04.4 LTS at `10.37.129.20` through Docker context `helix-runtime` |
| Deployment | One Compose service using pinned image `jetbrains/youtrack:2026.2.18991` |
| Persistent storage | Host bind mounts for `data`, `conf`, `logs`, and `backups` under `/srv/youtrack-trial` |
| Access | `http://dev-tools.helix-onprem.net:8080` through Mac and Ubuntu hosts entries |
| YouTrack data | Project `TRIAL`; issues `TRIAL-1` to `TRIAL-3`; articles `TRIAL-A-1` to `TRIAL-A-3` |
| Identities | One human administrator and restricted non-admin `trial-agent` |
| Git | Work completed on `trial/youtrack-evaluation`; secrets and runtime data excluded |

## Journeys proved

### Human and documentation use

- Completed normal first-run setup and created the `TRIAL` project.
- Created a human-readable issue and Knowledge Base article containing Markdown, a
  screenshot, and a Mermaid diagram derived from Git-controlled source.
- Human review from the Mac confirmed that the issue and article were clear and suitable.
- Created nested articles and reordered the top-level article tree.

### Agent access and permissions

- Configured Codex to use YouTrack's native MCP endpoint with an environment-provided
  permanent token.
- The actual Codex client loaded the 15 intended issue, article, project, and identity
  tools and authenticated as `trial-agent`.
- MCP created, read, and updated issues and articles and added and retrieved comments.
- REST uploaded attachments and executed workflow events.
- The restricted identity could read and mutate permitted project data but received
  `403 Forbidden` from the database-backup administration endpoint.
- Credentials, tokens, runtime data, and backup contents were not committed to Git.

### Workflow enforcement

The visual state machine used these states:

```text
TO DO       -> IN PROGRESS
IN PROGRESS -> TO DO | IN REVIEW
IN REVIEW   -> TO DO | IN PROGRESS | DONE
DONE        -> TO DO
```

All seven allowed edges worked through the workflow event interface. The unlisted
`TO DO -> DONE` transition returned HTTP 400 and left the issue in `TO DO`. The same
allowed and denied behaviour remained present after backup restoration.

One material product limitation was found: native MCP `update_issue` can write the raw
State field without invoking a state-machine event. Agent-driven state changes should
therefore use the REST command/event path until this is guarded or corrected upstream.

### Representative issue and Knowledge Base work

- Created parent issue `TRIAL-2` with comments and small attachments.
- Created child issue `TRIAL-3`, preserved its parent link, and added comments and
  attachments.
- Exercised IN PROGRESS, IN REVIEW, TO DO, and DONE transitions with representative
  progress and review comments.
- Read the original article `TRIAL-A-1`, created `TRIAL-A-2`, and created `TRIAL-A-3`
  as its child.
- Moved `TRIAL-A-2` above `TRIAL-A-1` and verified the stored order.
- Read all final state back and found both issues and both new articles through search.

## Timing observation

The 21 requested action timings totalled **1,629.7 ms** on the warm local VM network:

| Requested action | Time |
| --- | ---: |
| Create parent issue, comment, and attachment | 527.0 ms |
| Create linked child, comment, and attachment | 204.1 ms |
| Move both to IN PROGRESS and comment | 279.1 ms |
| Add larger child comment | 63.0 ms |
| Child to IN REVIEW and comment | 80.5 ms |
| Child to TO DO and comment | 68.4 ms |
| Parent to IN REVIEW, then DONE | 88.4 ms |
| Read existing article | 30.0 ms |
| Create top-level article | 65.0 ms |
| Create child article | 44.0 ms |
| Reorder top-level articles and read back | 180.2 ms |

These are single-run client-to-service observations, not a capacity benchmark. They
exclude human interaction, model reasoning, browser startup, and exploratory setup.
The participant reports that comparable Jira and Confluence interactions commonly take
3–10 seconds each, but that comparison was not measured under controlled conditions.
See [timing-validation.md](timing-validation.md) for component timings and read-back
checks.

## Persistence, backup, and recovery

- `TRIAL-1` and `TRIAL-A-1` survived forced container recreation while retaining the
  host bind mounts.
- The built-in backup utility was available with the free license.
- A final supported backup, `2026-09-17-15-03-36.tar.gz` (7,218,770 bytes), passed an
  archive integrity check.
- The final archive was restored with the same pinned image into empty, isolated data,
  configuration, log, and backup directories on temporary port 8081.
- All three issues and all three articles matched the original content exactly.
- All five attachments were downloaded from both instances and were byte-for-byte
  identical.
- Parent/child relationships, article ordering, administrator login, restricted-agent
  authentication, and workflow enforcement were preserved.
- The temporary restore container and directories were removed after verification; the
  accepted instance on port 8080 remained healthy.

An earlier backup also restored successfully but correctly represented its older point
in time and did not contain the later timing fixtures. A fresh backup was therefore
created and used for the final proof.

## Explicitly not done

- Automatic backups are not enabled.
- No backup schedule, rotation, failure notification, or automated restore rehearsal was
  configured.
- The backup archive has not been copied to off-host or separately protected storage;
  it currently shares the runtime filesystem with the deployment.
- TLS, a reverse proxy, and Route53 DNS were not added. HTTP was explicitly accepted for
  this trusted local scope and must be reconsidered if exposure changes.
- SSO/OAuth, Jira import, Confluence publication, email integrations, monitoring, HA,
  Kubernetes, and an external database were not evaluated.
- No custom MCP server or automated documentation publisher was built because the native
  interfaces were sufficient.
- No long-running load, concurrency, upgrade, or controlled Jira-versus-YouTrack
  benchmark was performed.
- The journeys were exercised manually and through live API/MCP calls; they were not
  delivered as an automated regression suite.

## KISS assessment

Complexity is scored lower when better; the other measures are scored higher when
better. These scores apply only to the tested local trial.

| Measure | Score | Evidence and principal weakness | Confidence |
| --- | ---: | --- | --- |
| Complexity | 2/10 | One pinned container, four bind mounts, native MCP/REST, and no extra platform. State changes currently need the REST event path. | High |
| Maintainability | 8/10 | Ordinary Compose and filesystem backup paths with concise Git documentation. Upgrade maintenance was not tested. | Medium |
| Supportability | 8/10 | Product logs, REST read-back, supported backups, and clean recovery were usable. No monitoring or backup-failure notification exists. | Medium |
| Usability | 9/10 | Human review and complete agent journeys passed with low observed latency. Article ordering required the product's dedicated ordering operation. | High |
| Security | 7/10 | Restricted identity and administrative denial were proved, and secrets stay outside Git. HTTP is unencrypted and raw MCP state writes can bypass workflow events. | Medium |

## Final decision

The trial is successful. The smallest sensible next operational step, if this becomes a
retained service, is to schedule supported YouTrack backups and copy them to separately
protected storage. TLS is not required for the accepted local scope, but should be added
if the service crosses that trust boundary.
