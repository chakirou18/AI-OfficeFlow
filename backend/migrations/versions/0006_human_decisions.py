"""Persist the human decision in the same transaction as approved tasks."""
from alembic import op
import sqlalchemy as sa

revision = "0006_human_decisions"
down_revision = "0005_model_metadata"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("analysis_runs", sa.Column("decided_by", sa.Uuid(), nullable=True))
    op.add_column("analysis_runs", sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("analysis_runs", sa.Column("rejection_reason", sa.String(1000), nullable=True))
    op.create_foreign_key("analysis_decided_by_fkey", "analysis_runs", "demo_users", ["decided_by"], ["id"])
    op.create_check_constraint("analysis_decision_identity", "analysis_runs",
        "(state IN ('approved', 'rejected') AND decided_by IS NOT NULL AND decided_at IS NOT NULL) OR "
        "(state NOT IN ('approved', 'rejected') AND decided_by IS NULL AND decided_at IS NULL AND rejection_reason IS NULL)")
    op.create_check_constraint("analysis_rejection_reason", "analysis_runs",
        "(state = 'rejected' AND rejection_reason IS NOT NULL AND length(btrim(rejection_reason)) BETWEEN 1 AND 1000) OR "
        "(state <> 'rejected' AND rejection_reason IS NULL)")


def downgrade():
    op.drop_constraint("analysis_rejection_reason", "analysis_runs", type_="check")
    op.drop_constraint("analysis_decision_identity", "analysis_runs", type_="check")
    op.drop_constraint("analysis_decided_by_fkey", "analysis_runs", type_="foreignkey")
    op.drop_column("analysis_runs", "rejection_reason")
    op.drop_column("analysis_runs", "decided_at")
    op.drop_column("analysis_runs", "decided_by")
