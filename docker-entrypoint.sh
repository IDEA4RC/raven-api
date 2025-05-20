#!/bin/sh
# Iniciar proceso de migración con validación
echo "Verificando estado de migraciones..."
python /app/scripts/fix_migrations.py

# Aplicar migraciones de Alembic
echo "Aplicando migraciones de base de datos..."
alembic upgrade head

# Iniciar la aplicación
exec "$@"
