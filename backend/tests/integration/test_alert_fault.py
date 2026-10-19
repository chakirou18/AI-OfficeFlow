from uuid import uuid4
import time
from sqlalchemy.orm import Session
from app.models import DemoUser
from app.dev_fault import DevAnalysisFault


def test_synthetic_fault_scoped_authenticated_bounded_and_no_tasks(auth_context, monkeypatch):
    client, engine, user_id, _, _ = auth_context
    record = client.post("/api/v1/requests", json={"title": "Synthetic alert test", "description": "Synthetic only"}).json()
    path = f"/api/v1/requests/{record['id']}/analyses"
    monkeypatch.setenv("DEV_ANALYSIS_FAILURE_REQUEST_ID", record["id"])
    monkeypatch.setenv("ENABLE_DEV_FAULTS", "true")
    monkeypatch.setenv("APP_ENV", "development")
    fault = DevAnalysisFault()
    client.app.state.dev_analysis_fault = fault
    headers = {"Idempotency-Key": str(uuid4())}
    # A configured UUID alone cannot affect an ordinary demo user.
    assert client.post(path, headers=headers).status_code == 201
    with Session(engine) as db:
        user = db.get(DemoUser, user_id)
        user.handle = "alert_verify_" + uuid4().hex[:12]
        db.commit()
    assert client.post(path, headers=headers | {"X-CSRF-Token": "wrong"}).status_code == 403
    assert fault.remaining == 40
    fault.remaining = 1
    assert client.post(path, headers=headers).status_code == 503
    assert fault.remaining == 0
    # Existing pending run replays, never activated, after budget expiry.
    assert client.post(path, headers=headers).status_code == 201
    fault.remaining = 1
    fault.until = time.monotonic() - 1
    assert client.post(path, headers=headers).status_code == 201
    assert fault.remaining == 1
    detail = client.get(f"/api/v1/requests/{record['id']}").json()
    assert detail["tasks"] == []
