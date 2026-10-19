"""Immutable requests and approved-task storage; no analysis/approval API yet."""
from alembic import op
import sqlalchemy as sa

revision = "0003_requests"
down_revision = "0002_auth"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("creator_id", sa.Uuid(), sa.ForeignKey("demo_users.id"), nullable=False),
        sa.Column("creator_handle", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(btrim(title)) BETWEEN 1 AND 200", name="request_title_length"),
        sa.CheckConstraint("length(btrim(description)) BETWEEN 1 AND 5000", name="request_description_length"),
    )
    op.create_index("ix_requests_created_at", "requests", ["created_at"])
    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("request_id", sa.Uuid(), sa.ForeignKey("requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("suggestion_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("rationale", sa.String(1000), nullable=False),
        sa.Column("priority", sa.String(6), nullable=False),
        sa.Column("state", sa.String(4), server_default="open", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("analysis_id", "suggestion_index", name="unique_approved_suggestion"),
        sa.CheckConstraint("state IN ('open', 'done')", name="task_state"),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high')", name="task_priority"),
        sa.CheckConstraint("suggestion_index BETWEEN 0 AND 4", name="task_suggestion_index"),
        sa.CheckConstraint("length(btrim(title)) BETWEEN 1 AND 200", name="task_title_length"),
        sa.CheckConstraint("length(btrim(rationale)) BETWEEN 1 AND 1000", name="task_rationale_length"),
    )
    op.create_index("ix_tasks_request_id", "tasks", ["request_id"])


def downgrade():
    op.drop_table("tasks")
    op.drop_table("requests")
