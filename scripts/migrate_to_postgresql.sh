#!/bin/bash

# Script completo para migrar de SQLite a PostgreSQL usando Docker

echo "=== RAVEN API MIGRATION TO POSTGRESQL (DOCKER) ==="
echo ""

echo "1. 📦 Instalando dependencias de PostgreSQL..."
echo "Verificando si psycopg2-binary está instalado..."

# Verificar si psycopg2 está instalado
if python -c "import psycopg2" 2>/dev/null; then
    echo "✅ psycopg2 ya está instalado"
else
    echo "📥 Instalando psycopg2-binary..."
    pip install psycopg2-binary
    
    # Verificar instalación
    if python -c "import psycopg2" 2>/dev/null; then
        echo "✅ psycopg2-binary instalado correctamente"
    else
        echo "❌ Error instalando psycopg2-binary"
        echo "💡 Intentando instalación alternativa..."
        pip install --no-cache-dir psycopg2-binary
        
        # Verificar de nuevo
        if python -c "import psycopg2" 2>/dev/null; then
            echo "✅ psycopg2-binary instalado correctamente (segunda tentativa)"
        else
            echo "❌ No se pudo instalar psycopg2-binary"
            echo "🔧 Soluciones posibles:"
            echo "   1. Instalar manualmente: pip install psycopg2-binary"
            echo "   2. Verificar que estás en el entorno virtual correcto"
            echo "   3. Actualizar pip: pip install --upgrade pip"
            exit 1
        fi
    fi
fi

echo ""
echo "2. 🐘 Configurando PostgreSQL con Docker..."
# Usar Docker Compose si está disponible, sino Docker normal
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    echo "Usando Docker Compose..."
    ./scripts/setup-postgresql-compose.sh
else
    echo "Usando Docker..."
    ./scripts/setup-postgresql.sh
fi

if [ $? -ne 0 ]; then
    echo "❌ Error configurando PostgreSQL. Abortando."
    exit 1
fi

echo ""
echo "3. 🔄 Creando tablas y aplicando estructura..."
export DATABASE_URI="postgresql://raven_user:raven_password@localhost:5432/raven_db"

# Crear tablas directamente con SQLAlchemy
python scripts/create_tables.py

if [ $? -ne 0 ]; then
    echo "❌ Error creando tablas. Abortando."
    exit 1
fi

echo ""
echo "4. 📊 Running data migration (if SQLite exists)..."
if [ -f "raven.db" ]; then
    echo "Base de datos SQLite encontrada, migrando datos..."
    python scripts/migrate_data.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Data migration completed"
    else
        echo "⚠️  Error in data migration, but PostgreSQL is configured"
    fi
else
    echo "ℹ️  SQLite database not found, skipping data migration"
fi

echo ""
echo "=== ✅ MIGRATION COMPLETED ==="
echo ""
echo "🐘 PostgreSQL ejecutándose en Docker"
echo "🚀 La aplicación ahora está configurada para usar PostgreSQL."
echo ""
echo "📝 Comandos útiles:"
echo "   ▶️  Iniciar API: uvicorn main:app --reload"
echo "   ⏹️  Detener PostgreSQL: docker stop raven-postgres"
echo "   📊 Ver logs de PostgreSQL: docker logs raven-postgres"
echo "   🔗 Conectar a PostgreSQL: docker exec -it raven-postgres psql -U raven_user -d raven_db"
