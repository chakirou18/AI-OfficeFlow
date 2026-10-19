import json
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from app.api import create_app
from app.model_adapter import OfflineAdapter

pytestmark = pytest.mark.integration


def test_instrumented_authenticated_journeys_preserve_context_and_redact_payloads(auth_context, observed_telemetry, monkeypatch):
    _, engine, _, handle, password = auth_context
    observer, spans, reader, logs = observed_telemetry
    secret = "synthetic-private-request-and-reason"
    ops = "synthetic-private-ops-token-at-least-32"
    monkeypatch.setenv("OPS_TOKEN", ops)
    trace_id = "abcdef1234567890abcdef1234567890"
    app = create_app(engine, telemetry=observer)
    with TestClient(app) as client:
        client.headers.update({"Origin": "http://testserver", "traceparent": f"00-{trace_id}-0011223344556677-01"})
        login = client.post("/api/v1/auth/login", json={"handle": handle, "password": password})
        assert login.status_code == 200
        csrf = login.json()["csrf_token"]
        client.headers.update({"X-CSRF-Token": csrf, "traceparent": login.headers["traceparent"]})
        for decision in ("approve", "reject"):
            saved = client.post("/api/v1/requests", json={"title": "Synthetic metadata test", "description": secret})
            assert saved.status_code == 201
            request_id = saved.json()["id"]
            run = client.post(f"/api/v1/requests/{request_id}/analyses", headers={"Idempotency-Key": str(uuid4())})
            assert run.status_code == 201
            body = {"decision": decision} | ({"reason": secret} if decision == "reject" else {})
            assert client.post(f"/api/v1/requests/{request_id}/analyses/{run.json()['id']}/decision", json=body).status_code == 200
        assert client.get("/api/v1/ops/health", headers={"Authorization": "Bearer " + ops}).status_code == 200
        assert client.get("/api/v1/ops/health").status_code == 403
    recorded = spans.get_finished_spans()
    assert all(span.context.trace_id == int(trace_id, 16) for span in recorded)
    assert {"model.analyze", "human.decision", "POST /api/v1/auth/login", "POST /api/v1/requests",
            "GET /api/v1/ops/health"} <= {span.name for span in recorded}
    assert all(request_id not in span.name for span in recorded)
    events = [json.loads(item.log_record.body) for item in logs.get_finished_logs()]
    assert {event.get("outcome") for event in events} >= {"pending", "approved", "rejected"}
    serialized = reader.get_metrics_data().to_json() + str(events) + "".join(span.to_json() for span in recorded)
    for private in (secret, password, handle, csrf, ops, request_id):
        assert private not in serialized


def test_provider_exception_text_is_not_recorded_in_spans_logs_or_metrics(auth_context, observed_telemetry):
    existing, engine, _, _, _ = auth_context
    observer, spans, reader, logs = observed_telemetry
    secret = "synthetic-provider-secret-never-export"

    class FailedProvider(OfflineAdapter):
        async def analyze(self, *_):
            raise RuntimeError(secret)

    app = create_app(engine, telemetry=observer)
    app.state.model_adapter = FailedProvider()
    with TestClient(app) as client:
        client.cookies.update(existing.cookies)
        client.headers.update(existing.headers)
        saved = client.post("/api/v1/requests", json={"title": "Synthetic failure", "description": secret}).json()
        response = client.post(f"/api/v1/requests/{saved['id']}/analyses", headers={"Idempotency-Key": str(uuid4())})
        assert response.status_code == 502
    recorded = spans.get_finished_spans()
    assert any(span.status.status_code.name == "ERROR" for span in recorded)
    assert all(not span.events for span in recorded)  # No automatic exception/stack events.
    events = [json.loads(item.log_record.body) for item in logs.get_finished_logs()]
    assert any(event.get("error_code") == "provider_error" and event["severity"] == "ERROR" for event in events)
    assert secret not in reader.get_metrics_data().to_json() + str(events) + "".join(span.to_json() for span in recorded)
