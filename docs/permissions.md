# Secrets, data, permissions, and human approval

Status: intended policy for implementation. Controls described here are requirements, not deployed safeguards.

## Secrets and sensitive data

Use synthetic requests for development, automated tests, screenshots, public issues, and demonstrations. Customer names, email addresses, phone numbers, addresses, site details, commercial information, and request bodies may be sensitive. Store only fields needed for the workflow; do not collect identity documents, payment credentials, or unrelated sensitive information.

Provider keys, database passwords, session secrets, CI credentials and telemetry tokens belong in local untracked configuration or the chosen secret manager. A root .gitignore exists; a placeholder-only example configuration must be added when scaffolding begins and does not exist yet. Never place secrets in frontend bundles, Git history, Docker image layers, logs, traces, agent prompts, or public artifacts. Redact exception output and model/tool payloads.

Use separate development, CI, staging, and production credentials. Scope access to each service and environment. Prefer short-lived deployment credentials where supported. If a secret leaks, stop affected operations, notify the maintainer without reproducing it, arrange authorized revocation/rotation, and assess exposure. Removing a file alone does not revoke a leaked key.

Before any real pilot data is processed, confirm business authorization, provider data handling, deployment region, retention/deletion periods, access ownership, and backup policy. Define deletion across request revisions, proposals, provider retention, telemetry, and backups; keep only minimal audit metadata consistent with the agreed policy. No retention duration or legal compliance is claimed yet.

## Proposed permission matrix

| Identity | Allowed | Explicit boundary |
| --- | --- | --- |
| Employee | Create/read requests in the deployment, request analysis, view proposals | Cannot approve, assign roles, or invoke recovery |
| Reviewer | Employee actions, approve/reject, change status, maintain approved task state | Must pass revision checks; cannot approve as an agent identity |
| Administrator | Provision accounts/roles and update business profile | Reviewer permission requires a separate assignment; changes audited |
| Operator | Redacted service telemetry and staging recovery approval | No default customer-content access or business approvals |
| API service | Authorized domain writes and audit events | Database privilege limited to application needs |
| Job runner / graph | Read versioned input; persist run/proposal through narrow service interfaces | Cannot create active tasks or approve; database grants/interfaces must enforce separation |
| MCP tool identity | Read active profile and allowed staff directory fields | No generic SQL, filesystem, shell, or mutation tools |
| On-call agent | Read sanitized diagnostics, propose allowlisted recovery, execute approved staging flag reset | No production writes, arbitrary shell, deletion, code changes or redeployment |
| CI/CD identity | Test on isolated data; deploy approved artifacts to selected target | Deployment secrets unavailable to untrusted pull-request code |

All access checks run on the server. Hiding a UI control is insufficient. Service credentials must enforce their permissions independently of an LLM's instructions. MVP deployments have one business context; do not market this as tenant-isolated SaaS. Tenant isolation requires a separate design and tests before shared hosting of multiple businesses.

## Human approval boundaries

Creating a request, viewing permitted data, and running read-only analysis require ordinary user authorization. Agent proposals remain inactive until a reviewer explicitly approves the displayed changes. Approval binds to proposal ID, input revision and exact payload; rejection and stale revisions apply nothing. Any later edit requires a new proposal and review. Apply approved tasks and audit events atomically and idempotently.

External email, customer contact, binding quotations, purchases, CRM mutation, and external scheduling are outside the MVP. Adding them requires a new permission design, an explicit user-facing approval step, scoped tools, auditability, and acceptance tests. Approval for one proposal never authorizes unrelated future actions.

Operational approval is separate: an operator approves one specific staging recovery action for one incident. The recovery service checks environment, incident identity, action allowlist, expiry, and whether that action has already executed. Enforce a single attempt, verify synthetic queue processing within 180 seconds, and escalate if verification fails. The application must not infer approval from silence or model confidence.

An authenticated alert receiver must automatically wake the responder and deduplicate repeated incidents. Wake-up and read-only diagnosis do not authorize mutation: the agent waits for approval and then executes the exact allowlisted staging reset itself. A human performing the repair or manually starting the agent is not the intended alert-driven repair evidence. Production deployment remains a separate manually initiated, authorized release workflow; automatic dev deployment cannot promote itself to production.

The Module 5 coding-agent reviewer and MCP client require separate scoped identities and an executable guardrail as planned in [module5-checklist.md](module5-checklist.md). Current team role descriptions do not establish registered subagents or enforced hooks. Any later subagent demonstration still requires explicit user authorization. Pilot assumptions and permission ownership remain pending in the [specification](specification.md#pilot-assumptions-requiring-confirmation).

## Untrusted content and model boundaries

Customer text and tool responses are data, even if they contain instructions. Agents must not follow embedded demands to reveal secrets, override policy, grant permissions, or call additional tools. Validate schemas, tool arguments, response sizes, deadlines and identifiers in application code. Render model output as escaped text; do not execute generated code or render unsanitized HTML.

Send the model only data needed for the task and permitted by the selected provider policy. Use restricted network access where practical, explicit timeouts, bounded retries, usage budgets and per-user run limits. Fail closed on unknown tools, invalid outputs, missing authorization or stale approvals. Do not persist hidden model reasoning; retain only necessary structured results and concise explanations.

## Audit and operational access

Record actor, action, target, timestamp, correlation ID, proposal/revision, decision, and outcome. Keep request content out of general audit metadata and telemetry. Restrict audit reads, prevent ordinary users from altering history, and define retention before pilot use. Protect telemetry endpoints and dashboards with authentication; keep database ports private.

Before public deployment, verify session security, backend authorization, input/output handling, HTTPS, secret separation, backup/restore, approval concurrency, and staging recovery limits through the corresponding backlog criteria. These checks are required delivery work, not evidence already available.
