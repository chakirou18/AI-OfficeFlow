# Actual main-agent skill review

Input: `agent-capabilities/review-api-change/fixtures/approval-change.diff`, an
isolated 32-line hypothetical file `synthetic/approval_candidate.py`. The main
coding agent read the canonical `SKILL.md` and invoked the guarded fixture read.
The patch was never applied, imported or executed. These findings come from that
actual main-agent review; they are not the independent subagent result or a test
oracle supplied to it. No business decision was approved.

| Severity | Candidate lines | Finding and verification needed |
| --- | --- | --- |
| P1 | 19-22 | A model result defaults to automatic approval and calls the task-creating decision function. This bypasses the human-only activation boundary. Verify that arbitrary model output cannot create active tasks and only an authenticated human decision can activate the saved proposal. |
| P1 | 10-16 | The approved state commits before task creation, followed by one commit per task. A later invalid task or database error can leave an approved run and partial tasks. Verify rollback of the complete decision/task/activity transaction on any failed insert. |
| P1 | 5, 13-15 | Tasks come from the caller rather than the persisted proposal, so the caller can replace suggested text/priority. Verify exact saved-proposal fidelity and bounded validated task fields. |
| P1 evidence gap | 8-9 | The shown route has only a database dependency, without human identity, CSRF/Origin or request-context checks. Router-level security is not provided, so its absence outside this excerpt cannot be asserted. Require anonymous/forbidden/CSRF denial evidence before accepting the change. |
| P2 | 4-6, 9-10, 24-31 | Untyped task dictionaries, an unvalidated string ID and a success-only test do not establish schema limits, missing-record behavior, replay/concurrency safety or uniqueness. Add invalid UUID/enum/size/extra-field, not-found, replay and concurrent-decision checks against isolated PostgreSQL. Existing database constraints are not shown, so their absence is not claimed. |

Disposition: reject this synthetic proposal pending corrections and the listed
verification. The production implementation was not changed or evaluated by
executing this candidate. Native reviewer invocation and its independent findings
remain a separate requirement until explicit authorization and real execution.
