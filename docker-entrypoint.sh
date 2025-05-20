#!/bin/sh
# Ejecutar migraciones de base de datos
alembic upgrade head

# Ejecutar scripts de actualización de tablas para garantizar estructura correcta
python /app/scripts/update_users_table.py
python /app/scripts/update_permits_table.py

# Iniciar la aplicación
exec "$@"
