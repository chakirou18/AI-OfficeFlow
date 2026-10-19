"""T04-only connectivity evidence, deliberately separate from future requests."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, Uuid, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class FoundationCheck(Base):
    __tablename__ = "foundation_checks"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    marker: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DemoUser(Base):
    __tablename__ = "demo_users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    handle: Mapped[str] = mapped_column(String(40), unique=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_logins: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LoginSession(Base):
    __tablename__ = "login_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("demo_users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class CustomerRequest(Base):
    __tablename__ = "requests"
    __table_args__ = (
        CheckConstraint("length(btrim(title)) BETWEEN 1 AND 200", name="request_title_length"),
        CheckConstraint("length(btrim(description)) BETWEEN 1 AND 5000", name="request_description_length"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    creator_id: Mapped[UUID] = mapped_column(ForeignKey("demo_users.id"))
    creator_handle: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Task(Base):
    """Approved-task storage. API creation is exclusively future T11 approval."""
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("analysis_id", "suggestion_index", name="unique_approved_suggestion"),
        CheckConstraint("state IN ('open', 'done')", name="task_state"),
        CheckConstraint("priority IN ('low', 'medium', 'high')", name="task_priority"),
        CheckConstraint("suggestion_index BETWEEN 0 AND 4", name="task_suggestion_index"),
        CheckConstraint("length(btrim(title)) BETWEEN 1 AND 200", name="task_title_length"),
        CheckConstraint("length(btrim(rationale)) BETWEEN 1 AND 1000", name="task_rationale_length"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"), index=True)
    # Reserved source identity: FK will be added when analysis_runs exists in T09/T11.
    analysis_id: Mapped[UUID] = mapped_column(Uuid)
    suggestion_index: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    rationale: Mapped[str] = mapped_column(String(1000))
    priority: Mapped[str] = mapped_column(String(6))
    state: Mapped[str] = mapped_column(String(4), default="open", server_default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    __table_args__ = (
        UniqueConstraint("request_id", "idempotency_key", name="unique_analysis_attempt_key"),
        Index("unique_active_analysis", "request_id", unique=True,
              postgresql_where=text("state IN ('running', 'pending')")),
        CheckConstraint("state IN ('running', 'pending', 'approved', 'rejected', 'failed')", name="analysis_state"),
        CheckConstraint("deadline_at > started_at AND deadline_at <= started_at + interval '30 seconds'", name="analysis_deadline"),
        CheckConstraint("state NOT IN ('pending', 'approved', 'rejected') OR proposal IS NOT NULL", name="analysis_proposal"),
        CheckConstraint("state <> 'failed' OR error_code IS NOT NULL", name="analysis_failure"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"), index=True)
    requested_by: Mapped[UUID] = mapped_column(ForeignKey("demo_users.id"))
    idempotency_key: Mapped[UUID] = mapped_column(Uuid)
    state: Mapped[str] = mapped_column(String(8))
    provider_mode: Mapped[str] = mapped_column(String(16), default="simulated")
    provider_model: Mapped[str | None] = mapped_column(String(64))
    schema_version: Mapped[str] = mapped_column(String(16), default="proposal-v1")
    prompt_version: Mapped[str] = mapped_column(String(16), default="offline-v1")
    proposal: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True))
    error_code: Mapped[str | None] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
