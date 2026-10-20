# Existing custom on-call agent package

This package documents the existing T15 custom agent; it does not introduce a
second agent loop, plugin, service or configuration format. Its implementation is
[OnCallAgent](../backend/app/oncall_agent.py), invoked automatically by the
[authenticated webhook listener](../backend/app/oncall.py). The actual runtime
configuration is the `oncall-listener` service and secret mounts in
[compose.yaml](../compose.yaml); the complete authorization/runbook is
[docs/oncall-agent.md](../docs/oncall-agent.md).

The webhook schedules the deterministic Python agent after durable incident
deduplication. The agent confirms the active incident against private Alertmanager,
reads redacted diagnostics, checks the exact development exercise/expiry and known
`analysis_disabled` cause, clears that flag once, then verifies persisted inactive
analysis suggestions and zero active tasks. Its four fixed HTTP tools are incident,
diagnostics, clear and verify. No tool accepts arbitrary shell, URL, SQL or file
repair input. Unknown cause, expired/missing scope, production and failed
verification stop the workflow and record a bounded reason.

`ALERT_TOKEN_FILE` authenticates webhook receipt; `ONCALL_OPS_TOKEN_FILE` authorizes
only diagnosis/clear/verification. The maintainer's separate
`EXERCISE_ADMIN_TOKEN_FILE` authorizes the expiring exercise and is not mounted in
the listener. Demo sessions cannot repair faults. The API exercise gate defaults
off. Enabling a gate is not permission to activate a fault; a new live exercise
requires fresh explicit authorization. No new exercise is run for T17.

## Reused actual T15 evidence

[Issue #15](https://github.com/chakirou18/AI-OfficeFlow/issues/15) records explicit
human approval, actual command, successful incident chronology and CI in PR #30.
The already-executed command was:

```text
python scripts/verify_oncall.py --approval-reference "User explicitly approved the exact bounded T15 exercise in this conversation"
```

It exited 0 on 2026-10-19. The real alert fired at 20:30:47.872Z; the agent was
automatically invoked at 20:31:02.787Z, diagnosed at 20:31:02.877Z, cleared the flag
at 20:31:02.912Z and verified recovery at 20:31:02.970Z. Normal user recovery followed
at 20:31:03.191Z; resolved receipt arrived at 20:33:02.820Z. Exactly 20 synthetic
503 responses were observed. Duplicate replay produced one duplicate and no second
clear/verification. Zero active tasks were created; data survived cleanup and the
exercise gate was disabled. Private raw evidence remains ignored at
`artifacts/t15-verification.json`; no credentials or request bodies are republished.

The T15 aggregate passed 188 tests and required CI
[39318848423](https://github.com/chakirou18/AI-OfficeFlow/actions/runs/39318848423).
These are reused historical results, not new T17 fault injection or a new test run.
This fulfills the Module 5 **plugin OR custom agent** branch with the actual
custom-agent workflow; no separate plugin package is claimed.
