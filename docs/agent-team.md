# Coding-agent team and collaboration

This document specifies responsibilities for coding assistance, not a deployed multi-agent product. The repository is exclusively an educational final project with synthetic data.

## Responsibilities

| Coding role | Responsibility | Handoff evidence |
| --- | --- | --- |
| Lead/integrator | Select issue, resolve interfaces/scope, review changes and maintain tracker | Issue ID, diff, checks, decisions and known gaps |
| Product/architecture | Keep small specification, ADR 0010, rubric and Module 5 mappings aligned | Acceptance criteria and design rationale |
| Implementer | Build the current small slice across UI/API/database as needed | Code/contract/migration changes with exact test outcomes |
| QA/API reviewer | Independently inspect behavior, approval consistency, access and failures | Reproduction, findings and evidence; later specialized-subagent artifact |
| Operations reviewer | Verify Compose, release paths, stored telemetry, alert and bounded recovery | Commands, dashboards, pipeline runs and recovery recording |

One coding agent may perform several roles sequentially. A role description is not evidence of a running specialized subagent. Do not spawn/delegate unless explicitly authorized by the user; this documentation session does not invoke a subagent. T17 demonstrated one separately authorized specialized reviewer in an independent CLI process/session; [evidence](evidence/t17-integrated-demo.md) distinguishes it from unsuccessful native spawn attempts. That authorization is consumed.

## Collaboration process

1. Read AGENTS.md, relevant modular docs and the current public issue, criteria, dependencies and latest comments before implementation.
2. State the smallest slice and interface assumptions. Use current ADR 0010; older ADRs 0001-0009 are historical and explicitly superseded.
3. Implement only authorized work; use deterministic model mode and real PostgreSQL integration tests where applicable. Update relevant docs with the change.
4. Record exact commands/results, commits/PRs, decisions, limitations and artifacts in the issue while work happens. Never claim unrun checks passed.
5. Move to review with evidence. Close only after current criteria and completion dependencies are satisfied; maintain exactly one status label. Reopen only with a documented reason.

Issue comments and commits already provide evidence of coding-agent tracker use for documentation/governance. They do not prove application tests, deployment or a multi-agent runtime. Keep credentials and private data out of public handoffs.

## Application and operational agents

The **Request Analysis Agent** is one bounded application workflow: read a synthetic request, call the model adapter once, validate proposed tasks/priorities and return a pending suggestion set. It cannot approve its own result. Sales/Coordination agents and company profiles are retired from current scope.

The **On-Call Agent** is a separate custom operational process triggered automatically by Alertmanager. Under the exact human-authorized T15 dev exercise, it reads bounded diagnostics, diagnoses the known analysis-disable flag, clears only that flag, and verifies recovery. It has no task-approval permission, shell, deployment ability or production mutation. Its explicit artifact and demonstration also fulfill the selected custom-agent branch of Module 5; that does not automatically satisfy the other six items.

See [permissions.md](permissions.md), [Module 5 checklist](module5-checklist.md) and [grading checklist](grading-checklist.md). No business workflow stakeholder approval is required or claimed in this project.
