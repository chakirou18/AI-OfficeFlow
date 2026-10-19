import json

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine

from app.api import create_app
from app.telemetry import configured_telemetry


def test_telemetry_is_disabled_by_default_and_remote_export_is_denied(monkeypatch):
    assert configured_telemetry() is None
    monkeypatch.setenv("TELEMETRY_ENABLED", "true")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "https://example.invalid:4318")
    with pytest.raises(ValueError, match="private local Collector"):
        configured_telemetry()


def test_unknown_urls_and_headers_never_become_telemetry_and_context_is_correlated(observed_telemetry):
    observer, spans, reader, logs = observed_telemetry
    secret = "synthetic-private-sentinel"
    trace_id = "1234567890abcdef1234567890abcdef"
    engine = create_engine("sqlite://")  # No persistence exercised by 404/liveness.
    app = create_app(engine, telemetry=observer)
    with TestClient(app) as client:
        headers = {"traceparent": f"00-{trace_id}-0011223344556677-01",
                   "authorization": secret, "cookie": secret, "baggage": secret,
                   "tracestate": f"private={secret}"}
        response = client.get(f"/unknown-{secret}?password={secret}", headers=headers)
        assert response.status_code == 404 and trace_id in response.headers["traceparent"]
        assert client.get("/api/v1/health/live", headers=headers).status_code == 200
    recorded = spans.get_finished_spans()
    assert {span.name for span in recorded} == {"GET /unmatched", "GET /api/v1/health/live"}
    assert all(span.context.trace_id == int(trace_id, 16) for span in recorded)
    assert all(span.parent.span_id == int("0011223344556677", 16) for span in recorded)
    data = reader.get_metrics_data()
    metrics = [m for r in data.resource_metrics for s in r.scope_metrics for m in s.metrics]
    histogram = next(m for m in metrics if m.name == "officeflow.http.duration")
    assert any(point.exemplars for point in histogram.data.data_points)
    for metric in metrics:
        for point in metric.data.data_points:
            assert set(point.attributes) <= {"http_method", "http_route", "http_status"}
    events = [json.loads(item.log_record.body) for item in logs.get_finished_logs()]
    assert all(item["trace_id"] == trace_id and len(item["span_id"]) == 16 for item in events)
    assert all({"timestamp", "severity", "event"} <= item.keys() for item in events)
    serialized = data.to_json() + str(events) + "".join(span.to_json() for span in recorded)
    assert secret not in serialized
    engine.dispose()
