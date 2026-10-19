# Architecture decision records

**Current:** [ADR 0010 — Minimal generic Zoomcamp final project](0010-minimal-zoomcamp-scope.md). It selects the small current architecture and explicitly supersedes the earlier pilot/enterprise design. Read it with [architecture.md](../architecture.md) and [specification.md](../specification.md). Design completion is not application implementation or approval to spend/deploy.

## Preserved, superseded history

ADRs 0001-0009 remain intact below their new supersession banner for rationale and history. Their company references, multi-agent/queue/revision/enterprise-role/package requirements and former live-provider/hosting blockers are not current scope. Do not implement them instead of ADR 0010.

| Historical ADR | Previous topic | Current disposition |
| --- | --- | --- |
| [0001](0001-system-stack.md) | Full-stack modular prototype | Retain React/FastAPI/PostgreSQL/Compose; simplify service boundaries |
| [0002](0002-persistence-and-jobs.md) | Revisions and durable queue | Replace with immutable requests and bounded synchronous analysis |
| [0003](0003-identity-and-approval.md) | Enterprise roles/session approval | Retain sessions/atomic human approval; remove role-management project |
| [0004](0004-agent-orchestration-and-mcp.md) | Sales/Coordination LangGraph and network MCP | One analyzer, ordinary Python; read-only MCP remains for Module 5 |
| [0005](0005-model-adapter-and-budgets.md) | Model abstraction/accounting | Retain disclosed stub/real evaluation and simple usage limits; final provider at T10 |
| [0006](0006-observability-and-alerting.md) | Stored telemetry/queue alert/repair | Retain signal stack; analysis-error alert and one pre-authorized dev repair |
| [0007](0007-delivery-hosting-and-rollback.md) | Release and hosting | Retain PR CI/dev-auto/prod-manual/compatible rollback; actual deployment choice at T16 |
| [0008](0008-tests-and-development-stages.md) | Verification/stages | Retain one-command tests/full boot; align with smaller backlog |
| [0009](0009-coding-agent-extension-pack.md) | Plugin package | Choose explicit custom-agent branch; preserve all seven Module 5 capabilities |

New ADRs should supersede, not erase, prior decisions. No installed version, model quality, live price, runtime command or deployed service is claimed by this index.
