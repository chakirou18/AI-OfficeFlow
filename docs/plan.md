# Incremental final-project roadmap

Target: all 12 official criteria / 24 available points, all seven Module 5 items and three peer reviews. No grading points are claimed; runtime evidence is versioned in the final handover. Scope and decisions are in [specification.md](specification.md) and [ADR 0010](adr/0010-minimal-zoomcamp-scope.md).

## Recovery and current position

T01-T17 are completed; T18 is preparing a review PR. Initial T18 local/remote main matched `6a6098f6baa36e3b49b2dfdaacc721981237f102` with a clean tree. See [final handover](final-handover.md) for actual evidence and blockers.

The current scope supersedes the commercial/pilot direction. A01-A06 are retired. Earlier ADRs and issue evidence remain historical; only the small generic educational app is current. T01/T02 acceptance evidence remains useful and is reassessed without reopening completed work unnecessarily. T03 is a design task, not model/hosting procurement.

## Milestones and evidence gates

| Existing phase | Tasks and smallest useful increment | Exit evidence |
| --- | --- | --- |
| M0 — Requirements/governance | T01-T03: generic scope, public tracker, rubric/Extension Pack mapping and minimal ADR | Source links, current criteria, design review and issue-linked commits; no company validation gate |
| M1 — Foundation | T04: React/FastAPI/PostgreSQL, migrations, health and first database round trip. T05: early PR CI. T06: demo session/access protection | Core one-command startup, real database check, meaningful initial tests/CI and authentication evidence |
| M2 — Request/task UI | T07-T08: immutable requests, lists/detail, task states and dashboard | Browser create/refresh/task flow backed by PostgreSQL |
| M3 — Analysis | T09: bounded synchronous adapter and small read-only MCP tool. T10: task/priority analysis | Deterministic fixtures, timeout/error evidence, simulated-mode labeling and one authorized real-model evaluation |
| M4 — Approval/tests | T11-T12: atomic approve/reject and aggregate test runner | Duplicate/concurrent approval check, rejection-with-no-tasks, browser smoke and one-command unit/integration pass |
| M5 — Telemetry/alert | T13-T14: stored OTel metrics/logs/traces in Grafana and user-impact analysis-error alert | Shared trace context, UI drill-down, redaction and actual authenticated alert delivery |
| M6 — On-call repair | T15: prior-authorized dev-only analysis-flag incident, automatic agent diagnosis/fix/verification | Recorded alert wake-up and agent-executed repair; unknown cause fails closed |
| M7 — Extension Pack | T17: instructions, reusable workflow, specialized subagent, MCP, guardrail, custom agent, permissions note | All seven artifacts invoked/demonstrated, including the explicit custom-agent branch; runtime binding and subagent authorization verified |
| M8 — Delivery/evidence | T16: actual deployment, automatic dev/manual production, compatible-image rollback and small restore check. T18: final rubric evidence and peer reviews | Public URL or clear actual-deployment demo, pipeline runs, final clean-checkout guide and three peer-review confirmations |

Add checks with each feature; T12 consolidates them rather than postponing testing. Preserve dependencies in the [backlog](backlog.md): T04 follows T03, T05 follows T02/T04, T06 follows T04/T05, requests precede analysis, approval precedes final coverage, T13 may start after T09, and T16 needs T03/T12/T13. T17 requires T01/T10/T11 and now T15 for its selected custom-agent demonstration; all original edges remain. Phases group work without adding unnecessary dependencies or a second tracker.

## Official assessment

The [grading checklist](grading-checklist.md) is the exact twelve-criterion evidence map with maxima. Product Specification includes written criteria plus public tracker use; coding-agent responsibilities/context are documented separately from application agents. Application/Containerization need frontend/backend/persistence and complete one-command Compose startup. Testing needs both unit/integration suites passing with one command. CI/CD needs PR tests, automatic dev deployment and manual production deployment. Observability needs stored, UI-visible metrics/traces/structured logs sharing trace context. Alerting and actual alert-triggered repair are separate demonstrations.

The [Module 5 checklist](module5-checklist.md) retains all seven requirements; there is no separate graded homework. Three peer reviews are mandatory, independently of score. The course platform controls assignments/deadlines; none is assumed complete.

## Decisions deliberately delayed to their delivery task

- T10 selected and evaluated the installed local Ollama model; default CI remains simulated.
- T16 demonstrated automatic dev/manual production delivery on localhost, with recordings and recovery evidence; no public hosting is configured.
- T15 completed the exact authorized dev incident and one narrow automatic repair; repeat authorization is required.
- T17 completed the separately authorized independent reviewer process and reused the custom on-call agent; native spawn attempts remain unverified.

**Current: T18 handover review preparation.** T17 PR #35 is merged. Preserve historical evidence; do not rerun the reviewer, incident, model evaluation or deployment controller. Keep #18 open until its remaining acceptance gates are verified. See [final-handover.md](final-handover.md).
