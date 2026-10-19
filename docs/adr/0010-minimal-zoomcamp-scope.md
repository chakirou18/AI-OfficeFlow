# ADR 0010 — Minimal generic Zoomcamp final project

Status: **Accepted for final-project design under the user's scope revision**. Owner: T03. Supersedes ADRs 0001-0009 as normative architecture. Their useful rationale/history remains available; retained technologies/boundaries are restated here. This decision authorizes documentation/tracker updates only, not implementation, installation, services, paid usage or deployment.

## Context and scope

The repository now serves only the DataTalksClub AI Dev Tools Zoomcamp 2026 final project, targeting 12 criteria/24 points. A separate real-business project is outside this repository. There is no pilot company, sector field schema or company validation obligation. A01-A06 are retired. Use synthetic data only.

The prior architecture introduced two business agents, queue leases, revisions, enterprise roles and package/runtime choices before delivering a small app. These are not needed to demonstrate the rubric. Preserve the public repository, T01-T18 identities, existing commits, useful security/approval concepts and the full operational/Extension Pack evidence targets.

## Decisions and alternatives

| Area | Current minimal choice | Alternative/trade-off and consequence |
| --- | --- | --- |
| UI/API/database | React/TypeScript/Vite, FastAPI/Pydantic, PostgreSQL with SQLAlchemy/Alembic; same-origin static frontend/API | Server-rendered UI could reduce tooling but would discard useful selected frontend work/design. Keep familiar stack; no extra frontend/backend service framework. |
| Analysis/orchestration | One Python analysis workflow makes one schema-validated call with 30-second deadline and explicit user retry | LangGraph/DeepAgents/two business agents and queues support longer workflows but add state/services/tests unnecessary here. No worker, broker, leases or graph checkpointing. |
| Model | Deterministic offline adapter for local/CI; optional approved real hosted/local model adapter with bounded usage | Stub alone does not demonstrate real AI quality. Provider/model/allowance must be chosen and real evaluation evidenced in T10; no purchase/model download is a T03/T04 prerequisite. |
| Persistence | Immutable requests, analysis payload/decision, approved tasks/priorities, sessions and minimal activity/incident records | Editable revisions, owners/deadlines, sector profiles and independent audit/budget platforms add implementation cost without current user need. Keep approval transaction/uniqueness and basic idempotency. |
| Authentication | Controlled equal-permission demo accounts, hashed passwords, opaque sessions and CSRF/Origin checks; separate scoped ops token | Enterprise RBAC/OIDC/admin UI is unnecessary. Public anonymous writes are undesirable even with synthetic data. No commercial access guarantees or multi-tenancy. |
| MCP | Small local stdio read-only synthetic request-summary tool for the Extension Pack | A network MCP platform or business-profile/staff service is not required for a one-call analyzer. Keep real tool invocation/denial evidence. |
| Observability | OTel Collector, Prometheus, Loki, Tempo, Grafana; trace context and metric exemplars/drill-down | Logs only would miss full-score requirements. A hosted bundle may reduce operation but adds account/spend; use self-hosted Compose design without procurement. |
| Alert/repair | Prometheus analysis-error ratio rule, Alertmanager and one custom on-call listener; diagnose and clear one pre-authorized dev flag | A read-only assistant/manual start misses the repair criterion. Arbitrary shell remediation is excessive. Prior exact exercise authorization avoids an extra per-incident approval UI while keeping a narrow human-controlled boundary. |
| Local/delivery | One full-stack Compose boot, one aggregate test command, PR CI, automatic dev and manual production promotion | Kubernetes/microservices/serverless add operations surfaces. Choose existing approved Compose-compatible infrastructure at T16; public URL OR clear actual deployment demo meets deployment evidence. No vendor/free-tier assumptions. |
| Extension Pack | Existing instructions/security note plus workflow, specialized API reviewer, MCP, executable guardrail and explicitly documented custom on-call agent | Choose custom-agent OR branch; retire the separate plugin package/native manifest project. Actual registration/invocation/guardrail/custom-loop demos remain required. |

## Costs and security

No paid service or nonzero API allowance is selected. Costs remain local CPU/disk/maintenance and actual CI allowances; provider and hosting costs require current verification and authorization at T10/T16. No price/free-tier claim is made. Live calls have bounded tokens/deadline/concurrency and a persisted call allowance consumed before dispatch, with no automatic retry/failover. Tokens remain backend-only. Default simulated mode is disclosed.

All real business data/integrations are out of scope. Demo tasks require explicit human approval; analysis cannot activate them. Ops credentials cannot approve tasks; demo credentials cannot clear flags. Keep telemetry metadata-only, private service networking and environment-separated secrets/databases. An unknown/unauthorized incident fails closed. The later exercise authorizes only one dev flag reset for a bounded window; production fault/repair is excluded. No exercise is run now.

Use a tested compatible image for rollback; additive migrations and a small isolated backup restore demonstrate recovery without a commercial operations platform. Commands/configurations must be implemented, version-pinned and verified later. [Docker startup ordering](https://docs.docker.com/compose/how-tos/startup-order/), [GitHub manual workflows](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow) and [OTel log context](https://opentelemetry.io/docs/concepts/signals/logs/) are primary implementation references, not evidence of configured behavior.

## Governance and completion boundary

T01's generic scope/rubric/gap documentation and T02's public tracker/use evidence can remain complete after current-scope review. T03 is assessed against this design decision, alternatives/cost/security coverage and documented delivery-stage choices; provider account procurement and actual runtime checks are not design completion criteria. It may complete after the revised documentation is committed and reviewed. This is an explicit scope change, not a claim the old unselected live services were delivered.

T04 is next: a small frontend/API/PostgreSQL/migration/health/Compose skeleton with a database round trip. T05 adds early CI, followed by access, requests, analysis, approval, telemetry/alert/repair and final delivery evidence. Preserve existing dependencies; add T15 to T17's completion dependencies because the selected custom-agent branch now explicitly uses its repair demonstration. No other dependency is removed.

T10/T16/T15/T17 retain real-model, real-deployment, exercise and specialized-subagent gates respectively. No runtime tests, deployment, alert/repair, Extension Pack demo, peer review or grading score is verified by this ADR. Source rubric and seven-item requirements remain pinned in the grading/Module 5 checklists.
