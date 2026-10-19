"""Human-only atomic decisions on one persisted pending proposal."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.analysis import AnalysisResponse, lock_request, now
from app.auth import require_mutation
from app.model_adapter import Proposal
from app.models import AnalysisRun, CustomerRequest, DemoUser, Task
from app.requests import RequestStatus, TaskResponse, status_expression


class DecisionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    decision: Literal["approve", "reject"]
    reason: str | None = Field(default=None, min_length=1, max_length=1000)

    @model_validator(mode="after")
    def require_rejection_reason(self):
        if (self.decision == "reject") != (self.reason is not None):
            raise ValueError("Rejection requires a reason; approval does not accept one")
        return self


class DecisionResponse(BaseModel):
    analysis: AnalysisResponse
    tasks: list[TaskResponse]
    status: RequestStatus


def decide_analysis(engine: Engine, request_id: UUID, analysis_id: UUID, user_id: UUID,
                    payload: DecisionInput) -> DecisionResponse:
    with Session(engine, expire_on_commit=False) as db:
        # Same lock order as analysis and task updates. Competing decisions serialize.
        record = lock_request(db, request_id)
        run = db.scalar(select(AnalysisRun).where(AnalysisRun.id == analysis_id,
                        AnalysisRun.request_id == request_id).with_for_update())
        if run is None:
            raise HTTPException(404, "Analysis not found")
        target = "approved" if payload.decision == "approve" else "rejected"
        if run.state in {"approved", "rejected"}:
            if run.state != target or run.rejection_reason != payload.reason:
                raise HTTPException(409, "This analysis already has a different decision")
            # Same decision is an idempotent replay; identity/timestamps stay original.
        elif run.state != "pending":
            raise HTTPException(409, "Only a pending analysis can be decided")
        else:
            if db.scalar(select(Task.id).where(Task.request_id == request_id).limit(1)):
                raise HTTPException(409, "This request already has approved tasks")
            if target == "approved":
                try:
                    proposal = Proposal.model_validate(run.proposal)
                except ValidationError:
                    raise HTTPException(409, "Stored proposal is invalid; approval denied") from None
                for index, suggestion in enumerate(proposal.tasks):
                    db.add(Task(request_id=request_id, analysis_id=analysis_id, suggestion_index=index,
                                **suggestion.model_dump(), state="open"))
            stamp = now()
            run.state, run.decided_by, run.decided_at = target, user_id, stamp
            run.rejection_reason = payload.reason
            record.updated_at = stamp
        db.flush()  # Any task/decision constraint failure rolls back the entire transaction.
        tasks = db.scalars(select(Task).where(Task.analysis_id == analysis_id,
                           Task.request_id == request_id).order_by(Task.suggestion_index)).all()
        status = db.scalar(select(status_expression()).select_from(CustomerRequest).where(CustomerRequest.id == request_id))
        result = DecisionResponse(analysis=AnalysisResponse.model_validate(run),
                                  tasks=[TaskResponse.model_validate(task) for task in tasks], status=status)
        db.commit()
        return result


router = APIRouter(prefix="/api/v1/requests")


@router.post("/{request_id}/analyses/{analysis_id}/decision", response_model=DecisionResponse)
def decide(request_id: UUID, analysis_id: UUID, payload: DecisionInput, request: Request,
           user: DemoUser = Depends(require_mutation)):
    return decide_analysis(request.app.state.engine, request_id, analysis_id, user.id, payload)
