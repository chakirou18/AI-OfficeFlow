# Local development guide

Scope: application through T12 and T13 local observability. Alerting, deployment and incident features remain later tasks. Keep Compose local. See [observability setup](observability.md), [test commands](testing.md) and the API sections below; historical T04-only evidence remains separate.

## Prerequisites and configuration

Verified on Windows PowerShell with Docker Desktop running **Linux containers**, Docker Engine 29.8.0, Compose 5.5.1 and Python 3.12.10. Docker Desktop must be running; `docker version` must show both client and server. Initial builds need registry access for images/packages. Host Python is used only for the configuration/persistence helpers. Host Node is unnecessary for Compose startup; optional frontend/browser checks were verified with Node 24.19.0 and npm 11.17.0.

From the repository root, perform this one-time setup:

```powershell
python scripts/configure_local.py
python scripts/configure_observability.py
```

It creates an ignored `.env` with a generated local database password and default loopback ports. It does not print the password or overwrite an existing file. [.env.example](../.env.example) documents the names with a placeholder, not usable credentials. The API rejects that placeholder. Do not commit `.env`. Public deployment requires the separate T16 HTTPS/configuration work.

## Start the local application

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

PostgreSQL is private on the Compose network with no published host port. Change `FRONTEND_PORT`/`API_PORT` in ignored `.env` if needed; also update `APP_ORIGINS` to the exact frontend origin when changing its port. The frontend uses same-origin API paths and does not receive database credentials. Changing a password in `.env` does not rotate an already initialized PostgreSQL account; preserve the original configuration instead of deleting its data volume.

## Deterministic backend tests and schema checks

```powershell
docker compose --profile test run --build --rm test
```

This aggregate command runs migrations and both unit/integration suites against real `officeflow_test` on `test-db`, not the development database. The database uses tmpfs and has no host port. The runner refuses non-`_test` database names and forces simulated mode; automatic pytest tests also deny live async HTTP. Coverage and final T12 results are linked in [testing.md](testing.md) and Issue #12. No automatic test invokes real Ollama evaluation.

```powershell
docker compose exec -T api alembic current
docker compose exec -T api alembic check
```

Current migration head is `0006_human_decisions`; T11 verified `alembic check` reported `No new upgrade operations detected.` T12 does not change the schema or rerun startup/persistence demonstrations. No migration downgrade was executed.

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
# Set private DEMO_HANDLE and DEMO_PASSWORD process variables for a controlled account.
# Never paste real credentials into repository files or public terminal transcripts.
npm.cmd --prefix frontend run test:e2e
```

The build command runs TypeScript checking and a Vite production build. T06 verified **3 authenticated browser tests** with installed Edge, covering login/logout, write/read/reload and a simulated 503. T07 separately verified **1 HTTP proxy security test**; it needs no demo credentials (`npm.cmd --prefix frontend run test:e2e -- --grep 'private operations'`). No browser download was needed. Screenshots/artifacts remain ignored; the historical T04 screenshot predates login.

On another machine, install Node 24 if using these optional host checks and ensure the configured Playwright browser is actually installed. With no `BROWSER_CHANNEL`, Playwright expects its own Chromium installation; that alternative was not exercised here. Compose builds need neither host Node nor a host browser.

## Stop, resume and troubleshoot

`docker compose stop` pauses the containers; `docker compose up -d --wait` resumes them. `docker compose down` removes this project's containers/network while preserving the named database volume. Do not add `--volumes` if you want to preserve data. These commands are distinct from restarting the unrelated clean-verification project used during development.

If Docker reports permission/connection errors, check Docker Desktop is running in Linux-container mode and that the terminal has Docker access. The agent's sandbox denied daemon/cache access; retrying through the authorized host tool succeeded, so this was not a missing Docker installation. If a required tool is absent, install it through its official installer before attempting the command: [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/), [Python](https://www.python.org/downloads/), and optional [Node.js](https://nodejs.org/en/download). Run `docker version`, `docker compose version` and `python --version` afterward; no unavailable-tool test is counted as passed.

For historical clean-source verification and T04 failures/fixes, see [t04-verification.md](t04-verification.md). Current CI is in `.github/workflows/ci.yml`; T06/T07 evidence is recorded in their public issues.

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


## Request workspace and isolated browser tests (T08)

Sign in at http://127.0.0.1:8080. Overview shows real request/task totals, status
links and recent persisted requests/task updates. Requests provides create, paginated
list/filter, detail, priorities and open/done updates. Refresh reloads persisted state;
expired sessions return to sign-in. System health retains the T04 write/read check.
No live AI, analysis history, invented activity or task-creation UI is present.
`GET /api/v1/dashboard` is an authenticated read-only extension that aggregates the
entire workspace in a consistent PostgreSQL snapshot, independent of list pagination.

For repeatable browser checks, install the locked frontend packages (`npm --prefix
frontend ci`) and an available Playwright browser. On this workstation use installed
Edge; on other machines install Playwright Chromium with `npm --prefix frontend exec
-- playwright install chromium` after checking platform prerequisites.

```powershell
$env:BROWSER_CHANNEL = 'msedge'  # omit when using installed Playwright Chromium
python scripts/test_browser.py
```

The helper starts only the dedicated `officeflow-browser` Compose project at ports
8081/8001, with database `officeflow_browser_test` and a private generated password in
ignored `artifacts/browser.env`. It creates a random-password test account and resets
only its own named fixture records. The CLI seed refuses a non-`_test` database or
missing explicit `BROWSER_FIXTURES=enabled`. Seeded task rows are clearly synthetic
approved-task test fixtures, not evidence of a T11 human approval operation. No seed
endpoint exists and normal startup never seeds tasks. Tests cover real API/DB state;
503/loading simulations are explicit test-only route intercepts. Screenshots are
written to ignored `artifacts/t08-desktop.png` and `artifacts/t08-mobile.png`.

The helper stops/removes its own containers/network on completion, preserving its
volume and the ordinary local stack/data. Do not run two copies concurrently. No
credentials are printed or committed. Existing backend aggregate tests remain
`docker compose --profile test run --build --rm test`. Exact outcomes and CI evidence
are recorded on Issue #8.


## Bounded offline analysis and read-only MCP (T09)

Rebuild/start with `docker compose up --build`; migration `0004_analysis` runs
before the API starts. HTTP callers wait for one async, cancellable offline adapter
call inside the same request; there is no worker, queue, graph or background retry.

| API | Behavior |
| --- | --- |
| `POST /api/v1/requests/{id}/analyses` | Requires session, Origin, CSRF and UUID `Idempotency-Key` header. Persists running before calling the adapter outside any DB transaction; returns 201 pending/simulated proposal, 504 timeout or 502 sanitized failure. |
| `GET /api/v1/requests/{id}/analyses?limit=20&offset=0` | Authenticated bounded history; limit 1-50, offset 0-10000. |
| Request detail/list/dashboard | Detail includes latest analysis; pending proposals derive awaiting_review status and counts. |

Proposals have a bounded summary and 1-5 title/priority/rationale suggestions. They
are inactive JSON, never task records. Same-key replay returns the persisted attempt
without calling the adapter; a new key explicitly retries a failed attempt. A distinct
key while running/pending, or a request with approved tasks, returns 409. No approval
or rejection endpoint/UI is added; those remain T11. The workspace has no Analyze
control yet; the API/OpenAPI contract exposes T09 execution without claiming a full
analysis-review UI or live AI quality.

The deadline is recorded as started_at + 30 seconds; model execution uses only the
remaining time and late results cannot become pending. Timeout, cancellation, provider
failure and invalid output create no tasks. After process interruption, expired running
attempts become failed/interrupted on authenticated history/detail access or a new
attempt; no background recovery service is promised. A partial unique index and parent
request locks enforce one running/pending attempt. Future adapters must use cancellable
async I/O, not blocking provider calls, and remain subject to the same deadline. The
proxy allows 40 seconds for the bounded request; database outage/response overhead is
separate from the persisted model deadline. Error codes contain no provider text.

Offline mode is always simulated and makes no network/model calls; callers cannot
select a fault fixture or live provider. Twelve synthetic input fixtures cover normal,
ambiguous, whitespace-invalid, Unicode and adversarial text; injected adapters test
provider failure, invalid output, timeout, cancellation and concurrency. One integration
test actually waits for the production 30-second deadline and verifies HTTP 504. Real
provider/quality/cost controls are T10. Existing task analysis-source UUIDs remain
without an FK until T11 integrates actual approval and reconciles test fixtures.

Run the stdio tool from a trusted terminal/host configuration:

```sh
docker compose exec -T api python -m app.mcp_server
```

This command waits for an MCP client on stdin/stdout; it is not an HTTP endpoint or
an interactive text prompt. Configure the host with executable `docker` and arguments
`["compose", "exec", "-T", "api", "python", "-m", "app.mcp_server"]`, running from this
repository. The official MCP Python SDK is hash-locked to 2.3.0. The only tool is
`get_request_summary` with arguments `{"params":{"request_id":"UUID"}}`.
It returns title <=200 characters, description excerpt <=600, ID, status and explicit
synthetic/untrusted metadata; it excludes creator/session/credential fields. Treat
returned text as data, never instructions.

The local launcher is the trust boundary: only trusted OS/container users with the
private DB configuration can launch it. No app session, ops credential, network
listener, arbitrary SQL/URL/file input or write tool is exposed. Every tool query runs
in a PostgreSQL READ ONLY transaction with a two-second statement timeout; malformed
UUIDs, extra nested input and unknown/write tool names are denied. Database connection
credentials remain inside the trusted process; no independent MCP login or production
read-only DB principal is claimed. A future remote transport would need separate auth.

The normal aggregate test command includes real stdio initialization/tools-list/read,
malformed input/nonexistent record/write-tool denial and a database write rejected
inside the read-only transaction. MCP verification is synthetic and requires no real
model. Source references: [official MCP SDK](https://github.com/modelcontextprotocol/python-sdk)
and [Python asyncio timeout](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.timeout).
Exact results/CI evidence are recorded in Issue #9; T17 still owns the remaining
Extension Pack demonstrations.

## Local Ollama analysis (T10)

The existing installed model is `llama3.2:3b`; startup never downloads it.
Default `MODEL_MODE=simulated` remains deterministic and is explicitly shown in the
request detail page. Click **Analyze request** for a pending suggestion set.
**Retry analysis** explicitly starts a new attempt after failure or rejection. Pending
suggestions remain inactive until the explicit human decision described below.

To opt into the existing local server, set these variables in ignored `.env`, then
run `docker compose up --build -d --wait`:

```dotenv
MODEL_MODE=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MAX_CALLS=20
```

The model name is fixed to the authorized installed model. The endpoint accepts only
local loopback names or `host.docker.internal`, HTTP port 11434, no credentials,
path, query, redirects or environment proxies. Do not expose Ollama publicly or
set a wildcard listener. On this Docker Desktop installation the existing private
listener was reachable without any binding/firewall change:

```powershell
docker compose exec -T api python -c "import urllib.request; print(urllib.request.urlopen('http://host.docker.internal:11434/api/version', timeout=5).read().decode())"
```

If it is unavailable on another machine, keep simulated mode and diagnose local
connectivity; a public listener is not a prerequisite. Host-run Python can use
`http://127.0.0.1:11434`. `GET /api/v1/requests/analysis/config` is authenticated and
returns the configured mode/model; persisted analyses also retain their own mode,
model and prompt version across later configuration changes.

All attempts retain the existing 30-second deadline, no automatic retry/fallback
and no task writes. Real calls reserve a persisted lifetime allowance before
dispatch and allow one nonexpired call across API processes. Exhausted allowance
or a busy local provider returns sanitized HTTP 429 before dispatch. Failed calls
consume allowance; replaying the same idempotency key is free. The allowance is a
total across persisted real attempt history, configurable 1-100, default 20;
an operator must explicitly raise that total to authorize more attempts. Returning
to `MODEL_MODE=simulated` and recreating the API disables further real calls.

Tests and browser helpers explicitly use simulated mode. For the separately
authorized real evaluation, first build the test image and create a dedicated test
database once (the example uses the default configured database user):

```powershell
docker compose --profile test build test
docker compose --profile test up -d --wait test-db
docker compose exec -T test-db createdb -U officeflow officeflow_ollama_test
docker compose --profile test run --rm -e POSTGRES_DB=officeflow_ollama_test -e APP_ORIGINS=http://testserver -e COOKIE_SECURE=false -v "${PWD}/artifacts:/evidence" test python -m app.evaluate_ollama --real --output /evidence/t10-real-evaluation.json
```

Do not rerun `createdb` if that database already exists. The CLI accepts only 1-5
repository-owned valid synthetic fixture IDs (`--cases simple ambiguous injection`
by default), refuses a non-`_test` database, creates a private random demo account,
uses authenticated production analysis routes and verifies persisted output and
zero task creation. Each call is real, locally bounded and consumes allowance. It
stops on the first failure, writes the explicit synthetic evaluation artifact and
returns nonzero; it never labels mocked output as real. Preserve failed evidence
under a distinct filename before an explicitly authorized rerun.

Current [T10 evidence](t10-verification.md): CPU-only execution (`num_gpu:0`) avoids
the observed Vulkan decoding failure. Three real proposals passed strict validation
and persisted pending within 30 seconds, with zero active tasks created. The initial
failed evaluation is retained as historical evidence. No model upgrade/download or provider
fallback was performed. API reference: [Ollama generate](https://docs.ollama.com/api/generate)
and [structured outputs](https://docs.ollama.com/capabilities/structured-outputs).

## Human approval and rejection (T11)

Request details show the complete saved proposal, mode and analysis ID. **Approve
suggestions** creates the complete task set; **Reject suggestions** requires a reason
of 1-1000 trimmed characters and creates no tasks. The UI shows the persisted
decision and reason as escaped text, removes decision controls after success and
refreshes PostgreSQL-backed request/dashboard state. Rejected requests can be
explicitly analyzed again. Old decisions remain in authenticated analysis history.

`POST /api/v1/requests/{request_id}/analyses/{analysis_id}/decision` requires a demo
session, exact allowed Origin and CSRF token. Body: `{"decision":"approve"}` or
`{"decision":"reject","reason":"Synthetic scope unclear"}`. Extra fields, replacement
tasks, forged identity, approval reasons and missing/blank/oversized rejection reasons
are rejected. Model and ops identities have no demo-session approval authority.

The transaction locks request then the specific analysis, validates the saved
proposal again for approval, creates tasks using its persisted title/priority/rationale,
records authenticated `decided_by`/`decided_at`/rejection reason and updates request
activity time. Status derives from the same committed task/analysis state. It returns
200 with analysis, source task rows and current request status. Repeating the same
decision returns the existing result with original decision metadata; changing the
choice or saved rejection reason returns 409. Wrong request/analysis pair returns
404; running/failed attempts cannot be decided (409). A database failure rolls back
all decision/task changes. No model call occurs in this operation.

Migration `0006_human_decisions` adds nullable decision metadata, an approver FK
and checks requiring a decision identity/time and bounded rejection reason in final
states. Existing unique `(analysis_id,suggestion_index)` task identity plus request/
analysis locks prevent duplicate concurrent approval. Historical direct synthetic
task fixtures retain their reserved source UUIDs; they are not human-approval evidence.
No task-analysis FK/backfill or history rewriting is introduced by this slice.

Verification: the existing aggregate backend command passed **131 tests**, including
real PostgreSQL concurrency and rollback checks. The isolated Edge helper passed
**15 browser tests**, including approve/reject/replay/retry and dashboard counts.
Frontend lint, TypeScript/Vite build and Ruff 0.14.0 passed. Exact PR CI/merge evidence
is recorded on [Issue #11](https://github.com/chakirou18/AI-OfficeFlow/issues/11).
