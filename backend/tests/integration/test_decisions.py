from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID, uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.analysis import begin_attempt
from app.api import create_app
from app.decisions import DecisionInput, decide_analysis
from app.model_adapter import OfflineAdapter
from app.models import AnalysisRun, CustomerRequest, Task

pytestmark = pytest.mark.integration


class MultipleSuggestions(OfflineAdapter):
    async def analyze(self, *_):
        return {"summary": "Synthetic human decision fixture", "tasks": [
            {"title": f"Synthetic suggestion {index}", "priority": priority,
             "rationale": "Timing and resources are unknown."} for index, priority in enumerate(["low", "medium", "high"])]}


def pending(client):
    client.app.state.model_adapter = MultipleSuggestions()
    record = client.post("/api/v1/requests", json={"title": "Synthetic human review",
                         "description": "Synthetic request requiring an explicit human decision."}).json()
    run = client.post(f"/api/v1/requests/{record['id']}/analyses", headers={"Idempotency-Key": str(uuid4())}).json()
    return UUID(record["id"]), UUID(run["id"]), run


def path(request_id, analysis_id):
    return f"/api/v1/requests/{request_id}/analyses/{analysis_id}/decision"


def test_approval_atomically_persists_exact_saved_proposal_and_replay_survives_restart(auth_context):
    client, engine, user_id, _, _ = auth_context
    request_id, analysis_id, proposal = pending(client)
    before = client.get("/api/v1/dashboard").json()
    response = client.post(path(request_id, analysis_id), json={"decision": "approve"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress" and data["analysis"]["state"] == "approved"
    assert data["analysis"]["decided_by"] == str(user_id)
    assert data["analysis"]["decided_at"] and data["analysis"]["rejection_reason"] is None
    assert len(data["tasks"]) == 3
    for index, task in enumerate(data["tasks"]):
        assert task["analysis_id"] == str(analysis_id) and task["suggestion_index"] == index
        assert task["state"] == "open"
        assert {k: task[k] for k in ("title", "priority", "rationale")} == proposal["proposal"]["tasks"][index]
    with Session(engine) as db:
        run = db.get(AnalysisRun, analysis_id)
        assert run.state == "approved" and run.decided_by == user_id
        assert db.scalar(select(func.count()).select_from(Task).where(Task.analysis_id == analysis_id)) == 3
        assert db.get(CustomerRequest, request_id).updated_at == run.decided_at
    assert client.post(path(request_id, analysis_id), json={"decision": "approve"}).json() == data
    with TestClient(create_app(engine)) as restarted:
        restarted.cookies.update(client.cookies)
        restarted.headers.update(client.headers)
        assert restarted.post(path(request_id, analysis_id), json={"decision": "approve"}).json() == data
    after = client.get("/api/v1/dashboard").json()
    assert after["total_tasks"] == before["total_tasks"] + 3
    assert after["open_tasks"] == before["open_tasks"] + 3
    assert after["requests_by_status"]["awaiting_review"] == before["requests_by_status"]["awaiting_review"] - 1
    assert after["requests_by_status"]["in_progress"] == before["requests_by_status"]["in_progress"] + 1
    assert client.post(path(request_id, analysis_id), json={"decision": "reject", "reason": "Late conflict"}).status_code == 409
    assert client.post(f"/api/v1/requests/{request_id}/analyses", headers={"Idempotency-Key": str(uuid4())}).status_code == 409


def test_rejection_creates_no_tasks_and_old_analysis_cannot_approve_new_attempt(auth_context):
    client, engine, user_id, _, _ = auth_context
    request_id, analysis_id, _ = pending(client)
    payload = {"decision": "reject", "reason": "  Synthetic clarification needed  "}
    response = client.post(path(request_id, analysis_id), json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["analysis"]["state"] == "rejected" and data["status"] == "new" and data["tasks"] == []
    assert data["analysis"]["rejection_reason"] == "Synthetic clarification needed"
    assert data["analysis"]["decided_by"] == str(user_id)
    assert client.post(path(request_id, analysis_id), json=payload).json() == data
    assert client.post(path(request_id, analysis_id), json={"decision": "reject", "reason": "Changed reason"}).status_code == 409
    retried = client.post(f"/api/v1/requests/{request_id}/analyses", headers={"Idempotency-Key": str(uuid4())})
    assert retried.status_code == 201 and retried.json()["id"] != str(analysis_id)
    assert client.post(path(request_id, analysis_id), json={"decision": "approve"}).status_code == 409
    assert client.get(f"/api/v1/requests/{request_id}").json()["analysis"]["state"] == "pending"
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 0
    assert client.get("/api/v1/dashboard").json()["total_tasks"] == 0


def test_decision_requires_session_origin_csrf_and_correct_specific_analysis(auth_context, monkeypatch):
    client, engine, _, _, _ = auth_context
    request_id, analysis_id, _ = pending(client)
    other_request, _, _ = pending(client)
    target = path(request_id, analysis_id)
    for headers in ({"X-CSRF-Token": "wrong"}, {"Origin": "https://evil.invalid"}, {"Origin": ""}):
        assert client.post(target, json={"decision": "approve"}, headers=headers).status_code == 403
    monkeypatch.setenv("OPS_TOKEN", "synthetic-ops-only-token-32-characters")
    with TestClient(create_app(engine)) as anonymous:
        for headers in ({}, {"Authorization": "Bearer synthetic-ops-only-token-32-characters"}):
            assert anonymous.post(target, json={"decision": "approve"}, headers=headers).status_code == 401
    for invalid in ({"decision": "reject"}, {"decision": "approve", "tasks": []}, {"decision": "approve", "decided_by": str(uuid4())}):
        assert client.post(target, json=invalid).status_code == 422
    for endpoint in (path(other_request, analysis_id), path(uuid4(), analysis_id), path(request_id, uuid4())):
        assert client.post(endpoint, json={"decision": "approve"}).status_code == 404
    with Session(engine) as db:
        assert db.get(AnalysisRun, analysis_id).state == "pending"
        assert db.scalar(select(func.count()).select_from(Task)) == 0


@pytest.mark.parametrize("mixed", [False, True])
def test_concurrent_decisions_serialize_without_duplicates(auth_context, mixed):
    client, engine, user_id, _, _ = auth_context
    request_id, analysis_id, _ = pending(client)
    choices = ["approve", "reject"] if mixed else ["approve"] * 4
    barrier = Barrier(len(choices))

    def submit(choice):
        barrier.wait(timeout=5)
        try:
            result = decide_analysis(engine, request_id, analysis_id, user_id,
                                     DecisionInput(decision=choice, reason="Synthetic rejection" if choice == "reject" else None))
            return result.analysis.state, [task.id for task in result.tasks]
        except HTTPException as error:
            return error.status_code, []

    with ThreadPoolExecutor(max_workers=len(choices)) as executor:
        results = list(executor.map(submit, choices))
    with Session(engine) as db:
        run = db.get(AnalysisRun, analysis_id)
        count = db.scalar(select(func.count()).select_from(Task).where(Task.analysis_id == analysis_id))
        assert count == (3 if run.state == "approved" else 0)
        assert run.decided_by == user_id and run.decided_at
    if mixed:
        assert sum(result[0] == 409 for result in results) == 1
    else:
        assert all(result == results[0] for result in results)


def test_task_insert_failure_rolls_back_decision_and_retry_is_safe(auth_context):
    client, engine, _, _, _ = auth_context
    request_id, analysis_id, _ = pending(client)
    before_dashboard = client.get("/api/v1/dashboard").json()
    with Session(engine) as db:
        before_updated = db.get(CustomerRequest, request_id).updated_at

    def fail_after_insert(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO tasks"):
            raise SQLAlchemyError("private simulated database failure")

    event.listen(engine, "after_cursor_execute", fail_after_insert)
    try:
        response = client.post(path(request_id, analysis_id), json={"decision": "approve"})
        assert response.status_code == 503 and "private" not in response.text
    finally:
        event.remove(engine, "after_cursor_execute", fail_after_insert)
    with Session(engine) as db:
        run = db.get(AnalysisRun, analysis_id)
        assert run.state == "pending" and run.decided_at is None and run.decided_by is None
        assert db.get(CustomerRequest, request_id).updated_at == before_updated
        assert db.scalar(select(func.count()).select_from(Task)) == 0
    assert client.get("/api/v1/dashboard").json() == before_dashboard
    assert client.post(path(request_id, analysis_id), json={"decision": "approve"}).status_code == 200


def test_invalid_stored_proposal_and_nonpending_run_cannot_activate_tasks(auth_context):
    client, engine, user_id, _, _ = auth_context
    request_id, analysis_id, _ = pending(client)
    with Session(engine) as db:
        db.get(AnalysisRun, analysis_id).proposal = {"summary": "Invalid synthetic stored fixture", "tasks": []}
        db.commit()
    assert client.post(path(request_id, analysis_id), json={"decision": "approve"}).status_code == 409
    another = UUID(client.post("/api/v1/requests", json={"title": "Synthetic running", "description": "Synthetic only"}).json()["id"])
    run, _ = begin_attempt(engine, another, user_id, uuid4(), 30)
    assert client.post(path(another, run.id), json={"decision": "approve"}).status_code == 409
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 0


def test_database_rejects_forged_decision_metadata_and_duplicate_source(auth_context):
    client, engine, _, _, _ = auth_context
    request_id, analysis_id, _ = pending(client)
    with Session(engine) as db:
        db.get(AnalysisRun, analysis_id).state = "approved"
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
    response = client.post(path(request_id, analysis_id), json={"decision": "approve"}).json()
    with Session(engine) as db:
        task = response["tasks"][0]
        db.add(Task(request_id=request_id, analysis_id=analysis_id, suggestion_index=0,
                    title=task["title"], priority=task["priority"], rationale=task["rationale"]))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        assert db.scalar(select(func.count()).select_from(Task).where(Task.analysis_id == analysis_id)) == 3
