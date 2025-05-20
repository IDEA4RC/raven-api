"""Añadir columna keycloak_id faltante a la tabla users

Revision ID: 20250520_105800
Revises: 20250519_114900
Create Date: 2025-05-20 10:58:00.000000+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '20250520_105800'
down_revision = '20250519_114900'
branch_labels = None
depends_on = None


def upgrade():
    # Verificar si la columna keycloak_id ya existe en la tabla users
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    # Solo añadir la columna si no existe
    if 'keycloak_id' not in columns:
        op.add_column('users', sa.Column('keycloak_id', sa.String(), nullable=True))
        op.create_index(op.f('ix_users_keycloak_id'), 'users', ['keycloak_id'], unique=True)
        
        # Actualizar los usuarios existentes con valores predeterminados para keycloak_id
        conn.execute(sa.text("""
            UPDATE users
            SET keycloak_id = 'keycloak-id-' || id
            WHERE keycloak_id IS NULL
        """))
        
        # Hacer que la columna sea no nullable después de actualizarla
        op.alter_column('users', 'keycloak_id', nullable=False)
    
    # Verificar y añadir otras columnas relacionadas que podrían faltar
    if 'first_name' not in columns:
        op.add_column('users', sa.Column('first_name', sa.String(), nullable=True))
    
    if 'last_name' not in columns:
        op.add_column('users', sa.Column('last_name', sa.String(), nullable=True))
    
    if 'is_active' not in columns:
        op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))


def downgrade():
    # Eliminar columnas añadidas
    op.drop_index(op.f('ix_users_keycloak_id'), table_name='users')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'keycloak_id')
