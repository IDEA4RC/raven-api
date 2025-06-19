#!/bin/bash

# Script para configurar PostgreSQL para el proyecto RAVEN API

echo "Configurando PostgreSQL para RAVEN API..."

# Verificar si PostgreSQL está instalado
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL no está instalado. Instalando..."
    sudo apt update
    sudo apt install -y postgresql postgresql-contrib
fi

# Verificar si PostgreSQL está ejecutándose
if ! sudo systemctl is-active --quiet postgresql; then
    echo "Iniciando PostgreSQL..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

echo "Configurando base de datos y usuario..."

# Crear usuario y base de datos
sudo -u postgres psql << EOF
-- Crear usuario
CREATE USER raven_user WITH PASSWORD 'raven_password';

-- Crear base de datos
CREATE DATABASE raven_db OWNER raven_user;

-- Otorgar privilegios
GRANT ALL PRIVILEGES ON DATABASE raven_db TO raven_user;

-- Otorgar privilegios en el esquema public
\c raven_db
GRANT ALL ON SCHEMA public TO raven_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO raven_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO raven_user;

\q
EOF

echo "PostgreSQL configurado correctamente."
echo "Base de datos: raven_db"
echo "Usuario: raven_user"
echo "Contraseña: raven_password"
echo ""
echo "Ahora puedes ejecutar las migraciones con:"
echo "alembic upgrade head"
