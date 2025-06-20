#!/bin/bash

# Quick start script for RAVEN API with PostgreSQL in Docker

echo "🚀 RAVEN API - Inicio Rápido con Docker"
echo "====================================="
echo ""

# Verificar si estamos en un entorno virtual
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  No estás en un entorno virtual."
    echo "📋 Recomendamos usar un entorno virtual:"
    echo "   python -m venv .venv"
    echo "   source .venv/bin/activate"
    echo ""
    read -p "¿Continuar sin entorno virtual? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        echo "Abortado."
        exit 1
    fi
fi

echo "1. 📦 Instalando dependencias..."
pip install -r requirements.txt

echo ""
echo "2. 🐘 Configurando PostgreSQL con Docker..."
./scripts/setup-postgresql-compose.sh

if [ $? -ne 0 ]; then
    echo "❌ Error configurando PostgreSQL. Abortando."
    exit 1
fi

echo ""
echo "3. 🔄 Aplicando migraciones..."
export DATABASE_URI="postgresql://raven_user:raven_password@localhost:5432/raven_db"
alembic upgrade head

if [ $? -ne 0 ]; then
    echo "❌ Error aplicando migraciones. Abortando."
    exit 1
fi

echo ""
echo "4. 🌱 Poblando base de datos (opcional)..."
if [ -f "scripts/seed_db.py" ]; then
    read -p "¿Quieres poblar la base de datos con datos de ejemplo? (y/N): " seed_confirm
    if [[ $seed_confirm == [yY] ]]; then
        python scripts/seed_db.py
    fi
fi

echo ""
echo "🎉 Setup completed!"
echo ""
echo "📋 Configuration summary:"
echo "   🐘 PostgreSQL: Running on Docker (port 5432)"
echo "   🗄️  Database: raven_db"
echo "   👤 User: raven_user"
echo "   🔗 URL: postgresql://raven_user:raven_password@localhost:5432/raven_db"
echo ""
echo "🚀 To start the API run:"
echo "   uvicorn main:app --reload"
echo ""
echo "📝 Comandos útiles:"
echo "   ⏹️  Detener PostgreSQL: docker compose -f docker-compose.postgres.yml down"
echo "   📊 Ver logs: docker compose -f docker-compose.postgres.yml logs -f"
echo "   🔍 API docs: http://localhost:8000/docs (una vez iniciada la API)"
