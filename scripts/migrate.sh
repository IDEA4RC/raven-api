#!/bin/bash

set -e

NAMESPACE="raven-api"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

show_help() {
    echo "Uso: $0 [migrate|clean|status]"
    echo ""
    echo "Comandos:"
    echo "  migrate  - Ejecutar migraciones de Alembic"
    echo "  clean    - Limpiar base de datos"
    echo "  status   - Ver estado de migraciones"
}

get_api_pod() {
    kubectl get pods -n $NAMESPACE -l app=raven-api -o jsonpath='{.items[0].metadata.name}' 2>/dev/null
}

get_postgres_pod() {
    kubectl get pods -n $NAMESPACE -l app=postgres -o jsonpath='{.items[0].metadata.name}' 2>/dev/null
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
}

show_status() {
    echo -e "${YELLOW}📊 Estado de migraciones:${NC}"
    
    API_POD=$(get_api_pod)
    if [ -z "$API_POD" ]; then
        echo -e "${RED}❌ No se encontró el pod de la API${NC}"
        exit 1
    fi
    
    kubectl exec -n $NAMESPACE $API_POD -- alembic current
    echo ""
    kubectl exec -n $NAMESPACE $API_POD -- alembic history
}

case "${1:-help}" in
    "migrate")
        migrate_db
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