# T13 local observability

The application sends real OTel metrics, traces and structured events to a private
Collector. Prometheus stores metrics/exemplars, Loki stores events and Tempo stores
traces. Grafana provisions all three data sources and dashboard `officeflow`.
This is local synthetic-data observability. T14 adds private Alertmanager routing
and a receipt-only listener; see the [analysis failure runbook](runbooks/analysis-http-failures.md).
No production SLA or autonomous remediation is provided.

## Start and access

```powershell
python scripts/configure_local.py
python scripts/configure_observability.py
docker compose up --build -d --wait
```

The second helper preserves existing credentials, creates a separate random Grafana
password in ignored `artifacts/grafana-admin-password`, and configures a random
read-only `OPS_TOKEN` in ignored `.env` if absent/empty. It never prints values.
Existing PostgreSQL credentials/data and Ollama configuration are preserved.

Open [Grafana](http://127.0.0.1:3000) as `monitor`, using that private password file.
Dashboard: [Application signals](http://127.0.0.1:3000/d/officeflow).
Only Grafana's local dashboard port is published. Collector, Prometheus, Loki and
Tempo have no published host ports. Optional `GRAFANA_PORT` changes the loopback port.
All monitoring stores use separate named volumes; never add volume deletion to stop
commands. Grafana anonymous access/signup and background plugin installation are
disabled. Backend telemetry defaults off outside Compose; Compose API enables it.
Tests/browser helpers explicitly disable exporters and do not require these services.

| Component | Pinned image |
| --- | --- |
| Collector | `otel/opentelemetry-collector-contrib:0.123.0` |
| Prometheus | `prom/prometheus:v3.2.1` |
| Loki | `grafana/loki:3.4.2` |
| Tempo | `grafana/tempo:2.7.2` |
| Grafana | `grafana/grafana:11.6.0` |

The Python SDK/HTTP exporters are hash-locked at 1.45.0. Configurations are under
`infra/observability/`. Storage retention is seven days. This small single-host
filesystem setup does not claim production availability or access isolation beyond
the private Compose network and authenticated loopback Grafana.

## Signals and navigation

HTTP server spans cover login, request creation, analysis, decisions and public/private
health routes. `model.analyze` and `human.decision` are child spans. The browser sends
W3C traceparent and continues the returned server context; login starts a new trace.
The adapter forwards traceparent on real Ollama calls but does not assume Ollama
exports server spans. Simulated analysis remains explicitly labeled simulated.

Metrics: `officeflow_http_requests_total`, `officeflow_http_errors_total`,
`officeflow_http_duration_seconds_bucket`, `officeflow_analysis_outcomes_total`,
`officeflow_analysis_duration_seconds_bucket`, `officeflow_decision_outcomes_total`.
HTTP labels are bounded method, matched route template and status; outcomes use
bounded state/error/provider-mode enums. IDs never become metric labels. Analysis
outcomes count newly executed attempts (pending means a validated proposal), not
idempotent replays. Decision outcomes count endpoint results, including replays.
The HTTP error metric includes 4xx and 5xx. Histograms include sampled exemplars.

Dashboard panels show request rate, HTTP p95 latency/error rate, actual analysis
outcomes, analysis p95 duration, decision outcomes and stored structured events.
An absent failed-analysis series means no failure was observed, not a fabricated
successful provider-failure demonstration. Latency exemplars open Tempo; expanded
log TraceID fields open traces. Tempo's **Logs for this span** opens correlated Loki
events; its metric links use the same service label. Exemplars are enabled only on
latency panels so absolute counter exemplar values cannot distort ratio/rate axes.

No request/response body, raw URL/query, credentials, cookie, CSRF value, user/request
UUID, rejection reason, prompt, model output, SQL or exception text is captured.
Only traceparent is extracted: baggage and tracestate are discarded. Resource
attributes are explicit rather than environment-detected. SDK automatic exception
recording and raw proxy/API access logs are disabled. Events have timestamp,
severity, event name, trace_id, span_id and allowlisted metadata. Logs/traces are
exported by bounded background SDK processors; no collector network I/O runs in an
application transaction. Telemetry outages do not authorize task activation/repair.

## Actual verification, 2026-10-19

```powershell
python scripts/verify_observability.py
```

This explicit helper creates a synthetic demo account privately, uses real login,
request/analysis/approve/reject APIs in simulated mode, exercises ops 200/403 and
HTTP 403/404 failures, and restarts only `api`. It refuses automatic real model
calls. It compares complete saved request/task/decision records after restart and
queries stores through authenticated Grafana proxies. Two traffic samples span
export/scrape intervals so rate/latency graphs have actual data.

Observed trace `666d3e9f412b4ca9a85ff4bc9f16a95a`: **11 HTTP metric series**,
**18 correlated log events**, **21 stored spans** rendered in Grafana, and a stored
latency exemplar pointing to the same trace. Queryable analysis p95 was **0.00975 s**
for simulated traffic (not a real Ollama performance claim). Redaction checks passed
for generated credentials/cookies/CSRF/ops token, private request/rejection sentinel
and model summary/rationale. Metric series contained no ID labels. API restart
preserved the complete saved records. All three data sources and four navigation
configurations were inspected; the real dashboard and trace were visually verified.

Private evidence: `artifacts/t13-verification.json`, `t13-grafana-ui.json`,
`t13-grafana.png`, `t13-trace.png`, and command/test logs. These contain no actual
credentials or request descriptions and are not published automatically.

Focused context/exemplar/redaction tests: **4 passed** (1.38 s). Final aggregate:
**149 passed** (67.37 s), isolated real PostgreSQL, once after code corrections.
Browser smoke: **15 passed** (14.6 s). Ruff, frontend lint, TypeScript/Vite passed.
The first focused run caught lazy route matching (fixed); an initial live verification
correctly found ops blocked by the frontend (verifier now uses the private API port).
Grafana trace query type and counter-exemplar display were corrected during UI QA.
No full suite was repeatedly run. Exact PR/CI/merge evidence belongs to
[Issue #13](https://github.com/chakirou18/AI-OfficeFlow/issues/13).

References: [OTel Python](https://opentelemetry.io/docs/languages/python/instrumentation/),
[Loki native OTLP](https://grafana.com/docs/loki/latest/send-data/otel/),
[Grafana Tempo configuration](https://grafana.com/docs/grafana/latest/datasources/tempo/configure-tempo-data-source/).
