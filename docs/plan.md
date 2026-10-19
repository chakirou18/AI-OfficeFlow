# Incremental implementation roadmap

Status: application implementation remains planned. Documentation, the public Git repository, and the [issue tracker](https://github.com/chakirou18/AI-OfficeFlow/issues) are available. T01–T18 have phase milestones and are linked in [the backlog](backlog.md). The official rubric and Module 5 requirements have been source-checked under T01; pilot assumptions remain pending, so M0 and T01 are not complete. Milestones are ordered by dependencies, not committed dates.

| Milestone | Scope | Exit evidence |
| --- | --- | --- |
| M0 — Requirements and project governance | Validate pilot assumptions, official rubric and Module 5 material; publish repository and tracker; refine acceptance criteria | Rubric links and mapping, prioritized issues, stakeholder assumptions, first ADRs |
| M1 — Runnable foundation | React, FastAPI, PostgreSQL, migrations, identity/roles, Compose, CI skeleton | Clean-checkout startup, protected endpoint checks, passing CI link |
| M2 — Request workflow | Create/list/detail, revisions, status rules, audit trail, minimal dashboard | Database integration tests and browser demonstration using synthetic data |
| M3 — Agent proposals | Durable jobs, provider adapter, Sales and Coordination graph, read-only MCP tools, fixture evaluation | Reproducible graph evaluation, failure/retry tests, persisted proposals |
| M4 — Human review | Review screens, atomic approval/rejection, stale-result protection and duplicate prevention; unified unit/integration runner | Browser flow and permission/concurrency integration tests; both suites pass with one command |
| M5 — Operational visibility | Structured logs, OpenTelemetry, metrics, signal collection/storage/UI, queue-age alert and runbook | Shared trace-ID correlation including async work, redaction checks, controlled alert delivery evidence |
| M6 — Safe on-call demonstration | Staging fault flag, automatic alert-triggered agent wake-up, diagnosis, operator approval and agent-executed repair | Incident report showing automatic invocation, allowlisted reset, verified recovery, audit trail and recording |
| M7 — Extension Pack and hardening | Implement all seven Module 5 items: instructions, workflow, specialized subagent, MCP, guardrail, package or custom agent, permission note | Each artifact demonstrated, including scoped coding-agent use; tests, permission review and human-reviewed diff |
| M8 — Public delivery and assessment | Public HTTPS staging/dev, automatic tested dev deployment, manually initiated production promotion, backup/restore and rollback rehearsal, final evidence and peer reviews | Working access instructions, both release-path runs, demo/evidence index and three course-platform peer-review confirmations |

Add inexpensive CI checks early, then expand them with each feature. Deploy a minimal staging slice once M1–M2 are stable if the chosen host permits; M8 is the final delivery gate. Operational demonstrations require M4 approval boundaries and M5 telemetry first. Extension work may be brought forward when required by official material, without bypassing those controls.

## Official assessment and Extension Pack gates

The [grading checklist](grading-checklist.md) is the detailed evidence map, using the official 12 criteria / 24-point rubric verified at pinned course commit `de41e4096d8ac08db3852dfda4ce802f9ac0c0d2`. It replaces the kickoff provisional grouping and records actual evidence status. No full-score claim is made.

| Official criterion (maximum) | Planned evidence | Milestone / backlog |
| --- | --- | --- |
| 1. Problem Description (2) | README explains problem, functionality and expected behavior | M0 / T01, T18 |
| 2. Product Specification (2) | Written specification plus public tasks with acceptance criteria and coding-agent use evidence | M0 onward / T01, T02 |
| 3. Agent Team Specification (2) | Coding roles, handoffs, and business-agent distinction | M0 / T01, T17 |
| 4. Context Management (2) | AGENTS.md, linked modular documents, later ADRs | All / T01, T03, T17 |
| 5. Application (2) | Connected frontend/backend/persistent database and one-command local startup | M2–M4 / T04–T11 |
| 6. Testing (2) | Unit and integration suites pass with one command; CI evidence | All implementation / T05, T12 |
| 7. Containerization (2) | One-command complete Compose startup including database | M1 / T04 |
| 8. Deployment (2) | Public URL or clear deployment demo; project retains HTTPS staging target | M8 / T16 |
| 9. CI/CD (3) | PR tests, automatic dev deployment, manual production deployment and rollback | M1, M8 / T05, T16 |
| 10. Observability (2) | Metrics/traces/structured logs share trace context, collected/stored and visible in UI without sensitive content | M5 / T13 |
| 11. Alerting on User Impact (1) | Working queue-age alert, delivery exercise and runbook | M5 / T14 |
| 12. On-Call Agent (2) | Alert wakes agent; operator-approved staging repair is executed by agent and verified | M6 / T15 |

The [Module 5 checklist](module5-checklist.md) maps all seven required Extension Pack capabilities to proposed artifacts, tasks and demo steps. Module 5 has no separately graded homework. Existing AGENTS.md and permissions.md provide two document artifacts; the full demonstration and other runtime artifacts remain unimplemented. T17 must not be closed on the basis of proposals alone.

**Three peer reviews are mandatory to pass**, independently of points. T18 owns completion evidence for three distinct course-assigned reviews; dates/assignments must be checked on the course platform. Do not publish private feedback or claim completion before submission is confirmed.

T01 remains open pending explicit decisions on the [pilot assumption register](specification.md#pilot-assumptions-requiring-confirmation). Review T02 for completion only after T01's dependency is satisfied. T03 architecture decisions follow that requirements gate; independent research does not waive it.

## Delivery discipline

Move one demonstrable vertical slice through implementation, tests, documentation, and review before expanding scope. Use deterministic provider stubs in CI and separate opt-in live model evaluations. Attach actual evidence to public issues, use synthetic data in screenshots, and record known gaps honestly. A milestone is complete only after its exit evidence exists.
