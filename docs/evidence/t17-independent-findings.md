# Actual independent subprocess reviewer findings

This is the actual response from the independent reviewer process, not native spawn_agent output.

I’m applying the supplied review-api-change skill to the synthetic patch only, focusing on validation, authorization, human approval, transaction safety, and test coverage.

Findings for the parent reviewer; all references are to `synthetic/approval_candidate.py`.

- **Critical — Model output activates tasks without a human decision (lines 19–22).** `after_model_result` calls `decide` when `auto_approve` is true or absent. That call marks the run approved and creates open tasks. This directly violates the human approval boundary. **Verify:** a model result with tasks and no approval flag must remain an inactive proposal and create no tasks.

- **High — Authentication and permission enforcement are absent from the supplied handler (lines 8–10).** No session, ownership, or decision permission check is visible before accessing and approving the run. Global middleware or router dependencies are unknown; CSRF/Origin protection is also not shown. **Verify:** unauthenticated and unauthorized cross-user decisions are rejected without mutations; verify CSRF/Origin rejection if cookie authentication is used.

- **High — Client tasks bypass saved-proposal integrity and validation (lines 4–6, 13–15).** The endpoint creates tasks from arbitrary client dictionaries rather than the saved proposal. Titles have no visible type/length constraints, priorities have no enum validation, and required dictionary keys are checked only during insertion. Identifier validation and explicit unknown-field rejection are absent. Raw model output is also assigned without visible proposal validation (line 20). **Verify:** altered proposals, invalid identifiers, missing keys, oversized titles, invalid priorities, and extra fields fail before any write.

- **High — Approval and task creation can partially commit (lines 11–16).** Approval commits first, followed by a separate commit for each task. A missing key or database failure can leave an approved run with zero or only some tasks. No atomic activity update is shown. **Verify:** force failure on a later task insert and assert that the decision, all task inserts, and activity changes roll back together.

- **High — Replay and concurrent decisions can duplicate tasks (lines 10–16).** The handler has no visible state transition guard, locking, idempotency check, or uniqueness enforcement. Repeating a request attempts the inserts again. Database constraints are unknown because no schema is supplied. **Verify:** replay and simultaneous decisions against isolated PostgreSQL produce exactly one decision and one task set.

- **Medium — Tests do not exercise the required safety properties (lines 24–31).** The sole test checks HTTP 200; it does not assert persisted state or task integrity. Denial, human approval enforcement, validation, rollback, replay, and concurrency coverage are absent. **Verify:** add those cases with isolated PostgreSQL for persistence behavior.

**Disposition:** Request changes. The model-driven activation and partial commits are explicit in the patch.

**Limitations and remaining questions:** Static review only; no tools or tests were run. Global authentication/CSRF controls, database constraints, activity handling, and proposal persistence are unavailable. The parent owns the final decision.