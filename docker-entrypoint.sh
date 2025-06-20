#!/bin/sh
# Start migration process with validation
echo "Verificando estado de migraciones..."
python /app/scripts/fix_migrations.py

# Aplicar migraciones de Alembic
echo "Aplicando migraciones de base de datos..."
alembic upgrade head

# Start the application
exec "$@"
