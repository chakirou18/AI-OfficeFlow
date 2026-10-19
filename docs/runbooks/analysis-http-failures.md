# Analysis HTTP failures

`AnalysisHttpFailureRatio` means users are receiving analysis HTTP 5xx responses.
The 2-minute sum of counter increases must contain at least five analysis POST
attempts, with **strictly more than 50%** returning 5xx, continuously for **1 minute**.
Prometheus evaluates every 15 seconds; scrape/export delay adds latency. Counter
`increase` extrapolates across scrape boundaries, so window counts are estimates.
Authentication/CSRF/conflict 4xx responses count as attempts, never as failures.
Health endpoints and other routes are excluded. Labels are environment/severity,
never user/request identifiers. No traffic is not an incident and does not prove recovery.

Prometheus → private Alertmanager → `oncall` receiver → private
`http://oncall-listener:8010/webhook`. Group wait is 5 seconds; group changes are
sent after 10 seconds; unchanged alerts repeat after 4 hours. Resolved messages
are enabled. A separate generated Docker secret authenticates delivery; the
listener has no published port, proxy route, application DB credential or tools.
It validates a <=64 KiB body with <=10 alerts and stores only fingerprint,
timestamps, status and delivery count in its dedicated SQLite volume. Duplicate
status deliveries do not create another event; late firing cannot undo resolution.
Retention is 7 days/500 events, pruned transactionally on writes and reads.
Restart preserves receipts. Nothing launches diagnosis, commands, models or repairs.

1. Inspect Grafana at http://127.0.0.1:3000, dashboard `officeflow`: analysis
   attempts, failure ratio and alert state. Confirm actual 5xx impacts, traffic
   volume and the pending/firing interval before treating it as a provider incident.
2. Use correlated metadata logs/traces to distinguish provider errors, timeouts,
   database availability and interrupted runs. Never copy request/model content,
   credentials or cookies into incident records. Keep any further diagnosis read-only.
3. A maintainer chooses and performs any repair separately. T14 does not authorize
   an autonomous repair agent or T15 exercise. Never delete database volumes.
4. Confirm successful authenticated analysis, persisted pending suggestions and
   zero automatic tasks. Observe ratio/traffic and the alert becoming inactive,
   then a resolved receipt. Silence alone or missing telemetry is not recovery.

If delivery is absent, inspect Prometheus rule evaluation and Alertmanager's
private API/logs, then routing labels, Docker DNS, listener health, secret mounts
and 403/422/413 responses. Do not print secrets or payloads. Collector/scrape
failure needs separate monitoring; this rule only measures observed application
HTTP results. The listener records receipts, not a durable work queue or diagnosis.

Opt-in verification: `python scripts/verify_alerting.py` uses only a newly created
synthetic demo identity and one UUID-scoped request. It temporarily recreates the
local API with explicit development opt-in, a 240-second expiry and 40-failure
budget, preserving sessions, PostgreSQL and telemetry. Auth/Origin/CSRF still apply.
Its `finally` removes the override and recreates the API, then verifies a genuine
successful pending proposal and subsequent resolved notification. Do not use this
local-only mechanism in deployment. No fault-control HTTP endpoint exists.

Setup: `python scripts/configure_observability.py`, then
`docker compose up -d --build --wait`. Rule tests:
`docker compose run --rm --no-deps --entrypoint promtool prometheus test rules /etc/prometheus/analysis-alerts.test.yaml`
(the test fixture is also mounted read-only). Backend aggregate:
`docker compose --profile test run --build --rm test`.
