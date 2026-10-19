# ADR 0003 — Controlled sessions, roles and human approval

Status: **Accepted for prototype design**. Owner: T03; implementation: T06, T11, T12. Actual company access policies remain provisional A03.

## Decision

Use controlled local accounts and opaque server-side sessions for the synthetic prototype. Store Argon2id password hashes; use an established library and never custom cryptography. Provision initial accounts through an explicit maintainer-controlled setup step with generated credentials, not a committed seed password or public self-registration. First startup may serve login/health without an account; provisioning is required before protected use.

The browser gets a random session cookie; store only its hash and metadata server-side. Public deployment requires `Secure`, `HttpOnly`, `SameSite=Lax`, a narrow path and HTTPS. Only explicit loopback local mode may relax `Secure`; that mode is rejected on public deployment. Proposed limits: 30-minute idle expiry and four-hour absolute expiry, logout/revocation on role/security changes and session rotation at login. Require a CSRF token plus same-origin/Origin checks for mutations, explicit CORS configuration and login/run rate limits. Never use long-lived bearer tokens in browser local storage. Application authorization is checked on every API action, not only in the UI.

Roles follow the specification: employee captures/reads/submits analysis; reviewer reviews proposals, maintains tasks and changes status; administrator provisions roles/profile; operator reads sanitized telemetry and approves recovery. No role implies reviewer permission automatically. Public demo operator access must not grant request-body access. The prototype permits a creator who also has reviewer role to approve a proposal; independent second-person approval is deferred pending A03 validation, and must not be advertised as four-eyes control.

## Transactional approval boundary

Request text, model fields and tool results cannot grant authority. Business agents only produce pending proposals. A human reviewer sees the original input, evidence, unknowns, assumptions and exact changes. Approval endpoint requires proposal ID, input revision, expected concurrency version and idempotency key. The request must be in `in_review`; the reviewer can explicitly move `new` to `in_review` first. Approval atomically applies approved tasks and transitions to `in_progress` if appropriate. Analysis does not silently move request status.

Within a database transaction, lock request then proposal; recheck active user/role, request revision, latest run ID, pending state and stored payload hash. Insert one decision, tasks with uniqueness constraints, status change and audit record together. A retry for the same approved payload returns the stored result; a conflicting decision, stale revision or terminal request returns conflict with no mutation. Rejection requires a reason and never applies proposed tasks. Revisions supersede old pending proposals; corrections require regeneration. API is the only domain write path. No external action tools exist in the MVP.

## Alternatives, cost and security

Managed OIDC reduces password lifecycle work and fits future business onboarding, but adds provider configuration, availability and potentially fees; reconsider before real users. Self-hosted OIDC adds another service and maintenance cost. Stateless JWT sessions reduce lookup costs but make immediate revocation/role changes harder. A no-auth demo is unsuitable for the intended public staging.

Benefits: one deployable API, revocable sessions and deterministic role tests. Trade-off: the project owns password/session security and controlled account lifecycle; production real-data readiness requires a new review. No external identity subscription is selected. Rate limiting, account recovery policy and brute-force tests must be implemented before public access. T06/T12 verify anonymous/forbidden paths, CSRF/session expiry and stale/concurrent approvals. Nothing is implemented yet.
