#!/bin/bash

# Script simple para gestión de migraciones con Alembic
# Facilita el uso de comandos comunes de migración

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar ayuda
show_help() {
    echo "🔄 Script de Migraciones RAVEN API"
    echo "=================================="
    echo ""
    echo "Uso: $0 <comando> [opciones]"
    echo ""
    echo "Comandos disponibles:"
    echo "  migrate          - Ejecutar todas las migraciones pendientes"
    echo "  rollback         - Revertir la última migración"
    echo "  status           - Mostrar estado actual de migraciones"
    echo "  create <mensaje> - Crear nueva migración"
    echo "  history          - Mostrar historial de migraciones"
    echo "  clean            - Limpiar datos de la base de datos (mantiene estructura)"
    echo "  reset            - Resetear completamente la base de datos"
    echo "  backup           - Crear backup de la base de datos"
    echo "  help             - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 migrate"
    echo "  $0 create 'agregar campo email a usuarios'"
    echo "  $0 rollback"
    echo "  $0 status"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "alembic.ini" ]; then
    echo -e "${RED}❌ Error: No se encontró alembic.ini${NC}"
    echo "Asegúrate de ejecutar este script desde el directorio raíz del proyecto"
    exit 1
fi

# Función para ejecutar migraciones
migrate() {
    echo -e "${BLUE}🔄 Ejecutando migraciones...${NC}"
    alembic upgrade head
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Migraciones ejecutadas correctamente${NC}"
    else
        echo -e "${RED}❌ Error ejecutando migraciones${NC}"
        exit 1
    fi
}

# Función para revertir migración
rollback() {
    echo -e "${YELLOW}⚠️ Revirtiendo última migración...${NC}"
    alembic downgrade -1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Migración revertida correctamente${NC}"
    else
        echo -e "${RED}❌ Error revirtiendo migración${NC}"
        exit 1
    fi
}

# Función para mostrar estado
status() {
    echo -e "${BLUE}📊 Estado actual de migraciones:${NC}"
    echo "=================================="
    alembic current
    echo ""
    echo -e "${BLUE}📋 Migraciones pendientes:${NC}"
    alembic show head
}

# Función para crear nueva migración
create_migration() {
    if [ -z "$1" ]; then
        echo -e "${RED}❌ Error: Se requiere un mensaje para la migración${NC}"
        echo "Uso: $0 create 'mensaje de la migración'"
        exit 1
    fi
    
    echo -e "${BLUE}📝 Creando nueva migración: $1${NC}"
    alembic revision --autogenerate -m "$1"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Migración creada correctamente${NC}"
        echo -e "${YELLOW}💡 No olvides revisar el archivo generado antes de aplicarlo${NC}"
    else
        echo -e "${RED}❌ Error creando migración${NC}"
        exit 1
    fi
}

# Función para mostrar historial
history() {
    echo -e "${BLUE}📋 Historial de migraciones:${NC}"
    echo "============================="
    alembic history --verbose
}

# Función para limpiar base de datos
clean_db() {
    echo -e "${YELLOW}⚠️ Esta operación limpiará TODOS los datos de la base de datos${NC}"
    echo -e "${YELLOW}   pero mantendrá la estructura de tablas${NC}"
    read -p "¿Estás seguro? Escribe 'LIMPIAR' para confirmar: " confirm
    
    if [ "$confirm" = "LIMPIAR" ]; then
        echo -e "${BLUE}🧹 Limpiando base de datos...${NC}"
        python scripts/db_manager.py clean --confirm
    else
        echo -e "${RED}❌ Operación cancelada${NC}"
    fi
}

# Función para resetear base de datos
reset_db() {
    echo -e "${RED}⚠️ Esta operación ELIMINARÁ COMPLETAMENTE la base de datos${NC}"
    echo -e "${RED}   y la recreará desde cero con las migraciones${NC}"
    read -p "¿Estás seguro? Escribe 'RESETEAR' para confirmar: " confirm
    
    if [ "$confirm" = "RESETEAR" ]; then
        echo -e "${BLUE}🔄 Reseteando base de datos...${NC}"
        python scripts/db_manager.py reset --confirm
    else
        echo -e "${RED}❌ Operación cancelada${NC}"
    fi
}

# Función para hacer backup
backup_db() {
    echo -e "${BLUE}💾 Creando backup de la base de datos...${NC}"
    python scripts/db_manager.py backup
}

# Procesar comando
case "$1" in
    migrate)
        migrate
        ;;
    rollback)
        rollback
        ;;
    status)
        status
        ;;
    create)
        create_migration "$2"
        ;;
    history)
        history
        ;;
    clean)
        clean_db
        ;;
    reset)
        reset_db
        ;;
    backup)
        backup_db
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        echo -e "${RED}❌ Error: Se requiere un comando${NC}"
        echo ""
        show_help
        exit 1
        ;;
    *)
        echo -e "${RED}❌ Error: Comando desconocido '$1'${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
