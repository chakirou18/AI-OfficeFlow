# Implemented architecture audit

Read against source `6a6098f6baa36e3b49b2dfdaacc721981237f102` on 2026-10-20.
[ADR 0010](adr/0010-minimal-zoomcamp-scope.md) remains the architectural decision.
This map distinguishes actual entry points from development instructions.

| Component | Entry point and actual calls | Enforced boundary / evidence |
| --- | --- | --- |
| Application analysis workflow | [analysis.py](../backend/app/analysis.py): authenticated `POST /api/v1/requests/{id}/analyses` → `execute_analysis` → [model adapter](../backend/app/model_adapter.py) → persisted pending proposal | `DEADLINE_SECONDS=30`, persisted deadline, cancellable call outside transactions, late-result rejection; no retries/tools/task inserts. Strict Pydantic schema: 1–5 tasks, bounded text, priority enum, extra fields forbidden |
| Real model adapter | `OllamaAdapter` uses fixed `llama3.2:3b`, local HTTP endpoint, bounded output and CPU configuration | Persisted allowance reserved under PostgreSQL advisory lock before dispatch; failures consume allowance; one active real call. Default/test mode simulated. [T10 actual evaluation](t10-verification.md) is separate |
| Human decision | [decisions.py](../backend/app/decisions.py): decision POST → `require_mutation` → `decide_analysis` | Session + Origin + CSRF; request then analysis locks; revalidates saved proposal; atomic task/decision commit and unique source index; rejection creates none. [Integration tests](../backend/tests/integration/test_decisions.py) |
| Read-only MCP | [mcp_server.py](../backend/app/mcp_server.py), `python -m app.mcp_server`, stdio `get_request_summary` | UUID input; one bounded read; PostgreSQL READ ONLY + 2 s statement timeout; no SQL/URL/write/approval tool. Trusted local launcher has DB configuration; no independent remote MCP auth/read-only DB principal claimed. [T17 protocol tests](../backend/tests/integration/test_extension_pack.py) |
| Specialized T17 reviewer | [.codex role](../.codex/agents/api-reviewer.toml), [portable Python launcher](../scripts/invoke_api_reviewer_process.py) supplies role/skill/patch to one fresh CLI process | Independent context/session, read-only/no escalation, tools disabled; six findings and unchanged source. [Evidence](evidence/t17-independent-reviewer.json). Earlier native attempts failed; no native spawn success or ongoing reviewer service |
| Review guardrail | [review_guard.py](../agent-hooks/review_guard.py): `guarded` checks exact role/actions/fixture digest before handler dispatch | Fixed read allowed; unknown/write/approval and corrupt policy denied before sentinel effects. Scope is this tool boundary, not a global shell sandbox or native lifecycle hook |
| Operational on-call | [oncall.py](../backend/app/oncall.py) authenticated webhook → [OnCallAgent.run](../backend/app/oncall_agent.py) → four fixed tools: incident, diagnostics, clear, verify | Deterministic Python, no LLM. Durable SQLite claim; 45 s workflow; development/exercise identity/expiry/known-cause checks; one authorized flag clear; bounded analysis verification with zero active tasks. [exercise.py](../backend/app/exercise.py) enforces the API boundary |
| Development instructions | [AGENTS.md](../AGENTS.md), [team/process](agent-team.md), [skill](../agent-capabilities/review-api-change/SKILL.md) | Context and working rules for coding assistance; not application agents, tool permissions or proof that delegation occurred |
| Telemetry | [telemetry.py](../backend/app/telemetry.py), [Compose](../compose.yaml), [collector](../infra/observability/collector.yaml) | Explicit metadata/route/outcome allowlists; no bodies, URLs, credentials or exception text; no ID metric labels. Collector → Prometheus/Loki/Tempo → authenticated loopback Grafana |
| Delivery | [CI](../.github/workflows/ci.yml) → [release](../.github/workflows/release.yml) → pending request → [controller](../scripts/deployment_controller.py); [manual promotion](../.github/workflows/promote.yml) | Trusted main CI, private immutable digests, fixed Compose commands, separate DB/secrets, compatible rollback. Controller stopped; no deployment in T18 |

The MCP tool and reviewer are not hops in the application analysis path. The
model cannot invoke on-call tools, approve its proposal or create active tasks.
The on-call identity cannot enable its own exercise or act as a demo user.
Browser fixture seeding is explicitly test-only; it is not human approval evidence.

Code inspection corroborates these controls; their executable evidence is linked
in [testing](testing.md), [Module 5](module5-checklist.md), [on-call](oncall-agent.md)
and [final handover](final-handover.md). No architecture/framework change was made.
