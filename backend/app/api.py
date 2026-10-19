"""Local foundation health and a fixed synthetic PostgreSQL round trip only."""

from contextlib import asynccontextmanager
from datetime import datetime
import logging
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Engine, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import build_engine
from app.models import FoundationCheck
from app.auth import current_user, require_mutation, router as auth_router
from app.requests import router as requests_router
from app.analysis import router as analysis_router
from app.decisions import router as decisions_router
from app.model_adapter import configured_adapter
from app.telemetry import Telemetry, TelemetryMiddleware, configured_telemetry
from app.dev_fault import DevAnalysisFault
from app.exercise import ExerciseControl, router as exercise_router

logger = logging.getLogger(__name__)


class CheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    marker: str
    created_at: datetime


def create_app(engine: Engine | None = None, *, telemetry: Telemetry | None = None) -> FastAPI:
    owns_engine = engine is None
    connection_engine = engine if engine is not None else build_engine()
    observer = telemetry if telemetry is not None else configured_telemetry()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        if observer and telemetry is None:
            observer.shutdown()
        if owns_engine:
            connection_engine.dispose()

    application = FastAPI(
        title="AI OfficeFlow",
        description="Authenticated synthetic demonstration API.",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
        lifespan=lifespan,
    )
    application.state.engine = connection_engine
    application.state.model_adapter = configured_adapter()
    application.state.telemetry = observer
    application.state.dev_analysis_fault = DevAnalysisFault()
    application.state.exercise = ExerciseControl()
    application.include_router(exercise_router)
    application.include_router(auth_router)
    application.include_router(requests_router)
    application.include_router(analysis_router)
    application.include_router(decisions_router)
    if observer:
        application.add_middleware(TelemetryMiddleware, observer=observer)

    @application.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @application.exception_handler(SQLAlchemyError)
    async def database_failure(_: Request, error: SQLAlchemyError) -> JSONResponse:
        # Never include driver messages, SQL, parameters or connection URLs.
        logger.warning("Database operation failed: %s", type(error).__name__)
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})

    @application.get("/api/v1/health/live")
    def liveness() -> dict[str, str]:
        return {"status": "ok", "service": "officeflow-api"}

    @application.get("/api/v1/health/ready")
    def readiness() -> dict[str, str]:
        with connection_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            connection.execute(select(FoundationCheck.id).limit(1))
        return {"status": "ok", "database": "ok", "migration": revision}

    @application.post(
        "/api/v1/foundation/checks", response_model=CheckResponse, status_code=201,
        dependencies=[Depends(require_mutation)],
    )
    def save_check() -> FoundationCheck:
        # Fixed synthetic payload, not a premature request-management endpoint.
        with Session(connection_engine, expire_on_commit=False) as session:
            record = FoundationCheck(marker="synthetic-foundation-check")
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    @application.get("/api/v1/foundation/checks/{check_id}", response_model=CheckResponse,
                     dependencies=[Depends(current_user)])
    def read_check(check_id: UUID) -> FoundationCheck:
        with Session(connection_engine) as session:
            record = session.get(FoundationCheck, check_id)
            if record is None:
                raise HTTPException(status_code=404, detail="Foundation check not found")
            return record

    return application
