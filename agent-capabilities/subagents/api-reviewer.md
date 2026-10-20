# Registered API reviewer

Current resolution: a freshly authorized single [portable supervisor](../../scripts/invoke_api_reviewer_process.py)
execution produced a genuine separate CLI reviewer process/session, exact existing
TOML instructions, six independent findings and unchanged source hashes.
See [actual evidence](../../docs/evidence/t17-independent-reviewer.json) and
[findings](../../docs/evidence/t17-independent-findings.md). This is explicitly
**subprocess orchestration**, not native spawning. No retry is authorized; approval
is consumed. The sections below retain the historical native mechanism/results.

The native Codex registration is
[.codex/agents/api-reviewer.toml](../../.codex/agents/api-reviewer.toml).
It uses the installed CLI's standalone TOML fields `name`, `description` and
`developer_instructions`, with supported capability reductions. No model or
reasoning override is selected. Shell, apps, plugins, memories and permission
requests are disabled. Its role is to review the supplied synthetic API change
and return independent findings; it cannot approve tasks or repair the app.

The [reusable review skill](../review-api-change/SKILL.md) defines the review.
The [.agents discovery entry](../../.agents/skills/review-api-change/SKILL.md)
routes to that canonical workflow. This project deliberately tracks only those
two explicit files in otherwise ignored local configuration directories.

Historical native mechanism (not a current invocation instruction): ask the human to authorize **one ephemeral Codex CLI supervisor
spawning one registered `api_reviewer`**, reviewing only the supplied synthetic
patch and reporting back. The exact prepared command is:

```powershell
python scripts/invoke_api_reviewer.py --approval-reference "<actual explicit user approval>"
```

The launcher uses the existing ChatGPT CLI login, a native read-only parent sandbox,
no approval escalation, no daemon, no shell/apps/plugins and at most one concurrent
subagent. It supplies guarded fixture data and canonical skill instructions without
the main agent's findings. Custom agent files inherit parent permissions; putting
`sandbox_mode` inside the custom agent file would not establish this boundary.

The approval reference is an audit aid, not authorization by itself. No invocation
is permitted before the separate user approval. Raw JSONL/final output is retained
locally under ignored `artifacts/t17-reviewer-*`; inspect native spawn identity,
returned findings and source hashes before reporting success. An unavailable
registered type, runtime failure or unexecuted invocation remains an unmet item.

Reference: [official Codex subagents](https://developers.openai.com/codex/subagents).

## Historical first native result

The user approved one exact invocation and the launcher ran once on source commit
`3404eacad124f664f695dfdd02924ef336dab662`. The native supervisor used the supplied
skill but reported `UNSUPPORTED`: its available interface could not select/invoke
the registered `api_reviewer` type. It spawned no child and returned no independent
findings. Source hashes were unchanged. Its zero process exit code means the
supervisor turn completed; it is **not** proof of a review.

[Sanitized actual result](../../docs/evidence/t17-reviewer-attempt.json) and
[native response](../../docs/evidence/t17-supervisor-response.md) are retained.
This first attempt did not satisfy the subagent requirement. The later independent
subprocess result above does; it is not native spawn evidence. Do not retry.
A compatible named-agent interface and fresh explicit invocation approval are
required for any new native attempt; no such attempt is needed for consolidation. This records a limitation of the observed invocation surface,
not a claim that every Codex surface lacks custom agents.
