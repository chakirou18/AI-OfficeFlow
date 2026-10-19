"""Opt-in bounded local synthetic HTTP failures, real rule and automatic delivery proof."""
import base64
from datetime import datetime, timezone
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def docker(*args, env=None, data=None):
    result = subprocess.run(["docker", "compose", *args], cwd=ROOT, env=env, input=data,
                            capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("Compose verification command failed; output withheld to protect credentials")
    return result.stdout


def internal(path, body=None, *, authenticated=True):
    # Fixed internal targets only; bearer credential read inside the private receiver.
    code = """import json,sys,urllib.request,urllib.error
from pathlib import Path
p=json.load(sys.stdin)
headers={}
if p['auth']: headers['Authorization']='Bearer '+Path('/run/secrets/alert_webhook_token').read_text().strip()
url=('http://127.0.0.1:8010' if p['path'].startswith(('/receipts','/webhook','/agent-runs')) else 'http://alertmanager:9093')+p['path']
data=json.dumps(p['body']).encode() if p['body'] is not None else None
if data is not None: headers['Content-Type']='application/json'
try: r=urllib.request.urlopen(urllib.request.Request(url,data=data,headers=headers),timeout=5)
except urllib.error.HTTPError as e: r=e
print(json.dumps({'status':r.status,'body':json.load(r)}))
"""
    return json.loads(docker("exec", "-T", "oncall-listener", "python", "-c", code,
                             data=json.dumps({"path": path, "body": body, "auth": authenticated})))


def main():
    config = dict(line.split("=", 1) for line in (ROOT / ".env").read_text().splitlines()
                  if "=" in line and not line.startswith("#"))
    assert not config.get("DEV_ANALYSIS_FAILURE_REQUEST_ID") and not os.getenv("DEV_ANALYSIS_FAILURE_REQUEST_ID")
    app = "http://127.0.0.1:" + config.get("FRONTEND_PORT", "8080")
    grafana = "http://127.0.0.1:" + config.get("GRAFANA_PORT", "3000")
    gf_secret = (ROOT / "artifacts/grafana-admin-password").read_text().strip()
    gf_auth = "Basic " + base64.b64encode(("monitor:" + gf_secret).encode()).decode()
    handle, password, marker = "alert_verify_" + secrets.token_hex(6), secrets.token_urlsafe(32), "private_" + secrets.token_hex(12)
    trace_id, csrf = uuid4().hex, ""
    browser = build_opener(HTTPCookieProcessor(CookieJar()))

    def call(url, body=None, *, expected=200, headers=None, method=None):
        metadata = ({"Origin": app, "X-CSRF-Token": csrf,
                     "traceparent": f"00-{trace_id}-{secrets.token_hex(8)}-01"}
                    if url.startswith(app) else {"Authorization": gf_auth})
        metadata.update(headers or {})
        data = json.dumps(body).encode() if body is not None else None
        if data is not None:
            metadata["Content-Type"] = "application/json"
        try:
            response = browser.open(Request(url, data=data, headers=metadata, method=method), timeout=10)
        except HTTPError as error:
            response = error
        assert response.status == expected, f"Unexpected HTTP {response.status}; body withheld"
        return json.load(response)

    def query(expr):
        return call(grafana + "/api/datasources/proxy/uid/prometheus/api/v1/query?" + urlencode({"query": expr}))["data"]["result"]

    def analysis(request_id, expected):
        return call(app + f"/api/v1/requests/{request_id}/analyses", method="POST", expected=expected,
                    headers={"Idempotency-Key": str(uuid4())})

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
    docker("exec", "-T", "api", "python", "-c", provision, data=json.dumps({"handle": handle, "password": password}))
    csrf = call(app + "/api/v1/auth/login", {"handle": handle, "password": password})["csrf_token"]
    assert call(app + "/api/v1/requests/analysis/config")["provider_mode"] == "simulated"
    record = call(app + "/api/v1/requests", {"title": "Synthetic local alert verification", "description": marker}, expected=201)
    before = call(app + "/api/v1/dashboard")["total_tasks"]
    assert internal("/receipts", authenticated=False)["status"] == 403
    assert internal("/api/v2/alerts", authenticated=False)["status"] == 200
    env = dict(os.environ, ENABLE_DEV_FAULTS="true", DEV_ANALYSIS_FAILURE_REQUEST_ID=record["id"], MODEL_MODE="simulated")
    baseline_events = internal("/receipts")["body"]["events"]
    # A prior interrupted verification must resolve before a fresh incident cycle.
    settle_deadline = time.monotonic() + 180
    while query('ALERTS{alertname="AnalysisHttpFailureRatio"}'):
        if time.monotonic() >= settle_deadline:
            raise RuntimeError("Existing analysis alert has not cleared; no new fault started")
        time.sleep(5)
    samples, failures, firing_receipt = [], 0, None
    started = datetime.now(timezone.utc).isoformat()
    try:
        docker("up", "-d", "--no-deps", "--wait", "api", env=env)
        deadline = time.monotonic() + 190
        while time.monotonic() < deadline:
            analysis(record["id"], 503)
            failures += 1
            active = query('ALERTS{alertname="AnalysisHttpFailureRatio"}')
            counts = query('officeflow:analysis_attempts:2m')
            ratio = query('officeflow:analysis_failures:2m / officeflow:analysis_attempts:2m')
            samples.append({"at": datetime.now(timezone.utc).isoformat(), "alerts": active, "attempts": counts, "ratio": ratio})
            receipts = internal("/receipts")["body"]["events"]
            fresh = [e for e in receipts if e not in baseline_events and e["status"] == "firing"
                     and datetime.fromisoformat(e["starts_at"]) > datetime.fromisoformat(started)]
            if fresh:
                firing_receipt = fresh[0]
                break
            assert failures < 39, "Bounded fault budget reached without automatic delivery"
            time.sleep(5)
        assert firing_receipt, "No automatic authenticated firing receipt"
        alerts = internal("/api/v2/alerts", authenticated=False)["body"]
        actual = next(a for a in alerts if a["fingerprint"] == firing_receipt["fingerprint"])
        rules = call(grafana + "/api/datasources/proxy/uid/prometheus/api/v1/rules")["data"]["groups"]
        rule = next(r for g in rules for r in g["rules"] if r["name"] == "AnalysisHttpFailureRatio")
        assert rule["duration"] == 60 and rule["state"] == "firing"
        pending_at = datetime.fromisoformat(rule["alerts"][0]["activeAt"].replace("Z", "+00:00")).timestamp()
        assert firing_receipt["received_at"] - pending_at >= 60
        payload_alert = {k: actual[k] for k in ("labels", "annotations", "startsAt", "endsAt", "generatorURL", "fingerprint")}
        payload_alert["status"] = "firing"
        notification = {"version": "4", "groupKey": "verification-replay", "truncatedAlerts": 0,
                        "status": "firing", "receiver": "oncall", "groupLabels": {"alertname": "AnalysisHttpFailureRatio"},
                        "commonLabels": actual["labels"], "commonAnnotations": actual["annotations"],
                        "externalURL": "http://alertmanager:9093", "alerts": [payload_alert]}
        duplicate = internal("/webhook", notification)
        assert duplicate == {"status": 200, "body": {"accepted": 0, "duplicates": 1}}
        print(json.dumps({"stage": "automatic_firing_received", "failures": failures,
                          "pending_at": pending_at, "receipt": firing_receipt, "duplicate": duplicate}), flush=True)
    finally:
        # Human-authorized local verifier cleanup, not an agent or automatic repair.
        clean = dict(os.environ, ENABLE_DEV_FAULTS="false", DEV_ANALYSIS_FAILURE_REQUEST_ID="")
        docker("up", "-d", "--no-deps", "--wait", "api", env=clean)
    recovered = analysis(record["id"], 201)
    assert recovered["state"] == "pending" and 1 <= len(recovered["proposal"]["tasks"]) <= 5
    assert call(app + f"/api/v1/requests/{record['id']}")["tasks"] == []
    assert call(app + "/api/v1/dashboard")["total_tasks"] == before
    deadline, resolved = time.monotonic() + 180, None
    while time.monotonic() < deadline:
        events = internal("/receipts")["body"]["events"]
        resolved = next((e for e in events if e["fingerprint"] == firing_receipt["fingerprint"]
                         and e["starts_at"] == firing_receipt["starts_at"] and e["status"] == "resolved"), None)
        if resolved and not query('ALERTS{alertname="AnalysisHttpFailureRatio"}'):
            break
        time.sleep(5)
    assert resolved, "No automatic resolved delivery"
    saved_events = internal("/receipts")["body"]["events"]
    docker("restart", "oncall-listener")
    time.sleep(3)
    assert internal("/receipts")["body"]["events"] == saved_events
    logs = call(grafana + "/api/datasources/proxy/uid/loki/loki/api/v1/query_range?" + urlencode(
        {"query": '{service_name="officeflow-api"} |= "' + trace_id + '"', "limit": 500}))
    assert logs["data"]["result"]
    serialized = json.dumps([samples, saved_events, logs])
    assert all(v not in serialized for v in (password, handle, marker, csrf, gf_secret))
    report = {"started_at": started, "trace_id": trace_id, "synthetic_http_503_count": failures,
              "hold_seconds": 60, "pending_at_epoch": pending_at, "firing_receipt": firing_receipt,
              "resolved_receipt": resolved, "duplicate_replay": duplicate, "receiver_restart_preserved": True,
              "real_recovery_pending": True, "automatically_created_tasks": 0, "redaction_passed": True,
              "grafana_url": grafana + "/d/officeflow", "samples": samples}
    (ROOT / "artifacts/t14-verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "samples"}), flush=True)


if __name__ == "__main__":
    main()
