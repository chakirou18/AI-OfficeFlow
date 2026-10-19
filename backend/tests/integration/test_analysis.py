import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event
from uuid import UUID, uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.analysis import DEADLINE_SECONDS, execute_analysis, now
from app.api import create_app
from app.model_adapter import OfflineAdapter
from app.models import AnalysisRun, Task

pytestmark = pytest.mark.integration


def request_id(client):
    return UUID(client.post("/api/v1/requests", json={"title": "Synthetic analysis request",
                "description": "Synthetic analysis context only."}).json()["id"])


def test_analysis_is_persisted_pending_simulated_and_never_creates_tasks(auth_context):
    client, engine, _, _, _ = auth_context
    request = request_id(client)
    key = str(uuid4())
    response = client.post(f"/api/v1/requests/{request}/analyses", headers={"Idempotency-Key": key})
    assert response.status_code == 201
    data = response.json()
    assert data["state"] == "pending" and data["provider_mode"] == "simulated"
    assert data["schema_version"] == "proposal-v1"
    assert data["error_code"] is None
    assert data["proposal"]["tasks"][0]["priority"] == "medium"
    with Session(engine) as db:
        run = db.get(AnalysisRun, UUID(data["id"]))
        assert (run.deadline_at - run.started_at).total_seconds() == DEADLINE_SECONDS == 30
        assert db.scalar(select(func.count()).select_from(Task)) == 0
    assert client.post(f"/api/v1/requests/{request}/analyses", headers={"Idempotency-Key": key}).json() == data
    assert client.post(f"/api/v1/requests/{request}/analyses", headers={"Idempotency-Key": str(uuid4())}).status_code == 409
    detail = client.get(f"/api/v1/requests/{request}").json()
    assert detail["status"] == "awaiting_review" and detail["analysis"]["id"] == data["id"]
    assert client.get("/api/v1/dashboard").json()["requests_by_status"]["awaiting_review"] == 1
    assert client.get("/api/v1/requests?status=awaiting_review").json()["total"] == 1
    with TestClient(create_app(engine)) as restarted:
        restarted.cookies.update(client.cookies)
        assert restarted.get(f"/api/v1/requests/{request}/analyses").json()[0] == data


class FailingAdapter:
    async def analyze(self, *_):
        raise RuntimeError("sensitive provider text must never escape")


class InvalidAdapter:
    async def analyze(self, *_):
        return {"summary": "Synthetic invalid output", "tasks": []}


class SlowAdapter:
    async def analyze(self, *_):
        await asyncio.sleep(60)


def test_real_http_analysis_deadline_is_thirty_seconds(auth_context):
    client, engine, _, _, _ = auth_context
    request = request_id(client)
    client.app.state.model_adapter = SlowAdapter()
    started = time.monotonic()
    response = client.post(f"/api/v1/requests/{request}/analyses", headers={"Idempotency-Key": str(uuid4())})
    assert response.status_code == 504
    assert response.json()["state"] == "failed" and response.json()["error_code"] == "timeout"
    assert 29 <= time.monotonic() - started < 40
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 0


@pytest.mark.parametrize("adapter,error", [(FailingAdapter(), "provider_error"), (InvalidAdapter(), "invalid_output"),
                                           (SlowAdapter(), "timeout")])
def test_failure_is_sanitized_creates_no_tasks_and_explicit_retry_works(auth_context, adapter, error):
    client, engine, user_id, _, _ = auth_context
    request = request_id(client)
    key = uuid4()
    run = asyncio.run(execute_analysis(engine, adapter, request, user_id, key, timeout_seconds=0.03))
    assert run.state == "failed" and run.error_code == error and run.proposal is None
    assert "sensitive" not in client.get(f"/api/v1/requests/{request}/analyses").text
    # Same key never calls the adapter again; new key is an explicit new attempt.
    cached = asyncio.run(execute_analysis(engine, OfflineAdapter(), request, user_id, key))
    assert cached.id == run.id and cached.state == "failed"
    retried = asyncio.run(execute_analysis(engine, OfflineAdapter(), request, user_id, uuid4()))
    assert retried.id != run.id and retried.state == "pending"
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 0


def test_failed_http_response_and_authorization(auth_context):
    client, engine, _, _, _ = auth_context
    request = request_id(client)
    path = f"/api/v1/requests/{request}/analyses"
    client.app.state.model_adapter = FailingAdapter()
    failure = client.post(path, headers={"Idempotency-Key": str(uuid4())})
    assert failure.status_code == 502 and failure.json()["error_code"] == "provider_error"
    assert failure.json()["state"] == "failed"
    assert "sensitive" not in failure.text
    assert client.get(f"/api/v1/requests/{request}").json()["status"] == "new"
    assert client.post(path).status_code == 422
    assert client.post(path, headers={"Idempotency-Key": "invalid"}).status_code == 422
    assert client.post(path, headers={"Idempotency-Key": str(uuid4()), "X-CSRF-Token": "wrong"}).status_code == 403
    assert client.post(path, headers={"Idempotency-Key": str(uuid4()), "Origin": "https://evil.invalid"}).status_code == 403
    assert client.post(f"/api/v1/requests/{uuid4()}/analyses", headers={"Idempotency-Key": str(uuid4())}).status_code == 404
    with TestClient(create_app(engine)) as anonymous:
        assert anonymous.get(path).status_code == 401
        assert anonymous.post(path, headers={"Idempotency-Key": str(uuid4())}).status_code == 401


def test_expired_interrupted_run_is_recovered_on_read_and_can_be_retried(auth_context):
    client, engine, user_id, _, _ = auth_context
    request = request_id(client)
    stamp = now() - timedelta(seconds=31)
    with Session(engine) as db:
        db.add(AnalysisRun(request_id=request, requested_by=user_id, idempotency_key=uuid4(), state="running",
                           started_at=stamp, deadline_at=stamp + timedelta(seconds=30)))
        db.commit()
    history = client.get(f"/api/v1/requests/{request}/analyses").json()
    assert history[0]["state"] == "failed" and history[0]["error_code"] == "interrupted"
    assert client.post(f"/api/v1/requests/{request}/analyses", headers={"Idempotency-Key": str(uuid4())}).status_code == 201
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 0


def test_cancellation_persists_interruption(auth_context):
    client, engine, user_id, _, _ = auth_context
    request = request_id(client)

    class CancelledAdapter:
        async def analyze(self, *_):
            raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(execute_analysis(engine, CancelledAdapter(), request, user_id, uuid4()))
    assert client.get(f"/api/v1/requests/{request}/analyses").json()[0]["error_code"] == "interrupted"


def test_concurrent_calls_are_serialized_and_model_has_no_database_transaction(auth_context):
    client, engine, user_id, _, _ = auth_context
    request = request_id(client)
    entered, release = Event(), Event()

    class ControlledAdapter(OfflineAdapter):
        async def analyze(self, *args):
            assert engine.pool.checkedout() == 0
            entered.set()
            while not release.is_set():
                await asyncio.sleep(0.01)
            return await super().analyze(*args)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(asyncio.run, execute_analysis(engine, ControlledAdapter(), request, user_id, uuid4()))
        try:
            assert entered.wait(5)
            with pytest.raises(HTTPException) as error:
                asyncio.run(execute_analysis(engine, OfflineAdapter(), request, user_id, uuid4()))
            assert error.value.status_code == 409
        finally:
            release.set()
        assert future.result(timeout=5).state == "pending"


def test_database_rejects_multiple_active_attempts_and_oversized_deadlines(auth_context):
    client, engine, user_id, _, _ = auth_context
    request = request_id(client)
    stamp = now()
    with Session(engine) as db:
        for seconds in (31,):
            db.add(AnalysisRun(request_id=request, requested_by=user_id, idempotency_key=uuid4(), state="running",
                               started_at=stamp, deadline_at=stamp + timedelta(seconds=seconds)))
            with pytest.raises(IntegrityError):
                db.commit()
            db.rollback()
        db.add_all([AnalysisRun(request_id=request, requested_by=user_id, idempotency_key=uuid4(), state="running",
                                started_at=stamp, deadline_at=stamp + timedelta(seconds=30)) for _ in range(2)])
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
