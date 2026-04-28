"""cohort_results: replace table with id PK + JSONB data_id

Revision ID: c7e2f84d9a1b
Revises: b8f3a91c5d2e
Create Date: 2026-04-27 12:00:00.000000+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c7e2f84d9a1b"
down_revision = "b8f3a91c5d2e"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("cohort_results")
    op.create_table(
        "cohort_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "data_id",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "cohort_id",
            sa.Integer(),
            sa.ForeignKey("cohorts.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    op.create_index("ix_cohort_results_id", "cohort_results", ["id"])
    op.create_index("ix_cohort_results_cohort_id", "cohort_results", ["cohort_id"])


def downgrade():
    op.drop_table("cohort_results")
    op.create_table(
        "cohort_results",
        sa.Column("data_id", sa.Integer(), nullable=False),
        sa.Column(
            "cohort_id",
            sa.Integer(),
            sa.ForeignKey("cohorts.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("data_id", "cohort_id"),
    )
    op.create_index(
        "ix_cohort_results_data_id", "cohort_results", ["data_id"], unique=False
    )
