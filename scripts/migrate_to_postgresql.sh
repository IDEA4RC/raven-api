#!/bin/bash

# Script completo para migrar de SQLite a PostgreSQL

echo "=== MIGRACIÓN DE RAVEN API A POSTGRESQL ==="
echo ""

echo "1. Instalando dependencias de PostgreSQL..."
pip install psycopg2-binary

echo ""
echo "2. Configurando PostgreSQL..."
./scripts/setup-postgresql.sh

echo ""
echo "3. Aplicando migraciones..."
export DATABASE_URI="postgresql://raven_user:raven_password@localhost:5432/raven_db"
alembic upgrade head

echo ""
echo "4. Ejecutando migración de datos..."
python scripts/migrate_data.py

echo ""
echo "=== MIGRACIÓN COMPLETADA ==="
echo ""
echo "La aplicación ahora está configurada para usar PostgreSQL."
echo "Puedes iniciar la aplicación con:"
echo "uvicorn main:app --reload"
