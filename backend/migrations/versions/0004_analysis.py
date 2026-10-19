"""Bounded persisted analysis attempts; no task creation or approval."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_analysis"
down_revision = "0003_requests"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("request_id", sa.Uuid(), sa.ForeignKey("requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requested_by", sa.Uuid(), sa.ForeignKey("demo_users.id"), nullable=False),
        sa.Column("idempotency_key", sa.Uuid(), nullable=False),
        sa.Column("state", sa.String(8), nullable=False),
        sa.Column("provider_mode", sa.String(16), nullable=False),
        sa.Column("schema_version", sa.String(16), nullable=False),
        sa.Column("prompt_version", sa.String(16), nullable=False),
        sa.Column("proposal", postgresql.JSONB(none_as_null=True)),
        sa.Column("error_code", sa.String(32)),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("request_id", "idempotency_key", name="unique_analysis_attempt_key"),
        sa.CheckConstraint("state IN ('running', 'pending', 'approved', 'rejected', 'failed')", name="analysis_state"),
        sa.CheckConstraint("deadline_at > started_at AND deadline_at <= started_at + interval '30 seconds'", name="analysis_deadline"),
        sa.CheckConstraint("state NOT IN ('pending', 'approved', 'rejected') OR proposal IS NOT NULL", name="analysis_proposal"),
        sa.CheckConstraint("state <> 'failed' OR error_code IS NOT NULL", name="analysis_failure"),
    )
    op.create_index("ix_analysis_runs_request_id", "analysis_runs", ["request_id"])
    op.create_index("unique_active_analysis", "analysis_runs", ["request_id"], unique=True,
                    postgresql_where=sa.text("state IN ('running', 'pending')"))


def downgrade():
    op.drop_table("analysis_runs")
