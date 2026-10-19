"""LIVE opt-in T15 exercise. Run only after explicit approval of docs/oncall-agent.md."""
import argparse
import base64
from datetime import datetime, timedelta, timezone
from http.cookiejar import CookieJar
import json
import os
import secrets
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener
from uuid import uuid4

from verify_alerting import ROOT, docker, internal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval-reference", required=True, help="Reference to explicit human approval of this exact local exercise")
    args = parser.parse_args()
    if not args.approval_reference.strip() or len(args.approval_reference) > 200:
        raise SystemExit("An explicit bounded approval reference is required")
    config = dict(line.split("=", 1) for line in (ROOT / ".env").read_text().splitlines()
                  if "=" in line and not line.startswith("#"))
    assert not config.get("DEV_ANALYSIS_FAILURE_REQUEST_ID") and not os.getenv("DEV_ANALYSIS_FAILURE_REQUEST_ID")
    app = "http://127.0.0.1:" + config.get("FRONTEND_PORT", "8080")
    api = "http://127.0.0.1:" + config.get("API_PORT", "8000")
    grafana = "http://127.0.0.1:" + config.get("GRAFANA_PORT", "3000")
    admin_secret = (ROOT / "artifacts/exercise-admin-token").read_text().strip()
    monitor_secret = (ROOT / "artifacts/grafana-admin-password").read_text().strip()
    monitor_auth = "Basic " + base64.b64encode(("monitor:" + monitor_secret).encode()).decode()
    handle, password, marker = "alert_verify_" + secrets.token_hex(6), secrets.token_urlsafe(32), "private_" + secrets.token_hex(12)
    trace_id, csrf = uuid4().hex, ""
    browser = build_opener(HTTPCookieProcessor(CookieJar()))

    def call(url, body=None, *, method=None, headers=None, expected=(200,)):
        metadata = ({"Origin": app, "X-CSRF-Token": csrf, "traceparent": f"00-{trace_id}-{secrets.token_hex(8)}-01"}
                    if url.startswith((app, api)) else {"Authorization": monitor_auth})
        metadata.update(headers or {})
        data = json.dumps(body).encode() if body is not None else None
        if data is not None:
            metadata["Content-Type"] = "application/json"
        try:
            response = browser.open(Request(url, data=data, method=method, headers=metadata), timeout=10)
        except HTTPError as error:
            response = error
        assert response.status in expected, f"Unexpected HTTP {response.status}; body withheld"
        return response.status, json.load(response)

    def query(expression):
        return call(grafana + "/api/datasources/proxy/uid/prometheus/api/v1/query?" + urlencode({"query": expression}))[1]["data"]["result"]

    # Start only the existing app/listener with the gate enabled; no fault yet.
    clean = dict(os.environ, ENABLE_ONCALL_EXERCISE="false", ENABLE_DEV_FAULTS="false", DEV_ANALYSIS_FAILURE_REQUEST_ID="", MODEL_MODE="simulated")
    enabled = dict(clean, ENABLE_ONCALL_EXERCISE="true")
    events, samples, run = [], [], None
    def event(name):
        events.append({"event": name, "at": datetime.now(timezone.utc).isoformat()})
    try:
        docker("up", "-d", "--build", "--wait", "api", "oncall-listener", env=enabled)
        assert not query('ALERTS{alertname="AnalysisHttpFailureRatio"}'), "An existing incident is active; no fault activated"
        provision = """import json,sys
from app.auth import hash_password
from app.database import build_engine
from app.models import DemoUser
from sqlalchemy.orm import Session
p=json.load(sys.stdin)
with Session(build_engine()) as db:
 u=DemoUser(handle=p['handle'],password_hash=hash_password(p['password']))
 db.add(u); db.commit(); print(u.id)
"""
        user_id = docker("exec", "-T", "api", "python", "-c", provision,
                         data=json.dumps({"handle": handle, "password": password})).strip()
        csrf = call(app + "/api/v1/auth/login", {"handle": handle, "password": password})[1]["csrf_token"]
        assert call(app + "/api/v1/requests/analysis/config")[1]["provider_mode"] == "simulated"
        records = [call(app + "/api/v1/requests", {"title": "Synthetic on-call exercise", "description": marker}, expected=(201,))[1] for _ in range(2)]
        saved = [call(app + f"/api/v1/requests/{r['id']}")[1] for r in records]
        tasks_before = call(app + "/api/v1/dashboard")[1]["total_tasks"]
        scope = {"exercise_id": str(uuid4()), "environment": "development", "flag": "analysis_disabled",
                 "request_id": records[0]["id"], "verification_request_id": records[1]["id"], "user_id": user_id,
                 "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=240)).isoformat(), "max_failures": 40}
        call(api + "/api/v1/ops/exercise/authorize", scope, headers={"Authorization": "Bearer " + admin_secret})
        event("human_authorized_fault_activated")
        failures, deadline = 0, time.monotonic() + 190
        while time.monotonic() < deadline:
            status, output = call(app + f"/api/v1/requests/{records[0]['id']}/analyses", method="POST",
                                  headers={"Idempotency-Key": str(uuid4())}, expected=(201, 503))
            if status == 201:
                assert output["state"] == "pending" and 1 <= len(output["proposal"]["tasks"]) <= 5
                event("user_analysis_recovered")
                break
            failures += 1
            if failures == 1:
                event("first_user_visible_503")
            assert call(app + f"/api/v1/requests/{records[0]['id']}")[0] == 200
            samples.append({"at": datetime.now(timezone.utc).isoformat(), "alerts": query('ALERTS{alertname="AnalysisHttpFailureRatio"}')})
            runs = internal("/agent-runs")["body"]["runs"]
            current = next((r for r in runs if r.get("events") and r["events"][0]["at"] >= events[0]["at"]), None)
            assert not current or current["state"] != "stopped", "Agent stopped safely; exercise did not recover"
            assert failures < 39, "Bounded failure budget reached"
            time.sleep(5)
        else:
            raise RuntimeError("No automatic repair within the bounded observation window")
        verify_deadline = time.monotonic() + 40
        while time.monotonic() < verify_deadline:
            run = next((r for r in internal("/agent-runs")["body"]["runs"] if r.get("events") and r["events"][0]["at"] >= events[0]["at"]), None)
            if run and run["state"] != "running":
                break
            time.sleep(1)
        assert run and run["state"] == "recovered", "No verified agent recovery"
        assert [e["event"] for e in run["events"]].count("cleared_analysis_disabled") == 1
        actual = next(a for a in internal("/api/v2/alerts", authenticated=False)["body"] if a["fingerprint"] == run["fingerprint"])
        alert = {k: actual[k] for k in ("labels", "annotations", "startsAt", "endsAt", "generatorURL", "fingerprint")}
        alert["status"] = "firing"
        notification = {"version": "4", "groupKey": "authorized-duplicate-check", "truncatedAlerts": 0,
                        "status": "firing", "receiver": "oncall", "groupLabels": {}, "commonLabels": actual["labels"],
                        "commonAnnotations": actual["annotations"], "externalURL": "http://alertmanager:9093", "alerts": [alert]}
        duplicate = internal("/webhook", notification)
        assert duplicate["body"] == {"accepted": 0, "duplicates": 1}
        time.sleep(2)
        assert next(r for r in internal("/agent-runs")["body"]["runs"] if r["fingerprint"] == run["fingerprint"] and r["starts_at"] == run["starts_at"]) == run
        assert call(app + "/api/v1/dashboard")[1]["total_tasks"] == tasks_before
        for record in records:
            detail = call(app + f"/api/v1/requests/{record['id']}")[1]
            assert detail["tasks"] == [] and detail["description"] == marker
        print(json.dumps({"automatic_agent": run, "failures": failures, "duplicate_suppressed": True}), flush=True)
    finally:
        # Cleanup is not evidence of an agent repair. Always disable the entire gate.
        try:
            call(api + "/api/v1/ops/exercise", method="DELETE", headers={"Authorization": "Bearer " + admin_secret})
        finally:
            docker("up", "-d", "--no-deps", "--wait", "api", env=clean)
    # Saved synthetic request text and PostgreSQL task count survive API recreation.
    for record in saved:
        detail = call(app + f"/api/v1/requests/{record['id']}")[1]
        assert all(detail[key] == record[key] for key in ("id", "title", "description", "creator_handle", "created_at"))
        assert detail["tasks"] == []
    deadline = time.monotonic() + 180
    while query('ALERTS{alertname="AnalysisHttpFailureRatio"}'):
        assert time.monotonic() < deadline, "Alert failed to resolve after successful recovery"
        time.sleep(5)
    deadline = time.monotonic() + 30
    while True:
        receipts = internal("/receipts")["body"]["events"]
        resolved = next((e for e in receipts if e["fingerprint"] == run["fingerprint"] and e["status"] == "resolved"
                         and datetime.fromisoformat(e["starts_at"]) == datetime.fromisoformat(run["starts_at"])), None)
        if resolved:
            break
        assert time.monotonic() < deadline, "No resolved receipt"
        time.sleep(2)
    event("alert_resolved")
    logs = call(grafana + "/api/datasources/proxy/uid/loki/loki/api/v1/query_range?" + urlencode(
        {"query": '{service_name="officeflow-api"} |= "' + trace_id + '"', "limit": 1000}))[1]
    assert logs["data"]["result"]
    assert all(value not in json.dumps([logs, run, receipts]) for value in (marker, password, handle, csrf, admin_secret, monitor_secret))
    report = {"approval_reference": args.approval_reference, "events": events, "agent": run,
              "http_503_count": failures, "samples": samples, "resolved_receipt": resolved,
              "duplicate_suppressed": True, "postgresql_preserved": True, "active_tasks_created": 0,
              "redaction_passed": True, "exercise_disabled": True, "trace_id": trace_id}
    (ROOT / "artifacts/t15-verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "samples"}), flush=True)


if __name__ == "__main__":
    main()
