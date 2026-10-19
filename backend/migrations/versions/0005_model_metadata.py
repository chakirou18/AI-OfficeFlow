"""Record real provider model identity; preserve historical simulated runs."""
from alembic import op
import sqlalchemy as sa

revision = "0005_model_metadata"
down_revision = "0004_analysis"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("analysis_runs", sa.Column("provider_model", sa.String(64), nullable=True))


def downgrade():
    op.drop_column("analysis_runs", "provider_model")
