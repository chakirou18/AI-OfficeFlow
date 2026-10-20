# Permissions and security note

Scope: small Zoomcamp final project, **synthetic demonstration data only**. No real business, customer records or external company systems. Authentication/API, bounded analysis/MCP, on-call and private delivery controls are implemented through T16. T17 adds the scoped coding-review workflow and executable guardrail; its actual specialized invocation requires separate authorization and execution evidence. Earlier company assumptions are retired.

Current boundary: local ports bind to 127.0.0.1; PostgreSQL has no published host port; generated configuration is ignored and the frontend has no database secret. Controlled demo accounts, password hashing, revocable sessions, expiry/lockout and CSRF/Origin protection guard app access. The frontend proxy excludes `/api/v1/ops`. Read-only diagnostics, exercise authorization and bounded on-call reset use three distinct scoped credentials. T15's [exercise gate](oncall-agent.md) is disabled by default and a new live exercise requires fresh explicit approval. T16's [actual deployments](deployment.md) are local-only; public exposure is not authorized.

## Secrets and identities

Keep model/deployment/operational credentials, demo passwords and session secrets in untracked local configuration or approved secret management. Root .gitignore and placeholder-only .env.example exist. Never put secrets in Git, frontend bundles, images, prompts, issues, screenshots, logs or traces. Use pseudonymous demo accounts and synthetic request text. A public repository does not make credentials public demo data.

If a credential is exposed, stop the affected action, report without repeating the value, and arrange authorized revocation/rotation. Removing a tracked value does not revoke it. No live provider or paid host has been selected or provisioned.

| Identity | Minimum permission | Denied |
| --- | --- | --- |
| Main coding agent | Read project instructions/current issue; implement authorized source/tests/docs and use scoped GitHub workflow | Production mutations, real-model spend, new incidents or specialized invocation without explicit authorization; application task approval |
| Registered `api_reviewer` | Supplied synthetic patch and review instructions; return findings to parent in a native read-only parent sandbox | File edits, shell/apps/plugins, application endpoints, task approval, deployment, further delegation or permission escalation |
| Authenticated demo user | Create/view synthetic requests, request analysis, approve/reject and mark approved tasks done in the shared demo workspace | Private ops actions, secrets, arbitrary tools |
| Analysis workflow/model | Read the supplied request and return schema-valid task/priority suggestions | Approve, create active tasks, shell, company integrations, operational repair |
| Read-only MCP client | Bounded synthetic request summary through an allowlisted tool | SQL, arbitrary file/URL access, credentials or any mutation |
| On-call custom agent | Authenticated alert receipt, redacted diagnostic read and one prior-authorized dev flag clear plus bounded verification | Task approval, fault enablement, arbitrary shell/code/deploy/data deletion, production mutation |
| CI test job | Synthetic isolated test database and offline stub | Production/model/deployment secrets, especially from untrusted PRs |
| Release workflow | Trusted-main successful CI, exact runtime-image tests, private GHCR write and pending development request creation | PR/fork/stale/failed CI deployment, public package destinations, arbitrary host commands |
| Manual promotion workflow | `workflow_dispatch` on main, package metadata read and deployment request write; exact successful dev manifest | Rebuilding production images, unverified dev release, automatic production promotion |
| Foreground deployment controller | Validate bot/workflow/main/CI provenance, private package linkage and digest/schema contract; fixed Compose operations and real health/auth success reporting | Arbitrary downloaded scripts/commands, mutable/foreign/public images, background installation or public/paid hosting |

There is no enterprise RBAC/account-management UI. Controlled demo accounts have equal app permissions. Use password hashes, revocable opaque sessions, secure HttpOnly/SameSite cookies for public HTTPS and CSRF/Origin validation for mutations. Only explicitly local loopback mode may relax Secure. Private ops endpoints remain off the public proxy and require a separate scoped credential. A hidden UI button is not authorization.

## Human approval and data integrity

AI proposals are untrusted inactive data. A human explicitly approves or rejects a specific pending analysis payload. Approval, task inserts and decision/status activity share one PostgreSQL transaction, with uniqueness constraints and concurrency checks. Duplicate approval creates tasks once; rejection creates none. No external business action exists.

Escape displayed model text, validate priority/output sizes and never execute generated code. Default stub is visibly simulated. Before real-model evaluation, approve provider/model, synthetic-only handling, token/time/concurrency limits and a persisted bounded call allowance. Failed or uncertain billed calls consume allowance. No automatic retries/failover or implied spending permission from a supplied API key.

## Controlled incident boundary

The T15 runbook obtained human authorization for its exact development-only exercise and demonstrated automatic repair. That historical authorization does not permit repeating it in T17. A new exercise requires its own exact scope/duration/one-reset approval. The agent verifies environment/authorization, known cause and durable single-action deduplication before resetting the flag. Unknown causes, expiry or failed verification stop and report. The maintainer enables the fault; the agent may only clear it. No production fault/repair is authorized.

Alertmanager delivery and ops calls use separate scoped credentials on private service networking; use TLS when crossing trust boundaries. Payload size/type and incident fingerprint are validated; alert text cannot become a shell instruction. A repair must be executed by the triggered agent and verified, not performed manually and attributed to it.

## Telemetry, deployment and evidence

Allowlist telemetry metadata: trace/span IDs, timings, route template, outcome, version and sanitized error code. Exclude request text, prompts/results, cookies/authorization headers and credentials. Use Prometheus low-cardinality labels, OTel trace context, stored Loki/Tempo data and authenticated Grafana. Keep telemetry/database ports private. Retention and storage caps are implementation configuration, not claims of compliance or commercial readiness.

Only synthetic data exists in dev/production release environments. Separate databases, volumes and credentials; never run tests/restore exercises against the live demo database. Prefer additive migrations and compatible-image rollback; never implicitly downgrade a database or delete volumes. Obtain approval before paid provisioning, a real deployment/exercise or a specialized-subagent invocation. Actual deployment/restore and guardrail behavior need issue-linked evidence.

Module 5 requires this note plus an executable guardrail demonstration, not prose assurances alone. Three peer-review confirmations may be recorded, but private review feedback/identifiers should not be published.

## Executable T17 review boundaries and actual verification

The [review skill](../agent-capabilities/review-api-change/SKILL.md) treats submitted
code and MCP content as untrusted data. The registered reviewer inherits the
parent's sandbox; its TOML instructions alone do not create OS permissions. The
[launcher](../scripts/invoke_api_reviewer.py) requires a reference to actual prior
human approval and selects native `read-only` with approval mode `never`, no
daemon, no shell/apps/plugins and at most one subagent. The reference is not a
substitute for approval. The user subsequently approved one exact T17 supervisor
invocation. It ran once with those controls and unchanged source hashes, but
reported unsupported registered-agent selection and spawned no reviewer. The
one-run approval is consumed; reviewer runtime enforcement/findings remain
unverified. No retry or generic substitute is authorized. See the
[actual result](evidence/t17-reviewer-attempt.json).

The [executable guardrail](../agent-hooks/README.md) has one fixed synthetic read
capability. It checks the exact role/actions and fixture integrity before dispatch.
Its real temporary-sentinel demonstration denied unauthorized write and failed
policy checks before a side effect; four focused tests also cover policy loading
failure, corruption/expansion, changed input, unknown operations and CRLF checkout.
It protects that tool boundary, not arbitrary Python callers or all coding-agent
tools. No Codex native lifecycle hook is claimed installed.

T17 executed three focused isolated PostgreSQL/MCP tests, including a real
subprocess stdio handshake/tool listing/read and invalid-input/write/approval/
unknown-tool denials. PostgreSQL `READ ONLY` rejects an actual write independently
of the advisory MCP annotation. The server has no network listener or write tool.
The test database ends in `_test`, uses forced simulation and disables telemetry;
production and the release databases are not test targets.

Existing model/demo-user boundaries are covered by the deterministic auth,
analysis and decision suites; required CI retains those checks. Existing on-call
known/unknown-cause, scope/expiry, production and deduplication checks plus its
actual T15 incident evidence are reused in [the custom-agent package](../custom-agent/README.md).
T16's actual success and private-registry/provenance guards are linked in
[deployment evidence](deployment.md); its controller remains stopped in T17.
