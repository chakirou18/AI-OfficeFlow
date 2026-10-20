# T17 consolidated actual demonstration — 2026-10-20

This record consolidates existing real executions and final inspection; it is not
a claim of a single continuous recording. No reviewer/supervisor or live incident
was repeated during finalization. The synthetic candidate was never applied.

| Step / requirement | Actual evidence and outcome |
| --- | --- |
| 1. Project instructions | Main agent read AGENTS.md, current Issue #17, scope, team and permission context before implementation; the issue records the read and authorized scope. Recovery/finalization reread the issue and preserved local work. |
| 2. Reusable workflow | Canonical [skill](../../agent-capabilities/review-api-change/SKILL.md) and repository discovery entry passed validation. Main agent invoked the guarded fixture read and applied the skill: [actual findings](t17-main-review.md). |
| 3. Specialized independent review | One Python supervisor launched one fresh read-only Codex CLI reviewer with the existing role and canonical skill instructions, synthetic patch only and no previous findings. [Process/session/hash evidence](t17-independent-reviewer.json) and [actual six findings](t17-independent-findings.md) establish independent execution. All five review dimensions were covered: validation, authorization, human approval, transaction safety and tests. Disposition: request changes to the hypothetical candidate; no application mutation. |
| 4. Read-only MCP | Existing T09 server reused. `docker compose --profile test run --build --rm test python -m alembic upgrade head` succeeded on the isolated test database. `docker compose --profile test run --rm test python -m pytest tests/integration/test_extension_pack.py tests/integration/test_mcp.py -q -s` passed 3 tests in 9.18s with MCP 2.3.0. Real stdio list/read, malformed/extra input, write/approval/unknown-tool denial and PostgreSQL READ ONLY write rejection; zero active tasks. [Tests](../../backend/tests/integration/test_extension_pack.py), [recorded issue](https://github.com/chakirou18/AI-OfficeFlow/issues/17#issuecomment-6283847659). |
| 5. Executable guardrail | `python agent-hooks/review_guard.py --demo` performed an allowed pinned read and denied a write/failed policy before handler effects; temporary sentinel unchanged. Four focused guardrail tests passed. [Implementation and boundaries](../../agent-hooks/README.md). |
| 6. Custom agent branch | [Package](../../custom-agent/README.md) reuses T15's actual authenticated alert-triggered diagnosis, single prior-authorized flag clear, recovery verification and deduplication. [Original incident evidence](https://github.com/chakirou18/AI-OfficeFlow/issues/15); no repeated fault or new agent loop. |
| 7. Permission/security note | [Permissions](../permissions.md) maps coding, reviewer, MCP, model, human, on-call and deployment identities to actual controls and limitations. Read-only is not OS read isolation. Reviewer emitted zero tool items; no file mutation occurred. |

## Historical failures preserved

The [first native attempt](t17-reviewer-attempt.json) reported unsupported named
selection and spawned no child. The [corrected native attempt](t17-corrected-attempt.json)
returned claimed findings without a verifiable child identity/spawn event and is
not counted as independent review. Their responses and diagnosis remain preserved.
The subsequent successful subprocess has a distinct PID and CLI session; it is
**not native spawn_agent**. All one-run approvals are consumed.

## Final inspection and delivery gate

Finalization compared all eight published artifact hashes with retained ignored
raw artifacts, verified exactly one separate reviewer process/session, compared
the 166 source hashes before/after, and matched the published response verbatim.
Only sanitized metadata, synthetic findings, source/tests and documentation are
committed; raw commands, local authentication/configuration and raw event files
remain ignored. Session IDs and PIDs are provenance identifiers, not credentials.

The recovered five offline launcher tests passed, and `git diff --check` passed.
These tests do not invoke models. Final diff inspection reconciles historical
versus current claims and preserves the required CI job names. Required final-head
Backend checks and Frontend checks gate protected merge; the PR/Issue record the
actual run URL, head SHA and merge result after execution. No T18 work or score is
claimed. All seven demonstration requirements above have evidence; CI is the
remaining delivery gate at the time this record is committed.
