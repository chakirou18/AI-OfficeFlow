"""One bounded, synchronous HTTP analysis journey; no queue or task-write path."""
import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy import Engine, func, select, text, update
from sqlalchemy.orm import Session

from app.auth import current_user, require_mutation
from app.model_adapter import InvalidModelOutput, ModelAdapter, Proposal
from app.models import AnalysisRun, CustomerRequest, DemoUser, Task

DEADLINE_SECONDS = 30


def now():
    return datetime.now(timezone.utc)


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    request_id: UUID
    state: str
    provider_mode: str
    provider_model: str | None
    schema_version: str
    prompt_version: str
    proposal: Proposal | None
    error_code: str | None
    started_at: datetime
    deadline_at: datetime
    ended_at: datetime | None


def expire_interrupted(db: Session, request_id: UUID):
    stamp = now()
    db.execute(update(AnalysisRun).where(AnalysisRun.request_id == request_id,
               AnalysisRun.state == "running", AnalysisRun.deadline_at <= stamp)
               .values(state="failed", error_code="interrupted", ended_at=stamp))


def lock_request(db: Session, request_id: UUID):
    record = db.scalar(select(CustomerRequest).where(CustomerRequest.id == request_id).with_for_update())
    if record is None:
        raise HTTPException(404, "Request not found")
    return record


def begin_attempt(engine: Engine, request_id: UUID, user_id: UUID, key: UUID, seconds: float, adapter=None):
    with Session(engine, expire_on_commit=False) as db:
        record = lock_request(db, request_id)
        expire_interrupted(db, request_id)
        existing = db.scalar(select(AnalysisRun).where(AnalysisRun.request_id == request_id, AnalysisRun.idempotency_key == key))
        if existing:
            db.commit()
            return existing, None
        if db.scalar(select(AnalysisRun.id).where(AnalysisRun.request_id == request_id,
                     AnalysisRun.state.in_(["running", "pending", "approved"]))) or db.scalar(select(Task.id).where(Task.request_id == request_id).limit(1)):
            raise HTTPException(409, "This request already has an active analysis or approved tasks")
        stamp = now()
        mode = getattr(adapter, "provider_mode", "simulated")
        if mode == "ollama":
            # Serialize real-call reservation across processes; consume before dispatch.
            db.execute(text("SELECT pg_advisory_xact_lock(101010)"))
            used = db.scalar(select(func.count()).select_from(AnalysisRun).where(AnalysisRun.provider_mode == "ollama"))
            if used >= adapter.max_calls:
                raise HTTPException(429, "Local model call allowance exhausted")
            if db.scalar(select(AnalysisRun.id).where(AnalysisRun.provider_mode == "ollama",
                         AnalysisRun.state == "running", AnalysisRun.deadline_at > stamp).limit(1)):
                raise HTTPException(429, "Local model is busy; retry explicitly later")
        run = AnalysisRun(request_id=request_id, requested_by=user_id, idempotency_key=key,
                          provider_mode=mode, provider_model=getattr(adapter, "provider_model", None),
                          prompt_version=getattr(adapter, "prompt_version", "offline-v1"),
                          state="running", started_at=stamp, deadline_at=stamp + timedelta(seconds=seconds))
        db.add(run)
        db.commit()
        return run, (record.title, record.description)


def finish_attempt(engine: Engine, run: AnalysisRun, proposal: Proposal | None, error: str | None):
    with Session(engine, expire_on_commit=False) as db:
        record = lock_request(db, run.request_id)
        stored = db.get(AnalysisRun, run.id)
        if stored.state != "running":
            return stored  # A late result cannot resurrect an expired/interrupted run.
        stamp = now()
        if stamp >= stored.deadline_at and error is None:
            error = "timeout"
        stored.ended_at = stamp
        stored.error_code = error
        stored.state = "failed" if error else "pending"
        stored.proposal = proposal.model_dump() if proposal and not error else None
        record.updated_at = stamp
        db.commit()
        return stored


async def execute_analysis(engine: Engine, adapter: ModelAdapter, request_id: UUID, user_id: UUID,
                           key: UUID, *, timeout_seconds: float = DEADLINE_SECONDS) -> AnalysisRun:
    if not 0 < timeout_seconds <= DEADLINE_SECONDS:
        raise ValueError("Analysis deadline must be within 30 seconds")
    run, content = begin_attempt(engine, request_id, user_id, key, timeout_seconds, adapter)
    if content is None:
        return run
    proposal, error = None, None
    try:
        # No database session/transaction is held across the cancellable model call.
        remaining = max(0, (run.deadline_at - now()).total_seconds())
        async with asyncio.timeout(remaining):
            proposal = Proposal.model_validate(await adapter.analyze(*content))
    except TimeoutError:
        error = "timeout"
    except (ValidationError, InvalidModelOutput):
        error = "invalid_output"
    except asyncio.CancelledError:
        finish_attempt(engine, run, None, "interrupted")
        raise
    except Exception:
        error = "provider_error"  # Never persist/log provider text, prompts or credentials.
    return finish_attempt(engine, run, proposal, error)


router = APIRouter(prefix="/api/v1/requests", dependencies=[Depends(current_user)])


@router.get("/analysis/config")
def analysis_config(request: Request):
    adapter = request.app.state.model_adapter
    return {"provider_mode": adapter.provider_mode, "provider_model": adapter.provider_model}


@router.post("/{request_id}/analyses", response_model=AnalysisResponse, status_code=201)
async def analyze(request_id: UUID, request: Request, idempotency_key: UUID = Header(),
                  user: DemoUser = Depends(require_mutation)):
    run = await execute_analysis(request.app.state.engine, request.app.state.model_adapter, request_id, user.id, idempotency_key)
    payload = AnalysisResponse.model_validate(run).model_dump(mode="json")
    if run.state == "failed":
        return JSONResponse(status_code=504 if run.error_code == "timeout" else 502, content=payload)
    return JSONResponse(status_code=202 if run.state == "running" else 201, content=payload)


@router.get("/{request_id}/analyses", response_model=list[AnalysisResponse])
def history(request_id: UUID, request: Request, limit: int = Query(20, ge=1, le=50), offset: int = Query(0, ge=0, le=10000)):
    with Session(request.app.state.engine) as db:
        lock_request(db, request_id)
        expire_interrupted(db, request_id)
        db.commit()
        rows = db.scalars(select(AnalysisRun).where(AnalysisRun.request_id == request_id)
                          .order_by(AnalysisRun.started_at.desc(), AnalysisRun.id.desc()).limit(limit).offset(offset)).all()
        return [AnalysisResponse.model_validate(row) for row in rows]
