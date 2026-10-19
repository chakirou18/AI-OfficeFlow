from uuid import UUID, uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app.api import create_app
from app.models import Task

pytestmark = pytest.mark.integration


def test_dashboard_aggregates_persisted_state_and_refreshes_after_task_update(auth_context):
    client, engine, _, _, _ = auth_context
    empty = client.get("/api/v1/dashboard").json()
    assert empty["total_requests"] == empty["total_tasks"] == 0
    assert empty["recent_requests"] == empty["recent_tasks"] == []
    ids = [client.post("/api/v1/requests", json={"title": f"Synthetic {index}",
           "description": "Synthetic dashboard verification"}).json()["id"] for index in range(7)]
    with Session(engine) as db:
        source = uuid4()
        db.add_all([Task(request_id=UUID(ids[0]), analysis_id=source, suggestion_index=index,
                        title=f"Synthetic task {index}", rationale="Synthetic fixture only",
                        priority=priority, state=state) for index, (priority, state) in
                   enumerate([("high", "open"), ("medium", "done"), ("low", "done")])])
        db.commit()
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["total_requests"] == 7
    assert data["requests_by_status"] == {"new": 6, "in_progress": 1, "completed": 0, "awaiting_review": 0}
    assert (data["total_tasks"], data["open_tasks"], data["completed_tasks"]) == (3, 1, 2)
    assert len(data["recent_requests"]) == 5 and len(data["recent_tasks"]) == 3
    task = next(task for task in data["recent_tasks"] if task["state"] == "open")
    assert client.patch(f"/api/v1/requests/{ids[0]}/tasks/{task['id']}", json={"state": "done"}).status_code == 200
    updated = client.get("/api/v1/dashboard").json()
    assert updated["open_tasks"] == 0 and updated["completed_tasks"] == 3
    assert updated["requests_by_status"]["completed"] == 1
    assert updated["recent_tasks"][0]["id"] == task["id"]
    with TestClient(create_app(engine)) as anonymous:
        assert anonymous.get("/api/v1/dashboard").status_code == 401
