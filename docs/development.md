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

## Controlled demo authentication (T06)

After Compose startup, create an account from a trusted terminal:

```sh
docker compose exec api python -m app.manage_users create demo_user
# Password is prompted without echo (16-128 characters); never use real personal data.
docker compose exec api python -m app.manage_users revoke demo_user
# revoke deletes all current sessions; disable also prevents future login:
docker compose exec api python -m app.manage_users disable demo_user
```

There is no signup API or default demo password. The CLI refuses to overwrite accounts.
Passwords use salted scrypt (N=16384, r=8, p=5); only SHA-256 session-token hashes
are stored. Login rotates the current session; logout deletes it. Sessions expire after
eight hours and disabled users are denied. Five failed account logins lock that account
for five minutes. This bounded demo still needs deployment-level traffic limits before
public exposure; it does not claim enterprise authentication guarantees.

`POST /api/v1/auth/login` accepts handle/password JSON with an allowlisted exact
`Origin`. `GET /api/v1/auth/me` returns handle and a session-bound CSRF token.
All authenticated mutations require that Origin and `X-CSRF-Token`; logout is POST.
Cookies are HttpOnly, SameSite=Strict, host-only and Secure by default in Python.
Compose explicitly permits non-Secure cookies only for its loopback HTTP demo.
For HTTPS deployment set `COOKIE_SECURE=true` and exact `APP_ORIGINS`; do not
include untrusted origins. Auth/API responses are not cached. TLS deployment is T16.

The foundation write/read endpoints now require login (write also requires CSRF).
Health probes remain public and metadata-only. `/api/v1/ops/health` requires a
separate `Authorization: Bearer ...` token configured privately as `OPS_TOKEN`
(at least 32 random characters). Empty/unconfigured tokens deny access. This route
only returns diagnostic health; no incident or repair controls are introduced.
Demo sessions cannot authorize ops, and the ops bearer token cannot authorize app writes.

The existing persistence script prompts for handle/password or uses private process
environment `DEMO_HANDLE`/`DEMO_PASSWORD`. Browser smoke tests require those variables
and an available browser (`BROWSER_CHANNEL=msedge` on this workstation); no credentials
are committed. The tests now cover sign-in, reload, write failure and sign-out.

Security references: [Python scrypt](https://docs.python.org/3/library/hashlib.html#hashlib.scrypt),
[OWASP sessions](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html),
and [OWASP CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).

## Request and task API (T07)

All routes below require a demo session. POST/PATCH also require the configured
Origin and `X-CSRF-Token` returned by login or `/auth/me`.

| Method and path | Contract |
| --- | --- |
| `POST /api/v1/requests` | Only `title` and `description`; trimmed lengths 1-200 and 1-5000. Returns 201 with immutable text, UUID, creator handle, timestamps, new status and empty tasks. |
| `GET /api/v1/requests` | `limit` 1-50 (default 20), `offset` 0-10000, optional `status`; returns items/total/limit/offset. Stable descending created_at/UUID order. |
| `GET /api/v1/requests/{id}` | Original text, creator, timestamps, derived status and persisted tasks. |
| `PATCH /api/v1/requests/{id}/tasks/{task_id}` | Only `state: open` or `state: done`; persists atomically, serializing updates through a parent request lock. Repeating the same state preserves timestamps. |

Invalid fields/limits/UUIDs return 422; missing records or mismatched request/task IDs
return 404; missing/invalid sessions return 401; CSRF/Origin failures return 403.
There are no request edit/delete endpoints and no public task-creation endpoint.
Accounts share the same synthetic workspace; access is not restricted to the creator.
Creator identity comes from the session, never the input payload.

Status derives from persisted task rows: no tasks means `new`, any open task means
`in_progress`, and all tasks done means `completed`. `awaiting_review` is a reserved
filter which currently returns no rows; pending analyses and their status integration
belong to T09/T11. T07 does not claim analysis/approval workflow completion.

Migration `0003_requests` adds requests/tasks, foreign keys, state/priority/length
constraints and unique `(analysis_id, suggestion_index)` source identity. Analysis IDs
are reserved UUIDs without an analysis foreign key until the analysis table exists in
T09/T11. Only future human approval may create tasks through the app; T07's integration
tests insert explicitly synthetic approved-task fixtures directly into PostgreSQL.
No task seed endpoint or implicit approval is provided. Request-management UI is T08.

Run the existing aggregate Compose test command for request validation, independent
session reads, fresh application instances, maximum page size, deterministic pagination,
state/filter derivation, repeat updates, database constraints and auth/CSRF/ops denials.
`docker compose --profile test run --rm test alembic check` verifies ORM/migration drift.
Actual local/CI counts and results are recorded on Issue #7.
