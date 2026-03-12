"""Replace deprecated algorithm dataframe field with crosstab fields

Revision ID: 3a9d7b6f21c4
Revises: 29b8373ce09a
Create Date: 2026-03-12 12:00:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3a9d7b6f21c4"
down_revision = "29b8373ce09a"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("algorithms", schema=None) as batch_op:
        batch_op.drop_column("new_dataframe_vantage_id")
        batch_op.add_column(sa.Column("col_var", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("row_var_list", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("algorithms", schema=None) as batch_op:
        batch_op.drop_column("row_var_list")
        batch_op.drop_column("col_var")
        batch_op.add_column(
            sa.Column("new_dataframe_vantage_id", sa.Integer(), nullable=True)
        )
