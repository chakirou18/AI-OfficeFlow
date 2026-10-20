# T18 verified local execution

Tested source: **`1024ed57a80df8ba59a8acebb7a0af97379be813`**, exported on
2026-10-20 from the T18 branch, after T17 merge `6a6098f`.
[PR #36](https://github.com/chakirou18/AI-OfficeFlow/pull/36) /
[Issue #18](https://github.com/chakirou18/AI-OfficeFlow/issues/18).
This is an actual **clean-source run using cached dependencies**, not a cold
installation, public deployment or new real-model evaluation.

The [sanitized JSON](t18-validation.json) contains exact command arrays, working
directory roles, exit codes, timings, environment, temporary override, persistence
hashes and source/resource preservation results. Local retained log names and
SHA-256 hashes identify the originals without publishing raw logs/private config.
All 27 retained log hashes and all 172 source files were rechecked before publication.

## Confirmed results

| Check | Result | Duration |
| --- | --- | --- |
| Backend | **190 passed: 105 unit, 85 integration**, exit 0; real isolated PostgreSQL | Pytest 83.95 s; Compose command 91.906 s |
| Browser | **15 passed**, installed Edge, exit 0 | Playwright 14.5 s; npm command 15.516 s |
| Frontend lint / typechecked build | Both exit 0 | 2.547 s / 2.172 s |
| Migration head | `0006_human_decisions`, exit 0 | 4.125 s |
| Migration drift | No new upgrade operations, exit 0 | 4.218 s |
| Initial full stack | Services started, exit 0; initial host port access failed | 29.187 s |
| Corrected loopback edge | Temporary API/frontend/Grafana network correction, exit 0 | 15.875 s; not a second cold startup |
| Proxied readiness | HTTP 200 with PostgreSQL readiness | 0.031 s |
| Restart persistence | Full-row hashes unchanged for 17 requests, 5 analysis runs, 5 tasks | 4.312 s |
| Isolated cleanup | Only temporary project's containers stopped; named volumes retained | 3.703 s |

Environment: Windows; Docker Engine 29.9.1 Linux, Compose 5.6.0, PostgreSQL 17.11;
host Python 3.12.10, container Python 3.12.15, Node 24.19.0, npm 11.17.0.
No dependency/model installation occurred. Model mode was simulated throughout.

The backend covers the actual 30-second deadline, strict output validation,
persisted call allowance, auth/CSRF, concurrency/rollback, human-only decisions,
MCP stdio/read-only denial, telemetry and isolated on-call failure boundaries.
Browser tests cover create/view/analyze/approve/reject, persisted task IDs/content,
dashboard counts, escaped text and failure states. Three initial tasks were
explicit browser fixtures; separate real authenticated approval tests created tasks.
Persistence compares all request/analysis/task column values before and after
isolated db/api restart. It is not a claim that the browser suite ran after restart.

## Recovery, errors and provenance

- The first `compose run --no-build` invocation exited **1 in 0.109 s**:
  `unknown flag: --no-build`. No backend tests ran in that invocation.
- The corrected `run --pull never --rm test` completed successfully. Its log and
  recorded exit code were recovered after session interruption; it was not rerun.
- The initial internal-only network exposed no host ports and HTTP failed with
  WinError 10061. The temporary override added a separate project edge network
  for the three services whose host bindings remained `127.0.0.1`.
- A Windows cp1252 console encoding error interrupted the temporary harness after
  the frontend build had returned 0 and saved its log. Only harness display was fixed.
- Browser output included a harmless NO_COLOR/FORCE_COLOR warning.

The corrected backend log's recorded filesystem last-write time is
`2026-10-20T07:41:44.616269+00:00`; browser log:
`2026-10-20T07:40:02.551790+00:00`. These are filesystem metadata, not independently
attested execution timestamps. Exact command-start timestamps were not captured.
Docker startup duration was terminal-only and is deliberately excluded from the
file-verified measurements. Original logs remain ignored in
`artifacts/t18-local-1024ed5/`; do not publish that directory.

## Isolation and limits

Project: `officeflow-t18-1024ed5`; runtime DB `officeflow_t18_test`; backend test DB
`officeflow_test` on a separate project-owned tmpfs container. Published ports:
frontend 9082, API 9002, Grafana 3002, all loopback. Each named volume has the new
project prefix. Source/migrations/frontend output were mounted read-only onto
existing images; backend lock hashes matched, and existing npm packages were copied.

API, PostgreSQL, frontend and test-db had Docker healthchecks passing; other
long-running services were running, not all independently healthchecked.
Collector/Prometheus/Loki/Tempo/Grafana/Alertmanager/listener startup does not
constitute a fresh telemetry UI or incident demonstration. T13-T17 evidence is
reused at its original commits.

All baseline volume names, image tags/IDs and container IDs remained present;
172 exported source files were byte-identical and tracked Git remained clean.
This is inventory preservation, not a content audit of production databases.
The temporary stack was stopped; its persistent volumes were retained. No existing
environment was recreated, no controller/reviewer/incident ran, and no release,
promotion, model call, deletion or public exposure occurred.

See the [reproduction guide](../t18-clean-checkout.md). Cold dependency installation
and an unmodified cold Docker build remain **NOT VERIFIED**. No commercial timing
guarantee, official score or course peer-review submission is claimed.
