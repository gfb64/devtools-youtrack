# KISS — Keep It Simple, Stupid

## Purpose and invocation

Use this methodology to design, implement, review and operate the simplest solution that reliably meets real user needs. Simplicity means less unnecessary machinery and less human effort across the whole lifecycle—not merely fewer lines of code.

When asked to invoke KISS, read this entire file and apply it to the requested scope. Follow the project's existing authority, branch, review and deployment rules. This file does not authorise unrelated changes, infrastructure modifications, destructive actions or bypassing required controls.

Example instruction:

> Read KISS.md and apply it throughout this task. Identify unnecessary complexity, preserve required behaviour, verify the real user journeys, and report the five KISS scores with evidence. Do not introduce a framework, policy or workflow unless its concrete benefit justifies its cost.

For an audit, inspect and recommend without implementing changes. For an implementation request, make the authorised changes and verify them. Do not create a new approval ceremony for ordinary in-scope work.

## Establish the actual context

Before judging the solution, establish enough context to answer:

- Who uses, administers, maintains and supports it?
- Where is it deployed: internal company use, customer-managed internal environments, public service, offline or another context?
- What data and actions are sensitive? Where are the actual trust boundaries?
- Which capabilities and user journeys are promised now? Which are explicitly future or out of scope?
- What existing tools, infrastructure and operational practices must it fit?
- Which constraints are mandatory, and which are conventions or assumptions?

Use existing evidence first. Ask only questions whose answers would materially change the decision; record other assumptions briefly. Do not treat an internal deployment as public SaaS, or assume internal users and workloads are all trustworthy.

## The five measures

Score each measure independently from 1 to 10. **Complexity: lower is better. All other measures: higher is better.** These are evidence-backed engineering judgements, not objective measurements. Never average them into a misleading overall pass.

| Measure | What to assess | Low score: 1–3 | Middle: 4–6 | High score: 7–10 |
| --- | --- | --- | --- | --- |
| Complexity | How much machinery, indirection, coupling and exceptional behaviour exists beyond what users need? | Direct, understandable paths; little unnecessary machinery | Some justified complexity, with avoidable layers or special cases | Extensive indirection, duplicate state, policy/workflow layers or complexity disproportionate to benefit |
| Maintainability | Can an engineer understand, change, test, upgrade, configure and deploy it safely without excessive ceremony? | Fragile, tightly coupled or dependent on specialist knowledge | Routine maintenance possible, but with notable friction | Clear ownership and boundaries; ordinary tools; predictable, testable changes |
| Supportability | Can a human identify, explain and recover from failures using supported logs, configuration and diagnostic surfaces? | Opaque errors, missing context, excessive redaction or inaccessible diagnostics | Common failures diagnosable; important gaps remain | Useful safe context, understandable configuration, clear recovery and proportionate history |
| Usability | Can users and administrators complete intended tasks easily and correctly? | Confusing setup, inconsistent authority, hidden prerequisites or frequent manual repair | Core tasks work, with meaningful friction | Coherent workflows, sensible defaults, actionable errors and straightforward administration |
| Security | Are controls effective and proportionate to actual risks and deployment context? | Material protection gaps, unsafe defaults or controls that do not work | Basic protections exist but have significant gaps or disproportionate burden | Appropriate protections, understandable controls and demonstrated trust-boundary enforcement |

For each score, provide the scope/version, evidence, principal weakness and confidence: High, Medium or Low. Use **Not assessed** when evidence is insufficient; do not invent a number. A 10 is not a claim of perfection or immunity from failure.

Suggested improvement targets, unless the project sets others: Complexity at most 4; Maintainability, Supportability, Usability and Security at least 7. These are discussion targets, not automatic release gates. A high score elsewhere never cancels a serious security or correctness defect.

## Decision rules

### 1. Require a concrete benefit for complexity

For a non-trivial abstraction, service, policy, workflow, cache, dependency or configuration option, answer:

1. Which current user need or demonstrated risk requires it?
2. What is the simplest adequate alternative?
3. What maintenance, support, usability and security cost does this choice introduce?
4. What evidence shows the additional complexity is worthwhile?

Prefer direct code and standard platform/library features. Do not build speculative extension points, general-purpose engines, custom report formats, compatibility layers or fallback chains for hypothetical needs. Small local duplication can be clearer than a premature abstraction. Conversely, do not remove a useful abstraction merely to reduce file or line counts.

Count complexity across application code, configuration, infrastructure, tests and delivery workflow. Moving it into scripts, agents or operator instructions does not remove it.

### 2. Make maintenance and support ordinary

- Prefer one coherent way to configure and operate each capability. Make defaults, precedence and overrides understandable.
- Avoid hidden state, duplicate sources of truth, environment-specific code paths and undocumented manual steps.
- Logs should explain the operation, outcome and useful cause. Include non-sensitive identifiers and correlation context where they help diagnosis; avoid logging entire payloads by default.
- Redact credentials, tokens, private keys and genuinely sensitive personal/business content. Do not blanket-redact harmless diagnostic context merely because a field name contains words such as `secret` or `credential`.
- Avoid mandatory durable auditing of every routine interaction without a concrete security, regulatory or operational need. Prefer concise records of meaningful changes and relevant security events, with sensible retention.
- Distinguish optional audit/history from durable state required for correctness, accounting, recovery or idempotency. Do not delete the latter under the banner of simplicity.
- Rate limits, quotas, timeouts and approval steps must address a real risk and have understandable defaults and failure messages. They must not make legitimate administration or recovery unnecessarily difficult.

### 3. Use proportionate security

Preserve required authentication, authorisation, tenant/data isolation, credential protection, safe execution and recovery. Match controls to exposure, data sensitivity, likely misuse and the impact of failure—not a generic maximum-hardening checklist.

More controls do not automatically mean better security. Assess whether people can configure, maintain and use those controls correctly. Do not improve usability by silently bypassing protection, suppressing findings or accepting material risk without the appropriate owner's decision.

Treat scanner results as evidence requiring assessment, not as automatic proof of exploitability or irrelevance. Check the exact dependency/image, affected versions, exposed behaviour, available fixes and actual deployment. Prefer compatible, bounded fixes; avoid blanket upgrades or introducing a new security framework just to resolve a local issue. Use current authoritative advisories when assessing vulnerability applicability.

### 4. Prove user journeys, not just components

- Express acceptance in observable user, administrator or client outcomes, including relevant denial and recovery paths.
- Exercise shipped interfaces with representative identities and data. Do not substitute privileged shortcuts, direct database seeding, mock-only results or a successful bootstrap identity for ordinary-user proof.
- A journey exercised manually is useful evidence, but is not a delivered automated regression test. When repeatability is required, commit the tests, dependencies and reproduction instructions.
- Prefer standard test tools, ordinary fixtures and native reports. One documented execution command with explicit prerequisites is better than a new orchestration framework.
- Assert the intended result. A network error must not pass as an authentication denial; HTTP 200 alone may not prove success; a command exit must reflect assertion and cleanup failures.
- Keep setup, product assertion and cleanup failures distinguishable. Skipped, Blocked and Not Run are not Passed.
- Create uniquely identifiable test-owned data, clean only those objects, and preserve unrelated data and intended persistent deployments. Make cleanup reliable after failure as well as success.
- Record the tested application revision/image and test revision separately, plus relevant environment/browser versions. Bind acceptance evidence to the final reviewed changes; rerun what those changes affect rather than repeating unrelated work mechanically.
- When proving repeatability, demonstrate consecutive independent runs without manual repair. New capabilities add journeys and rerun affected existing journeys, including when shared fixtures change.

### 5. Respect tooling ownership

Separate repository-owned dependencies and tests from environment-managed runtimes, browsers, credentials and infrastructure. Inspect what already exists before installing alternatives.

Do not upgrade, replace or patch shared/global tools merely because a local test needs a dependency. A pinned repository-local test dependency may be appropriate for reproducibility; it should coexist with the managed environment through supported configuration. Avoid loading multiple physical instances of the same test runner into one execution or adding dynamic import workarounds when one runner and ordinary configuration suffice.

Document the supported execution path and who owns updates. If the environment contract truly requires a particular wrapper or global tool, resolve incompatibility with its owner rather than bypassing it silently. Raise a precise limitation instead of building another compatibility framework by default.

## Applying KISS during development

### Before changing

Read the relevant requirement, code and tests. State the bounded outcome, affected journeys and simplest plausible approach. Identify any proposed complexity increase or risk trade-off. A small task needs only a brief explanation, not a separate design document.

### While implementing

Keep the change focused. Use existing supported mechanisms and remove obsolete code/configuration made unnecessary by the change. Maintain real tests alongside the implementation. If a failure changes your understanding, revisit the assumption before adding another layer.

Correct failed or incomplete original acceptance within the existing work item/PR where the project's lifecycle permits. A new issue should represent a distinct requirement or independently scoped problem—not just another unsuccessful attempt. Preserve completed evidence and use the project's supported reopening/recovery process; never erase workflow history to manufacture a clean start.

If you encounter repeated remediation, stop adding machinery long enough to identify the common cause: unclear acceptance, wrong baseline, broken fixture, environment mismatch, ownership gap or product defect. Do not assume a larger model, more agents, more retries or more gates will solve it.

### During review

Challenge both correctness and unnecessary complexity:

- Does the user journey work through the intended interfaces, without hidden manual repair?
- Does the evidence support the claim, and can another engineer reproduce it?
- Is any added abstraction, dependency, policy or configuration option unnecessary?
- Can an administrator understand and a support engineer diagnose the resulting behaviour?
- Are controls and redaction proportionate, without losing essential protection?
- Were environment ownership and existing data respected?
- What can safely be deleted or simplified before merge?

Tests are implementation work even when application code does not change. Do not skip required review of newly written tests by declaring that no product fix was needed. Independent review follows the project's existing rules; KISS does not add an extra review bureaucracy.

### Before claiming completion

Distinguish work-item closure, successful observations, repeatable regression coverage and release readiness. Report actual results and remaining scope. Required failed or unrun journeys remain unresolved; documentation or workflow completion cannot turn them into a product pass.

For a substantial audit or milestone, reassess all five measures. For a small change, report only materially affected measures and reference the existing baseline; do not create five new scores after every edit. Keep existing debt visible without absorbing unrelated remediation into the task.

## Compact reporting format

Use only the detail justified by the task. For a full audit:

1. **Scope and confidence:** exact baseline, deployment assumptions, sources inspected and limits.
2. **Scorecard:** five scores, their direction, concise evidence and confidence.
3. **Findings:** concrete location/behaviour, user or operator impact, simplest remedy and verification. Separate observed facts from hypotheses.
4. **Recommendation:** retain, simplify, remove or investigate, in priority order. Explain trade-offs and any decision requiring human authority.
5. **Journey status:** what passed, failed, was blocked or was not run; distinguish manual observations from committed automated coverage.
6. **Next bounded action:** one useful delivery step, not a speculative chain of tickets or a platform redesign.

Do not manufacture numerical precision, inflate scores because tests pass, or treat compliance with this file as proof of quality. The outcome is software people can understand, use, maintain and support—with appropriate protection and demonstrably working journeys.
