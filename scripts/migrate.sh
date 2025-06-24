#!/bin/bash

set -e

NAMESPACE="raven-api"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_help() {
    echo "Uso: $0 [migrate|clean|status|create|seed]"
    echo ""
    echo "Comandos:"
    echo "  migrate  - Ejecutar migraciones de Alembic"
    echo "  clean    - Limpiar base de datos"
    echo "  status   - Ver estado de migraciones"
    echo "  create   - Crear nueva migración"
    echo "  seed     - Insertar datos iniciales"
}

get_api_pod() {
    kubectl get pods -n $NAMESPACE -l app=raven-api -o jsonpath='{.items[0].metadata.name}' 2>/dev/null
}

get_postgres_pod() {
    kubectl get pods -n $NAMESPACE -l app=postgres -o jsonpath='{.items[0].metadata.name}' 2>/dev/null
}

create_migration() {
    echo -e "${YELLOW}🔧 Creando nueva migración...${NC}"
    
    API_POD=$(get_api_pod)
    if [ -z "$API_POD" ]; then
        echo -e "${RED}❌ No se encontró el pod de la API${NC}"
        exit 1
    fi
    
    # Solicitar mensaje para la migración
    read -p "Ingrese el mensaje para la migración: " MIGRATION_MESSAGE
    
    if [ -z "$MIGRATION_MESSAGE" ]; then
        echo -e "${RED}❌ El mensaje de migración es requerido${NC}"
        exit 1
    fi
    
    kubectl exec -n $NAMESPACE $API_POD -- alembic revision --autogenerate -m "$MIGRATION_MESSAGE"
    echo -e "${GREEN}✅ Migración creada: $MIGRATION_MESSAGE${NC}"
}

migrate_db() {
    echo -e "${YELLOW}🔄 Ejecutando migraciones...${NC}"
    
    API_POD=$(get_api_pod)
    if [ -z "$API_POD" ]; then
        echo -e "${RED}❌ No se encontró el pod de la API${NC}"
        exit 1
    fi
    
    kubectl exec -n $NAMESPACE $API_POD -- alembic upgrade head
    echo -e "${GREEN}✅ Migraciones completadas${NC}"
}

seed_db() {
    echo -e "${YELLOW}🌱 Insertando datos iniciales...${NC}"
    
    POSTGRES_POD=$(get_postgres_pod)
    if [ -z "$POSTGRES_POD" ]; then
        echo -e "${RED}❌ No se encontró el pod de PostgreSQL${NC}"
        exit 1
    fi
    
    # Insertar tipos de usuario por defecto
    kubectl exec -n $NAMESPACE $POSTGRES_POD -- psql -U raven_user -d raven_db -c "
        INSERT INTO user_types (
            id, description, metadata_search, permissions, cohort_builder, 
            data_quality, export, results_report
        ) VALUES 
        (1, 'Usuario básico', 1, 0, 0, 1, 0, 1),
        (2, 'Usuario premium', 2, 1, 1, 2, 2, 2),
        (3, 'Administrador', 4, 1, 1, 2, 4, 2),
        (4, 'Usuario estándar', 1, 1, 1, 1, 1, 1),
        (5, 'Usuario invitado', 1, 0, 0, 1, 0, 1)
        ON CONFLICT (id) DO UPDATE SET
            description = EXCLUDED.description,
            metadata_search = EXCLUDED.metadata_search,
            permissions = EXCLUDED.permissions,
            cohort_builder = EXCLUDED.cohort_builder,
            data_quality = EXCLUDED.data_quality,
            export = EXCLUDED.export,
            results_report = EXCLUDED.results_report;
    "
    
    echo -e "${GREEN}✅ Datos iniciales insertados${NC}"
}

clean_db() {
    echo -e "${YELLOW}🗑️ Limpiando base de datos...${NC}"
    
    POSTGRES_POD=$(get_postgres_pod)
    if [ -z "$POSTGRES_POD" ]; then
        echo -e "${RED}❌ No se encontró el pod de PostgreSQL${NC}"
        exit 1
    fi
    
    kubectl exec -n $NAMESPACE $POSTGRES_POD -- psql -U raven_user -d raven_db -c "
        DROP SCHEMA public CASCADE;
        CREATE SCHEMA public;
        GRANT ALL ON SCHEMA public TO raven_user;
        GRANT ALL ON SCHEMA public TO public;
    "
    
    echo -e "${GREEN}✅ Base de datos limpiada${NC}"
    echo -e "${YELLOW}💡 Ejecuta './scripts/migrate.sh migrate' para recrear las tablas${NC}"
    echo -e "${YELLOW}💡 Después ejecuta './scripts/migrate.sh seed' para insertar datos iniciales${NC}"
}

show_status() {
    echo -e "${YELLOW}📊 Estado de migraciones:${NC}"
    
    API_POD=$(get_api_pod)
    if [ -z "$API_POD" ]; then
        echo -e "${RED}❌ No se encontró el pod de la API${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}🔍 Migración actual:${NC}"
    kubectl exec -n $NAMESPACE $API_POD -- alembic current
    echo ""
    echo -e "${BLUE}📋 Historial de migraciones:${NC}"
    kubectl exec -n $NAMESPACE $API_POD -- alembic history
}

case "${1:-help}" in
    "create")
        create_migration
        ;;
    "migrate")
        migrate_db
        ;;
    "seed")
        seed_db
        ;;
    "clean")
        clean_db
        ;;
    "status")
        show_status
        ;;
    "help"|*)
        show_help
        ;;
esac