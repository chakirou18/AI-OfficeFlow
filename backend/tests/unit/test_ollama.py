import asyncio
import json
from pathlib import Path

import httpx
import pytest

from app.model_adapter import InvalidModelOutput, OfflineAdapter, OllamaAdapter, Proposal, configured_adapter

FIXTURES = json.loads((Path(__file__).parents[1] / "fixtures/ollama_evaluations.json").read_text())
VALID = {"summary": "Synthetic proposal; timing and resources are unknown.", "tasks": [
    {"title": "Clarify scope", "priority": "medium", "rationale": "Confirm unspecified details with a human."}]}


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda item: item["id"])
def test_mocked_provider_evaluation(fixture):
    """Transport fixtures verify the real adapter protocol, never real AI quality."""
    calls = []

    async def handler(request):
        calls.append(request)
        body = json.loads(request.content)
        assert request.url == "http://localhost:11434/api/generate"
        assert body["model"] == "llama3.2:3b" and body["stream"] is False
        assert body["options"] == {"temperature": 0, "seed": 0, "num_ctx": 4096, "num_predict": 512}
        assert body["format"] == Proposal.model_json_schema()
        assert json.loads(body["prompt"]) == {"title": fixture["title"], "description": fixture["description"]}
        assert "untrusted" in body["system"] and "No tools exist" in body["system"]
        case = fixture["case"]
        if case == "unavailable":
            return httpx.Response(503, text="private provider details")
        if case == "timeout":
            raise httpx.ReadTimeout("private timeout details")
        payload = json.loads(json.dumps(VALID))
        if case == "empty":
            payload["tasks"] = []
        if case == "priority":
            payload["tasks"][0]["priority"] = "urgent"
        if case == "extra":
            payload["approved"] = True
        envelope = {"model": "llama3.2:3b", "done": True,
                    "response": "not json" if case == "json" else json.dumps(payload)}
        if case == "truncated":
            envelope["done_reason"] = "length"
        return httpx.Response(200, json=envelope)

    adapter = OllamaAdapter("http://localhost:11434", transport=httpx.MockTransport(handler))
    if fixture["case"] == "valid":
        assert asyncio.run(adapter.analyze(fixture["title"], fixture["description"])) == VALID
    else:
        expected = httpx.HTTPStatusError if fixture["case"] == "unavailable" else TimeoutError if fixture["case"] == "timeout" else InvalidModelOutput
        with pytest.raises(expected):
            asyncio.run(adapter.analyze(fixture["title"], fixture["description"]))
    assert len(calls) == 1  # No hidden retries/fallback.


@pytest.mark.parametrize("url", ["https://ollama.com:11434", "http://example.com:11434",
    "http://localhost:11434/other", "http://user:secret@localhost:11434", "http://localhost:80",
    "http://localhost:11434?url=other"])
def test_remote_and_credential_urls_are_denied(url):
    with pytest.raises(ValueError):
        OllamaAdapter(url)


@pytest.mark.parametrize("envelope", [[], {}, {"done": False},
    {"model": "another-model", "done": True, "response": json.dumps(VALID)},
    {"model": "llama3.2:3b", "done": True, "response": {}},
    {"model": "llama3.2:3b", "done": True, "response": "x" * 33000}])
def test_invalid_or_oversized_envelope(envelope):
    adapter = OllamaAdapter("http://localhost:11434", transport=httpx.MockTransport(
        lambda _: httpx.Response(200, json=envelope)))
    with pytest.raises(InvalidModelOutput):
        asyncio.run(adapter.analyze("Synthetic", "Synthetic context"))


def test_default_mode_and_fail_closed_configuration(monkeypatch):
    monkeypatch.delenv("MODEL_MODE", raising=False)
    assert isinstance(configured_adapter(), OfflineAdapter)
    monkeypatch.setenv("MODEL_MODE", "ollama")
    assert isinstance(configured_adapter(), OllamaAdapter)
    monkeypatch.setenv("OLLAMA_MAX_CALLS", "0")
    with pytest.raises(ValueError):
        configured_adapter()
    monkeypatch.setenv("MODEL_MODE", "paid-fallback")
    with pytest.raises(ValueError):
        configured_adapter()


def test_redirect_is_not_followed():
    calls = []

    def redirect(request):
        calls.append(request)
        return httpx.Response(302, headers={"Location": "https://example.invalid"})

    adapter = OllamaAdapter("http://localhost:11434", transport=httpx.MockTransport(redirect))
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(adapter.analyze("Synthetic", "Synthetic context"))
    assert len(calls) == 1
