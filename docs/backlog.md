# Implementation backlog

The [public GitHub issue tracker](https://github.com/chakirou18/AI-OfficeFlow/issues) contains one issue for every stable task ID T01–T18. All tasks remain open. T01 has undergone a requirements audit with pilot confirmation still pending; T02 has partial tracker-setup evidence. GitHub holds the live status labels. No application acceptance criteria are claimed complete. Dependencies mean prerequisites for completion; independent preparation may start earlier.

Use the public tracker actively throughout development. Before implementing work, read and reference its issue, acceptance criteria, dependencies, and latest comments. Record progress, blockers, decisions/ADRs, exact check commands and outcomes, commit/PR links, and completion evidence in the issue. Keep this backlog and issue scope synchronized. A list of newly created issues alone is not evidence of sustained tracker use.

## Labels and milestones

Each task has one label from each of four groups:

- **Type:** `type:governance`, `type:architecture`, `type:feature`, `type:platform`, `type:testing`, `type:security`, or `type:documentation` identifies its primary responsibility.
- **Priority:** `priority:p0` means foundational work before dependent implementation; `priority:p1` means a core delivery requirement; `priority:p2` means a later delivery/extension checkpoint. Priority does not remove completion dependencies or make a grading requirement optional.
- **Phase:** `phase:m0` through `phase:m8` map to the roadmap. Each issue also belongs to the matching named GitHub milestone. No due dates are committed.
- **Status:** keep exactly one of `status:todo`, `status:in-progress`, `status:in-review`, `status:blocked`, or `status:done`.

Existing GitHub default labels are preserved. Milestones group work; labels provide the status workflow without requiring a GitHub Projects board.

## Issue status workflow

1. **Todo:** keep the issue open with `status:todo` until work starts.
2. **In progress:** replace the status label with `status:in-progress`, reference the issue in commits/PRs, and record scope and checks as work proceeds.
3. **Blocked:** keep the issue open with `status:blocked`; explain the blocker, dependency, and required next step. Restore todo or in-progress when resolved.
4. **In review:** keep the issue open with `status:in-review` when changes and evidence are ready. Record exact tests/checks, results, limitations, decisions and artifact links. Unrun checks must be identified as unrun.
5. **Done:** only after all acceptance criteria and completion dependencies are satisfied and reviewed, check off supported criteria, record the completion evidence, apply `status:done`, and close as completed. Reopen with an appropriate open status if completion is invalidated.

Partial completion remains open. Avoid automatic closing keywords when criteria remain unmet. T02 remains in progress because T01 validation and evidence of ongoing tracker use are still outstanding; tracker preparation does not waive those requirements.

The [T02 setup evidence comment](https://github.com/chakirou18/AI-OfficeFlow/issues/2#issuecomment-6268487143) records issue creation, preserved criteria/dependencies, label and milestone setup, verification outcomes, and remaining gaps. It is partial evidence, not a completion claim.

## Task-to-issue mapping

| ID | Task | Acceptance criteria | Dependencies | GitHub Issue |
| --- | --- | --- | --- | --- |
| T01 | Validate requirements and assessment targets | Pilot assumptions reviewed; official 2026 rubric and Module 5 sources linked; every official criterion mapped to an issue/evidence item; specification gaps recorded | None | [#1](https://github.com/chakirou18/AI-OfficeFlow/issues/1) |
| T02 | Establish public project tracking | Public repository/tracker URLs recorded; T01–T18 imported with criteria and dependencies; milestones and status workflow configured; ongoing work updates visible | T01 | [#2](https://github.com/chakirou18/AI-OfficeFlow/issues/2) |
| T03 | Resolve foundational architecture | ADRs select orchestration, model, authentication, hosting, and telemetry; decisions include alternatives, costs, data handling, and permission implications | T01 | [#3](https://github.com/chakirou18/AI-OfficeFlow/issues/3) |
| T04 | Create runnable full-stack skeleton | React, API, worker, database and migrations start from a clean checkout through Compose; health checks succeed; example environment file contains placeholders only | T03 | [#4](https://github.com/chakirou18/AI-OfficeFlow/issues/4) |
| T05 | Establish CI checks | Pull-request workflow runs lint/type checks, unit tests and PostgreSQL integration tests; deliberate failed check blocks merge under configured branch rules; actual run linked | T02, T04 | [#5](https://github.com/chakirou18/AI-OfficeFlow/issues/5) |
| T06 | Implement identity and role enforcement | Controlled accounts and backend role checks match specification; anonymous and forbidden cases tested; public access requires authentication; role changes audited | T04, T05 | [#6](https://github.com/chakirou18/AI-OfficeFlow/issues/6) |
| T07 | Implement request persistence and API | Create/list/detail, validation, pagination, immutable revisions and legal transitions satisfy US-01/02; migrations and real-database tests pass | T06 | [#7](https://github.com/chakirou18/AI-OfficeFlow/issues/7) |
| T08 | Build request UI and dashboard | Forms, list, detail, status filters, counts and activity display persisted data; loading/empty/error states demonstrated; browser smoke check covers capture and reload | T07 | [#8](https://github.com/chakirou18/AI-OfficeFlow/issues/8) |
| T09 | Implement durable agent execution and tools | Jobs survive worker restart; leases and bounded retries tested; MCP exposes only profile/staff reads with scoped authorization; provider adapter supports deterministic stubs | T03, T07 | [#9](https://github.com/chakirou18/AI-OfficeFlow/issues/9) |
| T10 | Implement Sales and Coordination agents | Versioned structured outputs and prompts; at least 10 synthetic fixtures evaluated against US-03/04; unknown facts remain unknown; failures and adversarial input cannot trigger mutations | T09 | [#10](https://github.com/chakirou18/AI-OfficeFlow/issues/10) |
| T11 | Implement human review and approval | US-05 passes end to end; transactions enforce revision checks and roles; rejection applies nothing; duplicate/concurrent approval creates tasks once | T08, T10 | [#11](https://github.com/chakirou18/AI-OfficeFlow/issues/11) |
| T12 | Complete meaningful automated coverage | Unit and PostgreSQL integration suites cover lifecycle, jobs, failures, permissions and concurrency; browser test covers approved/rejected paths; CI results linked; live-model tests opt-in | T05, T11 | [#12](https://github.com/chakirou18/AI-OfficeFlow/issues/12) |
| T13 | Add observability | API/worker/MCP traces correlate; Prometheus metrics and Grafana dashboard expose API latency/errors and queue age; logs/traces pass redaction review; setup documented | T09 | [#13](https://github.com/chakirou18/AI-OfficeFlow/issues/13) |
| T14 | Add user-impact alert and runbook | Queue age over 120 seconds for 2 minutes triggers a routed staging alert; runbook links and recovery instructions work; exercise timing and alert evidence recorded | T13 | [#14](https://github.com/chakirou18/AI-OfficeFlow/issues/14) |
| T15 | Demonstrate constrained on-call recovery | Staging fault injection, redacted diagnosis, operator-approved flag reset, single-action limit, audit and synthetic verification satisfy US-08; failed recovery stops and escalates | T11, T14 | [#15](https://github.com/chakirou18/AI-OfficeFlow/issues/15) |
| T16 | Deploy publicly through CI/CD | Authenticated HTTPS staging contains synthetic data; release uses required checks and protected secrets; migrations, backup/restore, rollback and access instructions verified; URL and pipeline evidence recorded | T03, T12, T13 | [#16](https://github.com/chakirou18/AI-OfficeFlow/issues/16) |
| T17 | Deliver Module 5 Agent Extension Pack checkpoint | Verified requirements mapped individually to implementation, tests and documentation; any deferred item has explicit rationale and assessment impact; scope/permission changes reviewed | T01, T10, T11 | [#17](https://github.com/chakirou18/AI-OfficeFlow/issues/17) |
| T18 | Assemble final evidence and handover | All official criteria cross-checked; actual CI/deployment/demo/alert/recovery links included; performance target measured; limitations, setup and operations docs validated from clean checkout | T02, T12, T15, T16, T17 | [#18](https://github.com/chakirou18/AI-OfficeFlow/issues/18) |

Each implementation task includes updating relevant documentation and recording evidence before closure. T12 consolidates coverage; testing begins with the first implementation task. T18 must flag unmet criteria rather than replacing missing evidence with claims.

## T01 assessment audit: additive acceptance refinements

The [grading checklist](grading-checklist.md) now maps all official twelve criteria and maximum scores (24 total) to tasks and evidence status. The [Module 5 checklist](module5-checklist.md) maps all seven required Extension Pack capabilities. Official source revisions are linked in both documents. The original task rows and dependencies above remain intact; the following refinements add the precise full-score and completion gates discovered during the audit. Read these with the linked issue before implementation and record evidence against that issue.

| Task | Additional acceptance detail / completion gate |
| --- | --- |
| T01 / #1 | Official rubric and Module 5 sources are pinned; all criteria mapped and gaps recorded. Pilot assumptions A01–A06 require user decisions or an explicit accepted deferral before the pilot-review criterion is complete. Do not infer approval from silence. |
| T03 / #3 | Decide separate dev/production release topology, trace/log storage and UI, alert receiver authentication/deduplication, and Extension Pack runtime/format. Existing provider, orchestration, identity and data-handling ADR scope is retained. |
| T04 / #4 | A single documented Compose command starts the connected complete application including PostgreSQL and required services; clean-checkout evidence includes persistence after application restart. |
| T05 / #5 | Run tests automatically on every PR; prepare the same tested versioned artifact for automatic dev and manually initiated production releases in T16. Keep existing lint, type and merge-check scope. |
| T12 / #12 | Both unit and integration suites must pass with one documented command, using isolated real PostgreSQL and deterministic model stubs; retain command, exit status and CI evidence. Separate suite commands do not replace this gate. |
| T13 / #13 | Metrics, traces and structured logs are collected, stored and visible in a UI for a key journey with shared trace context and trace-ID correlation. Demonstrate async propagation and metric exemplars/drill-down; do not add high-cardinality trace-ID metric labels or sensitive telemetry. |
| T14 / #14 | The user-impact alert is routed to an authenticated receiver that automatically wakes the on-call agent; retain receipt, invocation and deduplication evidence as well as threshold/runbook evidence. |
| T15 / #15 | Show automatic alert-triggered wake-up, diagnosis, operator approval, agent-executed allowlisted repair and verified recovery. A manually started agent, diagnosis-only result, or human-executed fix does not complete this gate. Existing staging-only single-action limits remain. |
| T16 / #16 | Demonstrate tests, automatic dev deployment and a separate manual production deployment of a tested versioned artifact, plus existing HTTPS, secret, migration, backup and rollback requirements. Production may still use synthetic demo data. |
| T17 / #17 | Demonstrate every requirement in module5-checklist.md: instructions, reusable workflow, specialized subagent, MCP, hook/guardrail, package OR custom agent, and permissions note. No separate graded Module 5 homework exists. Defer an item only as an explicitly unmet requirement. |
| T18 / #18 | Audit actual evidence for all 12 criteria and all seven Module 5 items; record course-platform confirmation for three distinct mandatory peer reviews before claiming course completion. Keep platform-sensitive review details private. |

The T01 pilot assumption register is in [specification.md](specification.md#pilot-assumptions-requiring-confirmation). The product owner has now accepted a generic synthetic-only prototype with all A01–A06 provisional, real data/company connections deferred and fault-injection authorization deferred. This explicitly accepted deferral satisfies the pilot-review gate without company sign-off. Review and record T01 completion first, then review T02's original four criteria using actual tracker activity; see the public issues for current states.
