from datetime import timedelta
import json
import secrets
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session
import pytest

from app.analysis import now
from app.models import AnalysisRun, CustomerRequest, DemoUser, Task
from app.oncall import Alert, create_listener
from app.oncall_agent import AgentStore, OnCallAgent
from fastapi.testclient import TestClient


@pytest.fixture
def exercise(auth_context, monkeypatch, tmp_path):
    client, engine, user_id, _, _ = auth_context
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ENABLE_ONCALL_EXERCISE", "true")
    credentials = {}
    for role, variable in (("admin", "EXERCISE_ADMIN_TOKEN_FILE"), ("operator", "ONCALL_OPS_TOKEN_FILE")):
        token = secrets.token_urlsafe(32)
        path = tmp_path / role
        path.write_text(token)
        monkeypatch.setenv(variable, str(path))
        credentials[role] = {"Authorization": "Bearer " + token}
    with Session(engine) as db:
        db.get(DemoUser, user_id).handle = "alert_verify_" + uuid4().hex[:12]
        db.commit()
    records = [client.post("/api/v1/requests", json={"title": "Synthetic exercise", "description": "private sentinel"}).json() for _ in range(2)]
    scope = {"exercise_id": str(uuid4()), "environment": "development", "flag": "analysis_disabled",
             "request_id": records[0]["id"], "verification_request_id": records[1]["id"], "user_id": str(user_id),
             "expires_at": (now() + timedelta(seconds=230)).isoformat(), "max_failures": 40}
    return client, engine, credentials, scope


def activate(exercise):
    client, _, keys, scope = exercise
    response = client.post("/api/v1/ops/exercise/authorize", json=scope, headers=keys["admin"])
    assert response.status_code == 200
    for _ in range(5):
        assert client.post(f"/api/v1/requests/{scope['request_id']}/analyses", headers={"Idempotency-Key": str(uuid4())}).status_code == 503
    return {"exercise_id": scope["exercise_id"], "fingerprint": "0123456789abcdef", "starts_at": now().isoformat()}


def test_scoped_identity_only_and_fault_preserves_viewing_and_postgres(exercise):
    client, engine, keys, scope = exercise
    with Session(engine) as db:
        before = db.scalar(select(func.count()).select_from(CustomerRequest))
        tasks = db.scalar(select(func.count()).select_from(Task))
    assert client.post("/api/v1/ops/exercise/authorize", json=scope).status_code == 403
    assert client.post("/api/v1/ops/exercise/authorize", json=scope, headers=keys["operator"]).status_code == 403
    incident = activate(exercise)
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(AnalysisRun).where(
            AnalysisRun.request_id.in_([scope["request_id"], scope["verification_request_id"]]))) == 0
    assert client.get(f"/api/v1/requests/{scope['request_id']}").status_code == 200
    assert client.get("/api/v1/ops/exercise/diagnostics").status_code == 403
    assert client.post("/api/v1/ops/exercise/clear", json=incident).status_code == 403
    diagnostic = client.get("/api/v1/ops/exercise/diagnostics", headers=keys["operator"])
    assert diagnostic.json()["cause"] == "analysis_disabled"
    assert "private sentinel" not in diagnostic.text
    assert client.post("/api/v1/ops/exercise/clear", json=incident, headers=keys["operator"]).status_code == 200
    assert client.post("/api/v1/ops/exercise/clear", json=incident, headers=keys["operator"]).status_code == 409
    verified = client.post("/api/v1/ops/exercise/verify", json=incident, headers=keys["operator"]).json()
    assert verified == {"recovered": True, "state": "pending", "suggestion_count": 1, "active_tasks": 0}
    assert client.post("/api/v1/ops/exercise/verify", json=incident, headers=keys["operator"]).status_code == 409
    assert client.post(f"/api/v1/requests/{scope['request_id']}/analyses", headers={"Idempotency-Key": str(uuid4())}).status_code == 201
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(CustomerRequest)) == before
        assert db.scalar(select(func.count()).select_from(Task)) == tasks


@pytest.mark.parametrize("failure", ["missing", "expired", "production", "scope", "old_incident"])
def test_authorization_boundaries_fail_closed(exercise, monkeypatch, failure):
    client, _, keys, scope = exercise
    if failure == "missing":
        incident = {"exercise_id": scope["exercise_id"], "fingerprint": "0123456789abcdef", "starts_at": now().isoformat()}
    else:
        incident = activate(exercise)
    if failure == "expired":
        client.app.state.exercise.scope = client.app.state.exercise.scope.model_copy(update={"expires_at": now() - timedelta(seconds=1)})
    elif failure == "production":
        monkeypatch.setenv("APP_ENV", "production")
    elif failure == "scope":
        incident["exercise_id"] = str(uuid4())
    elif failure == "old_incident":
        incident["starts_at"] = (now() - timedelta(minutes=10)).isoformat()
    assert client.post("/api/v1/ops/exercise/clear", json=incident, headers=keys["operator"]).status_code in (403, 409)
    assert client.app.state.exercise.repairs == 0


@pytest.mark.parametrize("change", [{"environment": "production"}, {"flag": "delete_database"},
                                     {"expires_at": "2099-01-01T00:00:00Z"}, {"max_failures": 41}])
def test_invalid_scope_is_not_activated(exercise, change):
    client, _, keys, scope = exercise
    assert client.post("/api/v1/ops/exercise/authorize", json=scope | change, headers=keys["admin"]).status_code == 422
    assert not client.app.state.exercise.enabled


def test_actual_agent_automatically_invoked_by_authenticated_webhook(exercise, tmp_path):
    client, _, keys, scope = exercise
    incident = activate(exercise)
    alert = Alert.model_validate({"status": "firing", "labels": {"alertname": "AnalysisHttpFailureRatio", "severity": "warning", "deployment_environment": "local"},
        "annotations": {}, "startsAt": incident["starts_at"], "endsAt": "0001-01-01T00:00:00Z",
        "generatorURL": "http://prometheus:9090", "fingerprint": incident["fingerprint"]})

    class InProcessTools:
        async def call(self, tool, body=None):
            if tool == "incident":
                return [{"fingerprint": alert.fingerprint, "startsAt": incident["starts_at"], "labels": alert.labels.model_dump(), "status": {"state": "active"}}]
            response = (client.get("/api/v1/ops/exercise/diagnostics", headers=keys["operator"]) if tool == "diagnostics"
                        else client.post("/api/v1/ops/exercise/" + tool, json=body, headers=keys["operator"]))
            assert response.status_code == 200
            return response.json()

    store = AgentStore(tmp_path / "agent.sqlite3")
    agent = OnCallAgent(store, InProcessTools())
    secret = secrets.token_urlsafe(32)
    notification = {"version": "4", "groupKey": "test", "truncatedAlerts": 0, "status": "firing", "receiver": "oncall",
                    "groupLabels": {}, "commonLabels": alert.labels.model_dump(), "commonAnnotations": {}, "externalURL": "http://alertmanager:9093",
                    "alerts": [alert.model_dump(mode="json")]}
    with TestClient(create_listener(token=secret, path=tmp_path / "receipts.sqlite3", agent=agent)) as listener:
        assert listener.post("/webhook", json=notification).status_code == 403
        assert store.runs() == []
        for _ in range(2):
            assert listener.post("/webhook", json=notification, headers={"Authorization": "Bearer " + secret}).status_code == 200
    assert client.app.state.exercise.repairs == 1
    assert len(store.runs()) == 1
    assert store.runs()[0]["state"] == "recovered"
    assert [e["event"] for e in store.runs()[0]["events"]] == ["invoked", "incident_confirmed", "diagnosed_analysis_disabled", "cleared_analysis_disabled", "recovery_verified"]
    assert all(value not in json.dumps(store.runs()) for value in (secret, "private sentinel", keys["operator"]["Authorization"]))


def test_failed_provider_verification_stops_after_one_action(exercise):
    from app.model_adapter import OfflineAdapter
    class FailingAdapter(OfflineAdapter):
        async def analyze(self, *args):
            raise RuntimeError("private provider details")
    client, engine, keys, scope = exercise
    incident = activate(exercise)
    assert client.post("/api/v1/ops/exercise/clear", json=incident, headers=keys["operator"]).status_code == 200
    client.app.state.model_adapter = FailingAdapter()
    result = client.post("/api/v1/ops/exercise/verify", json=incident, headers=keys["operator"])
    assert result.json() == {"recovered": False, "state": "failed", "suggestion_count": 0, "active_tasks": 0}
    assert "private" not in result.text
    assert client.post("/api/v1/ops/exercise/verify", json=incident, headers=keys["operator"]).status_code == 409
    assert client.app.state.exercise.repairs == 1
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(CustomerRequest).where(CustomerRequest.id.in_(
            [scope["request_id"], scope["verification_request_id"]]))) == 2
