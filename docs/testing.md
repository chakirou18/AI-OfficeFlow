# T12 test coverage and commands

Historical T12 baseline below. Later T15 evidence records 188 backend tests (81.22 s); current T18 checks and their limits are in [final-handover.md](final-handover.md). No historical result is a fresh T18 run.

Scope: synthetic request/analysis/human-decision functionality through T11.
No telemetry, alerting, deployment or T13+ coverage is claimed. Final executed
results and required CI links are recorded on [Issue #12](https://github.com/chakirou18/AI-OfficeFlow/issues/12).

## Four acceptance criteria

| T12 criterion | Existing evidence and focused completion |
| --- | --- |
| One command: deterministic unit + real PostgreSQL integration | `docker compose --profile test run --build --rm test` builds locked test dependencies, waits for private tmpfs `test-db`, migrates `officeflow_test`, and runs both suites. The runner refuses non-`_test` databases, forces simulated mode, stops on migration failure and propagates pytest's exit status. Runner tests verify those protections. |
| Timeout/interruption, auth, task/priority validation, concurrent approval | `test_auth.py` and `test_requests.py` cover session/CSRF/Origin, validation, independent database reads and task constraints. `test_model_adapter.py`/`test_ollama.py` cover schema/priority/size bounds and mocked provider failures. `test_analysis.py` covers the actual 30-second HTTP timeout, cancellation, interrupted recovery, late-result rejection and replay. `test_decisions.py` covers duplicate/opposing concurrent decisions, 409 conflicts, rejected/stale analyses and PostgreSQL rollback including request activity/dashboard state. |
| Browser approved/rejected smoke and linked CI | `frontend/tests/workspace.spec.ts` creates requests, displays simulated suggestions, explicitly approves/rejects, checks saved task IDs/text/priority after reload, retries rejection, and checks dashboard counts. It also checks escaped text and explicit unavailable states. Required `Backend checks` and `Frontend checks` run in existing CI; exact PR runs are linked in Issue #12. Browser smoke is a separately executed local check, not claimed as a CI job. |
| Opt-in real model evaluation, separate from default tests | Compose, CI and the aggregate runner select simulated mode. An autouse pytest fixture also selects simulated mode and denies real HTTPX async transport before network access; mocked transports and in-process API tests still work. `python -m app.evaluate_ollama --real --output ...` is a separate explicit CLI, never collected/invoked by pytest or CI. Historical real results remain [T10 evidence](t10-verification.md). |

The T12 audit reuses the 131-backend/15-browser T11 baseline. Additions close
specific gaps: aggregate runner/live-call guards, maximum proposal/text bounds,
late valid results after expiration/retry, rollback activity/dashboard assertions,
and explicit saved approved-task assertions. Existing auth, failure, concurrency,
request persistence and rejection suites are preserved rather than duplicated.

Final local execution: **145 backend tests passed in 64.21 seconds**, including
real PostgreSQL and the actual 30-second timeout; **15 installed-Edge browser tests
passed in 14.9 seconds**. Each suite ran once after the changes, with no failures
or reruns. Ruff 0.14.0, frontend lint, TypeScript and Vite build passed. Private logs
are `artifacts/t12-backend-tests.log` and `artifacts/t12-browser-tests.log`.

## Run

From the repository root, after the existing one-time local setup and with Docker
Desktop running Linux containers:

```powershell
docker compose --profile test run --build --rm test
```

This is the single aggregate backend command. It includes the production 30-second
timeout test; that intentional wait is not a real model call. It does not use the
development database or require Ollama, a model download, provider keys or paid services.

Installed-Edge browser smoke uses the existing isolated browser helper:

```powershell
$env:BROWSER_CHANNEL = 'msedge'
python scripts/test_browser.py
```

The helper supplies private generated credentials and resets only named synthetic
fixtures in `officeflow_browser_test`, forces simulated mode, and preserves volumes.
It runs all 15 existing browser tests, including the affected approval/rejection flows.
See [development prerequisites](development.md) for locked npm dependencies/browser setup.

```powershell
uv tool run --from ruff==0.14.0 ruff check --select E9,F backend scripts
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend run build
```

The last command includes TypeScript checking. CI retains its required job names and
existing isolated PostgreSQL setup. Tests are not evidence that the complete 24-point
project or future operational features are finished.
