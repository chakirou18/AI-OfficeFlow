# ADR 0008 — Verification contracts and incremental delivery

> SUPERSEDED by [ADR 0010](0010-minimal-zoomcamp-scope.md). Historical design only: company references and prior requirements/statuses below are not current scope. Retained for rationale and Git/issue evidence; use the current specification and ADR 0010 for implementation.

Status: **Accepted for prototype design**. Owner: T03; implementation: T04–T18. No test command or application exists yet.

## Decision

Preserve the existing backlog IDs and completion dependencies. Deliver vertical slices with documentation, tests and public issue evidence; do not introduce a second untracked implementation plan. Adopt these planned verification contracts:

- `docker compose up --build`: core UI/API/database/worker/MCP startup, migration readiness and persistent data. The stub permits startup without model credentials. Initial protected user access requires a controlled account provision step, documented separately; no insecure built-in password.
- `docker compose --profile test run --build --rm test`: a single aggregate unit/integration command. Its service dependencies provision an isolated PostgreSQL database, apply schema and run both suites; nonzero status from any suite fails the command. It never uses development/production connection strings.
- `docker compose --profile observability up --build`: planned full monitoring demonstration stack with core services and persistent signal storage. Actual service names/configuration must be verified during implementation.
- Frontend checks and browser smoke tests remain required additional scope, with commands updated in AGENTS.md once scripts exist. CI uses deterministic model/tool stubs and a real PostgreSQL test service; live-provider evaluations are separately authorized opt-in evidence, not default CI requirements.

Unit tests cover domain validation, lifecycle, role policy, schema/agent output and budget calculations. Integration tests exercise transactions, lease fencing, restart/retry, concurrency/idempotency, approval atomicity, session/CSRF boundaries, MCP denial and database constraints. Browser tests cover create → persisted detail → analysis → review → approve/reject → dashboard. Later operational tests demonstrate signal redaction/correlation, alert delivery and an explicitly authorized recovery exercise. Do not create tests that merely mirror implementation or claim performance targets before measurement.

## Stages and completion dependencies

| Stage | Backlog | Gate |
| --- | --- | --- |
| Governance/design | T01, T02, T03 | Accepted prototype deferral, functioning tracker and ADR baseline; finish outstanding paid/live-service decisions before T03 completion |
| Foundation and early CI | T04, T05 | Local stack/schema/health and contract baseline; PR checks; version pins/lockfiles verified |
| Access and requests | T06, T07, T08 | Protected persisted API plus UI/dashboard; role checks and account procedure |
| Jobs/tools/agents | T09, T10 | Durable execution, scoped MCP, typed graph, synthetic evaluation and visible stub mode |
| Review and consolidated tests | T11, T12 | Atomic human approval, stale/duplicate protection; one-command unit/integration pass and browser evidence |
| Telemetry and alerts | T13, T14 | Collected/stored/UI-visible signals, correlation and working user-impact alert |
| Operational demo | T15 | Explicit exercise authorization plus alert-triggered actual approved repair and recovery evidence |
| Extensions and delivery | T17, T16, T18 | Seven Module 5 demos, approved hosting, automatic dev/manual production evidence, rollback, final rubric audit and three peer reviews |

This table groups work, not new dependency edges: T13 can start after T09; T16 requires T03/T12/T13; T17 requires T01/T10/T11. Early implementation may prepare independent parts of a dependency-gated task, but cannot close it before prerequisites. Local-only T04 preparation needs a new implementation instruction; this design request does not authorize code generation.

## Alternatives, costs and security

A big-bang full stack hides integration risk; incremental slices expose it sooner. Mocking the entire database is fast but insufficient for transaction/queue behavior. Requiring live model responses in CI introduces cost, nondeterminism and secrets, so use offline fixtures with separate quality evaluation. A single test script outside containers is possible but adds local Python/database setup and weaker startup parity.

Benefits: reproducibility and visible evidence; trade-offs: real-database CI and browser tests consume runtime, memory and maintenance effort. CI usage is subject to actual platform allowances; no free unlimited runner claim is made. Test credentials are scoped to synthetic ephemeral databases; teardown must target only verified test resources and must never use indiscriminate volume deletion. No tests have been run because implementation has not started.
