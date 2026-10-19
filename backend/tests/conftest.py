"""Isolated PostgreSQL identities, never runtime/demo credentials."""
import secrets

from fastapi.testclient import TestClient
import httpx
import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.api import create_app
from app.auth import hash_password
from app.database import build_engine, database_url
from app.models import CustomerRequest, DemoUser

ORIGIN = "http://testserver"


@pytest.fixture(autouse=True)
def deterministic_model_only(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "simulated")
    monkeypatch.setenv("TELEMETRY_ENABLED", "false")

    async def deny_live_http(*args, **kwargs):
        # MockTransport and in-process API tests remain available. A real model call
        # must fail the test, not be swallowed as an expected provider_error.
        pytest.fail("Live async HTTP is disabled in automatic tests; use the opt-in evaluation CLI")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", deny_live_http)


@pytest.fixture
def observed_telemetry():
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk._logs.export import InMemoryLogRecordExporter, SimpleLogRecordProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import InMemoryMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
    from app.telemetry import Telemetry

    resource = Resource({"service.name": "officeflow-api", "deployment.environment": "local"})
    traces, spans = TracerProvider(resource=resource), InMemorySpanExporter()
    traces.add_span_processor(SimpleSpanProcessor(spans))
    reader = InMemoryMetricReader()
    metrics = MeterProvider(resource=resource, metric_readers=[reader])
    logs, events = LoggerProvider(resource=resource), InMemoryLogRecordExporter()
    logs.add_log_record_processor(SimpleLogRecordProcessor(events))
    observer = Telemetry(traces, metrics, logs)
    try:
        yield observer, spans, reader, events
    finally:
        observer.shutdown()


@pytest.fixture
def auth_context(monkeypatch):
    if not (database_url().database or "").endswith("_test"):
        pytest.fail("Tests require an isolated database ending in _test")
    monkeypatch.setenv("APP_ORIGINS", ORIGIN)
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.setenv("MODEL_MODE", "simulated")
    engine = build_engine()
    password = secrets.token_urlsafe(24)
    handle = "test_" + secrets.token_hex(8)
    with Session(engine) as db:
        user = DemoUser(handle=handle, password_hash=hash_password(password))
        db.add(user)
        db.commit()
        user_id = user.id
    try:
        with TestClient(create_app(engine)) as client:
            response = client.post("/api/v1/auth/login", json={"handle": handle, "password": password},
                                   headers={"Origin": ORIGIN})
            assert response.status_code == 200
            client.headers.update({"Origin": ORIGIN, "X-CSRF-Token": response.json()["csrf_token"]})
            yield client, engine, user_id, handle, password
    finally:
        with Session(engine) as db:
            db.execute(delete(CustomerRequest).where(CustomerRequest.creator_id == user_id))
            db.execute(delete(DemoUser).where(DemoUser.id == user_id))
            db.commit()
        engine.dispose()
