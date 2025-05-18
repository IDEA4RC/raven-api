#!/bin/sh
# Ejecutar migraciones de base de datos
alembic upgrade head

# Iniciar la aplicación
exec "$@"
