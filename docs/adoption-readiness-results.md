# YouTrack adoption-readiness follow-up

**Run:** 2026-09-17

**Version:** YouTrack Server `2026.2.18991`

**Scope:** Isolated additions to the accepted local trial; no retained deployment or
Atlassian migration

## Outcome

The remaining adoption questions are resolved sufficiently to commission a separate
retained deployment later.

- A small, project-scoped native YouTrack workflow now enforces the state graph for
  event commands and native MCP field updates. The previously observed MCP bypass is
  closed in the tested configuration.
- `Agent Readiness` is a two-value enum, readable and writable through REST and native
  MCP. Reopening `DONE -> TO DO` resets it to `Pending Review`.
- Git-authoritative Markdown can be published as a parent/child Knowledge Base pair,
  updated in place, and checked for human divergence before overwrite.
- No replacement service, custom MCP server, publisher, migration, or retained
  deployment was created.

All results below are live observations. The committed workflow and Markdown fixtures
are reproducible configuration/source artefacts, not an automated regression suite.

## 1. Workflow enforcement

### Baseline discrepancy

The restricted `trial-agent` identity was used for all three mutation paths.

| Path and fixture | Request | Actual response | Stored State |
| --- | --- | --- | --- |
| Event command, `TRIAL-4` | `TO DO -> DONE` | HTTP `400`; `State expected: Done` | `TO DO` |
| Direct REST field update, `TRIAL-5` | Correctly typed `StateMachineIssueCustomField` set to `DONE` | HTTP `200`; response still contained `TO DO` | `TO DO` |
| Native MCP `update_issue`, `TRIAL-6` | Raw `State: DONE` | JSON-RPC success; `updatedFields:["State"]` | `DONE` |
| Backup administration | Read backup settings | HTTP `403`; `HTTP 403 Forbidden` | Not applicable |

The direct REST write is a silent no-op for this state-machine field, not an allowed
way to change state. An earlier probe with the wrong REST field type was discarded as
a client setup error and is not part of the comparison.

### Smallest native fix

The `Trial adoption readiness` workflow was uploaded with YouTrack's supported ZIP
import and attached only to project `TRIAL`. Its on-change rule checks every reported
issue State change against the seven accepted edges and calls `workflow.check` for any
other pair. This rolls back the complete transaction, including raw MCP field writes.

Source:

- [`workflows/adoption-readiness/state-transition-guard.js`](../workflows/adoption-readiness/state-transition-guard.js)
- [`workflows/adoption-readiness/reset-readiness.js`](../workflows/adoption-readiness/reset-readiness.js)

This uses native workflow enforcement, not agent instructions, a proxy, or a custom
MCP server. YouTrack documents that on-change rules run when an issue changes and that
`workflow.check` rolls back the transaction when its condition is false:
[on-change rules](https://www.jetbrains.com/help/youtrack/devportal/on-change-rules.html),
[`workflow.check`](https://www.jetbrains.com/help/youtrack/devportal/v1-workflow.html).

### Retest with the guard active

| Path and fixture | Prohibited result | Allowed result | Final read-back |
| --- | --- | --- | --- |
| Event command, `TRIAL-8` | `TO DO -> DONE`: HTTP `400`, State stayed `TO DO` | `TO DO -> IN PROGRESS`: HTTP `200` | `IN PROGRESS` |
| Direct REST field update, `TRIAL-9` | Target `DONE`: HTTP `200`, no change | Target `IN PROGRESS`: HTTP `200`, no change | `TO DO` |
| Native MCP, `TRIAL-10` | JSON-RPC `-32603`: `State transition TO DO->DONE is not allowed.` | Success with `updatedFields:["State"]` | `IN PROGRESS` |

Thus the two actual mutation interfaces are enforced: the supported event route uses
the state machine, and native MCP is now guarded transactionally. Direct REST assignment
to a state-machine field does not mutate either allowed or forbidden values and should
not be offered as a state-change interface. Use the REST command endpoint when a REST
client needs a transition.

### Agent Readiness

The project now has a public, single-value enum field:

```text
Agent Readiness = Pending Review | Approved
default = Pending Review
```

On `TRIAL-11`:

- REST read the default `Pending Review` and updated it to `Approved` with HTTP `200`.
- Native MCP read `Approved`, updated it to `Pending Review`, then back to `Approved`.
- Event commands moved the issue through `TO DO -> IN PROGRESS -> IN REVIEW -> DONE`.
- Reopening with `DONE -> TO DO` returned HTTP `200` and the workflow reset readiness
  from `Approved` to `Pending Review` in the same transaction.

## 2. Documentation-first publishing

### Published fixture

Git sources:

- [`docs/knowledge/adoption-publishing-parent.md`](knowledge/adoption-publishing-parent.md)
- [`docs/knowledge/adoption-publishing-child.md`](knowledge/adoption-publishing-child.md)
- reused screenshot [`docs/images/trial-screen.png`](images/trial-screen.png)
- reused diagram source [`docs/diagrams/trial-flow.mmd`](diagrams/trial-flow.mmd)

Published copies:

- parent `TRIAL-A-4`
- child `TRIAL-A-6`, whose stored parent is `TRIAL-A-4`

The pair contains a table, shell code block, Mermaid code block, links in both
directions, screenshot, and attached diagram source. Each page records the repository,
source path, and exact source commit. The parent records commit
`b0c4658fde10073a7de8f61ddacff0502d9e9238`; the corrected child records
`c99216e44cd360717ebf84c47e8578e8d333d337`.

The correction was made in Git first and committed, then native MCP `update_article`
rewrote `TRIAL-A-6`; no replacement article was created. Independent native MCP and
REST reads confirmed content, parent/child hierarchy, one 134,683-byte PNG on the
parent, and one 212-byte Mermaid source attachment on the child. Both downloaded files
matched their Git sources byte-for-byte (SHA-256
`b62adfc4d150e91a9167cfbc0ca035fad3cea252698905ad3e5592cd78a796d0` for the PNG and
`421dacf50651b9566489ebc1f7bc0849a78be4064e36c08431cab2d5f4944a22` for the
Mermaid source). An accidentally
created parentless trial duplicate from a malformed first child request was removed by
the administrator; the restricted identity correctly lacked delete permission. The
final exact-title query returned only the intended pair. That removed duplicate is not
recoverable from the live article list except through a suitable backup.

### Human-edit divergence

A simulated human edit was applied to the published child before the Git correction
was published. The exact last-published content hash was
`984783e3463dacba3b04e75bd8265afd3000bf3bd9785c7d0b3da2d7e6af8e8e`; the human edit
changed it to
`d754d52e967634ba0eac438827ff527112f0992a99f4e06981eed19d7b2c32a5`.
The mismatch was reported before overwrite. After explicit reconciliation, the updated
Git-derived content and independent read-back both hashed to
`23f1a443ad72d5b82934da8b6a6eae4a53b4157f97db86c81c77f4b8e92c9e95`.

The simple retained approach is therefore:

1. Store the article ID and SHA-256 of the last published body with the publication
   record.
2. Before updating, GET that article and hash its exact current body.
3. If it differs, stop and report divergence; reconcile the human change into Git or
   explicitly discard it.
4. Update the same article ID and record the new source commit and published hash.

This detects divergence without bidirectional synchronisation or silent overwrites.
The trial executed these steps manually; it did not build a publisher.

### Supported and undocumented surfaces

Article CRUD, hierarchy, and attachments used documented native MCP or REST surfaces.
YouTrack documents the REST
[article resource](https://www.jetbrains.com/help/youtrack/devportal/resource-api-articles.html)
and [article attachment resource](https://www.jetbrains.com/help/youtrack/devportal/resource-api-articles-articleID-attachments.html).

The earlier timing trial reordered articles through the product UI's private
`PUT /api/admin/projects/0-1/articles` request. No public documentation for that
ordering endpoint was found, so it must not become an integration dependency. Use
manual UI drag-and-drop if ordering is needed; publishing does not otherwise depend on
order.

## 3. Remaining limits and KISS assessment

- The observations are one live trial run, not committed automated regression tests.
- Workflow upload/attachment and documentation publication were manual supported
  operations. A retained deployment should rerun the three transition checks after a
  YouTrack upgrade or workflow change.
- Direct REST State assignment returning `200` without mutation can mislead clients
  that check status only. Do not expose it as a supported state-change path.
- Backup scheduling, off-host transfer, and failure notification are still unconfigured.
- The accepted trial remains HTTP-only on a trusted local network.

Complexity is lower when better; other scores are higher when better.

| Measure | Score | Evidence and principal weakness | Confidence |
| --- | ---: | --- | --- |
| Complexity | 3/10 | One native workflow and one enum close the enforcement gap; no proxy, publisher, or custom MCP service. Publication is still manual. | High |
| Maintainability | 8/10 | Workflow and article sources are in Git and use supported import/update paths. Live checks are not automated. | Medium |
| Supportability | 8/10 | Exact interface responses, stored states, source commits, hashes, and restore evidence are available. No operational alerting exists. | High |
| Usability | 9/10 | Event and MCP paths both support valid work; articles remain browser-readable. REST raw State writes are a confusing no-op. | High |
| Security | 8/10 | Restricted backup access and native transactional enforcement are proved. HTTP remains appropriate only inside the accepted trust boundary. | High |

## Recommendation

Retain the trial decision. For a separately authorised retained deployment, reproduce
the pinned container, field, workflow, restricted identities, scheduled/off-host
backup, and divergence check described in
[`retained-deployment-handoff.md`](retained-deployment-handoff.md). Do not carry over
the undocumented ordering endpoint.
