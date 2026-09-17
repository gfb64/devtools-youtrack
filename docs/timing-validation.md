# YouTrack action timing validation

**Run:** 2026-09-17 on YouTrack `2026.2.18991`

**Transport:** local Parallels network to `10.37.129.20` over HTTP

**Fixtures:** `TRIAL-2`, `TRIAL-3`, `TRIAL-A-2`, and `TRIAL-A-3`

## Result

All requested actions completed and their final state was read back successfully.
The 21 measured action timings took **1,629.7 ms** in total when their individual
round trips are added together.

These are single-run, warm-environment observations, not a capacity benchmark. They
measure client-to-service round trips only; they exclude human typing, model reasoning,
browser startup, and exploratory setup.

| Requested action | Components | Time |
| --- | --- | ---: |
| Create parent issue, comment, and small attachment | 324 + 168 + 35.0 ms | **527.0 ms** |
| Create linked child, comment, and small attachment | 114 + 62 + 28.1 ms | **204.1 ms** |
| Move both to IN PROGRESS and comment on each | 124.6 + 65 + 30.5 + 59 ms | **279.1 ms** |
| Add larger child comment | 63 ms | **63.0 ms** |
| Child to IN REVIEW and comment | 28.5 + 52 ms | **80.5 ms** |
| Child to TO DO and comment | 28.4 + 40 ms | **68.4 ms** |
| Parent to IN REVIEW, then DONE | 53.3 + 35.1 ms | **88.4 ms** |
| Read existing article `TRIAL-A-1` | 30 ms | **30.0 ms** |
| Create top-level article `TRIAL-A-2` | 65 ms | **65.0 ms** |
| Create child article `TRIAL-A-3` | 44 ms | **44.0 ms** |
| Move `TRIAL-A-2` above `TRIAL-A-1` and read back order | 180.2 ms | **180.2 ms** |

Issue and article CRUD used the native YouTrack MCP tools. Attachments used the REST
attachment endpoint. State changes used the workflow event command endpoint so the
configured state machine, rather than a raw field write, decided each transition.
Article ordering used YouTrack's own article-order request because `ordinal` is a
read-only REST property and ordering is exposed as drag-and-drop in the product UI.

The first attachment timing attempt used an invalid workstation wall-clock comparison.
The uploads themselves succeeded, so both issues contain that first file plus the
distinct retry measured with a monotonic timer. Only the valid retry timings appear
above; all four files are small and were retained as trial evidence.

## Final read-back

- `TRIAL-2` is DONE, has two comments and two 212-byte attachments, and is parent for
  `TRIAL-3`.
- `TRIAL-3` is TO DO, has five comments and two 2,012-byte attachments, and reports
  `TRIAL-2` as its parent.
- `TRIAL-A-2` is a top-level article and lists `TRIAL-A-3` as its child.
- `TRIAL-A-3` reports `TRIAL-A-2` as its parent.
- The stored top-level article ordinals are `TRIAL-A-2 = 1` and `TRIAL-A-1 = 2`.

As small additional checks, the final objects were fetched through MCP and searched by
their unique title phrase. Both issue results and both new article results were found.
The parallel post-check observations were:

| Check | Time |
| --- | ---: |
| Parent issue read-back | 231 ms |
| Child issue read-back | 176 ms |
| Parent article read-back | 263 ms |
| Child article read-back | 477 ms |
| Issue search | 571 ms |
| Article search | 454 ms |

These post-checks are not included in the requested-operation total. They ran in
parallel and are useful integrity evidence, not comparative performance data.

## KISS conclusion

The exercised flow needs no custom integration service. Native MCP covers the normal
issue and Knowledge Base work, REST covers file upload and workflow-event transitions,
and the built-in article tree covers ordering. At the time of this timing run, raw MCP
State updates bypassed visual state-machine events, so agent-driven changes needed the
event command path. The later adoption-readiness follow-up reproduced and then closed
that bypass with a small native on-change guard; see
[adoption-readiness-results.md](adoption-readiness-results.md).
