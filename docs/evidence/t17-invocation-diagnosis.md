# T17 non-invoking launcher diagnosis — 2026-10-20

Historical preparation record. A subsequent explicitly authorized single execution
is recorded in [the corrected-attempt summary](t17-corrected-attempt.json). It
returned claimed reviewer findings but no verifiable native spawn/child identity.
The fresh approval below has been consumed; no retry is authorized.

No supervisor/model turn or subagent was invoked during this diagnosis. The
previous one-time approval remains consumed. Issue #17 stays open and PR #35
stays draft/unmerged. No runtime/model update was performed.

## Findings and limits

Installed CLI: `codex-cli 0.163.0`. `codex features list` reports `multi_agent`
stable/enabled and `multi_agent_v2` stable/disabled. The existing standalone
`.codex/agents/api-reviewer.toml` parses as TOML with the expected name,
description, developer instructions and tool restrictions.

The claim that `--ignore-user-config` directly disables project configuration is
**not confirmed for this release**. Official CLI help says it skips the user
configuration. The exact release loader has separate `ignore_user_config` and
`ignore_project_config` controls; project discovery consults merged trust
configuration, so removing user configuration can also remove user trust settings.
Normal `config/read` returned an enabled project layer, no disabled reason and no
explicit agent mapping. Standalone discovery is resolved later: this response
alone cannot establish whether the native role registry was populated.

The exact release's tool builder exposes `agent_type` only when its custom role
registry is nonempty. That matches the earlier supervisor's reported missing
selection interface, but the historical JSONL does not contain its tool schema.
An empty/unloaded role registry remains the suspected immediate cause, not a
proven flag-specific defect. Debug prompt rendering returns messages, not the
tool schema, and is not treated as proof of discovery.

Primary references:

- [Official CLI reference](https://developers.openai.com/codex/cli/reference)
- [Official project configuration and trust](https://developers.openai.com/codex/config-basic)
- [Official named subagents](https://developers.openai.com/codex/subagents)
- [Exact release configuration loader](https://github.com/openai/codex/blob/rust-v0.163.0/codex-rs/config/src/loader/mod.rs)
- [Exact release role loader](https://github.com/openai/codex/blob/rust-v0.163.0/codex-rs/agent-roles/src/loader.rs)
- [Exact release tool selection](https://github.com/openai/codex/blob/rust-v0.163.0/codex-rs/core/src/tools/spec_plan.rs)

## Prepared correction

Keep `--ignore-user-config`, avoiding unrelated user MCP integrations. Pin the
existing real registered role through the supported command-scoped override:

```text
--enable multi_agent
-c agents.max_concurrent_threads_per_session=1
-c agents.max_depth=1
-c agents.api_reviewer.config_file="C:/Users/chaki/AIproject/.codex/agents/api-reviewer.toml"
```

Keep native `--sandbox read-only`, `--ask-for-approval never`, ephemeral mode,
shell/apps/plugins/memories/permission-request tools disabled, the guarded
synthetic fixture and the no-generic-fallback prompt. Depth one blocks child
delegation; the prompt authorizes exactly one named reviewer, no application
access or mutations. This is a native supervisor `spawn_agent` selection of the
registered `api_reviewer`, not direct execution of the TOML or a generic agent.
The original attempt artifacts are preserved; a retry uses a separate directory
and refuses to overwrite existing retry evidence.

## Actual non-invoking verification

- `python scripts/invoke_api_reviewer.py --check-config`: exit 0; validates the
  local registration and prints the prepared command; starts no Codex process.
- A temporary foreground `codex app-server --stdio` diagnostic used only
  `initialize`, `initialized` and `config/read`, then terminated. No thread/start,
  turn/start or spawn call was sent. With the prepared global overrides,
  `config/read` accepted `api_reviewer.config_file`, `multi_agent=true`,
  `max_concurrent_threads_per_session=1`, `max_depth=1`, and reported no layer
  disabled reason. The app-server diagnostic cannot reproduce exec's
  `--ignore-user-config` flag, so this verifies the override parsing, not the full
  exec discovery path. Raw private configuration remains ignored and unpublished.
- `codex ... debug prompt-input` with the explicit role mapping exited 0, without
  sending a model request. Its message-only output does not verify tool exposure.
- `git diff --check`: passed. No full suite rerun was needed for this diagnosis.

No update appears necessary: this exact CLI release implements custom role file
loading and `agent_type` selection. Actual role exposure and execution remain
unverified until one newly authorized attempt. If that attempt still reports
UNSUPPORTED, stop and retain its evidence; do not substitute another agent.

## Historical fresh approval request (subsequently consumed)

Authorize exactly one execution of:

```powershell
python scripts/invoke_api_reviewer.py --approval-reference "Fresh user approval of one corrected read-only T17 supervisor and registered api_reviewer invocation"
```

This would run one ephemeral supervisor and at most one registered reviewer on
the supplied synthetic patch, return independent findings and record native
events. No file/application mutation, production access, further delegation,
paid service, merge or issue closure is included in that approval request.
