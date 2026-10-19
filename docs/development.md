# T04 local foundation guide

Scope: the frontend/API/PostgreSQL foundation for [Issue #4](https://github.com/chakirou18/AI-OfficeFlow/issues/4). This is not the request/task application yet. The only write operation saves a fixed synthetic connectivity record. No authentication, AI, CI, deployment, telemetry or incident feature is implemented; keep this foundation local.

## Prerequisites and configuration

Verified on Windows PowerShell with Docker Desktop running **Linux containers**, Docker Engine 29.8.0, Compose 5.5.1 and Python 3.12.10. Docker Desktop must be running; `docker version` must show both client and server. Initial builds need registry access for images/packages. Host Python is used only for the configuration/persistence helpers. Host Node is unnecessary for Compose startup; optional frontend/browser checks were verified with Node 24.19.0 and npm 11.17.0.

From the repository root, perform this one-time setup:

```powershell
python scripts/configure_local.py
```

It creates an ignored `.env` with a generated local database password and default loopback ports. It does not print the password or overwrite an existing file. [.env.example](../.env.example) documents the names with a placeholder, not usable credentials. The API rejects that placeholder. Do not commit `.env` or use this unauthenticated foundation as a public deployment.

## Start the complete T04 foundation

```powershell
docker compose up --build
```

This verified runtime command builds the frontend/API, starts PostgreSQL, waits for database health, runs `alembic upgrade head` automatically, waits for API readiness and serves the frontend. No manual schema creation is needed. The foreground command intentionally stays attached; use a second terminal for checks. Detached alternative, also verified:

```powershell
docker compose up -d --wait
docker compose ps --all
```

Expected: `frontend`, `api`, `db` healthy; `migrate` exited **0** (successful one-shot job, not a crashed service). A `test-db` container may be stopped after running tests. T04 has four core services; the final project's telemetry/on-call services are later scope and are not claimed present.

| Local address | Purpose |
| --- | --- |
| [http://127.0.0.1:8080](http://127.0.0.1:8080) | React page, health cards and synthetic write/read check |
| [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs) | FastAPI/OpenAPI docs; also `/api/docs` through the frontend proxy |
| [API liveness](http://127.0.0.1:8000/api/v1/health/live) | Process-only HTTP 200 independent of database availability |
| [API readiness](http://127.0.0.1:8000/api/v1/health/ready) | Real PostgreSQL query, Alembic revision and migrated-table check; unavailable database returns sanitized 503 |

PostgreSQL is private on the Compose network with no published host port. Change `FRONTEND_PORT`/`API_PORT` in ignored `.env` if needed; the frontend uses same-origin API paths and does not receive database credentials. Changing a password in `.env` does not rotate an already initialized PostgreSQL account; preserve the original configuration instead of deleting its data volume.

## Foundation tests and schema checks

```powershell
docker compose --profile test run --build --rm test
```

Verified: **5 passed** (2 unit, 3 PostgreSQL integration), one upstream Starlette TestClient/httpx deprecation warning. This command runs migrations and both suites against `officeflow_test` on `test-db`, not the development database. That database uses tmpfs and has no host port. The runner refuses migration/test execution unless the database name ends in `_test`. These are foundation checks, not completed T12 product coverage or T05 CI.

```powershell
docker compose exec -T api alembic current
docker compose exec -T api alembic check
```

Verified outputs: `0001_foundation (head)` and `No new upgrade operations detected.` No migration downgrade was executed.

## Persistence after container restart

With the local stack running:

```powershell
python scripts/verify_persistence.py
```

This verified helper creates a fixed synthetic check via the frontend proxy, independently reads it, runs `docker compose restart db api`, waits for API/database readiness and verifies the identical ID, marker and timestamp. It writes a synthetic JSON evidence file to ignored `artifacts/t04-persistence.json`. It preserves the named `postgres_data` volume. The initial successful check ID was `e7767c71-9d2a-470b-8ea4-36c274a3860e`; rerunning creates a fresh ID.

If using a nondefault frontend port, set `FRONTEND_URL` to its loopback URL in the helper's environment. Avoid concurrent persistence/browser tests because the helper deliberately restarts services.

## Optional host frontend/browser checks

```powershell
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run build
$env:BROWSER_CHANNEL = 'msedge'
npm.cmd --prefix frontend run test:e2e
```

The build command runs TypeScript checking and a Vite production build. The browser command was verified with the **already-installed Microsoft Edge**, headless: **2 passed**. No browser download was needed. Tests cover the UI → API → database write/read, page reload with the same record, and a simulated HTTP 503 error. A screenshot is written to ignored `artifacts/t04-foundation.png`; the reviewed example is also included in the verification record.

On another machine, install Node 24 if using these optional host checks and ensure the configured Playwright browser is actually installed. With no `BROWSER_CHANNEL`, Playwright expects its own Chromium installation; that alternative was not exercised here. Compose builds need neither host Node nor a host browser.

## Stop, resume and troubleshoot

`docker compose stop` pauses the containers; `docker compose up -d --wait` resumes them. `docker compose down` removes this project's containers/network while preserving the named database volume. Do not add `--volumes` if you want to preserve data. These commands are distinct from restarting the unrelated clean-verification project used during development.

If Docker reports permission/connection errors, check Docker Desktop is running in Linux-container mode and that the terminal has Docker access. The agent's sandbox denied daemon/cache access; retrying through the authorized host tool succeeded, so this was not a missing Docker installation. If a required tool is absent, install it through its official installer before attempting the command: [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/), [Python](https://www.python.org/downloads/), and optional [Node.js](https://nodejs.org/en/download). Run `docker version`, `docker compose version` and `python --version` afterward; no unavailable-tool test is counted as passed.

For reproducible source verification and actual failures/fixes, see [t04-verification.md](t04-verification.md). No `.github/workflows` is added; stop at the T04 PR review.

## Continuous integration (T05)

`.github/workflows/ci.yml` runs on every pull request and push to `main`.
`Backend checks` runs Ruff 0.14.0 (`--select E9,F`), unit tests, Alembic migrations,
and integration tests against a disposable PostgreSQL 17 service and `_test` database.
`Frontend checks` runs locked `npm ci`, Oxlint, and `npm run build` (including strict
TypeScript checking). Both jobs are required by main branch protection, including
administrator merges. CI has read-only repository permissions and no deployment,
model or production credentials. Its public database password is an ephemeral fixture.

For equivalent focused checks, install `backend/requirements-test.lock` with
`pip install --require-hashes`, install `ruff==0.14.0`, and run
`ruff check --select E9,F backend scripts`. From `backend`, run
`python -m pytest tests/unit -v`; integration additionally needs the isolated test
database configuration and `python -m alembic upgrade head` before
`python -m pytest tests/integration -v`. Existing Compose test instructions above
remain the simplest full database test command. Frontend checks are
`npm --prefix frontend run lint` and `npm --prefix frontend run build` after `npm ci`.

T16 can consume a successful CI run on trusted `main` via a separate
`workflow_run` workflow, checking success, repository, branch and commit before
using deployment credentials. PR runs never deploy. Automatic development deployment,
manual production promotion and environment approvals are deliberately not implemented
in T05. Exact CI and merge-gate verification evidence is recorded in Issue #5.
