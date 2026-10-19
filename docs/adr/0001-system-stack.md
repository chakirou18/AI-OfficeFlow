# ADR 0001 — Modular full-stack prototype

> SUPERSEDED by [ADR 0010](0010-minimal-zoomcamp-scope.md). Historical design only: company references and prior requirements/statuses below are not current scope. Retained for rationale and Git/issue evidence; use the current specification and ADR 0010 for implementation.

Status: **Accepted for prototype design**. Owner: T03; implementation: T04–T08. Context: a small team needs a connected full-stack app with one-command local startup and clear future extraction boundaries.

## Decision

Use React + TypeScript + Vite for the browser UI, Python + FastAPI/Pydantic for a versioned `/api/v1` JSON API, and PostgreSQL for durable state. Maintain a modular backend with domain services separate from HTTP routes, database repositories, jobs, graph nodes and MCP adapters. Use SQLAlchemy and Alembic for persistence/migrations. Lock dependency versions when scaffolding, not by inventing an untested lockfile now.

The UI communicates only with the API through the same public origin. A reverse proxy serves the built frontend and forwards `/api` to FastAPI; Vite is a local development server only. Generate or validate the TypeScript client against the OpenAPI contract. Use polling for run status; WebSocket/streaming delivery is deferred.

Compose services: proxy/frontend, API, worker, PostgreSQL, MCP and one-shot migration job. An `observability` profile adds collector, Prometheus, Loki, Tempo, Grafana and Alertmanager. A `test` profile has an isolated test database and aggregate test runner. Core startup is planned as `docker compose up --build`; include health/readiness and migration completion dependencies so database startup is not mistaken for schema readiness. This follows the distinction in [Docker's startup-order documentation](https://docs.docker.com/compose/how-tos/startup-order/).

Proposed package locations remain `frontend/`, `backend/`, `agents/`, `tools/`, `tests/`, `infra/`. They are boundaries, not existing directories. Share typed schemas through explicit interfaces; avoid a distributed microservice per business agent.

## Alternatives and trade-offs

| Alternative | Advantage | Reason not selected / cost |
| --- | --- | --- |
| Django full stack | Built-in administrative capabilities and authentication | Good alternative, but changes the requested React/FastAPI baseline and couples UI choices differently |
| Next.js with server backend | Integrated web delivery | Adds another backend runtime without removing the Python orchestration requirement |
| Microservices/Kubernetes | Independent scaling and releases | Excessive network, operations and deployment cost for two agents and one pilot deployment |
| Serverless functions | Low idle resource use | Durable jobs and a full local stack need additional infrastructure and lifecycle design |

Benefits: one repository, deployable components with testable internal modules, reusable business profiles. Trade-off: API, jobs and database must still be separated operationally; a single host is not high availability.

## Costs, security and verification

No paid service is selected. Local CPU, memory, disk and maintenance remain real costs. Do not promise free hosting or quote unverified prices. Only proxy ports are externally exposed; database, MCP and telemetry ingest stay private. No provider key enters the frontend. Default configuration rejects real integrations/data.

T04 verifies clean-checkout startup, migrations, health checks and persistent writes. T05/T08 verify contract compatibility and browser-to-database behavior. None has run. Reconsider service extraction only with measured scaling or team-ownership needs.
