# Incremental implementation roadmap

Status: application implementation remains planned. Documentation, the public Git repository, and the [issue tracker](https://github.com/chakirou18/AI-OfficeFlow/issues) are available. T01–T18 have phase milestones and are linked in [the backlog](backlog.md). This setup does not complete M0 or validate the official rubric. Milestones are ordered by dependencies, not committed dates.

| Milestone | Scope | Exit evidence |
| --- | --- | --- |
| M0 — Requirements and project governance | Validate pilot assumptions, official rubric and Module 5 material; publish repository and tracker; refine acceptance criteria | Rubric links and mapping, prioritized issues, stakeholder assumptions, first ADRs |
| M1 — Runnable foundation | React, FastAPI, PostgreSQL, migrations, identity/roles, Compose, CI skeleton | Clean-checkout startup, protected endpoint checks, passing CI link |
| M2 — Request workflow | Create/list/detail, revisions, status rules, audit trail, minimal dashboard | Database integration tests and browser demonstration using synthetic data |
| M3 — Agent proposals | Durable jobs, provider adapter, Sales and Coordination graph, read-only MCP tools, fixture evaluation | Reproducible graph evaluation, failure/retry tests, persisted proposals |
| M4 — Human review | Review screens, atomic approval/rejection, stale-result protection and duplicate prevention | Browser flow and permission/concurrency integration tests |
| M5 — Operational visibility | Structured logs, OpenTelemetry, metrics, dashboards, queue-age alert and runbook | Trace correlation, redaction checks, controlled alert evidence |
| M6 — Safe on-call demonstration | Staging fault flag, constrained diagnostic agent, approval and verified recovery | Incident report, audit trail, demonstration recording |
| M7 — Extension Pack and hardening | Implement verified Module 5 Agent Extension Pack requirements; evaluate any additions against MVP boundaries | Requirement-to-artifact mapping, extension tests, permission review, updated docs |
| M8 — Public delivery and assessment | Public HTTPS staging, CI/CD, backup/restore and rollback rehearsal, final evidence review | Working access instructions, deployed release, pipeline links, demo and evidence index |

Add inexpensive CI checks early, then expand them with each feature. Deploy a minimal staging slice once M1–M2 are stable if the chosen host permits; M8 is the final delivery gate. Operational demonstrations require M4 approval boundaries and M5 telemetry first. Extension work may be brought forward when required by official material, without bypassing those controls.

## Provisional twelve-area evidence map

These areas reflect the project targets supplied at kickoff. Their numbering and grouping are **not a verified reproduction of the official grading rubric**. At M0, replace or reconcile this table with official criteria and exact source links. Do not claim full marks based on documentation alone.

| Area | Planned evidence | Milestone / backlog |
| --- | --- | --- |
| 1. Specification | User stories and measurable criteria in specification | M0 / T01 |
| 2. Public task tracking | Public issues with acceptance criteria, dependencies, and active status history | M0 onward / T02 |
| 3. Agent team specification | Coding roles, handoffs, and business-agent distinction | M0 / T01, T02 |
| 4. Modular context documentation | AGENTS.md, linked domain documents, later ADRs | All / T01, T03, T17 |
| 5. Working full-stack application | Persisted browser-to-API-to-database demonstration | M2–M4 / T04–T11 |
| 6. Unit and integration tests | Automated test suites and CI results | All implementation / T12 |
| 7. Containerization | Reproducible Compose startup and health checks | M1 / T04 |
| 8. Public deployment | Verified HTTPS staging URL and access instructions | M8 / T16 |
| 9. CI/CD | Required checks, release workflow, rollback evidence | M1, M8 / T05, T16 |
| 10. Observability | Traces, metrics, structured logs and dashboards | M5 / T13 |
| 11. User-impact alerting | Queue-age alert exercise and runbook | M5 / T14 |
| 12. On-call agent | Scoped recovery, human approval, verification evidence | M6 / T15 |

The Module 5 Agent Extension Pack is an additional explicit checkpoint, tracked by T01 and T17. Its contents have not been supplied or verified; no particular extension is claimed as mandatory or implemented.

## Delivery discipline

Move one demonstrable vertical slice through implementation, tests, documentation, and review before expanding scope. Use deterministic provider stubs in CI and separate opt-in live model evaluations. Attach actual evidence to public issues, use synthetic data in screenshots, and record known gaps honestly. A milestone is complete only after its exit evidence exists.
