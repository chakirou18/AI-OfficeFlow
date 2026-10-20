# Module 5 Agent Extension Pack checklist

Owner: [T17](https://github.com/chakirou18/AI-OfficeFlow/issues/17). [Official Module 5 source](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp/blob/de41e4096d8ac08db3852dfda4ce802f9ac0c0d2/05-agent-capabilities/README.md). There is **no separate graded Module 5 homework**; all seven requirements carry into the final project. The simpler MVP does not remove them.

The selected OR branch is the **existing T15 custom on-call agent**, not a new plugin. T09 MCP and T15 live evidence are reused. T17 implementation and isolated checks are in progress; the exact specialized reviewer invocation remains pending separate explicit approval. Registration files alone do not complete that item.

| Requirement | Existing or proposed artifact | Task and demonstration | Verified status |
| --- | --- | --- | --- |
| One project instructions file | [AGENTS.md](../AGENTS.md) and current Issue #17 | Main agent read instructions/current issue before work | Actual read completed; integrated reviewer still pending |
| One reusable skill/workflow/command | [Canonical skill](../agent-capabilities/review-api-change/SKILL.md), [Codex discovery entry](../.agents/skills/review-api-change/SKILL.md) | [Actual main-agent review](evidence/t17-main-review.md) of the guarded synthetic patch | Both skill validators passed; runtime prompt inspection listed the skill; main agent loaded/applied it without executing the candidate |
| One specialized subagent | [Native TOML registration](../.codex/agents/api-reviewer.toml), [scope and launcher](../agent-capabilities/subagents/api-reviewer.md) | One separately approved read-only native reviewer invocation | Prepared, not invoked; explicit approval and actual spawn/findings evidence pending |
| One MCP tool/server | Existing [app.mcp_server](../backend/app/mcp_server.py), [T09](https://github.com/chakirou18/AI-OfficeFlow/issues/9) | [Real T17 stdio protocol test](../backend/tests/integration/test_extension_pack.py) plus existing PostgreSQL READ ONLY denial | Bounded read, invalid input, write/approval and unknown tool denials passed; zero tasks |
| One hook or guardrail | [Executable tool guardrail](../agent-hooks/README.md), [focused tests](../scripts/tests/test_review_guard.py) | Actual allowed read, blocked write and failed policy before side effects | Four focused tests passed; isolated sentinel unchanged. Tool-boundary guardrail, not a native lifecycle hook |
| One plugin/extension package OR custom agent | [Existing custom on-call package](../custom-agent/README.md), [implementation](../backend/app/oncall_agent.py) | Reuse [T15 actual incident](https://github.com/chakirou18/AI-OfficeFlow/issues/15) invocation/diagnosis/one authorized clear/recovery/deduplication | Real historical evidence reused; no new fault exercise or duplicate loop/plugin |
| One permission/security note | [permissions.md](permissions.md) | Actual MCP/guardrail denials, existing model/auth/on-call/deployment controls | Updated; native reviewer runtime enforcement awaits approved invocation |

## Planned integrated demonstration

Read AGENTS.md and the relevant issue; invoke the reusable API-review workflow; invoke the authorized specialized reviewer; call the read-only MCP tool; show the guardrail preventing a forbidden write; inspect the final diff. The first two steps and isolated MCP/guardrail checks have run; the actual reviewer and final integrated sequence remain gated. Record native spawn identity, findings, unchanged source hashes, commands and limitations. Reuse the real T15 repair evidence rather than repeat a live fault.

Installed Codex CLI **0.163.0** uses the documented [standalone custom-agent TOML format](https://developers.openai.com/codex/subagents); parent permissions are inherited. The launcher selects native read-only/no-escalation and disables shell/apps/plugins. `codex debug prompt-input` listed the repo skill without invoking a model; it is not spawn proof. [Supported skill discovery](https://developers.openai.com/codex/skills) uses `.agents/skills`. No model/runtime/framework installation occurred. The launcher refused without an approval reference; that reference records actual consent and cannot create it. Any unavailable/unexecuted item stays incomplete.

## Executed preparation checks

- Skill creator `quick_validate.py` passed for both canonical skill and discovery entry.
- `python agent-hooks/review_guard.py --read-fixture` returned the pinned synthetic diff; the main agent applied the skill and recorded its actual findings separately from the future independent review. The candidate was not applied/imported/executed.
- `python agent-hooks/review_guard.py --demo`: allowed read; unauthorized write and invalid policy denied with unchanged temporary sentinel.
- `python -m unittest discover -s scripts/tests -p test_review_guard.py -v`: **4 passed**; policy failure/corruption/expansion, changed fixture, unknown/approval operations and LF/CRLF handling covered.
- `docker compose --profile test run --build --rm test python -m alembic upgrade head`: exit 0 against the isolated `_test` database only; locked dependency layers reused.
- `docker compose --profile test run --rm test python -m pytest tests/integration/test_extension_pack.py tests/integration/test_mcp.py -q -s`: **3 passed in 9.18s**, MCP **2.3.0**, real subprocess stdio initialization/list/read/denials and actual PostgreSQL READ ONLY write rejection. Sanitized output records booleans, not request bodies or credentials.
- `python scripts/invoke_api_reviewer.py --help` and the missing-approval parser refusal were exercised without a model/subagent invocation.

Required CI job names remain Backend checks and Frontend checks. No final grading score or peer-review completion is claimed. T18 remains outside this task.

T17 retains T01/T10/T11 and additionally depends on T15 for the custom-agent demonstration. No original dependency is removed; preparation may proceed earlier but completion must link the actual evidence. See [ADR 0010](adr/0010-minimal-zoomcamp-scope.md) and the [grading checklist](grading-checklist.md).
