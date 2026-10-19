"""Opt-in, expiring, single synthetic request failure for local alert verification."""
import os
import threading
import time
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import CustomerRequest


class DevAnalysisFault:
    def __init__(self):
        configured = os.getenv("DEV_ANALYSIS_FAILURE_REQUEST_ID", "")
        if configured and (os.getenv("ENABLE_DEV_FAULTS", "false") != "true"
                           or os.getenv("APP_ENV", "") != "development"):
            raise ValueError("Fault injection requires explicit local development opt-in")
        self.request_id = UUID(configured) if configured else None
        self.until = time.monotonic() + 240
        self.remaining = 40
        self.lock = threading.Lock()
        if self.request_id and os.getenv("MODEL_MODE", "simulated") != "simulated":
            raise ValueError("Synthetic fault verification requires simulated mode")

    def check(self, engine, request_id, user):
        if request_id != self.request_id or not user.handle.startswith("alert_verify_"):
            return
        with Session(engine) as db:
            record = db.get(CustomerRequest, request_id)
            if not record or record.creator_id != user.id:
                return
        with self.lock:
            if self.remaining <= 0 or time.monotonic() >= self.until:
                return
            self.remaining -= 1
        raise HTTPException(503, "Synthetic development analysis unavailable")
