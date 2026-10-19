import asyncio
import json
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analysis import begin_attempt, execute_analysis
from app.model_adapter import OllamaAdapter
from app.models import AnalysisRun, Task

pytestmark = pytest.mark.integration


def new_request(client):
    return client.post("/api/v1/requests", json={"title": "Synthetic local model",
        "description": "Synthetic context; no execution authorized."}).json()["id"]


def adapter_for(case, calls):
    async def handler(request):
        calls.append(request)
        if case == "timeout":
            await asyncio.sleep(60)
        if case == "provider_error":
            return httpx.Response(503, text="private provider details")
        proposal = {"summary": "Synthetic transport fixture", "tasks": [] if case == "invalid_output" else [
            {"title": "Clarify synthetic scope", "priority": "low", "rationale": "Timing is unknown."}]}
        return httpx.Response(200, json={"model": "llama3.2:3b", "done": True, "response": json.dumps(proposal)})
    return OllamaAdapter("http://localhost:11434", max_calls=100, transport=httpx.MockTransport(handler))


@pytest.mark.parametrize("case", ["valid", "invalid_output", "provider_error", "timeout"])
def test_real_adapter_persistence_and_no_task_mutation(auth_context, case):
    client, engine, user_id, _, _ = auth_context
    calls = []
    adapter = adapter_for(case, calls)
    request_id = new_request(client)
    key = uuid4()
    run = asyncio.run(execute_analysis(engine, adapter, request_id, user_id, key, timeout_seconds=0.1))
    assert run.provider_mode == "ollama" and run.provider_model == "llama3.2:3b"
    assert run.prompt_version == "ollama-v2"
    assert run.state == ("pending" if case == "valid" else "failed")
    assert run.error_code == (None if case == "valid" else case)
    assert asyncio.run(execute_analysis(engine, adapter, request_id, user_id, key)).id == run.id
    assert len(calls) == 1
    history = client.get(f"/api/v1/requests/{request_id}/analyses")
    assert "private" not in history.text
    assert history.json()[0]["provider_model"] == "llama3.2:3b"
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Task)) == 0


def test_allowance_is_persisted_consumed_on_failure_and_replay_is_free(auth_context):
    client, engine, user_id, _, _ = auth_context
    calls = []
    adapter = adapter_for("provider_error", calls)
    adapter.max_calls = 1
    request_id = new_request(client)
    key = uuid4()
    failed = asyncio.run(execute_analysis(engine, adapter, request_id, user_id, key))
    assert failed.error_code == "provider_error"
    assert asyncio.run(execute_analysis(engine, adapter, request_id, user_id, key)).id == failed.id
    for target in (request_id, new_request(client)):
        with pytest.raises(HTTPException) as error:
            asyncio.run(execute_analysis(engine, adapter, target, user_id, uuid4()))
        assert error.value.status_code == 429
    assert len(calls) == 1
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(AnalysisRun).where(AnalysisRun.provider_mode == "ollama")) == 1


def test_global_real_call_reservation_blocks_another_request(auth_context):
    client, engine, user_id, _, _ = auth_context
    adapter = adapter_for("valid", [])
    begin_attempt(engine, new_request(client), user_id, uuid4(), 30, adapter)
    with pytest.raises(HTTPException) as error:
        begin_attempt(engine, new_request(client), user_id, uuid4(), 30, adapter)
    assert error.value.status_code == 429


def test_config_is_authenticated_and_discloses_mode(auth_context):
    client, _, _, _, _ = auth_context
    assert client.get("/api/v1/requests/analysis/config").json() == {"provider_mode": "simulated", "provider_model": None}
    client.app.state.model_adapter = adapter_for("valid", [])
    assert client.get("/api/v1/requests/analysis/config").json()["provider_mode"] == "ollama"
