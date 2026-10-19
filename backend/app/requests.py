"""Authenticated shared synthetic workspace; no request edit or task creation route."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.auth import current_user, require_mutation
from app.models import AnalysisRun, CustomerRequest, DemoUser, Task
from app.analysis import AnalysisResponse, expire_interrupted

RequestStatus = Literal["new", "awaiting_review", "in_progress", "completed"]


class RequestInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state: Literal["open", "done"]


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    request_id: UUID
    analysis_id: UUID
    suggestion_index: int
    title: str
    rationale: str
    priority: Literal["low", "medium", "high"]
    state: Literal["open", "done"]
    created_at: datetime
    updated_at: datetime


class RequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    description: str
    creator_handle: str
    created_at: datetime
    updated_at: datetime
    status: RequestStatus


class RequestDetail(RequestResponse):
    tasks: list[TaskResponse]
    analysis: AnalysisResponse | None = None


class RequestPage(BaseModel):
    items: list[RequestResponse]
    total: int
    limit: int
    offset: int


def session(request: Request):
    with Session(request.app.state.engine) as db:
        yield db


def status_expression():
    has_open = select(Task.id).where(Task.request_id == CustomerRequest.id, Task.state == "open").exists()
    has_tasks = select(Task.id).where(Task.request_id == CustomerRequest.id).exists()
    has_pending = select(AnalysisRun.id).where(AnalysisRun.request_id == CustomerRequest.id, AnalysisRun.state == "pending").exists()
    return case((has_open, "in_progress"), (has_tasks, "completed"), (has_pending, "awaiting_review"), else_="new")


def serialize_request(record: CustomerRequest, status: str):
    return {key: getattr(record, key) for key in RequestResponse.model_fields if key != "status"} | {"status": status}


router = APIRouter(prefix="/api/v1", dependencies=[Depends(current_user)])


class DashboardResponse(BaseModel):
    total_requests: int
    requests_by_status: dict[RequestStatus, int]
    total_tasks: int
    open_tasks: int
    completed_tasks: int
    recent_requests: list[RequestResponse]
    recent_tasks: list[TaskResponse]


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: Session = Depends(session)):
    # A repeatable-read transaction keeps all aggregates/recent rows consistent.
    db.connection(execution_options={"isolation_level": "REPEATABLE READ"})
    derived = status_expression()
    counts = dict(db.execute(select(derived, func.count()).select_from(CustomerRequest).group_by(derived)).all())
    states = {state: counts.get(state, 0) for state in ("new", "awaiting_review", "in_progress", "completed")}
    task_counts = dict(db.execute(select(Task.state, func.count()).group_by(Task.state)).all())
    rows = db.execute(select(CustomerRequest, derived)
                      .order_by(CustomerRequest.created_at.desc(), CustomerRequest.id.desc()).limit(5)).all()
    return {
        "total_requests": sum(states.values()), "requests_by_status": states,
        "total_tasks": sum(task_counts.values()), "open_tasks": task_counts.get("open", 0),
        "completed_tasks": task_counts.get("done", 0),
        "recent_requests": [serialize_request(record, state) for record, state in rows],
        "recent_tasks": db.scalars(select(Task).order_by(Task.updated_at.desc(), Task.id.desc()).limit(5)).all(),
    }


@router.post("/requests", response_model=RequestDetail, status_code=201)
def create_request(payload: RequestInput, user: DemoUser = Depends(require_mutation), db: Session = Depends(session)):
    record = CustomerRequest(title=payload.title, description=payload.description,
                             creator_id=user.id, creator_handle=user.handle)
    db.add(record)
    db.commit()
    db.refresh(record)
    return serialize_request(record, "new") | {"tasks": []}


@router.get("/requests", response_model=RequestPage)
def list_requests(limit: int = Query(20, ge=1, le=50), offset: int = Query(0, ge=0, le=10000),
                  status: RequestStatus | None = None, db: Session = Depends(session)):
    derived = status_expression()
    statement = select(CustomerRequest, derived.label("status"))
    count = select(func.count()).select_from(CustomerRequest)
    if status:
        statement = statement.where(derived == status)
        count = count.where(derived == status)
    rows = db.execute(statement.order_by(CustomerRequest.created_at.desc(), CustomerRequest.id.desc())
                      .limit(limit).offset(offset)).all()
    return {"items": [serialize_request(record, state) for record, state in rows],
            "total": db.scalar(count), "limit": limit, "offset": offset}


@router.get("/requests/{request_id}", response_model=RequestDetail)
def request_detail(request_id: UUID, db: Session = Depends(session)):
    record = db.get(CustomerRequest, request_id)
    if not record:
        raise HTTPException(404, "Request not found")
    expire_interrupted(db, request_id)
    db.commit()
    analysis = db.scalar(select(AnalysisRun).where(AnalysisRun.request_id == request_id)
                         .order_by(AnalysisRun.started_at.desc(), AnalysisRun.id.desc()).limit(1))
    tasks = db.scalars(select(Task).where(Task.request_id == request_id)
                       .order_by(Task.created_at, Task.id)).all()
    # Derive from the returned task snapshot, even if a concurrent update commits.
    status = "in_progress" if any(task.state == "open" for task in tasks) else "completed" if tasks else "awaiting_review" if analysis and analysis.state == "pending" else "new"
    return serialize_request(record, status) | {"tasks": tasks, "analysis": analysis}


@router.patch("/requests/{request_id}/tasks/{task_id}", response_model=TaskResponse,
              dependencies=[Depends(require_mutation)])
def update_task(request_id: UUID, task_id: UUID, payload: TaskUpdate, db: Session = Depends(session)):
    # Serialize sibling task updates and future approval on the parent request.
    record = db.scalar(select(CustomerRequest).where(CustomerRequest.id == request_id).with_for_update())
    if not record:
        raise HTTPException(404, "Request not found")
    task = db.scalar(select(Task).where(Task.id == task_id, Task.request_id == request_id))
    if not task:
        raise HTTPException(404, "Task not found")
    if task.state != payload.state:
        task.state = payload.state
        task.updated_at = func.now()
        record.updated_at = func.now()
        db.commit()
        db.refresh(task)
    return task
