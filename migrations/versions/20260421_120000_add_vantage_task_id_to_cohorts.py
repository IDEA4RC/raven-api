"""Add vantage_task_id to cohorts

Revision ID: c9f4b92d6e3f
Revises: b8f3a91c5d2e
Create Date: 2026-04-21 12:00:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c9f4b92d6e3f"
down_revision = "b8f3a91c5d2e"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("cohorts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("vantage_task_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_cohorts_vantage_task_id", ["vantage_task_id"])


def downgrade():
    with op.batch_alter_table("cohorts", schema=None) as batch_op:
        batch_op.drop_index("ix_cohorts_vantage_task_id")
        batch_op.drop_column("vantage_task_id")
