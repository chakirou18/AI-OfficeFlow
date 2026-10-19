import asyncio
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.model_adapter import OfflineAdapter, Proposal
from app.requests import RequestInput

FIXTURES = json.loads((Path(__file__).parents[1] / "fixtures/analysis_requests.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("fixture", FIXTURES, ids=[str(index) for index in range(len(FIXTURES))])
def test_offline_fixtures_are_deterministic_and_untrusted_text_is_only_data(fixture):
    if not fixture["valid"]:
        with pytest.raises(ValidationError):
            RequestInput(title=fixture["title"], description=fixture["description"])
        return
    adapter = OfflineAdapter()
    first = asyncio.run(adapter.analyze(fixture["title"], fixture["description"]))
    assert first == asyncio.run(adapter.analyze(fixture["title"], fixture["description"]))
    result = Proposal.model_validate(first)
    assert 1 <= len(result.tasks) <= 5
    assert result.tasks[0].priority == "medium"
    assert "Simulated" in result.summary


@pytest.mark.parametrize("payload", [{"summary": "x", "tasks": []}, {"summary": " ", "tasks": []},
    {"summary": "x", "tasks": [{"title": "x", "priority": "urgent", "rationale": "x"}]},
    {"summary": "x", "tasks": [{"title": "x", "priority": "low", "rationale": "x", "approved": True}]}])
def test_invalid_model_output_is_rejected(payload):
    with pytest.raises(ValidationError):
        Proposal.model_validate(payload)
