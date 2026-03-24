"""Add task tracking columns to algorithms

Revision ID: b8f3a91c5d2e
Revises: 3a9d7b6f21c4
Create Date: 2026-03-16 12:00:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b8f3a91c5d2e"
down_revision = "3a9d7b6f21c4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("algorithms", schema=None) as batch_op:
        batch_op.add_column(sa.Column("task_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("status_task", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("subtask_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("status_subtask", sa.Text(), nullable=True))
        batch_op.create_index("ix_algorithms_task_id", ["task_id"])


def downgrade():
    with op.batch_alter_table("algorithms", schema=None) as batch_op:
        batch_op.drop_index("ix_algorithms_task_id")
        batch_op.drop_column("status_subtask")
        batch_op.drop_column("subtask_id")
        batch_op.drop_column("status_task")
        batch_op.drop_column("task_id")
