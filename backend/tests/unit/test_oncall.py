import copy
import json
import secrets
import sqlite3
import time

from fastapi.testclient import TestClient
import pytest

from app.oncall import MAX_BYTES, MAX_EVENTS, Notification, ReceiptStore, create_listener


@pytest.fixture
def notification():
    labels = {"alertname": "AnalysisHttpFailureRatio", "severity": "warning", "deployment_environment": "local"}
    return {"version": "4", "groupKey": "safe-group", "truncatedAlerts": 0, "status": "firing",
            "receiver": "oncall", "groupLabels": {"alertname": labels["alertname"]}, "commonLabels": labels,
            "commonAnnotations": {}, "externalURL": "http://alertmanager:9093",
            "alerts": [{"status": "firing", "labels": labels, "annotations": {},
                        "startsAt": "2026-10-19T12:00:00Z", "endsAt": "2026-10-19T12:05:00Z",
                        "generatorURL": "http://prometheus:9090/graph", "fingerprint": "0123456789abcdef"}]}


@pytest.fixture
def listener(tmp_path):
    token = secrets.token_urlsafe(32)
    with TestClient(create_listener(token=token, path=tmp_path / "events.sqlite3")) as client:
        yield client, {"Authorization": "Bearer " + token}


def test_authentication_before_parsing_and_no_secret_echo(listener):
    client, headers = listener
    secret = headers["Authorization"]
    for route, method in (("/webhook", "post"), ("/receipts", "get")):
        response = getattr(client, method)(route, headers={"Authorization": secret + "wrong"})
        assert response.status_code == 403
        assert secret not in response.text
    assert client.get("/docs").status_code == 404


@pytest.mark.parametrize("mutation", ["syntax", "extra", "priority", "truncated", "empty", "labels", "dates"])
def test_reject_invalid_without_echo(listener, notification, mutation):
    client, headers = listener
    marker = "private-do-not-log"
    body = copy.deepcopy(notification)
    if mutation == "extra":
        body[marker] = marker
    elif mutation == "priority":
        body["status"] = marker
    elif mutation == "truncated":
        body["truncatedAlerts"] = 1
    elif mutation == "empty":
        body["alerts"] = []
    elif mutation == "labels":
        body["alerts"][0]["labels"]["user_id"] = marker
    elif mutation == "dates":
        body["alerts"][0]["endsAt"] = "2020-01-01T00:00:00Z"
    response = client.post("/webhook", content=(marker if mutation == "syntax" else json.dumps(body)), headers=headers)
    assert response.status_code == 422
    assert marker not in response.text
    assert client.get("/receipts", headers=headers).json() == {"events": []}


def test_oversized_body_including_chunked(listener):
    client, headers = listener
    response = client.post("/webhook", content=iter([b"x" * 32768, b"x" * (MAX_BYTES // 2 + 1)]), headers=headers)
    assert response.status_code == 413


def test_duplicate_resolution_and_no_resurrection(listener, notification):
    client, headers = listener
    def send(body):
        response = client.post("/webhook", json=body, headers=headers)
        assert response.status_code == 200
        return response.json()
    assert send(notification) == {"accepted": 1, "duplicates": 0}
    assert send(notification) == {"accepted": 0, "duplicates": 1}
    resolved = copy.deepcopy(notification)
    resolved["status"] = resolved["alerts"][0]["status"] = "resolved"
    assert send(resolved)["accepted"] == 1
    assert send(resolved)["accepted"] == 0
    assert send(notification)["accepted"] == 0
    events = client.get("/receipts", headers=headers).json()["events"]
    assert len(events) == 2
    assert {e["status"] for e in events} == {"firing", "resolved"}
    assert all(e["deliveries"] == 2 for e in events)


def test_retention_restart_and_untrusted_metadata_not_stored(tmp_path, notification):
    path = tmp_path / "store.sqlite3"
    store = ReceiptStore(path)
    notification["alerts"][0]["annotations"] = {"summary": "untrusted secret"}
    for index in range(MAX_EVENTS + 5):
        notification["alerts"][0]["fingerprint"] = f"{index:016x}"
        store.record(Notification.model_validate(notification))
    events = ReceiptStore(path).events()
    assert len(events) == MAX_EVENTS
    assert "untrusted secret" not in json.dumps(events)
    with sqlite3.connect(path) as db:
        db.execute("UPDATE receipts SET last_received_at=?", (time.time() - 8 * 86400,))
    assert store.events() == []


def test_concurrent_duplicate_is_one_receipt(tmp_path, notification):
    from concurrent.futures import ThreadPoolExecutor
    store = ReceiptStore(tmp_path / "concurrent.sqlite3")
    body = Notification.model_validate(notification)
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(store.record, [body] * 12)) == 1
    assert len(store.events()) == 1
    assert store.events()[0]["deliveries"] == 12


def test_short_token_refused(tmp_path):
    with pytest.raises(ValueError):
        create_listener(token="short", path=tmp_path / "short.sqlite3")


def test_alertmanager_active_zero_end_is_valid_but_resolved_zero_is_not(notification):
    from pydantic import ValidationError
    notification["alerts"][0]["endsAt"] = "0001-01-01T00:00:00Z"
    assert Notification.model_validate(notification).alerts[0].status == "firing"
    notification["alerts"][0]["status"] = "resolved"
    with pytest.raises(ValidationError):
        Notification.model_validate(notification)


def test_fault_disabled_and_requires_explicit_development(monkeypatch):
    from uuid import uuid4
    from app.dev_fault import DevAnalysisFault
    monkeypatch.delenv("DEV_ANALYSIS_FAILURE_REQUEST_ID", raising=False)
    assert DevAnalysisFault().request_id is None
    monkeypatch.setenv("DEV_ANALYSIS_FAILURE_REQUEST_ID", str(uuid4()))
    with pytest.raises(ValueError):
        DevAnalysisFault()
