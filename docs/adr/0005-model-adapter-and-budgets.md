# ADR 0005 — Offline default, model adapter and cost limits

Status: **Accepted for prototype design** for the adapter/stub. **Proposed / product-owner approval required** for every live provider/model and nonzero budget. Owner: T03; implementation: T09, T10, T12.

## Decision

Define a provider-neutral backend interface that accepts a versioned task/schema, bounded synthetic input, timeout, token limit and trace context; returns validated structured data, provider/model identifier, normalized usage and sanitized error classification. Domain code must not depend on vendor response objects. An adapter cannot bypass schema, permissions or spending policy.

Default to `stub` mode: deterministic fixture responses for complete, incomplete, ambiguous, malicious and failure scenarios. CI and the one-command local stack require no provider key, outbound model network or external billing. Make simulated analysis visible in the UI/run metadata so it is never presented as demonstrated live AI quality. Live evaluation is opt-in and separate from deterministic tests.

No commercial provider/model is selected or authorized. Compare a hosted API adapter with a locally hosted model after product-owner approval of the evaluation environment. Selection evidence must include synthetic-fixture accuracy, structured-output reliability, latency, token cost, context limits, provider retention/training settings and region. Obtain a current quote/rate reference at selection time; do not invent prices or free quotas. Pin the exact model/version and provider settings in the later approved ADR amendment.

## Preliminary limits and accounting

- Live mode is disabled until a provider, model, currency and nonzero hard spending cap are explicitly approved. A missing/zero budget blocks live calls, rather than falling back to an unbudgeted provider.
- Initial design caps: two logical model nodes per run; at most three total job attempts inside the 120-second execution deadline; at most six physical model calls across attempts; at most 2,000 output tokens per call and an explicit input-token ceiling configured to the chosen model. Validate input length before reserving cost.
- Enforce per-user run-rate and deployment concurrent-run limits; proposed starting limits are five submissions/minute/user, one active run/request and two concurrent live runs/deployment. Tune with measured performance, not assumptions about company demand.
- Reserve worst-case cost transactionally before each physical call against per-run and daily envelopes. A validated rate table includes input/output pricing and currency; unknown pricing blocks live mode. Record actual usage/cost after completion and retain the conservative reservation for a timeout/unknown billed result until reconciled. Parallel workers cannot overspend the reserved application envelope.
- Provider-side limits/alerts are an additional safeguard. Application accounting cannot guarantee instantaneous upstream billing accuracy; exposure, reconciliation and a kill switch must be disclosed. Do not retry budget, authorization or permanent schema failures as transient network failures.

## Alternatives, costs and security

| Option | Advantage | Trade-off / approval |
| --- | --- | --- |
| Deterministic stub (selected default) | Reproducible tests, no external usage charge | Does not prove model quality or live inference; disclose simulation |
| Hosted model API | Simpler model operations, provider-managed inference | Per-token/usage spend, external processing, rate/retention constraints; provider/model/budget require approval |
| Local model runtime | Keeps inputs on approved hardware and avoids API usage billing | RAM/GPU/energy and model-license/maintenance costs; quality/latency unmeasured; hardware/download approval needed later |
| Provider router with automatic failover | Potential availability gains | Expands data recipients and spending paths; deferred to avoid implicit provider switching |

Secrets stay in backend/worker secret management, never UI/MCP/model prompts. Only synthetic data may leave the process. Disable prompt/completion recording in third-party telemetry by default; log usage metadata without request content. A live API key supplied later is not blanket authorization for spend or real data. T03 remains open on this live-service choice; T09 can prepare the stub independently after implementation authorization. No evaluation or billing result exists.
