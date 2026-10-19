# Coding-agent team and collaboration

Status: proposed working model. No persistent agent team, delegated sessions, or completed agent work is claimed.

## Two distinct kinds of agents

**Coding agents** help developers design, implement, test, and document this repository. Their access comes from the developer environment and task authorization. They are not deployed product features.

**Business agents** run inside AI OfficeFlow. The Sales Agent extracts request information; the Coordination Agent proposes tasks and deadlines. They operate with scoped application identities and cannot approve or apply consequential changes. A separate **on-call agent** supports a constrained staging operations demonstration; it is neither a sales agent nor a general coding agent.

## Coding responsibilities

| Role | Owns | Expected handoff |
| --- | --- | --- |
| Lead / integrator | Scope, dependencies, public issue status, integration and honest evidence | Task identifier, acceptance criteria, affected interfaces, final review |
| Product / architecture | Stories, lifecycle rules, sector configuration, ADRs | Versioned requirements and interface decisions |
| Frontend | Request UI, review screens, dashboard and accessible feedback | UI changes, API assumptions, browser verification |
| Backend / data | APIs, persistence, identity, revisions, atomic approvals and migrations | Contracts, migration notes, integration results |
| Agent / tools | Graph, model adapter, prompts, MCP schemas and permission enforcement | Fixture evaluation, output schemas, failure behavior |
| QA / security | Behavioral, concurrency, access-control and adversarial checks | Reproduction steps, evidence, unresolved risks |
| Platform / operations | Compose, CI/CD, telemetry, runbooks and recovery exercise | Reproducible setup, dashboards, alert and rollback evidence |

One developer or coding agent may perform several roles. This document does not authorize spawning agents. Use a single active coding agent by default; delegate only when explicitly requested by the user. If delegation is authorized later, define non-overlapping file ownership and shared interface contracts before parallel edits.

## Collaboration workflow

1. Select a public issue (or local backlog ID until the tracker exists); read its criteria, prerequisites, AGENTS.md and relevant domain documents.
2. State the intended slice, ownership, interfaces, assumptions, and verification approach. Resolve requirements that affect permissions before implementing them.
3. Make a focused change, update documentation, and verify behavior with suitable tests. Coordinate interface changes before dependent work proceeds.
4. Handoff the changed files, exact checks and outcomes, known limitations, and evidence links. Do not claim unexecuted checks passed.
5. Review against acceptance criteria and security boundaries. The integrator resolves conflicts and records final evidence; maintainers authorize merge/release according to the task.

Public issues must show real progress and decisions throughout development. Never include secrets, private customer content, raw model prompts containing sensitive data, or internal access links in public handoffs.

## Business-agent contracts

The Sales Agent receives a versioned request snapshot and configured required fields; it returns structured facts, supporting excerpts, unknowns, and missing details. The Coordination Agent consumes that validated result and returns suggested internal tasks with assumptions. Neither has database write tools, approval rights, or outbound communication permissions.

The on-call agent reads a redacted incident view, proposes one bounded staging flag reset, waits for operator approval, and verifies recovery through a synthetic probe. Its credentials and audit trail remain separate from business-agent identities. Full rules are in [permissions.md](permissions.md).
