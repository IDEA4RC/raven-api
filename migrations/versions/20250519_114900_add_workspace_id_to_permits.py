"""Add workspace_id to permits table
"""

import sqlalchemy as sa
from alembic import op

revision = '20250519_114900'
down_revision = '193a5e67d12a'  # Revisión de add_keycloak_id
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade migration."""
    # Añadir la columna workspace_id a la tabla permits
    op.add_column('permits', sa.Column('workspace_id', sa.Integer(), nullable=True))
    op.add_column('permits', sa.Column('update_date', sa.DateTime(timezone=True), nullable=True))
    
    # Crear un índice para workspace_id
    op.create_index(op.f('ix_permits_workspace_id'), 'permits', ['workspace_id'], unique=False)
    
    # Crear una clave foránea a la tabla workspaces
    op.create_foreign_key(
        'fk_permits_workspace_id', 
        'permits', 'workspaces', 
        ['workspace_id'], ['id']
    )


def downgrade():
    """Downgrade migration."""
    # Eliminar la clave foránea
    op.drop_constraint('fk_permits_workspace_id', 'permits', type_='foreignkey')
    
    # Eliminar el índice
    op.drop_index(op.f('ix_permits_workspace_id'), table_name='permits')
    
    # Eliminar la columna
    op.drop_column('permits', 'workspace_id')
    op.drop_column('permits', 'update_date')
