# Product specification

Owner: [T01](https://github.com/chakirou18/AI-OfficeFlow/issues/1). Current scope supersedes the earlier pilot/enterprise specification under [ADR 0010](adr/0010-minimal-zoomcamp-scope.md). The product stories below define acceptance behavior implemented through T15; current evidence and remaining delivery gates are in [final-handover.md](final-handover.md). T04's separate fixed-payload health/connectivity foundation has verified tests and persistence evidence in [t04-verification.md](t04-verification.md); it does not implement request/task/AI/approval stories.

## Scope and users

Build a small request/task manager for the Zoomcamp final project. A demonstration user can capture a request, ask an AI agent for tasks and priorities, approve/reject the complete proposal, and track approved tasks. Use a shared synthetic workspace with controlled demo accounts; every authenticated demo account has the same application permissions. There is no enterprise role matrix, business onboarding or company integration.

Only title and description are needed. Requests are immutable after creation in the MVP; create another request to correct input. No customer contacts, service types, addresses, owners, deadlines or sector profiles. Do not collect real personal or company data. No external business action is permitted.

## Retired assumptions

**A01–A06 are superseded and have no current acceptance or approval authority.** Their earlier content remains in Git history and explicitly superseded ADRs only. There is no pilot company and no company stakeholder-validation gate. In particular, sector fields/access policies/deadline assumptions are removed, synthetic-only data is a current project rule, and the controlled incident is an educational demonstration rather than a company operational workflow. No stakeholder approval is claimed.

Current decisions: small generic scope, synthetic-only data, human approval before activating tasks, a single analysis agent, and no real integrations. This documentation task does not authorize implementation, paid services, live API spend, deployment, a subagent invocation or executing a fault exercise. T15 obtained one exact authorization and demonstrated its bounded exercise; a repeat needs fresh authorization.

## States and invariants

- Request display status: `new`, `awaiting_review`, `in_progress`, `completed`. Initially new; pending valid suggestions mean awaiting_review; approval with open tasks means in_progress; completing all approved tasks means completed. Rejection/failed analysis returns an otherwise task-free request to new. No request editing/cancellation workflow.
- Analysis state: `running`, `pending`, `approved`, `rejected`, `failed`. Only one running/pending analysis may exist per request. A new attempt is allowed after failure or rejection; approved requests do not need re-analysis in this MVP.
- Task state: `open` or `done`; priority: `low`, `medium`, `high`. Task rows can be created only by the approval transaction, with a unique analysis/task-index key.
- Requests, model results, approval decisions and tasks persist. An application restart must not remove them. A crashed synchronous analysis becomes failed/interrupted after its deadline; no automatic background resumption is promised.

## User stories and acceptance criteria

### US-01 — Create a request

As a user, I can save a request as the starting point for work.

- Title is 1–200 trimmed characters and description is 1–5,000 trimmed characters; invalid/blank input returns field errors and creates no request.
- A successful create persists an ID, title, description, creator handle and timestamps in PostgreSQL.
- Refresh and application restart show the saved values. Only synthetic content is used in fixtures and demonstrations.

### US-02 — View requests and tasks

As a user, I can inspect requests and their approved tasks.

- A paginated request list returns at most 50 records per page in stable creation-time/ID order, with a status filter.
- Detail shows original text, analysis state, pending suggestions or decision, and approved tasks/statuses.
- Marking a task done persists and updates the request/dashboard status consistently. No mutable request text or revision feature is required.

### US-03 — Analyze a request

As a user, I can obtain proposed tasks without activating them.

- The API records an analysis attempt, makes one bounded model call outside a database transaction and validates the response before storing pending suggestions.
- Response has a concise summary and 1–5 proposed tasks with a title, priority enum and rationale. Unsupported facts are not presented as established facts.
- Local/CI stub mode is deterministic, labeled simulated in API/UI metadata and needs no model key. At least ten synthetic fixtures include ambiguous, empty/invalid, adversarial and provider-failure cases.
- Analysis has a 30-second deadline and no automatic retries; timeout/invalid output/provider error is visible and creates no tasks. A user may explicitly retry a failed attempt.
- At least one separately authorized real hosted or local model evaluation is recorded before T10 is complete. Passing stub tests alone is not evidence of real AI quality.

### US-04 — Understand priorities

As a user, I can inspect the reasoning before deciding.

- Each proposed task has exactly one of low/medium/high priority and a brief explanation grounded in the request.
- Unknown timing/resources are described as assumptions or missing information, not invented deadlines or staff assignments.
- The UI displays the entire proposal and its simulated/live mode before approval; it does not render model text as executable HTML/code.

### US-05 — Approve or reject

As a user, I explicitly control which suggestions become work.

- Approve/reject requires an authenticated session and CSRF protection. It targets a specific pending analysis ID and its persisted payload.
- Approval locks the request/analysis and atomically saves the decision, task rows and status/activity change. Duplicate/concurrent approval creates each task once and returns the existing approved result.
- Rejection records a reason and creates zero tasks. A conflicting decision returns 409 without effects.
- The analyzer and on-call identity cannot call the human approval operation. There are no outbound business actions.

### US-06 — See the dashboard

As a user, I can see the current workload.

- Request/task counts and status filters match persisted data for the seeded fixture set.
- Dashboard shows recent analysis outcomes and approved tasks; refreshing after a decision shows the database state.
- Loading, empty, validation and unavailable states are explicit. Counts and successful results are never fabricated placeholders.

### US-07 — Protect the demonstration

As the maintainer, I can publish a bounded synthetic demo without exposing credentials.

- Protected app routes return 401 without a valid session; private ops routes reject the demo user and accept only scoped operational credentials.
- Demo accounts are controlled, credentials are generated/configured outside Git, passwords are hashed, and logout/expiry invalidate sessions.
- Logs/traces exclude request bodies, prompts, credentials and contact information; model content is treated as untrusted data.
- No real data, company connection, unrestricted shell, public write tool or paid-service provisioning is enabled by default.

### US-08 — Detect and repair a controlled incident

As the maintainer, I can demonstrate user-impact alerting and an actual alert-triggered repair.

- In an explicitly authorized development-only exercise, an allowlisted analysis-disable flag makes analysis return 503 before any provider call; normal request viewing still works.
- An alert fires when at least five analysis attempts occurred in a two-minute window and their server-error ratio exceeds 50% continuously for one minute. The runbook records the synthetic traffic and actual firing time; production thresholds may be tuned separately.
- Alertmanager automatically invokes the custom on-call agent through an authenticated internal webhook. Repeated delivery for the same incident is deduplicated.
- The agent reads redacted diagnostics, confirms the known flag is the cause, and clears that exact dev flag under the exercise's prior human authorization. The human does not perform the repair manually. No general infrastructure/code/shell action exists.
- The agent verifies analysis health through a bounded synthetic check of the same analysis service; the recording also shows a user analysis succeeding after repair. If cause/authorization/environment checks fail or verification fails, stop and report; do not improvise another fix.
- Record alert → automatic invocation → diagnosis → single allowlisted repair → recovery evidence. The actual T15 exercise is recorded in [oncall-agent.md](oncall-agent.md); this specification does not authorize a repeat.

## Delivery acceptance

- One documented command starts the complete demonstration stack including PostgreSQL, the app, stored telemetry, alert routing and on-call listener. Docker/image prerequisites and placeholder-only configuration are documented.
- One command runs both unit and real-PostgreSQL integration suites and returns success only when both pass; deterministic model mode is default. Add a browser smoke flow for create → analyze → approve/reject → dashboard.
- PR CI runs tests; a tested main release automatically deploys to dev; manual production promotion uses the same tested image digest. Both environments use synthetic data and separate databases/secrets.
- A working public URL or a clear deployed demonstration is provided. The project prefers a public authenticated HTTPS demo if feasible; a recorded actual deployment is an allowed fallback, not a README-only deployment plan.
- OTel metrics/traces/structured logs share trace context, are collected/stored and are visible in Grafana with trace-to-log and metric-to-trace navigation. No trace IDs as metric labels.
- Show working user-impact alert and actual automatic on-call recovery. Complete all seven Module 5 artifacts and three mandatory peer reviews.
- Record exact commands, observed smoke timings, versions, CI runs, deployment/demo and limitations on the relevant issues. No arbitrary commercial load/SLA target is required; test and deployment evidence is linked in [final-handover.md](final-handover.md); no score is claimed.
