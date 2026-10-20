# Module 5 Agent Extension Pack checklist

Current specialized-reviewer result: **verified independent subprocess execution**
on 2026-10-20 after fresh explicit approval. One Python supervisor (PID 18392)
launched one read-only CLI reviewer (PID 10512), fresh session
`01a157ef-afad-7132-933d-3c149d391fcd`. Exact instructions/input were verified,
six actual findings returned, zero tool items observed, and all 166 source hashes
were unchanged. See [execution evidence](evidence/t17-independent-reviewer.json)
and [independent findings](evidence/t17-independent-findings.md).
This is subprocess orchestration, **not native spawn_agent**. No retry occurred;
the one-run approval is consumed. The [consolidated demonstration](evidence/t17-integrated-demo.md) links all seven
requirements. Final-head required CI gates merge and issue closure.

Owner: [T17](https://github.com/chakirou18/AI-OfficeFlow/issues/17). [Official Module 5 source](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp/blob/de41e4096d8ac08db3852dfda4ce802f9ac0c0d2/05-agent-capabilities/README.md). There is **no separate graded Module 5 homework**; all seven requirements carry into the final project. The simpler MVP does not remove them.

The selected OR branch is the **existing T15 custom on-call agent**, not a new plugin. T09 MCP and T15 live evidence are reused. **All seven artifact/demonstration requirements are verified; final-head CI gates delivery**. The two native attempts remain unverified historical evidence; the separately authorized portable execution above supplies genuine isolated reviewer provenance. Registration files and exit codes alone never establish completion.

| Requirement | Existing or proposed artifact | Task and demonstration | Verified status |
| --- | --- | --- | --- |
| One project instructions file | [AGENTS.md](../AGENTS.md) and current Issue #17 | Main agent read instructions/current issue before work | Actual read completed; consolidated demonstration recorded |
| One reusable skill/workflow/command | [Canonical skill](../agent-capabilities/review-api-change/SKILL.md), [Codex discovery entry](../.agents/skills/review-api-change/SKILL.md) | [Actual main-agent review](evidence/t17-main-review.md) of the guarded synthetic patch | Both skill validators passed; runtime prompt inspection listed the skill; main agent loaded/applied it without executing the candidate |
| One specialized subagent | [Existing role instructions](../.codex/agents/api-reviewer.toml), [portable supervisor](../scripts/invoke_api_reviewer_process.py) | [Actual process/session evidence](evidence/t17-independent-reviewer.json), [independent findings](evidence/t17-independent-findings.md) | Verified one independent CLI reviewer in its own context; exact instructions/patch; zero tool items; unchanged source. Subprocess, not native spawn |
| One MCP tool/server | Existing [app.mcp_server](../backend/app/mcp_server.py), [T09](https://github.com/chakirou18/AI-OfficeFlow/issues/9) | [Real T17 stdio protocol test](../backend/tests/integration/test_extension_pack.py) plus existing PostgreSQL READ ONLY denial | Bounded read, invalid input, write/approval and unknown tool denials passed; zero tasks |
| One hook or guardrail | [Executable tool guardrail](../agent-hooks/README.md), [focused tests](../scripts/tests/test_review_guard.py) | Actual allowed read, blocked write and failed policy before side effects | Four focused tests passed; isolated sentinel unchanged. Tool-boundary guardrail, not a native lifecycle hook |
| One plugin/extension package OR custom agent | [Existing custom on-call package](../custom-agent/README.md), [implementation](../backend/app/oncall_agent.py) | Reuse [T15 actual incident](https://github.com/chakirou18/AI-OfficeFlow/issues/15) invocation/diagnosis/one authorized clear/recovery/deduplication | Real historical evidence reused; no new fault exercise or duplicate loop/plugin |
| One permission/security note | [permissions.md](permissions.md) | Actual MCP/guardrail denials, isolated read-only reviewer and existing model/auth/on-call/deployment controls | Updated; actual reviewer returned findings without tool calls or changed source; evidence reviewed; final-head CI gates delivery |

## Consolidated integrated demonstration

The [recorded sequence](evidence/t17-integrated-demo.md) consolidates actual
instruction/skill review, independent reviewer, read-only MCP, denied write and
final diff inspection. These were separate recorded steps, not a claimed single
continuous capture. Existing T15 repair evidence is reused. No reviewer, supervisor
or incident was rerun for consolidation.

Installed Codex CLI **0.163.0** uses the documented [standalone custom-agent TOML format](https://developers.openai.com/codex/subagents); parent permissions are inherited. The launcher selects native read-only/no-escalation and disables shell/apps/plugins. `codex debug prompt-input` listed the repo skill without invoking a model; it is not spawn proof. [Supported skill discovery](https://developers.openai.com/codex/skills) uses `.agents/skills`. No model/runtime/framework installation occurred. The launcher refused without an approval reference; that reference records actual consent and cannot create it. Any unavailable/unexecuted item stays incomplete.

## Historical first native attempt (failed)

After separate explicit user approval, the main agent ran exactly once:

```powershell
python scripts/invoke_api_reviewer.py --approval-reference "User explicitly authorized one read-only Codex supervisor and registered api_reviewer invocation for T17 in this conversation"
```

The supervisor explicitly used the supplied `review-api-change` skill, then returned
`UNSUPPORTED`: its available agent interface could not select/invoke the registered
type. Native JSONL contains one thread start, one turn start, two agent messages
and one turn completion, with **no subagent/tool invocation events**. It exited 0
as a completed supervisor turn, not as a successful review. Source hashes before
and after were identical. Raw events remain ignored in
`artifacts/t17-reviewer-events.jsonl`; the sanitized actual response and counts are
linked above. No application service was accessed, no file changed by the supervisor,
no generic reviewer substituted and no second supervisor invocation performed.

That approval was consumed. This attempt did not satisfy the reviewer requirement.
The later independently authorized subprocess execution supplies the successful
review evidence; it does not establish native spawn support. No further invocation
is authorized or needed.

## Executed preparation checks

The [2026-10-20 non-invoking diagnosis and prepared correction](evidence/t17-invocation-diagnosis.md)
pins the existing named role through a supported command override. No new model
turn or reviewer ran during that diagnosis. Subsequently, one freshly authorized
corrected launcher execution returned findings but **did not provide verifiable
native child invocation evidence**. See the [actual event summary](evidence/t17-corrected-attempt.json)
and [supervisor response, with provenance limitation](evidence/t17-corrected-supervisor-response.md).
Source hashes were unchanged; no retry occurred. That one-run approval is now
consumed. That native attempt did not satisfy the reviewer requirement. The later independent
subprocess result at the top of this document is the current successful evidence.

- Skill creator `quick_validate.py` passed for both canonical skill and discovery entry.
- `python agent-hooks/review_guard.py --read-fixture` returned the pinned synthetic diff; the main agent applied the skill and recorded its actual findings separately from the future independent review. The candidate was not applied/imported/executed.
- `python agent-hooks/review_guard.py --demo`: allowed read; unauthorized write and invalid policy denied with unchanged temporary sentinel.
- `python -m unittest discover -s scripts/tests -p test_review_guard.py -v`: **4 passed**; policy failure/corruption/expansion, changed fixture, unknown/approval operations and LF/CRLF handling covered.
- `docker compose --profile test run --build --rm test python -m alembic upgrade head`: exit 0 against the isolated `_test` database only; locked dependency layers reused.
- `docker compose --profile test run --rm test python -m pytest tests/integration/test_extension_pack.py tests/integration/test_mcp.py -q -s`: **3 passed in 9.18s**, MCP **2.3.0**, real subprocess stdio initialization/list/read/denials and actual PostgreSQL READ ONLY write rejection. Sanitized output records booleans, not request bodies or credentials.
- `python scripts/invoke_api_reviewer.py --help` and the missing-approval parser refusal were exercised without a model/subagent invocation.

Required CI job names remain Backend checks and Frontend checks. No final grading score or peer-review completion is claimed. T18 remains outside this task.

T17 retains T01/T10/T11 and additionally depends on T15 for the custom-agent demonstration. No original dependency is removed; preparation may proceed earlier but completion must link the actual evidence. See [ADR 0010](adr/0010-minimal-zoomcamp-scope.md) and the [grading checklist](grading-checklist.md).
