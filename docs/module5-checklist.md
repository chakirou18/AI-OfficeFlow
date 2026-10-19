# Module 5 Agent Extension Pack checklist

Owner: [T17](https://github.com/chakirou18/AI-OfficeFlow/issues/17). [Official Module 5 source](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp/blob/de41e4096d8ac08db3852dfda4ce802f9ac0c0d2/05-agent-capabilities/README.md). There is **no separate graded Module 5 homework**; all seven requirements carry into the final project. The simpler MVP does not remove them.

The selected OR branch is **custom agent**, using the explicitly documented/tested on-call agent. This supersedes the earlier proposed plugin package and avoids a second package platform. It counts only with a real custom-agent artifact/loop/demo, not because an operational role is mentioned. No runtime item is implemented yet.

| Requirement | Existing or proposed artifact | Task and demonstration | Verified status |
| --- | --- | --- | --- |
| One project instructions file | Existing AGENTS.md and modular context links | T01/T17: show agent reads instructions and current issue, obeys scope and records evidence | File exists; full integrated demo pending |
| One reusable skill/workflow/command | Proposed `agent-capabilities/review-api-change/SKILL.md` | T17: invoke repeatable API/approval review workflow on a synthetic change; record input, findings and checks | Not created/invoked |
| One specialized subagent | Proposed `agent-capabilities/subagents/api-reviewer.md` plus supported runtime registration | T17: explicitly authorized invocation in separate scoped context; review schema/approval changes and hand findings back | Not registered/invoked; role prose is insufficient |
| One MCP tool/server | Proposed local read-only stdio tool `get_request_summary` under `tools/` | T09/T17: invoke on a synthetic request using scoped read access; show bounded result and denied write/unknown tool | Not implemented/invoked; no business-profile/staff service required |
| One hook or guardrail | Proposed executable guardrail under `agent-hooks/` for reviewer/tool scope | T17: intercept an unauthorized write before effects and demonstrate an allowed read | Policy only; enforcement/demo absent |
| One plugin/extension package OR custom agent | Proposed on-call custom agent under `custom-agent/`, with README/configuration and bounded diagnostic/action loop | T15/T17: show alert invocation, diagnosis, permitted fix and verification, including explicit custom-agent setup/loop evidence; no separate plugin required | Custom-agent branch selected; artifact/demo absent |
| One permission/security note | Existing permissions.md, updated for small scope | T17: explain demo/model/MCP/on-call/CI identities and demonstrate denial without secrets | Note exists; runtime verification pending |

## Planned integrated demonstration

Read AGENTS.md and the relevant issue; invoke the reusable API-review workflow; invoke the authorized specialized reviewer; call the read-only MCP tool; show the guardrail preventing a forbidden write; have a human inspect the final diff. Link exact checks, findings, runtime versions, commit and sanitized transcript to T17. Separately show the custom on-call loop and actual alert-driven repair in T15/T17. One recording may combine steps but must make all seven artifacts clear.

Runtime registration syntax is selected against an available supported tool at T17, not invented now. No subagent spawning, model spend, custom-agent execution or operational exercise is authorized by this documentation task. Default tests use deterministic fixtures. An unimplemented/deferred item stays an unmet requirement, never a completed checkbox.

T17 retains T01/T10/T11 and additionally depends on T15 for the custom-agent demonstration. No original dependency is removed; preparation may proceed earlier but completion must link the actual evidence. See [ADR 0010](adr/0010-minimal-zoomcamp-scope.md) and the [grading checklist](grading-checklist.md).
