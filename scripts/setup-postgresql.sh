#!/bin/bash

# Script to set up PostgreSQL with Docker for the RAVEN API project

echo "Configurando PostgreSQL con Docker para RAVEN API..."

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "Error: Docker no está instalado. Por favor instala Docker primero."
    echo "Visita: https://docs.docker.com/get-docker/"
    exit 1
fi

# Verificar si Docker está ejecutándose
if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker no está ejecutándose. Por favor inicia Docker."
    exit 1
fi

# Definir variables
CONTAINER_NAME="raven-postgres"
POSTGRES_DB="raven_db"
POSTGRES_USER="raven_user"
POSTGRES_PASSWORD="raven_password"
POSTGRES_PORT="5432"

# Verificar si el contenedor ya existe
if docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "El contenedor ${CONTAINER_NAME} ya existe."
    
    # Verificar si está ejecutándose
    if docker ps --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "El contenedor ya está ejecutándose."
    else
        echo "Iniciando el contenedor existente..."
        docker start ${CONTAINER_NAME}
    fi
else
    echo "Creando y ejecutando contenedor PostgreSQL..."
    docker run -d \
        --name ${CONTAINER_NAME} \
        -e POSTGRES_DB=${POSTGRES_DB} \
        -e POSTGRES_USER=${POSTGRES_USER} \
        -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
        -p ${POSTGRES_PORT}:5432 \
        -v raven-postgres-data:/var/lib/postgresql/data \
        postgres:15-alpine
fi

# Esperar a que PostgreSQL esté listo
echo "Esperando a que PostgreSQL esté listo..."
for i in {1..30}; do
    if docker exec ${CONTAINER_NAME} pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} >/dev/null 2>&1; then
        echo "PostgreSQL está listo!"
        break
    fi
    echo "Esperando... ($i/30)"
    sleep 2
done

# Verificar la conexión final
if docker exec ${CONTAINER_NAME} pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} >/dev/null 2>&1; then
    echo ""
    echo "✅ PostgreSQL configurado correctamente con Docker!"
    echo "📋 Detalles de la conexión:"
    echo "   - Host: localhost"
    echo "   - Puerto: ${POSTGRES_PORT}"
    echo "   - Base de datos: ${POSTGRES_DB}"
    echo "   - User: ${POSTGRES_USER}"
    echo "   - Password: ${POSTGRES_PASSWORD}"
    echo "   - Contenedor: ${CONTAINER_NAME}"
    echo ""
    echo "🔗 URL de conexión:"
    echo "   DATABASE_URI=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}"
    echo ""
    echo "🚀 Ahora puedes ejecutar las migraciones con:"
    echo "   alembic upgrade head"
    echo ""
    echo "🛑 Para detener PostgreSQL:"
    echo "   docker stop ${CONTAINER_NAME}"
    echo ""
    echo "🗑️  Para eliminar PostgreSQL y sus datos:"
    echo "   docker stop ${CONTAINER_NAME} && docker rm ${CONTAINER_NAME} && docker volume rm raven-postgres-data"
else
    echo "❌ Error: No se pudo conectar a PostgreSQL"
    exit 1
fi
