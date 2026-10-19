# Implementation backlog

All tasks are **planned**. Identifiers below are stable local references, not existing public issues. Dependencies mean prerequisites for completion; independent preparation may start earlier.

A **public tracker must be created and actively used** after the repository/platform is selected. Create one public issue per task, copy its acceptance criteria and dependencies, add labels and milestones, and link issue URLs here. Maintain Todo / In progress / In review / Done states throughout development. Link changes, tests, ADRs, and demonstrations to the issues; do not create a retrospective tracker only at submission time. No tracker exists yet.

| ID | Task | Acceptance criteria | Dependencies |
| --- | --- | --- | --- |
| T01 | Validate requirements and assessment targets | Pilot assumptions reviewed; official 2026 rubric and Module 5 sources linked; every official criterion mapped to an issue/evidence item; specification gaps recorded | None |
| T02 | Establish public project tracking | Public repository/tracker URLs recorded; T01–T18 imported with criteria and dependencies; milestones and status workflow configured; ongoing work updates visible | T01 |
| T03 | Resolve foundational architecture | ADRs select orchestration, model, authentication, hosting, and telemetry; decisions include alternatives, costs, data handling, and permission implications | T01 |
| T04 | Create runnable full-stack skeleton | React, API, worker, database and migrations start from a clean checkout through Compose; health checks succeed; example environment file contains placeholders only | T03 |
| T05 | Establish CI checks | Pull-request workflow runs lint/type checks, unit tests and PostgreSQL integration tests; deliberate failed check blocks merge under configured branch rules; actual run linked | T02, T04 |
| T06 | Implement identity and role enforcement | Controlled accounts and backend role checks match specification; anonymous and forbidden cases tested; public access requires authentication; role changes audited | T04, T05 |
| T07 | Implement request persistence and API | Create/list/detail, validation, pagination, immutable revisions and legal transitions satisfy US-01/02; migrations and real-database tests pass | T06 |
| T08 | Build request UI and dashboard | Forms, list, detail, status filters, counts and activity display persisted data; loading/empty/error states demonstrated; browser smoke check covers capture and reload | T07 |
| T09 | Implement durable agent execution and tools | Jobs survive worker restart; leases and bounded retries tested; MCP exposes only profile/staff reads with scoped authorization; provider adapter supports deterministic stubs | T03, T07 |
| T10 | Implement Sales and Coordination agents | Versioned structured outputs and prompts; at least 10 synthetic fixtures evaluated against US-03/04; unknown facts remain unknown; failures and adversarial input cannot trigger mutations | T09 |
| T11 | Implement human review and approval | US-05 passes end to end; transactions enforce revision checks and roles; rejection applies nothing; duplicate/concurrent approval creates tasks once | T08, T10 |
| T12 | Complete meaningful automated coverage | Unit and PostgreSQL integration suites cover lifecycle, jobs, failures, permissions and concurrency; browser test covers approved/rejected paths; CI results linked; live-model tests opt-in | T05, T11 |
| T13 | Add observability | API/worker/MCP traces correlate; Prometheus metrics and Grafana dashboard expose API latency/errors and queue age; logs/traces pass redaction review; setup documented | T09 |
| T14 | Add user-impact alert and runbook | Queue age over 120 seconds for 2 minutes triggers a routed staging alert; runbook links and recovery instructions work; exercise timing and alert evidence recorded | T13 |
| T15 | Demonstrate constrained on-call recovery | Staging fault injection, redacted diagnosis, operator-approved flag reset, single-action limit, audit and synthetic verification satisfy US-08; failed recovery stops and escalates | T11, T14 |
| T16 | Deploy publicly through CI/CD | Authenticated HTTPS staging contains synthetic data; release uses required checks and protected secrets; migrations, backup/restore, rollback and access instructions verified; URL and pipeline evidence recorded | T03, T12, T13 |
| T17 | Deliver Module 5 Agent Extension Pack checkpoint | Verified requirements mapped individually to implementation, tests and documentation; any deferred item has explicit rationale and assessment impact; scope/permission changes reviewed | T01, T10, T11 |
| T18 | Assemble final evidence and handover | All official criteria cross-checked; actual CI/deployment/demo/alert/recovery links included; performance target measured; limitations, setup and operations docs validated from clean checkout | T02, T12, T15, T16, T17 |

Each implementation task includes updating relevant documentation and recording evidence before closure. T12 consolidates coverage; testing begins with the first implementation task. T18 must flag unmet criteria rather than replacing missing evidence with claims.
