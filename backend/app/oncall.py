"""Private alert receipt only. No model, command runner or remediation capability."""
from datetime import datetime, timezone
import hmac
import os
from pathlib import Path
import sqlite3
import time
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Request
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, ValidationError, model_validator

MAX_BYTES, MAX_EVENTS, RETENTION_SECONDS = 65536, 500, 7 * 86400


class Labels(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alertname: Literal["AnalysisHttpFailureRatio"]
    severity: Literal["warning"]
    deployment_environment: Literal["local"]


class Alert(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["firing", "resolved"]
    labels: Labels
    annotations: dict[Annotated[str, Field(max_length=64)], Annotated[str, Field(max_length=512)]] = Field(max_length=4)
    startsAt: AwareDatetime
    endsAt: AwareDatetime
    generatorURL: str = Field(max_length=2048)
    fingerprint: str = Field(pattern=r"^[0-9a-f]{16}$")

    @model_validator(mode="after")
    def dates(self):
        active_zero_end = self.status == "firing" and self.endsAt == datetime.min.replace(tzinfo=timezone.utc)
        if self.endsAt < self.startsAt and not active_zero_end:
            raise ValueError("Invalid alert interval")
        return self


class Notification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal["4"]
    groupKey: str = Field(max_length=1024)
    truncatedAlerts: Literal[0]
    status: Literal["firing", "resolved"]
    receiver: Literal["oncall"]
    groupLabels: dict[str, str] = Field(max_length=3)
    commonLabels: Labels
    commonAnnotations: dict[Annotated[str, Field(max_length=64)], Annotated[str, Field(max_length=512)]] = Field(max_length=4)
    externalURL: str = Field(max_length=2048)
    alerts: list[Alert] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def consistent(self):
        if (self.status == "resolved" and any(a.status != "resolved" for a in self.alerts)):
            raise ValueError("Inconsistent status")
        if any(a.labels != self.commonLabels for a in self.alerts):
            raise ValueError("Inconsistent labels")
        return self


class ReceiptStore:
    def __init__(self, path):
        self.path = path
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS receipts (
                fingerprint TEXT NOT NULL, starts_at TEXT NOT NULL, status TEXT NOT NULL,
                received_at REAL NOT NULL, last_received_at REAL NOT NULL, deliveries INTEGER NOT NULL,
                ends_at TEXT NOT NULL, PRIMARY KEY(fingerprint, starts_at, status))""")

    def connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def record(self, notification):
        stamp, inserted = time.time(), 0
        with self.connect() as db:
            # Serialize pruning and inserts; cap includes a whole concurrent batch.
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM receipts WHERE last_received_at < ?", (stamp - RETENTION_SECONDS,))
            for alert in notification.alerts:
                start = alert.startsAt.astimezone(timezone.utc).isoformat()
                end = alert.endsAt.astimezone(timezone.utc).isoformat()
                # A delayed firing notification cannot resurrect a resolved incident.
                if alert.status == "firing" and db.execute(
                        "SELECT 1 FROM receipts WHERE fingerprint=? AND starts_at=? AND status='resolved'",
                        (alert.fingerprint, start)).fetchone():
                    continue
                inserted += db.execute("""INSERT OR IGNORE INTO receipts VALUES(?,?,?,?,?,1,?)""",
                    (alert.fingerprint, start, alert.status, stamp, stamp, end)).rowcount
                db.execute("""UPDATE receipts SET last_received_at=?, deliveries=min(deliveries+1,10000)
                    WHERE fingerprint=? AND starts_at=? AND status=? AND received_at<>?""",
                    (stamp, alert.fingerprint, start, alert.status, stamp))
            db.execute("""DELETE FROM receipts WHERE rowid IN (SELECT rowid FROM receipts
                ORDER BY last_received_at DESC, rowid DESC LIMIT -1 OFFSET ?)""", (MAX_EVENTS,))
        return inserted

    def events(self):
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            db.execute("DELETE FROM receipts WHERE last_received_at < ?", (time.time() - RETENTION_SECONDS,))
            return [dict(row) for row in db.execute("SELECT * FROM receipts ORDER BY received_at DESC LIMIT ?", (MAX_EVENTS,))]


def create_listener(*, token=None, path=None):
    secret = token if token is not None else Path(os.environ["ALERT_TOKEN_FILE"]).read_text().strip()
    if len(secret) < 32:
        raise ValueError("A separate private alert credential is required")
    store = ReceiptStore(path or os.getenv("ALERT_STORE_PATH", "/data/receipts.sqlite3"))
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    def authorize(request):
        supplied = request.headers.get("authorization", "")
        if not hmac.compare_digest(supplied.encode(), ("Bearer " + secret).encode()):
            raise HTTPException(403, "Forbidden")

    @app.get("/receipts")
    def receipts(request: Request):
        authorize(request)
        return {"events": store.events()}

    @app.post("/webhook")
    async def webhook(request: Request):
        authorize(request)
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > MAX_BYTES:
                raise HTTPException(413, "Payload too large")
            body.extend(chunk)
        try:
            notification = Notification.model_validate_json(body)
        except (ValidationError, ValueError):
            # Never echo Pydantic errors: they contain untrusted input values.
            raise HTTPException(422, "Invalid alert notification") from None
        accepted = store.record(notification)
        return {"accepted": accepted, "duplicates": len(notification.alerts) - accepted}

    return app
