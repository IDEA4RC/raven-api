#!/bin/bash

# Script simple para configurar PostgreSQL con Docker Compose

echo "🐘 Configurando PostgreSQL con Docker Compose..."

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker no está instalado."
    echo "📥 Instala Docker desde: https://docs.docker.com/get-docker/"
    exit 1
fi

# Verificar si Docker Compose está disponible
if ! docker compose version &> /dev/null && ! docker-compose --version &> /dev/null; then
    echo "❌ Error: Docker Compose no está disponible."
    echo "📥 Instala Docker Compose o usa una versión más reciente de Docker."
    exit 1
fi

# Determinar comando de Docker Compose
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo "🚀 Iniciando PostgreSQL con $DOCKER_COMPOSE..."

# Iniciar PostgreSQL
$DOCKER_COMPOSE -f docker-compose.postgres.yml up -d

# Esperar a que esté listo
echo "⏳ Esperando a que PostgreSQL esté listo..."
for i in {1..30}; do
    if $DOCKER_COMPOSE -f docker-compose.postgres.yml exec postgres pg_isready -U raven_user -d raven_db >/dev/null 2>&1; then
        echo "✅ PostgreSQL está listo!"
        break
    fi
    echo "Esperando... ($i/30)"
    sleep 2
done

# Verificar estado
if $DOCKER_COMPOSE -f docker-compose.postgres.yml exec postgres pg_isready -U raven_user -d raven_db >/dev/null 2>&1; then
    echo ""
    echo "🎉 PostgreSQL configurado correctamente!"
    echo ""
    echo "📋 Detalles de la conexión:"
    echo "   - Host: localhost"
    echo "   - Puerto: 5432"
    echo "   - Base de datos: raven_db"
    echo "   - Usuario: raven_user"
    echo "   - Contraseña: raven_password"
    echo ""
    echo "🔗 URL de conexión:"
    echo "   DATABASE_URI=postgresql://raven_user:raven_password@localhost:5432/raven_db"
    echo ""
    echo "📝 Comandos útiles:"
    echo "   🚀 Ejecutar migraciones: alembic upgrade head"
    echo "   ⏹️  Detener PostgreSQL: $DOCKER_COMPOSE -f docker-compose.postgres.yml down"
    echo "   🗑️  Eliminar datos: $DOCKER_COMPOSE -f docker-compose.postgres.yml down -v"
    echo "   📊 Ver logs: $DOCKER_COMPOSE -f docker-compose.postgres.yml logs -f"
else
    echo "❌ Error: No se pudo conectar a PostgreSQL"
    echo "📋 Para ver los logs: $DOCKER_COMPOSE -f docker-compose.postgres.yml logs"
    exit 1
fi
