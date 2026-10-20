# T18 clean-source validation

**VERIFIED: clean tracked source with cached dependencies. NOT VERIFIED: cold
dependency installation or an unmodified cold Docker build.**
Tested commit: `1024ed57a80df8ba59a8acebb7a0af97379be813`, 2026-10-20.
[Evidence summary](evidence/t18-validation.md) / [exact command ledger](evidence/t18-validation.json).

The initial stopped-Docker observation is preserved below as historical evidence.
After explicit authorization, a new export of `1024ed5` ran successfully. The
following is the actual cached-dependency method, not a newly executed cold build.

## Verified preparation and prerequisites

Observed Windows environment: Docker Engine 29.9.1 Linux, Compose 5.6.0,
Python 3.12.10, Node 24.19.0/npm 11.17.0 and installed Edge. Images and frontend
packages already existed. No download/install, npm ci or image build ran.
Missing caches require separate approval; [development.md](development.md) describes
the general installation path, which is not claimed newly verified here.

From the repository, the exact export command (output path normalized relative
to the repository root) was:

```powershell
git archive --format=zip --output=artifacts/t18-local-1024ed5/source.zip 1024ed5
```

The temporary harness extracted with Python `zipfile.ZipFile.extractall` into a
new empty `artifacts/t18-local-1024ed5/source`. It copied existing
`frontend/node_modules` with `shutil.copytree`, without installation. In that source:

```powershell
python scripts/configure_local.py
python scripts/configure_observability.py
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend run build
```

All exited 0. Fresh private credentials were generated. The harness retained them
and set these non-secret values in the isolated `.env`:

```dotenv
POSTGRES_DB=officeflow_t18_test
FRONTEND_PORT=9082
API_PORT=9002
GRAFANA_PORT=3002
APP_ORIGINS=http://127.0.0.1:9082
MODEL_MODE=simulated
ENABLE_DEV_FAULTS=false
ENABLE_ONCALL_EXERCISE=false
```

Before repeating, choose an unused directory/project/ports and verify its named
volumes do not already exist. Never run fixture reset on retained or deployment data.
Existing secrets/images/volumes must not be overwritten.

## Exact final temporary override

Save the following as `compose.t18.json` in the isolated source root. This records
the final tested override; it is not a production/release configuration change.
The initial internal-only network started services but blocked host ports. The
edge network below corrected access while host bindings remained loopback-only.

```json
{
  "services": {
    "api": {
      "image": "officeflow-api:local",
      "pull_policy": "never",
      "volumes": [
        "./backend/app:/app/app:ro",
        "./backend/migrations:/app/migrations:ro",
        "./backend/alembic.ini:/app/alembic.ini:ro"
      ],
      "networks": [
        "default",
        "edge"
      ]
    },
    "migrate": {
      "image": "officeflow-api:local",
      "pull_policy": "never",
      "volumes": [
        "./backend/app:/app/app:ro",
        "./backend/migrations:/app/migrations:ro",
        "./backend/alembic.ini:/app/alembic.ini:ro"
      ]
    },
    "oncall-listener": {
      "image": "officeflow-api:local",
      "pull_policy": "never",
      "volumes": [
        "./backend/app:/app/app:ro",
        "./backend/migrations:/app/migrations:ro",
        "./backend/alembic.ini:/app/alembic.ini:ro"
      ]
    },
    "frontend": {
      "image": "officeflow-frontend:latest",
      "pull_policy": "never",
      "volumes": [
        "./frontend/dist:/usr/share/nginx/html:ro",
        "./frontend/nginx.conf:/etc/nginx/conf.d/default.conf:ro"
      ],
      "networks": [
        "default",
        "edge"
      ]
    },
    "test": {
      "image": "officeflow-test:latest",
      "pull_policy": "never",
      "volumes": [
        "./backend:/app:ro"
      ],
      "environment": {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTEST_ADDOPTS": "-o cache_dir=/tmp/t18-pytest-cache"
      }
    },
    "grafana": {
      "networks": [
        "default",
        "edge"
      ]
    }
  },
  "networks": {
    "default": {
      "internal": true
    },
    "edge": {}
  }
}
```

The cached image locks were SHA-256 compared with the exported
`backend/requirements.lock` and `backend/requirements-test.lock`; both matched.
Exact read-only hash commands and retained output hashes are in the evidence JSON.
Cached tags are observed local prerequisites, not portable registry attestations.
Source/migrations/frontend assets were mounted read-only; no application edits.

## Executed startup and test commands

From the isolated source root:

```powershell
docker compose -p officeflow-t18-1024ed5 -f compose.yaml -f compose.t18.json config --quiet
docker compose -p officeflow-t18-1024ed5 -f compose.yaml -f compose.t18.json up --no-build --pull never -d --wait --wait-timeout 180
docker compose -p officeflow-t18-1024ed5 -f compose.yaml -f compose.t18.json ps --all
docker compose -p officeflow-t18-1024ed5 -f compose.yaml -f compose.t18.json exec -T api alembic current
docker compose -p officeflow-t18-1024ed5 -f compose.yaml -f compose.t18.json exec -T api alembic check
docker compose -p officeflow-t18-1024ed5 -f compose.yaml -f compose.t18.json --profile test run --pull never --rm test
```

The first backend invocation used `run --no-build` and exited 1 before tests:
that option is not supported by `run`. The corrected command above used an existing
explicit image, no `--build`, and `--pull never`. It passed 190 tests (105 unit /
85 integration), exit 0, using the project's separate tmpfs `officeflow_test`.
Pytest cache was redirected to `/tmp`; test source and assertions were unchanged.

The existing fixture entry point ran on the fresh `officeflow_t18_test` only:

```powershell
docker compose -p officeflow-t18-1024ed5 -f compose.yaml -f compose.t18.json exec -T -e BROWSER_FIXTURES=enabled api python -m app.browser_fixture
```

The harness supplied a randomly generated password as JSON on stdin, then passed
the same value privately in `DEMO_PASSWORD`, with `DEMO_HANDLE=t08_browser_fixture`.
Do not print credentials or commit configuration. With those private variables:

```powershell
$env:BROWSER_CHANNEL = 'msedge'
$env:FRONTEND_URL = 'http://127.0.0.1:9082'
$env:API_URL = 'http://127.0.0.1:9002'
$env:PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = '1'
npm.cmd --prefix frontend run test:e2e
```

All 15 tests passed, including simulated pending analysis, explicit authenticated
approval/rejection, saved tasks and dashboard counts. Initial test-only fixture
tasks are not human-approval evidence; separate approval tests cover that workflow.

For persistence the harness asserted DB name `officeflow_t18_test`, read all columns
of requests/analyses/tasks ordered by ID, hashed sorted-key JSON, restarted only
this project's db/api and compared the same complete rows after HTTP readiness.
The exact read-only Python command and hashes are in the evidence JSON.

```powershell
docker compose -p officeflow-t18-1024ed5 -f compose.yaml -f compose.t18.json restart db api
```

All 17 requests / 5 analyses / 5 tasks were identical after restart. No production
DB was read. The browser suite was not rerun after this persistence check.

## Measured results and cleanup

| Operation | Observation |
| --- | --- |
| Initial full stack | 29.187 s; services started, initial host network failed |
| Corrected edge startup | 15.875 s; not another cold startup |
| HTTP readiness | 0.031 s, HTTP 200 |
| Backend | 83.95 s pytest / 91.906 s command, 190 passed |
| Frontend lint / build | 2.547 s / 2.172 s, exit 0 |
| Browser | 14.5 s Playwright / 15.516 s command, 15 passed |
| Restart persistence | 4.312 s; complete-row hashes identical |
| Migration | `0006_human_decisions`; no drift |
| Integrity | 172 exported files byte-identical |

The temporary harness's Windows console failed to print a Vite checkmark after
the successful build. Its saved exit code/log remained valid; only the display
encoding was fixed. Successful suites were recovered, not rerun.

After recovery, only this project's containers were stopped:

```powershell
docker compose -p officeflow-t18-1024ed5 -f compose.yaml -f compose.t18.json --profile test stop
```

Named volumes and containers were retained. Baseline volume names, image tag/ID
pairs and container IDs remained present. This is resource-inventory preservation,
not a content audit of production databases. Existing release stacks stayed stopped.

Linux uses `npm` instead of `npm.cmd` and may extract with `tar`; Edge availability
is workstation-specific. Timings are local observations, not an SLA.
Cold installation remains unverified; three course-review confirmations are missing.

## Historical initial audit and unexecuted plan

The following pre-authorization record is preserved verbatim. Its blocked/current
statements and proposed `up --build` commands describe that earlier point, not
the later cached-dependency execution above.

## T18 clean-source validation

Status: **PARTIAL**; configuration verified, current runtime **BLOCKED**.
Source: `6a6098f6baa36e3b49b2dfdaacc721981237f102`. Date: 2026-10-20.
The existing [T04 clean-source execution](t04-verification.md) remains historical
foundation evidence and does not establish clean startup of the final full stack.

### Actually executed

From the working repository in PowerShell:

```powershell
git archive --format=zip --output=artifacts/t18-clean-6a6098f.zip 6a6098f
Expand-Archive -LiteralPath artifacts/t18-clean-6a6098f.zip -DestinationPath artifacts/t18-clean-6a6098f
```

From that isolated source directory:

```powershell
python scripts/configure_local.py
python scripts/configure_observability.py
docker compose -p officeflow-t18-clean config --quiet
```

All three commands returned 0. Fresh private configuration and monitoring/ops
credentials were generated without printing their values. The archive contains
tracked source only: no original `.env`, node_modules, deployment state or DB data.
This is a clean tracked-source export, not a network clone or a clean dependency
installation. It does not share the working repository's private configuration.

`docker version` outside the sandbox could not connect to
`//./pipe/dockerDesktopLinuxEngine`: the engine was absent. Client 29.9.1 and
Compose 5.6.0 were observed, but no server version or cached images could be
inspected. No build/start/test was represented as passing. Startup and HTTP/browser
smoke durations are **not measured**, not zero. Docker startup approval was requested.

### Remaining safe reproduction procedure

Prerequisites: Docker Desktop Linux engine on Windows, or Docker Engine/Compose
on Linux; Python 3.12 for helpers; approved cached images/build dependencies or
explicit download approval. Node 24/npm and a Playwright-compatible browser are
only needed for host frontend/browser checks. Do not install a model for default
simulation. Check `docker version` for a server before proceeding.

In the isolated copy's generated `.env`, set distinct values:

```dotenv
POSTGRES_DB=officeflow_t18_test
FRONTEND_PORT=9082
API_PORT=9002
GRAFANA_PORT=3002
APP_ORIGINS=http://127.0.0.1:9082
MODEL_MODE=simulated
ENABLE_DEV_FAULTS=false
ENABLE_ONCALL_EXERCISE=false
```

Retain the generated password and ops settings. Check these ports are unused.
Use project `officeflow-t18-clean` for **every** Compose command. Its newly named
volumes are distinct from existing development/production/telemetry volumes.
An isolated override should also give API/migrate/listener a distinct local image
tag before building, so the shared `officeflow-api:local` tag is not overwritten.

After image/cache inspection and any necessary explicit download approval:

```powershell
docker compose -p officeflow-t18-clean up --build -d --wait --wait-timeout 180
docker compose -p officeflow-t18-clean ps --all
docker compose -p officeflow-t18-clean exec -T api alembic current
docker compose -p officeflow-t18-clean exec -T api alembic check
docker compose -p officeflow-t18-clean exec api python -m app.manage_users create demo_user
docker compose -p officeflow-t18-clean --profile test run --build --rm test
```

These are pending commands, not executed T18 results. Measure wall time with
`[Diagnostics.Stopwatch]::StartNew()` on PowerShell or `time` on Linux. Check
frontend `/`, proxied readiness, authenticated create/analyze/approve/reject and
reloaded database-backed tasks. Report individual startup and smoke durations.
Never print login/configuration secrets. Stop only this project's containers with
`docker compose -p officeflow-t18-clean down`; do not add volume removal.

Linux can export source with
`git archive 6a6098f | tar -x -C <new-empty-directory>` and uses `npm` instead of
`npm.cmd`. Browser channel `msedge` is workstation-specific; absent browsers or
dependencies require explicit installation approval in this session. Existing
`scripts/test_browser.py` uses its own fixed `officeflow-browser` project, ports
8081/8001 and synthetic test database; do not run copies concurrently or mistake
it for the full clean-source stack.

No existing database, telemetry volume, backup or GHCR package was removed.
