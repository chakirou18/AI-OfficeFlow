"""Deterministic custom agent: observe -> diagnose -> one authorized action -> verify.

Tools have fixed private endpoints, not shell/code/URL capabilities. No LLM is used.
"""
import asyncio
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import time

import httpx

LABELS = {"alertname": "AnalysisHttpFailureRatio", "severity": "warning", "deployment_environment": "local"}


class AgentStore:
    def __init__(self, path):
        self.path = path
        with self.connection() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS agent_runs (
                fingerprint TEXT, starts_at TEXT, created_at REAL, result TEXT,
                PRIMARY KEY(fingerprint, starts_at))""")

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.path, timeout=5)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def claim(self, alert):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM agent_runs WHERE created_at < ?", (time.time() - 7 * 86400,))
            changed = db.execute("INSERT OR IGNORE INTO agent_runs VALUES(?,?,?,?)",
                (alert.fingerprint, alert.startsAt.isoformat(), time.time(), json.dumps({"state": "running"}))).rowcount
            db.execute("""DELETE FROM agent_runs WHERE rowid IN (SELECT rowid FROM agent_runs
                ORDER BY created_at DESC,rowid DESC LIMIT -1 OFFSET 500)""")
        return bool(changed)

    def finish(self, alert, result):
        with self.connection() as db:
            db.execute("UPDATE agent_runs SET result=? WHERE fingerprint=? AND starts_at=?",
                       (json.dumps(result), alert.fingerprint, alert.startsAt.isoformat()))

    def runs(self):
        with self.connection() as db:
            db.execute("DELETE FROM agent_runs WHERE created_at < ?", (time.time() - 7 * 86400,))
            return [{"fingerprint": row[0], "starts_at": row[1], **json.loads(row[2])}
                    for row in db.execute("SELECT fingerprint,starts_at,result FROM agent_runs ORDER BY created_at DESC LIMIT 500")]


class PrivateTools:
    def __init__(self, token_file):
        self.secret = Path(token_file).read_text().strip()
        if len(self.secret) < 32:
            raise ValueError("Separate scoped on-call credential required")

    async def call(self, tool, body=None):
        method, url, timeout = {
            "incident": ("GET", "http://alertmanager:9093/api/v2/alerts", 5),
            "diagnostics": ("GET", "http://api:8000/api/v1/ops/exercise/diagnostics", 5),
            "clear": ("POST", "http://api:8000/api/v1/ops/exercise/clear", 5),
            "verify": ("POST", "http://api:8000/api/v1/ops/exercise/verify", 32),
        }[tool]
        headers = {} if tool == "incident" else {"Authorization": "Bearer " + self.secret}
        async with httpx.AsyncClient(trust_env=False, follow_redirects=False, timeout=timeout) as client:
            async with client.stream(method, url, headers=headers, json=body) as response:
                response.raise_for_status()
                raw = bytearray()
                async for chunk in response.aiter_bytes():
                    if len(raw) + len(chunk) > 65536:
                        raise ValueError("Diagnostic response too large")
                    raw.extend(chunk)
                return json.loads(raw)


class OnCallAgent:
    def __init__(self, store, tools):
        self.store, self.tools = store, tools

    async def run(self, alert):
        stamp = datetime.now(timezone.utc)
        if alert.status != "firing" or not 0 <= (stamp - alert.startsAt).total_seconds() <= 240:
            return
        if not self.store.claim(alert):
            return
        events = []

        def event(name):
            events.append({"event": name, "at": datetime.now(timezone.utc).isoformat()})
            # Persist each step; a process interruption never retries an action.
            self.store.finish(alert, {"state": "running", "agent": "python-oncall-v1", "events": events})

        reason, outcome = "incident_unconfirmed", "stopped"
        event("invoked")
        try:
            async with asyncio.timeout(45):
                incidents = await self.tools.call("incident")
                if not isinstance(incidents, list) or len(incidents) > 100 or not any(
                        a.get("fingerprint") == alert.fingerprint and a.get("labels") == LABELS
                        and datetime.fromisoformat(a["startsAt"].replace("Z", "+00:00")) == alert.startsAt
                        and a.get("status", {}).get("state") == "active" for a in incidents):
                    raise ValueError("Unconfirmed incident")
                event("incident_confirmed")
                reason = "authorization_unavailable"
                diagnostic = await self.tools.call("diagnostics")
                if diagnostic.get("environment") != "development":
                    reason = "production_denied"
                    raise ValueError("Environment denied")
                expiry = datetime.fromisoformat(diagnostic["expires_at"].replace("Z", "+00:00"))
                activated = datetime.fromisoformat(diagnostic["activated_at"].replace("Z", "+00:00"))
                if not activated <= alert.startsAt <= datetime.now(timezone.utc) < expiry:
                    reason = "authorization_expired_or_mismatched"
                    raise ValueError("Scope expired")
                if (diagnostic.get("cause") != "analysis_disabled" or diagnostic.get("flag") != "analysis_disabled"
                        or diagnostic.get("repairs") != 0 or diagnostic.get("failures", 0) < 5):
                    reason = "unknown_cause"
                    raise ValueError("Unknown cause")
                event("diagnosed_analysis_disabled")
                from uuid import UUID
                scope_id = str(UUID(diagnostic["exercise_id"]))
                incident = {"exercise_id": scope_id, "fingerprint": alert.fingerprint, "starts_at": alert.startsAt.isoformat()}
                reason = "repair_failed"
                repaired = await self.tools.call("clear", incident)
                if repaired != {"action": "clear_analysis_disabled", "repairs": 1}:
                    raise ValueError("Repair not confirmed")
                event("cleared_analysis_disabled")
                reason = "verification_failed"
                verified = await self.tools.call("verify", incident)
                if (verified.get("recovered") is not True or verified.get("state") != "pending"
                        or verified.get("active_tasks") != 0 or not 1 <= verified.get("suggestion_count", 0) <= 5):
                    raise ValueError("Recovery not verified")
                event("recovery_verified")
                outcome, reason = "recovered", "verified"
        except Exception:
            # Provider/HTTP/Pydantic errors may contain credentials or input. Never persist them.
            event("stopped")
        finally:
            self.store.finish(alert, {"state": outcome, "reason": reason, "agent": "python-oncall-v1", "events": events})
