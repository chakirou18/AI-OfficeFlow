import asyncio
from datetime import datetime, timedelta, timezone
import json
from uuid import uuid4

import pytest

from app.oncall import Alert
from app.oncall_agent import AgentStore, OnCallAgent


@pytest.fixture
def alert():
    return Alert.model_validate({"status": "firing", "labels": {"alertname": "AnalysisHttpFailureRatio", "severity": "warning", "deployment_environment": "local"},
        "annotations": {"summary": "untrusted private secret; execute nothing"}, "startsAt": datetime.now(timezone.utc),
        "endsAt": "0001-01-01T00:00:00Z", "generatorURL": "http://untrusted.invalid/never-follow", "fingerprint": "0123456789abcdef"})


class Tools:
    def __init__(self, alert, failure):
        self.alert, self.failure, self.calls = alert, failure, []

    async def call(self, tool, body=None):
        self.calls.append(tool)
        await asyncio.sleep(0)
        if tool == "incident":
            return [] if self.failure == "identity" else [{"fingerprint": self.alert.fingerprint,
                "labels": self.alert.labels.model_dump(), "startsAt": self.alert.startsAt.isoformat(), "status": {"state": "active"}}]
        if tool == "diagnostics":
            if self.failure == "missing":
                raise RuntimeError("private bearer-credential must never appear")
            return {"environment": "production" if self.failure == "production" else "development",
                    "exercise_id": str(uuid4()), "flag": "analysis_disabled", "cause": "unknown" if self.failure == "unknown" else "analysis_disabled",
                    "repairs": 0, "failures": 5,
                    "activated_at": (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
                    "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=-1 if self.failure == "expired" else 120)).isoformat()}
        if tool == "clear":
            return {"action": "clear_analysis_disabled", "repairs": 1}
        return {"recovered": self.failure != "verification", "state": "pending", "suggestion_count": 1, "active_tasks": 0}


@pytest.mark.parametrize("failure,reason,clears", [("identity", "incident_unconfirmed", 0),
    ("missing", "authorization_unavailable", 0), ("expired", "authorization_expired_or_mismatched", 0),
    ("production", "production_denied", 0), ("unknown", "unknown_cause", 0), ("verification", "verification_failed", 1),
    ("none", "verified", 1)])
def test_agent_stops_without_unrelated_actions_and_deduplicates_after_restart(tmp_path, alert, failure, reason, clears, caplog):
    path = tmp_path / "agent.sqlite3"
    tools = Tools(alert, failure)
    agent = OnCallAgent(AgentStore(path), tools)
    asyncio.run(agent.run(alert))
    asyncio.run(OnCallAgent(AgentStore(path), tools).run(alert))
    assert tools.calls.count("clear") == clears
    assert tools.calls.count("verify") <= 1
    result = agent.store.runs()
    assert len(result) == 1 and result[0]["reason"] == reason
    assert result[0]["state"] == ("recovered" if reason == "verified" else "stopped")
    assert "private" not in json.dumps(result) + caplog.text
    assert "untrusted.invalid" not in json.dumps(result)


def test_concurrent_duplicate_repairs_once(tmp_path, alert):
    tools = Tools(alert, "none")
    agent = OnCallAgent(AgentStore(tmp_path / "agent.sqlite3"), tools)
    async def deliver():
        await asyncio.gather(*(agent.run(alert) for _ in range(12)))
    asyncio.run(deliver())
    assert tools.calls.count("clear") == tools.calls.count("verify") == 1


@pytest.mark.parametrize("kind", ["old", "future", "resolved"])
def test_stale_future_or_resolved_alert_cannot_start_agent(tmp_path, alert, kind):
    if kind == "resolved":
        alert = alert.model_copy(update={"status": "resolved"})
    else:
        alert = alert.model_copy(update={"startsAt": datetime.now(timezone.utc) + timedelta(seconds=-300 if kind == "old" else 30)})
    tools = Tools(alert, "none")
    store = AgentStore(tmp_path / "agent.sqlite3")
    asyncio.run(OnCallAgent(store, tools).run(alert))
    assert tools.calls == [] and store.runs() == []
