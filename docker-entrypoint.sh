#!/bin/sh
# Ejecutar migraciones de base de datos
alembic upgrade head

# Inicializar la base de datos SQLite con la estructura correcta
# Este script se asegura de que las tablas tengan todas las columnas necesarias
python -m app.db.init_sqlite

# Iniciar la aplicación
exec "$@"
