# Product specification

Status: proposed requirements; none are implemented or verified. Acceptance criteria below define future checks, not passing results.

## Scope and assumptions

The MVP serves one configured business per deployment. Employees enter plain-text customer requests; two business agents generate proposals; authorized humans apply approved changes. The pilot business is Entropie Energies, subject to stakeholder validation. Business configuration defines required fields and terminology so another sector can use the same core workflow.

No outbound communication or external-system mutation is included. The platform does not provide binding energy advice or generate executable commercial commitments. Account provisioning is controlled; public self-registration is excluded.

## Pilot assumptions requiring confirmation

T01 audit status: these are proposed project choices, not confirmed Entropie operating procedures. The user identified the intended pilot and sector; this does not validate detailed workflows or grant access to company systems/data. User confirmation has been requested; no response or authorized stakeholder sign-off is recorded yet. Record explicit decisions on Issue #1 before marking its pilot-review criterion complete. An unresolved assumption may be deliberately deferred for a synthetic prototype only if that boundary is explicitly accepted and documented.

| ID | Proposed assumption | Required confirmation / decision owner | Current status |
| --- | --- | --- | --- |
| A01 | Manual text entry, one business per deployment, internal tasks only, and human approval are sufficient for the initial pilot | User/product owner confirms scope; business stakeholder later validates fit | Pending |
| A02 | Service type, site location, customer contact, project description and desired timeframe are the correct required fields | Authorized pilot stakeholder confirms fields and supplies only synthetic examples initially | Pending |
| A03 | Employees can view requests across the single-business deployment; reviewer, administrator and operator permissions are separate | User identifies role policy and who is authorized to validate it; private identities need not be published | Pending |
| A04 | Owners may be unassigned, deadlines are advisory, and a reviewer resolves missing information before work begins | Pilot workflow owner confirms assignment, business calendar/timezone and deadline policy; no default SLA is promised | Pending |
| A05 | Development, CI, screenshots and public demonstrations use synthetic data; real pilot data/provider processing is deferred | User confirms synthetic-only prototype boundary; authorized business owner must separately approve any later real-data use, retention and provider handling | Pending; synthetic data remains the safe working default |
| A06 | Staging fault injection and operator-approved recovery are acceptable for the demonstration | User/operator confirms later test environment and action boundary before an operational exercise | Pending; no operational exercise authorized by this audit |

Architecture choices such as provider, hosting, identity/session mechanism, trace storage and release controls remain T03 decisions. These must not be conflated with stakeholder confirmation of business behavior. See [permissions.md](permissions.md) for data authorization boundaries.

## Roles and lifecycle

- **Employee:** create and read requests, request analysis, and view proposals.
- **Reviewer:** employee permissions plus approve/reject proposals and update request status.
- **Administrator:** manage accounts, roles, and business configuration; does not automatically receive reviewer authority.
- **Operator:** view redacted operational information and operate approved recovery procedures; no implicit access to request bodies.

Request statuses: `new`, `in_review`, `in_progress`, `completed`, `cancelled`. Legal transitions are `new → in_review`, `in_review → in_progress`, `in_progress → completed`, and any nonterminal status → `cancelled`. Completion requires every approved task to be completed or explicitly cancelled with a reason. Terminal records remain readable; reopening is deferred.

Agent run states: `queued`, `running`, `succeeded`, `failed`, `cancelled`. Proposal states: `pending`, `approved`, `rejected`, `superseded`. Request status, execution state, and approval state are independent. Request revisions invalidate pending proposals based on older revisions.

## User stories and measurable acceptance criteria

### US-01 — Capture a request

As an employee, I can record a request so the team has a shared starting point.

- A valid title (1–200 characters) and body (1–10,000 characters) produce one persisted request with an identifier, creator, timestamps, revision, and `new` status.
- Blank or oversized values return a field-specific validation error without inserting a row.
- After refresh, the detail view displays the saved values; customer contact details are optional and treated as sensitive.

### US-02 — Find and track requests

As an employee, I can list and inspect requests so I can follow their progress.

- The list supports status filtering and pagination of at most 50 records per page, with deterministic ordering by creation time and identifier.
- Detail views show status, approved tasks, pending proposals, and run history.
- Authorized status transitions persist an audit event; invalid transitions return a conflict with no change.

### US-03 — Analyze sales information

As an employee, I can request analysis to reduce manual extraction work.

- A submitted run records its input revision and returns a run identifier without waiting for a model response.
- The Sales Agent returns schema-valid fields, source excerpts for extracted facts, explicit unknown values, and a list of missing required fields based on the active business profile.
- A pilot profile covers service type, site location, customer contact, project description, and desired timeframe; unknown values remain unknown.
- A versioned set of at least 10 synthetic requests includes complete, incomplete, ambiguous, and malicious-input examples. Every result validates against the schema; missing mandatory fields are identified in every deliberately incomplete fixture. Fixture expectations and evaluation results are recorded.
- Timeouts, invalid model output, and tool failures lead to a visible failed run after bounded retries; they never apply changes.

### US-04 — Propose coordination work

As a coordinator, I receive actionable task proposals after analysis.

- The Coordination Agent consumes the validated sales result and original input revision.
- Each proposed task contains a title, rationale, suggested deadline or explicit unknown, and suggested owner or unassigned value.
- Proposed deadlines include timezone and an explanation of assumptions; impossible or past deadlines are flagged for review.
- Proposals remain separate from active tasks until approval. Unknown staff identifiers cannot be assigned.

### US-05 — Review and apply proposals

As a reviewer, I can approve or reject a proposal while preserving accountability.

- Review displays original request, extracted evidence, assumptions, missing details, and exact proposed changes.
- Approval requires a reviewer role and a matching request revision; unauthorized attempts return 403 and stale proposals return 409 without mutation.
- Approval applies the complete proposal and records reviewer, timestamp, input revision, and resulting changes atomically.
- Repeated approval submissions create no duplicate tasks. Rejection requires a reason and applies no proposed changes.
- Corrections are made by revising the request and generating a new proposal in the MVP; inline proposal editing is deferred.

### US-06 — Monitor work

As a manager, I can see workload and agent activity in a dashboard.

- Counts by request status and pending approvals match database-backed lists for seeded test data.
- Recent activity shows run state, start/end time, and sanitized failure summaries.
- Loading, empty, and failed API states render explicit feedback; no dashboard count depends on a fabricated placeholder.

### US-07 — Enforce access and data boundaries

As an administrator, I can restrict access without exposing sensitive data.

- Every protected API route rejects anonymous access with 401; role enforcement is tested for each privileged action.
- Role changes and approval decisions produce audit events. The client cannot grant itself privileges.
- Public demos contain synthetic data only. Logs and traces omit request bodies, contact information, credentials, and model prompts by default.
- Business agents cannot call mutation tools or approve their own proposals; adversarial request text cannot expand tool permissions.

### US-08 — Operate and demonstrate recovery

As an operator, I can detect user impact and supervise a bounded recovery action.

- A staging exercise pauses agent processing through an explicit fault flag; analysis submissions remain accepted but queue age exceeds the alert threshold.
- An alert fires when the oldest queued run exceeds 120 seconds for 2 minutes and links to a runbook and dashboard.
- Authenticated alert delivery automatically invokes the on-call agent; incident identifiers deduplicate repeated delivery. Record alert receipt and agent wake-up without manual initiation.
- The on-call agent can inspect redacted telemetry and propose only an allowlisted reset of that staging flag.
- An authorized operator approves recovery; execution is audited, limited to one action per incident, and followed by a probe showing queued work finishes within 180 seconds. Failed verification escalates to a human without further autonomous mutation.
- A recording and incident report capture alert, diagnosis, approval, recovery, and measured timing using synthetic requests.

## Quality and delivery acceptance

- Unit tests cover validation, role policy, status transitions, stale approvals, idempotency, and agent schemas; integration tests use real PostgreSQL and a deterministic model stub.
- Both unit and integration suites run and pass through one documented command with an aggregate exit code; separate per-suite commands remain useful for development. Proposed `docker compose --profile test run --build --rm test` is not implemented yet.
- A browser smoke test covers create → analyze → review → approve → dashboard update, plus rejection and unauthorized approval.
- Local acceptance target: seeded 1,000-request dataset, 10 concurrent users, request list/detail p95 under 1 second over a 5-minute run on documented hardware. Provider latency is measured separately, with a configurable 120-second run timeout and at most two retries for transient failures.
- A clean checkout starts through documented Docker Compose instructions, runs migrations, and exposes health checks; CI runs required checks before deployment.
- A public HTTPS staging demonstration uses access control, synthetic records, a documented deployment procedure, and a verified rollback procedure.
- CI runs tests on every pull request; successful tested main releases deploy automatically to a separate dev environment. Production promotion is explicitly initiated through a manual deployment workflow using the tested versioned artifact. Record both deployment paths and rollback evidence.
- Telemetry includes metrics, traces and structured logs with shared trace context, collected and stored for viewing in a UI. Show trace-ID correlation across API requests and agent work using log fields and trace-linked metric exemplars/drill-down; metrics retain low-cardinality labels. Approval requests may start new traces explicitly linked to the originating run. No customer data, prompts or credentials enter telemetry. Dashboard and alert evidence is reproducible.
- T18 records three completed course-assigned peer reviews; these are mandatory for passing regardless of points. T17 demonstrates all seven [Module 5 Extension Pack items](module5-checklist.md). Runtime evidence is tracked separately in the [grading checklist](grading-checklist.md).

## Deferred scope

Inbound email, attachments, retrieval over internal documents, autonomous external actions, customer portals, billing, complex scheduling, production multi-tenancy, and unrestricted remediation are deferred. Changes require updated acceptance criteria and permissions review.
