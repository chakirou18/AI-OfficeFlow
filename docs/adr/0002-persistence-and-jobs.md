# ADR 0002 — PostgreSQL source of truth and durable jobs

Status: **Accepted for prototype design**. Owner: T03; implementation: T04, T07, T09, T11, T12.

## Decision and principal entities

Use one PostgreSQL database per environment. One business context per deployment is a product limit, not tenant isolation. Persist domain relationships as foreign keys and constraints; use versioned JSONB only for evolving extraction/task-proposal payloads. IDs are UUIDs, timestamps UTC, business timezone an explicit profile field, and deadlines nullable. Proposed entities:

| Entity | Key data and relationships |
| --- | --- |
| business_profiles / profile_versions | Configurable required fields, terminology and timezone; immutable version referenced by request input |
| users / role_assignments / sessions | Controlled credentials, roles and revocable server sessions; no business agent is a reviewer |
| requests / request_revisions | Creator, status, content revision, concurrency version, latest run ID; immutable text/contact snapshots and profile version |
| agent_runs / run_attempts | Request revision, graph/prompt/schema versions, queued/running/outcome, lease token/expiry, attempt deadline and trace context |
| proposals / approval_decisions | Run and input revision, typed payload/hash, pending/approved/rejected/superseded state, actor/time/reason |
| tasks | Approved proposal and stable proposal-task key, title, owner or null, deadline or null, completion/cancellation reason |
| audit_events | Actor/type, action, target, minimized change summary, timestamp and trace/run references |
| model_budget_reservations / usage_records | Approved spending envelope, token limits, reserved/actual usage; uncertain billed attempts retained conservatively |
| operational_incidents / recovery_approvals | Separate incident identity, dedup key, diagnostic metadata, expiring action-specific approval and single execution outcome |
| operational_flags | Environment-scoped staging pause flag, disabled by default; separate narrow execution grant and audit reference for a later authorized exercise |

Physical operational tables can wait until T14/T15; do not collect fault data or run exercises now. Index status/created_at/id for request lists, state/available_at for queue claiming, proposal run IDs and audit target/time. Enforce unique proposal-per-run and task-per-proposal-task-key constraints.

## Queue and consistency

Accept analysis by inserting the durable run in a transaction, return HTTP 202 with a run ID, and let a separate worker poll. Claim eligible jobs in a short transaction with `FOR UPDATE SKIP LOCKED`, an incrementing fencing token, lease expiry and attempt number. [PostgreSQL documents this locking option](https://www.postgresql.org/docs/current/sql-select.html); this design uses it for queue consumers, not general consistent reporting. Never hold a transaction open during model/network work.

Preliminary timing: 30-second lease, heartbeat every 10 seconds, at most three attempts total and a 120-second wall-clock execution deadline from first start including retries/backoff. Queue waiting is measured separately. Retry only transient failures with backoff while time remains. Recover expired leases; all publishing/heartbeat writes must match the current fencing token. Late workers cannot publish after lease loss. Cancellation is cooperative; stale revision, terminal request or a newer run prevents proposal publication.

Persist each completed validated node result with its run/profile version. A retry can reuse that result; restart a whole uncompleted node rather than claim exactly-once model calls. A crash after provider completion can still cause another charge; budget accounting must reserve conservatively. No Redis or Celery is required initially. Worker SQL grants allow only necessary snapshot reads and run/proposal writes; graph code has no connection handle or mutation tool, and worker credentials cannot write tasks, roles or decisions.

Approval locks request then proposal consistently, rechecks reviewer/revision/latest-run/payload, and writes decisions, tasks, request state and audit atomically. See ADR 0003. At-least-once jobs and HTTP retries must produce idempotent domain effects. Logical input revision is distinct from row concurrency version; status updates must not silently change model input.

## Alternatives, cost and security

SQLite simplifies initial boot but loses target database concurrency parity. Redis/Celery offers mature queue features at extra broker/deployment cost; revisit when queue load or scheduling needs justify it. A dedicated workflow engine improves long workflows at greater operations complexity. Native graph checkpoint persistence alone does not replace the product's durable submission queue and approval records.

Benefits: atomic submissions and approvals, few services, migration/test parity. Trade-offs: custom lease/retry behavior needs meaningful concurrency tests, and queue traffic competes with domain queries. Storage grows with snapshots and runs; proposed synthetic prototype retention is 30 days for completed run payloads, subject to later policy approval before real data. Audit retention must be designed before real use. Encrypt public-host storage/backups and keep PostgreSQL private. T09/T12 must verify restart, duplicate submission, expired lease, stale result and concurrent approval behavior; no results exist yet.
