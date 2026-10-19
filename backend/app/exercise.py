"""Development-only, prior-authorized single flag reset; no general repair API."""
import hmac
import os
from pathlib import Path
import threading
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.analysis import execute_analysis, now
from app.models import AnalysisRun, CustomerRequest, DemoUser, Task
from sqlalchemy import func, select


class Scope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exercise_id: UUID
    environment: Literal["development"]
    flag: Literal["analysis_disabled"]
    request_id: UUID
    verification_request_id: UUID
    user_id: UUID
    expires_at: AwareDatetime
    max_failures: int = Field(default=40, ge=5, le=40)


class Incident(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exercise_id: UUID
    fingerprint: str = Field(pattern=r"^[0-9a-f]{16}$")
    starts_at: AwareDatetime


def credential(request, name):
    location = os.getenv(name, "")
    secret = Path(location).read_text().strip() if location else ""
    if len(secret) < 32 or not hmac.compare_digest(
            request.headers.get("authorization", "").encode(), ("Bearer " + secret).encode()):
        raise HTTPException(403, "Forbidden")


def admin(request: Request):
    credential(request, "EXERCISE_ADMIN_TOKEN_FILE")


def operator(request: Request):
    credential(request, "ONCALL_OPS_TOKEN_FILE")


class ExerciseControl:
    def __init__(self):
        self.lock = threading.RLock()
        self.scope = None
        self.activated_at = None
        self.enabled = False
        self.failures = self.repairs = 0
        self.incident = None
        self.verification_started = False
        self.closed = False

    def development(self):
        if (self.closed or os.getenv("APP_ENV") != "development" or os.getenv("ENABLE_ONCALL_EXERCISE", "false") != "true"
                or os.getenv("MODEL_MODE", "simulated") != "simulated"):
            raise HTTPException(403, "Development exercise disabled")

    def active(self):
        self.development()
        if self.scope is None or now() >= self.scope.expires_at:
            raise HTTPException(409, "Authorization missing or expired")

    def authorize(self, scope, engine):
        with self.lock:
            self.development()
            stamp = now()
            if not 30 <= (scope.expires_at - stamp).total_seconds() <= 240:
                raise HTTPException(422, "Authorization must expire within 30 to 240 seconds")
            if self.scope is not None:
                raise HTTPException(409, "One exercise per process; disable and restart before another")
            with Session(engine) as db:
                user = db.get(DemoUser, scope.user_id)
                records = [db.get(CustomerRequest, key) for key in (scope.request_id, scope.verification_request_id)]
                if (scope.request_id == scope.verification_request_id or not user or not user.active
                        or not user.handle.startswith("alert_verify_")
                        or any(not r or r.creator_id != user.id or not r.title.startswith("Synthetic ") for r in records)
                        or db.scalar(select(func.count()).select_from(Task).where(Task.request_id.in_(
                            [scope.request_id, scope.verification_request_id]))) != 0
                        or db.scalar(select(func.count()).select_from(AnalysisRun).where(AnalysisRun.request_id.in_(
                            [scope.request_id, scope.verification_request_id]))) != 0):
                    raise HTTPException(422, "Scope must contain two owned synthetic requests with no tasks")
            self.scope, self.activated_at, self.enabled = scope, stamp, True

    def check(self, request_id, user):
        with self.lock:
            if not self.enabled or not self.scope or request_id != self.scope.request_id or user.id != self.scope.user_id:
                return
            try:
                self.active()
            except HTTPException:
                # Expired scope cannot keep producing failures or authorize repair.
                self.enabled = False
                return
            if self.failures >= self.scope.max_failures:
                self.enabled = False
                return
            self.failures += 1
            raise HTTPException(503, "Synthetic development analysis unavailable")

    def validate_incident(self, incident):
        self.active()
        if (incident.exercise_id != self.scope.exercise_id or incident.starts_at < self.activated_at
                or incident.starts_at > now() or (now() - incident.starts_at).total_seconds() > 240):
            raise HTTPException(409, "Incident outside authorized scope")

    def diagnose(self):
        with self.lock:
            self.active()
            return {"environment": "development", "exercise_id": str(self.scope.exercise_id),
                    "flag": "analysis_disabled", "cause": "analysis_disabled" if self.enabled and self.failures >= 5 else "unknown",
                    "expires_at": self.scope.expires_at.isoformat(), "activated_at": self.activated_at.isoformat(),
                    "failures": self.failures, "repairs": self.repairs}

    def clear(self, incident):
        with self.lock:
            self.validate_incident(incident)
            if not self.enabled or self.failures < 5 or self.repairs or self.incident:
                raise HTTPException(409, "Known active flag and unused authorization required")
            self.incident = incident
            self.enabled, self.repairs = False, 1
            return {"action": "clear_analysis_disabled", "repairs": 1}


router = APIRouter(prefix="/api/v1/ops/exercise")


@router.post("/authorize", dependencies=[Depends(admin)])
def authorize(scope: Scope, request: Request):
    request.app.state.exercise.authorize(scope, request.app.state.engine)
    return {"status": "authorized", "exercise_id": str(scope.exercise_id)}


@router.delete("", dependencies=[Depends(admin)])
def disable(request: Request):
    control = request.app.state.exercise
    with control.lock:
        control.enabled = False
        control.scope = None
        # Prevent reauthorization in the same process after cleanup.
        control.closed = True
    return {"status": "disabled"}


@router.get("/diagnostics", dependencies=[Depends(operator)])
def diagnostics(request: Request):
    return request.app.state.exercise.diagnose()


@router.post("/clear", dependencies=[Depends(operator)])
def clear(incident: Incident, request: Request):
    return request.app.state.exercise.clear(incident)


@router.post("/verify", dependencies=[Depends(operator)])
async def verify(incident: Incident, request: Request):
    control = request.app.state.exercise
    with control.lock:
        control.validate_incident(incident)
        if control.incident != incident or control.enabled or control.repairs != 1 or control.verification_started:
            raise HTTPException(409, "One verification after the authorized repair is required")
        control.verification_started = True
        scope = control.scope
        remaining = min(30, (scope.expires_at - now()).total_seconds())
    if remaining <= 0:
        raise HTTPException(409, "Authorization expired")
    run = await execute_analysis(request.app.state.engine, request.app.state.model_adapter,
                                 scope.verification_request_id, scope.user_id, scope.exercise_id,
                                 timeout_seconds=remaining)
    with Session(request.app.state.engine) as db:
        tasks = db.scalar(select(func.count()).select_from(Task).where(Task.request_id.in_(
            [scope.request_id, scope.verification_request_id])))
    return {"recovered": run.state == "pending" and tasks == 0, "state": run.state,
            "suggestion_count": len(run.proposal["tasks"]) if run.proposal else 0, "active_tasks": tasks}
