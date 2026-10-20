# T18 final evidence and handover

Audit date: 2026-10-20. Owner: [Issue #18](https://github.com/chakirou18/AI-OfficeFlow/issues/18).
Audited application source: `6a6098f6baa36e3b49b2dfdaacc721981237f102`,
the verified merge of [T17 PR #35](https://github.com/chakirou18/AI-OfficeFlow/pull/35).
Initial local main and remote main matched; the working tree was clean.
Dependencies T02, T12, T15, T16 and T17 were read and confirmed closed.
T18 remains open: current clean-source runtime validation and three course review
confirmations are outstanding. No grading score or course submission is claimed.

## Product and architecture

AI OfficeFlow is a synthetic shared request/task workspace: create/view immutable
requests, obtain proposed tasks and priorities, approve/reject them explicitly,
persist approved tasks, update open/done state and inspect dashboard totals.
See [specification](specification.md) and [code-based architecture map](implementation-map.md).
There is no company integration, external business action or enterprise role UI.

The [12-criterion evidence matrix](grading-checklist.md) gives maximum available
points, evidence and limitations. The [seven Module 5 requirements](module5-checklist.md)
are individually backed by the [T17 demonstration](evidence/t17-integrated-demo.md).
VERIFIED means sufficient inspectable evidence for the stated behavior, including
explicitly dated historical evidence; it does not mean points awarded or a new run.
PARTIAL means incomplete evidence; MISSING means no artifact; BLOCKED means a
specified external condition prevents verification.

## Technical validation

New T18 checks on the audited source, using existing installed tools only:

| Command/check | Observed result | Timing and limit |
| --- | --- | --- |
| `python -m unittest discover -s scripts/tests -v` | 21 passed; deployment provenance/privacy/isolation and review guardrail tests | unittest 0.034 s; full command 0.294 s; mocked deployment/CLI boundaries, no reviewer invocation |
| `npm.cmd --prefix frontend run lint` then `npm.cmd --prefix frontend run build` | Passed, including TypeScript and Vite production output | Combined 1.851 s; Vite 161 ms; existing node_modules, not a clean install |
| `docker version`, `docker image ls`, `docker ps` | BLOCKED: Docker Desktop Linux engine named pipe absent, including outside sandbox | No container, backend PostgreSQL, browser or live telemetry run claimed |
| Clean tracked-source configuration | Both setup helpers and `docker compose -p officeflow-t18-clean config --quiet` passed | Configuration parse only; runtime and smoke timings unavailable |
| Documentation checks | 17 changed Markdown files; 187 local file/anchor links and balanced fences verified; limited credential-pattern scan found no candidates; `git diff --check` passed | Local script `python artifacts/t18_check_docs.py`; no blanket security-audit claim |
| Initial main CI | [39382640382](https://github.com/chakirou18/AI-OfficeFlow/actions/runs/39382640382), both required jobs success at audited SHA | Backend checks 107 s; Frontend checks 7 s; hosted execution, not local tests |

Installed tools observed: Windows PowerShell, Python 3.12.10, Node 24.19.0,
npm 11.17.0, Docker client 29.9.1 and Compose v5.6.0. No running Docker server
version could be measured. No dependency, model or runtime was installed.

Historical checks reused, not rerun:

| Evidence | Source/results |
| --- | --- |
| Full application coverage T12 | [Testing](testing.md), [PR #27](https://github.com/chakirou18/AI-OfficeFlow/pull/27): 145 backend tests, 64.21 s; 15 Edge tests, 14.9 s |
| Later on-call/backend coverage T15 | [Issue #15](https://github.com/chakirou18/AI-OfficeFlow/issues/15), [PR #30](https://github.com/chakirou18/AI-OfficeFlow/pull/30), source `e8705e1`: 188 backend tests, 81.22 s |
| Real model T10 | [Recorded evaluation](t10-verification.md), [PR #25](https://github.com/chakirou18/AI-OfficeFlow/pull/25): three real local Ollama proposals; failed first attempt preserved; no new inference |
| MCP T17 | [Checklist](module5-checklist.md): 3 real stdio/PostgreSQL tests, 9.18 s; read allowed, writes/approval denied |
| Reviewer T17 | Independent CLI process/session, six findings, zero tool items, 166 unchanged files; no native spawn success claimed |

Frontend validation consists of lint/typechecked build and real browser tests;
there is no separately claimed frontend unit-test suite. The backend aggregate
suite covers actual PostgreSQL concurrency/rollback and a real 30-second timeout
using deterministic model simulation.

## Reproduction from clean source

Use [clean-source instructions and actual observations](t18-clean-checkout.md).
The complete installation procedure is [development.md](development.md).
Initial builds require approved image/package downloads if caches are absent.
Default model mode is simulated. A new local runtime check must use separate
Compose project/ports/credentials and retain every existing volume.

## Deployment, monitoring and recovery

T16 delivered release `a43d7ddbbc4bfcb347941371dd6a14f1334ceb36`, not the later
T17/T18 documentation head. [Deployment evidence](deployment.md) includes
[development video](evidence/t16-development.webm),
[production video](evidence/t16-production.webm) and
[sanitized delivery proof](evidence/t16-delivery.json).
Automatic development deployment `7191601728` and manual production deployment
`7191726926` succeeded with identical tested private image digests. Development
rollback/forward recovery retained prior row IDs; isolated restores matched
development 7/0/7 and production 3/0/3 request/task/run counts at schema
`0006_human_decisions`. No live restore-over or downgrade occurred.

These are actual localhost deployments with recordings, not public hosting.
The foreground controller was stopped after T16. Current Docker unavailability
means the recorded apps are not claimed reachable during T18. Later successful
release workflows can enqueue requests without deploying them; initial-main
[release 39382827351](https://github.com/chakirou18/AI-OfficeFlow/actions/runs/39382827351)
is not evidence that its source was applied by a running controller.

[T13 observability](observability.md), source `175848c`, records real stored
metrics, 18 correlated events, a 21-span trace, exemplars and Grafana navigation.
[T15 recovery](oncall-agent.md), source `e8705e1`, records the real automatic
alert/diagnosis/one-clear/verification journey. Both are historical demonstrations;
no incident, recovery, deployment controller or promotion was repeated for T18.
Telemetry retention is seven days; live historical data is not guaranteed to remain.

## Demonstration and submission

1. Present the README scope and the implementation map; show the simulated mode label.
2. Once Docker is available, follow the isolated setup guide. Create a controlled
   account locally; never show its password, session or configuration.
3. Create a synthetic request, analyze, inspect the pending proposal, approve as a
   human and reload the saved tasks/dashboard. Use a second request to show rejection
   creates no task. This is a demo script, not a claim of a new T18 execution.
4. Show existing deployment recordings, exact CI/deployment IDs and restore results.
5. Show the stored observability evidence and historical T15 timeline. Do not trigger
   a new incident. Explain the four fixed on-call tools and authorization boundary.
6. Walk through the seven Module 5 links, including failed native attempts and the
   successful separately authorized subprocess review. Do not rerun the reviewer.
7. Submit the repository/PR or final approved commit and evidence entry point through
   the course platform. Check current deadlines and assigned review workflow there.

## Mandatory course peer reviews

| Assigned review | Status | Confirmation |
| --- | --- | --- |
| Review 1 | BLOCKED | No accessible submission confirmation |
| Review 2 | BLOCKED | No accessible submission confirmation |
| Review 3 | BLOCKED | No accessible submission confirmation |

The repository and inspected issue evidence contain no confirmations. The private
course dashboard has not been accessed; no claim is made that the user has not
completed reviews elsewhere. On the [course platform](https://courses.datatalks.club/ai-dev-tools-2026/),
the user must open the three distinct assigned projects, complete each rubric
evaluation, submit each review and retain its confirmation/date/status. Provide
only sanitized confirmation evidence; private feedback and identities stay private.
The T17 Codex reviewer counts as none of these three reviews. No exact current
deadline or platform button name is invented.

## Remaining gates and limitations

- BLOCKED: Docker engine availability and permission to start it before current
  clean-source startup/backend/browser timing evidence can be completed.
- BLOCKED: three genuine course-assigned review confirmations.
- PR required checks must pass on its final head; do not infer this from initial-main CI.
- Public application hosting, continuous availability, new live model calls,
  incident repetition, controller activation and production promotion are outside
  this T18 authorization. Existing public GHCR packages remain preserved.
- Runtime evidence spans identified commits. The documentation-only T18 diff does
  not establish a fresh deployment or alter application/dependency behavior.

Keep Issue #18 open and do not merge this handover prematurely. Historical ADRs,
failed attempts and evidence remain available in place and in Git/issue history.
