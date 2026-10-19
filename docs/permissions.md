# Permissions and security note

Scope: small Zoomcamp final project, **synthetic demonstration data only**. No real business, customer records or external company systems. T06 authentication and T07 API controls are implemented as described below; model, MCP, deployment and incident controls remain later requirements. Earlier company assumptions are retired.

Current boundary: local ports bind to 127.0.0.1; PostgreSQL has no published host port; generated configuration is ignored and the frontend has no database secret. Controlled demo accounts, password hashing, revocable sessions, expiry/lockout and CSRF/Origin protection guard app access. The frontend proxy excludes `/api/v1/ops`. Read-only diagnostics, exercise authorization and bounded on-call reset use three distinct scoped credentials. T15's [exercise gate](oncall-agent.md) is disabled by default and live execution requires explicit human approval. Public exposure still requires T16 HTTPS/deployment controls. See [the local guide](development.md).

## Secrets and identities

Keep model/deployment/operational credentials, demo passwords and session secrets in untracked local configuration or approved secret management. Root .gitignore and placeholder-only .env.example exist. Never put secrets in Git, frontend bundles, images, prompts, issues, screenshots, logs or traces. Use pseudonymous demo accounts and synthetic request text. A public repository does not make credentials public demo data.

If a credential is exposed, stop the affected action, report without repeating the value, and arrange authorized revocation/rotation. Removing a tracked value does not revoke it. No live provider or paid host has been selected or provisioned.

| Identity | Minimum permission | Denied |
| --- | --- | --- |
| Authenticated demo user | Create/view synthetic requests, request analysis, approve/reject and mark approved tasks done in the shared demo workspace | Private ops actions, secrets, arbitrary tools |
| Analysis workflow/model | Read the supplied request and return schema-valid task/priority suggestions | Approve, create active tasks, shell, company integrations, operational repair |
| Read-only MCP client | Bounded synthetic request summary through an allowlisted tool | SQL, arbitrary file/URL access, credentials or any mutation |
| On-call custom agent | Authenticated alert receipt, redacted diagnostic read and one prior-authorized dev flag clear plus bounded verification | Task approval, fault enablement, arbitrary shell/code/deploy/data deletion, production mutation |
| CI test job | Synthetic isolated test database and offline stub | Production/model/deployment secrets, especially from untrusted PRs |
| Release job | Environment-scoped approved artifact deployment with distinct dev/production secrets | Automatic production promotion, unapproved provisioning/spend |

There is no enterprise RBAC/account-management UI. Controlled demo accounts have equal app permissions. Use password hashes, revocable opaque sessions, secure HttpOnly/SameSite cookies for public HTTPS and CSRF/Origin validation for mutations. Only explicitly local loopback mode may relax Secure. Private ops endpoints remain off the public proxy and require a separate scoped credential. A hidden UI button is not authorization.

## Human approval and data integrity

AI proposals are untrusted inactive data. A human explicitly approves or rejects a specific pending analysis payload. Approval, task inserts and decision/status activity share one PostgreSQL transaction, with uniqueness constraints and concurrency checks. Duplicate approval creates tasks once; rejection creates none. No external business action exists.

Escape displayed model text, validate priority/output sizes and never execute generated code. Default stub is visibly simulated. Before real-model evaluation, approve provider/model, synthetic-only handling, token/time/concurrency limits and a persisted bounded call allowance. Failed or uncertain billed calls consume allowance. No automatic retries/failover or implied spending permission from a supplied API key.

## Controlled incident boundary

A later T15 runbook must obtain human authorization for an exact development-only analysis-disable exercise, its duration and one permitted reset. That prior exercise authorization allows automatic repair after the alert; it does not require building an extra approval UI for each incident. The agent must verify environment/authorization, known cause and single-action deduplication before resetting the flag. Unknown causes, expiry or failed verification stop and report. The maintainer enables the fault; the agent may only clear it. No production fault/repair or exercise execution is authorized by this documentation change.

Alertmanager delivery and ops calls use separate scoped credentials on private service networking; use TLS when crossing trust boundaries. Payload size/type and incident fingerprint are validated; alert text cannot become a shell instruction. A repair must be executed by the triggered agent and verified, not performed manually and attributed to it.

## Telemetry, deployment and evidence

Allowlist telemetry metadata: trace/span IDs, timings, route template, outcome, version and sanitized error code. Exclude request text, prompts/results, cookies/authorization headers and credentials. Use Prometheus low-cardinality labels, OTel trace context, stored Loki/Tempo data and authenticated Grafana. Keep telemetry/database ports private. Retention and storage caps are implementation configuration, not claims of compliance or commercial readiness.

Only synthetic data exists in dev/production release environments. Separate databases, volumes and credentials; never run tests/restore exercises against the live demo database. Prefer additive migrations and compatible-image rollback; never implicitly downgrade a database or delete volumes. Obtain approval before paid provisioning, a real deployment/exercise or a specialized-subagent invocation. Actual deployment/restore and guardrail behavior need issue-linked evidence.

Module 5 requires this note plus an executable guardrail demonstration, not prose assurances alone. Three peer-review confirmations may be recorded, but private review feedback/identifiers should not be published.
