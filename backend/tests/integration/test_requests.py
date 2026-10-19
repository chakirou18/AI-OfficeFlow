from datetime import datetime, timezone
import secrets
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api import create_app
from app.auth import hash_password
from app.models import CustomerRequest, DemoUser, Task

pytestmark = pytest.mark.integration


def create(client, title="Synthetic inventory review", description="Review demonstration stock only."):
    response = client.post("/api/v1/requests", json={"title": title, "description": description})
    assert response.status_code == 201, response.text
    return response.json()


def seed_tasks(engine, request_id):
    """Direct synthetic approved-task fixtures; does not demonstrate T11 approval."""
    with Session(engine) as db:
        source_id = uuid4()
        tasks = [Task(request_id=UUID(request_id), analysis_id=source_id, suggestion_index=index,
                      title=f"Synthetic approved task {index}", rationale="Synthetic fixture rationale",
                      priority="high" if index else "low") for index in range(2)]
        db.add_all(tasks)
        db.commit()
        return [str(task.id) for task in tasks]


def test_create_is_committed_and_survives_new_application_instance(auth_context):
    client, engine, user_id, handle, _ = auth_context
    saved = create(client, "  Synthetic request  ", "  Synthetic description  ")
    assert saved["title"] == "Synthetic request"
    assert saved["description"] == "Synthetic description"
    assert saved["creator_handle"] == handle
    assert saved["status"] == "new" and saved["tasks"] == []
    assert saved["created_at"] and saved["updated_at"]
    with Session(engine) as independent:
        assert independent.get(CustomerRequest, UUID(saved["id"])).creator_id == user_id
    with TestClient(create_app(engine)) as restarted:
        restarted.cookies.update(client.cookies)
        assert restarted.get(f"/api/v1/requests/{saved['id']}").json() == saved


def test_exact_input_limits_and_maximum_page_size(auth_context):
    client, engine, user_id, handle, _ = auth_context
    saved = create(client, "x" * 200, "x" * 5000)
    assert len(saved["description"]) == 5000
    with Session(engine) as db:
        db.add_all([CustomerRequest(title=f"Synthetic page fixture {index}", description="Synthetic only",
                                   creator_id=user_id, creator_handle=handle) for index in range(50)])
        db.commit()
    result = client.get("/api/v1/requests?limit=50").json()
    assert result["total"] == 51 and len(result["items"]) == 50
    assert len(client.get("/api/v1/requests?limit=50&offset=50").json()["items"]) == 1


@pytest.mark.parametrize("payload", [
    {}, {"title": "valid"}, {"title": " ", "description": "valid"},
    {"title": "valid", "description": "\t"}, {"title": "x" * 201, "description": "valid"},
    {"title": "valid", "description": "x" * 5001}, {"title": 1, "description": "valid"},
    {"title": "valid", "description": "valid", "creator_handle": "forged"},
    {"title": "valid", "description": "valid", "tasks": []},
])
def test_invalid_create_has_no_database_effect(auth_context, payload):
    client, engine, _, _, _ = auth_context
    with Session(engine) as db:
        before = db.scalar(select(func.count()).select_from(CustomerRequest))
    assert client.post("/api/v1/requests", json=payload).status_code == 422
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(CustomerRequest)) == before


def test_stable_pagination_and_status_filters(auth_context):
    client, engine, _, _, _ = auth_context
    ids = [create(client, f"Synthetic request {index}")["id"] for index in range(3)]
    with Session(engine) as db:
        for request_id in ids:
            db.get(CustomerRequest, UUID(request_id)).created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        db.commit()
    expected = sorted(ids, reverse=True)
    first = client.get("/api/v1/requests?limit=2&offset=0&status=new").json()
    second = client.get("/api/v1/requests?limit=2&offset=2&status=new").json()
    assert first["total"] == second["total"] == 3
    assert [row["id"] for row in first["items"] + second["items"]] == expected
    assert client.get("/api/v1/requests?offset=10000").json()["items"] == []
    assert client.get("/api/v1/requests?status=awaiting_review").json()["total"] == 0
    assert client.get("/api/v1/requests?status=completed").json()["total"] == 0


@pytest.mark.parametrize("query", ["limit=0", "limit=51", "offset=-1", "offset=10001", "status=invalid", "limit=abc"])
def test_invalid_pagination_or_filter_is_422(auth_context, query):
    assert auth_context[0].get(f"/api/v1/requests?{query}").status_code == 422


def test_task_updates_are_persisted_idempotent_and_derive_request_status(auth_context):
    client, engine, _, _, _ = auth_context
    request_id = create(client)["id"]
    tasks = seed_tasks(engine, request_id)
    endpoint = f"/api/v1/requests/{request_id}"
    assert client.get(endpoint).json()["status"] == "in_progress"
    assert client.get("/api/v1/requests?status=in_progress").json()["total"] == 1
    for task_id in tasks:
        result = client.patch(f"{endpoint}/tasks/{task_id}", json={"state": "done"})
        assert result.status_code == 200
        assert result.json()["state"] == "done"
    detail = client.get(endpoint).json()
    assert detail["status"] == "completed"
    assert all(task["state"] == "done" for task in detail["tasks"])
    assert client.get("/api/v1/requests?status=completed").json()["total"] == 1
    assert client.get("/api/v1/requests?status=in_progress").json()["total"] == 0
    repeated = client.patch(f"{endpoint}/tasks/{tasks[0]}", json={"state": "done"})
    assert repeated.json()["updated_at"] == next(task for task in detail["tasks"] if task["id"] == tasks[0])["updated_at"]
    assert client.patch(f"{endpoint}/tasks/{tasks[0]}", json={"state": "open"}).status_code == 200
    assert client.get(endpoint).json()["status"] == "in_progress"
    with Session(engine) as independent:
        assert independent.get(Task, UUID(tasks[0])).state == "open"
        assert independent.get(Task, UUID(tasks[1])).state == "done"


def test_missing_malformed_immutable_and_task_validation(auth_context):
    client, engine, _, _, _ = auth_context
    request_id = create(client)["id"]
    task_id = seed_tasks(engine, request_id)[0]
    endpoint = f"/api/v1/requests/{request_id}"
    assert client.get(f"/api/v1/requests/{uuid4()}").status_code == 404
    assert client.get("/api/v1/requests/not-a-uuid").status_code == 422
    assert client.patch(endpoint, json={"title": "edited"}).status_code == 405
    assert client.delete(endpoint).status_code == 405
    assert client.post(f"{endpoint}/tasks", json={"title": "unapproved"}).status_code == 404
    assert client.patch(f"{endpoint}/tasks/{task_id}", json={"state": "invalid"}).status_code == 422
    assert client.patch(f"{endpoint}/tasks/{task_id}", json={"state": "done", "priority": "high"}).status_code == 422
    assert client.patch(f"{endpoint}/tasks/{uuid4()}", json={"state": "done"}).status_code == 404
    other = create(client)["id"]
    assert client.patch(f"/api/v1/requests/{other}/tasks/{task_id}", json={"state": "done"}).status_code == 404


def test_auth_csrf_origin_and_operations_boundaries(auth_context, monkeypatch):
    client, engine, _, _, _ = auth_context
    request_id = create(client)["id"]
    task_id = seed_tasks(engine, request_id)[0]
    task_url = f"/api/v1/requests/{request_id}/tasks/{task_id}"
    token = secrets.token_urlsafe(32)
    monkeypatch.setenv("OPS_TOKEN", token)
    with TestClient(create_app(engine)) as anonymous:
        for url in ("/api/v1/requests", f"/api/v1/requests/{request_id}"):
            assert anonymous.get(url).status_code == 401
        assert anonymous.post("/api/v1/requests", json={"title": "valid", "description": "valid"}).status_code == 401
        assert anonymous.patch(task_url, json={"state": "done"}).status_code == 401
        assert anonymous.post("/api/v1/requests", json={"title": "valid", "description": "valid"},
                              headers={"Authorization": f"Bearer {token}"}).status_code == 401
    for headers in ({"X-CSRF-Token": ""}, {"Origin": "https://evil.invalid"}):
        assert client.post("/api/v1/requests", json={"title": "valid", "description": "valid"}, headers=headers).status_code == 403
        assert client.patch(task_url, json={"state": "done"}, headers=headers).status_code == 403
    with Session(engine) as db:
        assert db.get(Task, UUID(task_id)).state == "open"
        assert db.scalar(select(func.count()).select_from(CustomerRequest)) == 1


@pytest.mark.parametrize("override", [{"state": "bad"}, {"priority": "urgent"}, {"suggestion_index": 5},
                                     {"title": " "}, {"rationale": ""}])
def test_task_database_constraints(auth_context, override):
    client, engine, _, _, _ = auth_context
    request_id = create(client)["id"]
    values = dict(request_id=UUID(request_id), analysis_id=uuid4(), suggestion_index=0,
                  title="Synthetic approved fixture", rationale="Synthetic rationale", priority="low", state="open")
    with Session(engine) as db:
        db.add(Task(**(values | override)))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_duplicate_source_suggestion_is_rejected(auth_context):
    client, engine, _, _, _ = auth_context
    request_id = create(client)["id"]
    tasks = seed_tasks(engine, request_id)
    with Session(engine) as db:
        original = db.get(Task, UUID(tasks[0]))
        db.add(Task(request_id=original.request_id, analysis_id=original.analysis_id,
                    suggestion_index=original.suggestion_index, title="Duplicate", rationale="Synthetic", priority="low"))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_demo_accounts_share_workspace_permissions(auth_context):
    client, engine, _, _, password = auth_context
    request_id = create(client)["id"]
    task_id = seed_tasks(engine, request_id)[0]
    with Session(engine) as db:
        other = DemoUser(handle="second_" + secrets.token_hex(8), password_hash=hash_password(password))
        db.add(other)
        db.commit()
        other_id, handle = other.id, other.handle
    try:
        with TestClient(create_app(engine)) as second:
            identity = second.post("/api/v1/auth/login", json={"handle": handle, "password": password},
                                   headers={"Origin": "http://testserver"}).json()
            second.headers.update({"Origin": "http://testserver", "X-CSRF-Token": identity["csrf_token"]})
            assert second.get(f"/api/v1/requests/{request_id}").status_code == 200
            assert second.patch(f"/api/v1/requests/{request_id}/tasks/{task_id}", json={"state": "done"}).status_code == 200
    finally:
        with Session(engine) as db:
            db.delete(db.get(DemoUser, other_id))
            db.commit()
