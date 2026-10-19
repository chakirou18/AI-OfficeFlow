"""T04-only connectivity evidence, deliberately separate from future requests."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Uuid, func
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
