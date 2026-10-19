"""Explicit local synthetic traffic and real Grafana-proxied storage verification."""
import base64
from http.cookiejar import CookieJar
import json
import math
from pathlib import Path
import secrets
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def main():
    config = dict(line.split("=", 1) for line in (ROOT / ".env").read_text().splitlines()
                  if "=" in line and not line.startswith("#"))
    app = "http://127.0.0.1:" + config.get("FRONTEND_PORT", "8080")
    api = "http://127.0.0.1:" + config.get("API_PORT", "8000")
    grafana = "http://127.0.0.1:" + config.get("GRAFANA_PORT", "3000")
    grafana_password = (ROOT / "artifacts/grafana-admin-password").read_text().strip()
    grafana_auth = "Basic " + base64.b64encode(("monitor:" + grafana_password).encode()).decode()
    password, marker, handle = secrets.token_urlsafe(32), "redact_" + secrets.token_hex(16), "otel_" + secrets.token_hex(6)
    trace_id = uuid4().hex
    parent = f"00-{trace_id}-{secrets.token_hex(8)}-01"
    jar = CookieJar()
    browser = build_opener(HTTPCookieProcessor(jar))
    csrf = ""
    private = [password, marker, handle, grafana_password, config["OPS_TOKEN"]]

    def call(url, body=None, *, headers=None, method=None, expected=200):
        nonlocal parent
        is_app = url.startswith((app, api))
        metadata = ({"Origin": app, "traceparent": parent, "X-CSRF-Token": csrf,
                     "baggage": marker, "tracestate": "private=" + marker} if is_app else {"Authorization": grafana_auth})
        metadata.update(headers or {})
        metadata["Accept"] = "application/json"
        data = json.dumps(body).encode() if body is not None else None
        if data is not None:
            metadata["Content-Type"] = "application/json"
        request = Request(url, data=data, headers=metadata, method=method)
        try:
            response = browser.open(request, timeout=10)
        except HTTPError as error:
            response = error
        assert response.status == expected, f"Unexpected HTTP {response.status}; response body intentionally omitted"
        if is_app and response.headers.get("traceparent"):
            parent = response.headers["traceparent"]
            assert parent.split("-")[1] == trace_id
        raw = response.read()
        return json.loads(raw) if raw else None

    # Trusted local account provisioning, exactly as a maintainer CLI (no signup API).
    provision = """import json,sys
from app.auth import hash_password
from app.database import build_engine
from app.models import DemoUser
from sqlalchemy.orm import Session
p=json.load(sys.stdin)
with Session(build_engine()) as db:
    db.add(DemoUser(handle=p['handle'],password_hash=hash_password(p['password'])))
    db.commit()
"""
    subprocess.run(["docker", "compose", "exec", "-T", "api", "python", "-c", provision], cwd=ROOT,
                   input=json.dumps({"handle": handle, "password": password}), text=True, check=True, capture_output=True)
    identity = call(app + "/api/v1/auth/login", {"handle": handle, "password": password})
    csrf = identity["csrf_token"]
    private.extend([csrf, *[cookie.value for cookie in jar]])
    assert call(app + "/api/v1/requests/analysis/config")["provider_mode"] == "simulated", "Verification refuses automatic real model calls"
    saved = []
    for decision in ("approve", "reject"):
        record = call(app + "/api/v1/requests", {"title": "Synthetic monitoring check", "description": marker}, expected=201)
        run = call(app + f"/api/v1/requests/{record['id']}/analyses", method="POST",
                   headers={"Idempotency-Key": str(uuid4())}, expected=201)
        private.extend([run["proposal"]["summary"], *[task["rationale"] for task in run["proposal"]["tasks"]]])
        chosen = call(app + f"/api/v1/requests/{record['id']}/analyses/{run['id']}/decision",
                      {"decision": decision} | ({"reason": marker} if decision == "reject" else {}))
        assert len(chosen["tasks"]) == (len(run["proposal"]["tasks"]) if decision == "approve" else 0)
        saved.append(call(app + f"/api/v1/requests/{record['id']}"))
        if decision == "approve":
            time.sleep(12)  # Two genuine traffic samples across metric export/scrape intervals.
    call(api + "/api/v1/ops/health", headers={"Authorization": "Bearer " + config["OPS_TOKEN"]})
    call(api + "/api/v1/ops/health", expected=403)
    call(app + "/api/v1/requests", {"title": marker, "description": marker}, headers={"X-CSRF-Token": "invalid"}, expected=403)
    call(app + "/api/v1/" + marker + "?password=" + marker, expected=404)
    subprocess.run(["docker", "compose", "restart", "api"], cwd=ROOT, check=True, capture_output=True)
    deadline = time.monotonic() + 45
    while True:
        try:
            call(app + "/api/v1/health/ready")
            break
        except (URLError, AssertionError):
            if time.monotonic() > deadline:
                raise RuntimeError("API restart readiness failed") from None
            time.sleep(2)
    for record in saved:
        assert call(app + f"/api/v1/requests/{record['id']}") == record, "Application persistence changed after API restart"

    def query(uid, path, params=None):
        return call(grafana + f"/api/datasources/proxy/uid/{uid}" + path + ("?" + urlencode(params) if params else ""))

    deadline = time.monotonic() + 60
    while True:
        try:
            metrics = query("prometheus", "/api/v1/query", {"query": 'officeflow_http_requests_total'})
            trace = query("tempo", "/api/traces/" + trace_id)
            logs = query("loki", "/loki/api/v1/query_range", {"query": '{service_name="officeflow-api"} |= "' + trace_id + '"', "limit": 500})
            exemplars = query("prometheus", "/api/v1/query_exemplars", {"query": "officeflow_http_duration_seconds_bucket",
                "start": str(time.time() - 600), "end": str(time.time())})
            assert metrics["data"]["result"] and logs["data"]["result"]
            assert trace_id in json.dumps(exemplars)
            latency = query("prometheus", "/api/v1/query", {"query": 'histogram_quantile(0.95, sum by (le) (rate(officeflow_analysis_duration_seconds_bucket[5m])))'})
            assert latency["data"]["result"] and math.isfinite(float(latency["data"]["result"][0]["value"][1]))
            break
        except (HTTPError, URLError, AssertionError):
            if time.monotonic() > deadline:
                raise RuntimeError("Stored signal/exemplar verification failed") from None
            time.sleep(2)
    # All current service logs + series, not only matching trace, are checked.
    all_logs = query("loki", "/loki/api/v1/query_range", {"query": '{service_name="officeflow-api"}', "limit": 1000})
    series = query("prometheus", "/api/v1/series", {"match[]": '{__name__=~"officeflow_.*"}'})
    serialized = json.dumps([trace, all_logs, series, metrics])
    assert all(value not in serialized for value in private), "Telemetry redaction failed; values intentionally omitted"
    entries = [json.loads(value[1]) for stream in logs["data"]["result"] for value in stream["values"]]
    assert all({"trace_id", "span_id", "severity", "timestamp", "event"} <= entry.keys() for entry in entries)
    trace_text = json.dumps(trace)
    assert "model.analyze" in trace_text and "human.decision" in trace_text and "/api/v1/ops/health" in trace_text
    for item in series["data"]:
        assert not ({"request_id", "user_id", "trace_id", "span_id"} & item.keys())
    dashboard = call(grafana + "/api/dashboards/uid/officeflow")
    assert {1, 2, 3, 4, 5, 6, 7} <= {panel["id"] for panel in dashboard["dashboard"]["panels"]}
    sources = call(grafana + "/api/datasources")
    assert {"prometheus", "loki", "tempo"} <= {item["uid"] for item in sources}
    report = {"trace_id": trace_id, "metrics_series": len(metrics["data"]["result"]),
              "correlated_log_events": len(entries), "tempo_trace_stored": True,
              "metric_exemplar_trace_link": True, "redaction_passed": True,
              "api_restart_persistence": True, "grafana_dashboard_uid": "officeflow",
              "analysis_p95_seconds": float(latency["data"]["result"][0]["value"][1]),
              "grafana_url": grafana, "model_mode": "simulated"}
    (ROOT / "artifacts/t13-verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
