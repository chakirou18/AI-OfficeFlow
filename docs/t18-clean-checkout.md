# T18 clean-source validation

Status: **PARTIAL**; configuration verified, current runtime **BLOCKED**.
Source: `6a6098f6baa36e3b49b2dfdaacc721981237f102`. Date: 2026-10-20.
The existing [T04 clean-source execution](t04-verification.md) remains historical
foundation evidence and does not establish clean startup of the final full stack.

## Actually executed

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

## Remaining safe reproduction procedure

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
