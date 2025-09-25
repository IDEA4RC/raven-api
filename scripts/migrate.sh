#!/bin/bash

set -euo pipefail

NAMESPACE="raven-api"
KUBECTL=""
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_help() {
    echo "Uso: $0 [migrate|clean|status|create|seed|diagnose] [--debug]"
    echo ""
    echo "Comandos:"
    echo "  migrate  - Ejecutar migraciones de Alembic"
    echo "  clean    - Limpiar base de datos"
    echo "  status   - Ver estado de migraciones"
    echo "  create   - Crear nueva migración"
    echo "  seed     - Insertar datos iniciales"
    echo "  diagnose - Diagnosticar problemas de migraciones / conectividad"
    echo ""
    echo "Flags:" 
    echo "  --debug  - Modo verbose (muestra más información de conexión y entorno)"
}

resolve_kubectl() {
    if command -v kubectl >/dev/null 2>&1; then
        KUBECTL="kubectl"
    elif command -v microk8s >/dev/null 2>&1; then
        KUBECTL="microk8s kubectl"
    else
        echo -e "${RED}❌ No se encontró kubectl ni microk8s${NC}" >&2
        exit 1
    fi
}

DEBUG="false"
for arg in "$@"; do
  if [ "$arg" = "--debug" ]; then
    DEBUG="true"
  fi
done

get_api_pod() {
    ${KUBECTL} get pods -n "$NAMESPACE" -l app=raven-api -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true
}

get_postgres_pod() {
    ${KUBECTL} get pods -n "$NAMESPACE" -l app=postgres -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true
}

create_migration() {
    echo -e "${YELLOW}🔧 Creando nueva migración...${NC}"
    resolve_kubectl
    # Intentar encontrar el pod hasta 10s (p.e. tras un rollout)
    for i in $(seq 1 10); do
        API_POD=$(get_api_pod)
        if [ -n "$API_POD" ]; then
            break
        fi
        sleep 1
    done
    if [ -z "$API_POD" ]; then
        echo -e "${RED}❌ No se encontró el pod de la API (label app=raven-api)${NC}"
        echo -e "${YELLOW}💡 Sugerencia:${NC} verifica: ${KUBECTL} get pods -n ${NAMESPACE}"
        exit 1
    fi
    if [ "$DEBUG" = "true" ]; then
        echo -e "${BLUE}🔍 Usando pod: ${API_POD}${NC}"
    fi
    
    # Solicitar mensaje para la migración
    read -p "Ingrese el mensaje para la migración: " MIGRATION_MESSAGE
    
    if [ -z "$MIGRATION_MESSAGE" ]; then
        echo -e "${RED}❌ El mensaje de migración es requerido${NC}"
        exit 1
    fi
    
    ${KUBECTL} exec -n "$NAMESPACE" "$API_POD" -- alembic revision --autogenerate -m "$MIGRATION_MESSAGE"
    echo -e "${GREEN}✅ Migración creada: $MIGRATION_MESSAGE${NC}"
}

migrate_db() {
    echo -e "${YELLOW}🔄 Ejecutando migraciones...${NC}"
    resolve_kubectl
    API_POD=$(get_api_pod)
    if [ -z "$API_POD" ]; then
        echo -e "${RED}❌ No se encontró el pod de la API${NC}"
        exit 1
    fi
    POSTGRES_POD=$(get_postgres_pod)
    if [ -z "$POSTGRES_POD" ]; then
        echo -e "${RED}❌ No se encontró el pod de PostgreSQL${NC}"
        exit 1
    fi

    # Esperar readiness Postgres (hasta 30s) comprobando estado del contenedor
    echo -e "${BLUE}⏱  Verificando readiness de Postgres...${NC}"
    for i in $(seq 1 30); do
        phase=$(${KUBECTL} get pod -n "$NAMESPACE" "$POSTGRES_POD" -o jsonpath='{.status.phase}' 2>/dev/null || echo "")
        ready=$(${KUBECTL} get pod -n "$NAMESPACE" "$POSTGRES_POD" -o jsonpath='{.status.containerStatuses[0].ready}' 2>/dev/null || echo "false")
        if [ "$phase" = "Running" ] && [ "$ready" = "true" ]; then
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            echo -e "${YELLOW}⚠️ Postgres aún no está Ready, continuando de todos modos...${NC}"
        fi
    done

    if [ "$DEBUG" = "true" ]; then
        echo -e "${BLUE}🔍 Pod API: ${API_POD}${NC}"
        echo -e "${BLUE}🔍 Pod Postgres: ${POSTGRES_POD}${NC}"
        echo -e "${BLUE}🔍 Variables de entorno relevantes:${NC}"
        ${KUBECTL} exec -n "$NAMESPACE" "$API_POD" -- /bin/sh -c 'echo DATABASE_URI=$DATABASE_URI; echo API_V1_STR=$API_V1_STR' || true
        echo -e "${BLUE}🔍 Comprobando conectividad a Postgres desde API (timeout 3s)...${NC}"
        ${KUBECTL} exec -n "$NAMESPACE" "$API_POD" -- /bin/sh -c 'command -v nc >/dev/null && nc -vz -w 3 postgres-service 5432 || echo "nc no disponible"' || true
    fi

    # Ejecutar migraciones con salida no bufferizada
    echo -e "${BLUE}🚚 Ejecutando: alembic upgrade head${NC}"
    if ! ${KUBECTL} exec -n "$NAMESPACE" "$API_POD" -- /bin/sh -c 'PYTHONUNBUFFERED=1 alembic upgrade head'; then
        echo -e "${RED}❌ Error al ejecutar migraciones${NC}"
        if [ "$DEBUG" = "true" ]; then
            echo -e "${BLUE}📄 Log de la API (últimas 50 líneas)${NC}"
            ${KUBECTL} logs -n "$NAMESPACE" "$API_POD" --tail=50 || true
        fi
        exit 1
    fi
    
    echo -e "${GREEN}✅ Migraciones completadas${NC}"
}

seed_db() {
    echo -e "${YELLOW}🌱 Insertando datos iniciales...${NC}"
    
    resolve_kubectl
    POSTGRES_POD=$(get_postgres_pod)
    if [ -z "$POSTGRES_POD" ]; then
        echo -e "${RED}❌ No se encontró el pod de PostgreSQL${NC}"
        exit 1
    fi
    
    # Insertar tipos de usuario por defecto
    ${KUBECTL} exec -n "$NAMESPACE" "$POSTGRES_POD" -- psql -U raven_user -d raven_db -c "
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

diagnose() {
    echo -e "${YELLOW}🩺 Diagnóstico de entorno de migraciones...${NC}"
    resolve_kubectl

    echo -e "${BLUE}📦 Pods en namespace ${NAMESPACE}:${NC}"
    ${KUBECTL} get pods -n "$NAMESPACE" -o wide || true
    echo ""

    API_POD=$(get_api_pod)
    POSTGRES_POD=$(get_postgres_pod)
    if [ -z "$API_POD" ]; then
        echo -e "${RED}❌ Pod de API no encontrado (label app=raven-api)${NC}"
    else
        echo -e "${GREEN}✅ Pod API: $API_POD${NC}"
        echo -e "${BLUE}🔎 Estado Pod API:${NC}"
        ${KUBECTL} get pod "$API_POD" -n "$NAMESPACE" -o jsonpath='{.status.phase} {.status.containerStatuses[0].ready}' 2>/dev/null || true
        echo ""
    fi
    if [ -z "$POSTGRES_POD" ]; then
        echo -e "${RED}❌ Pod de Postgres no encontrado (label app=postgres)${NC}"
    else
        echo -e "${GREEN}✅ Pod Postgres: $POSTGRES_POD${NC}"
        echo -e "${BLUE}🔎 Estado Pod Postgres:${NC}"
        ${KUBECTL} get pod "$POSTGRES_POD" -n "$NAMESPACE" -o jsonpath='{.status.phase} {.status.containerStatuses[0].ready}' 2>/dev/null || true
        echo ""
    fi

    if [ -n "$API_POD" ]; then
        echo -e "${BLUE}🔧 Version Alembic dentro de API:${NC}"
        ${KUBECTL} exec -n "$NAMESPACE" "$API_POD" -- /bin/sh -c 'alembic --version 2>/dev/null || echo "alembic no disponible"'
        echo ""
        echo -e "${BLUE}⚙️  Variables de entorno relevantes:${NC}"
        ${KUBECTL} exec -n "$NAMESPACE" "$API_POD" -- /bin/sh -c 'echo DATABASE_URI=$DATABASE_URI; echo API_V1_STR=$API_V1_STR'
        echo ""
        echo -e "${BLUE}🛣  Alembic current:${NC}"
        ${KUBECTL} exec -n "$NAMESPACE" "$API_POD" -- /bin/sh -c 'alembic current || true'
        echo ""
        echo -e "${BLUE}🗂  Alembic history (últimas 10):${NC}"
        ${KUBECTL} exec -n "$NAMESPACE" "$API_POD" -- /bin/sh -c 'alembic history | tail -n 20 || true'
        echo ""
        echo -e "${BLUE}🔌 Test conexión a Postgres (nc 3s):${NC}"
        ${KUBECTL} exec -n "$NAMESPACE" "$API_POD" -- /bin/sh -c 'command -v nc >/dev/null && nc -vz -w 3 postgres-service 5432 || echo "nc no disponible"' || true
        echo ""
        echo -e "${BLUE}📄 Últimos logs API (50):${NC}"
        ${KUBECTL} logs -n "$NAMESPACE" "$API_POD" --tail=50 || true
        echo ""
    fi

    if [ -n "$POSTGRES_POD" ]; then
        echo -e "${BLUE}🧪 Consulta versión de Postgres:${NC}"
        ${KUBECTL} exec -n "$NAMESPACE" "$POSTGRES_POD" -- psql -U raven_user -d raven_db -c 'SELECT version();' || true
        echo ""
        echo -e "${BLUE}📄 Tabla alembic_version:${NC}"
        ${KUBECTL} exec -n "$NAMESPACE" "$POSTGRES_POD" -- psql -U raven_user -d raven_db -c 'SELECT * FROM alembic_version;' 2>/dev/null || echo -e "${YELLOW}⚠️ Tabla alembic_version no existe todavía${NC}"
        echo ""
                echo -e "${BLUE}🔒 Locks en espera (si hay bloqueos activos aparecerán aquí):${NC}"
                ${KUBECTL} exec -n "$NAMESPACE" "$POSTGRES_POD" -- psql -U raven_user -d raven_db -c "\
                    SELECT pid, locktype, mode, relation::regclass AS relation, granted, pg_blocking_pids(pid) AS blocking_pids, LEFT(query,120) AS query_snippet \
                    FROM pg_locks l \
                    JOIN pg_stat_activity a USING (pid) \
                    WHERE NOT granted;" 2>/dev/null || true
                echo ""
                echo -e "${BLUE}🧷 Resumen de locks sobre alembic_version / migraciones:${NC}"
                ${KUBECTL} exec -n "$NAMESPACE" "$POSTGRES_POD" -- psql -U raven_user -d raven_db -c "\
                    SELECT a.pid, a.usename, a.state, l.mode, l.granted, pg_blocking_pids(a.pid) AS blocking, LEFT(a.query,120) AS query_snippet \
                    FROM pg_stat_activity a \
                    JOIN pg_locks l ON l.pid = a.pid \
                    LEFT JOIN pg_class c ON c.oid = l.relation \
                    WHERE a.datname = 'raven_db' \
                        AND (c.relname ILIKE 'alembic%' OR a.query ILIKE '%alembic%' OR a.query ILIKE '%ALTER TABLE%' OR a.query ILIKE '%CREATE TABLE%') \
                    ORDER BY l.granted DESC;" 2>/dev/null || true
                echo ""
                echo -e "${BLUE}🧪 PIDs bloqueados y quién los bloquea (si aplica):${NC}"
                ${KUBECTL} exec -n "$NAMESPACE" "$POSTGRES_POD" -- psql -U raven_user -d raven_db -c "\
                    WITH waiting AS ( \
                        SELECT pid, unnest(pg_blocking_pids(pid)) AS blocker \
                        FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0 \
                    ) \
                    SELECT w.pid AS waiting_pid, a.query AS waiting_query, w.blocker AS blocker_pid, b.query AS blocker_query \
                    FROM waiting w \
                    JOIN pg_stat_activity a ON a.pid = w.pid \
                    JOIN pg_stat_activity b ON b.pid = w.blocker;" 2>/dev/null || true
                echo ""
    fi

    echo -e "${GREEN}✅ Diagnóstico completado${NC}"
    echo -e "${YELLOW}Siguientes pasos sugeridos:${NC}"
    echo " - Revisa si alembic_version está vacía o inexistente: ejecutar migrate si procede"
    echo " - Si la conexión falla: verifica secrets y variable DATABASE_URI"
    echo " - Si alembic se cuelga: mirar locks en Postgres (pg_locks)"
}

clean_db() {
    echo -e "${YELLOW}🗑️ Limpiando base de datos...${NC}"
    
    resolve_kubectl
    POSTGRES_POD=$(get_postgres_pod)
    if [ -z "$POSTGRES_POD" ]; then
        echo -e "${RED}❌ No se encontró el pod de PostgreSQL${NC}"
        exit 1
    fi
    
    ${KUBECTL} exec -n "$NAMESPACE" "$POSTGRES_POD" -- psql -U raven_user -d raven_db -c "
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
    
    resolve_kubectl
    API_POD=$(get_api_pod)
    if [ -z "$API_POD" ]; then
        echo -e "${RED}❌ No se encontró el pod de la API${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}🔍 Migración actual:${NC}"
    ${KUBECTL} exec -n "$NAMESPACE" "$API_POD" -- alembic current
    echo ""
    echo -e "${BLUE}📋 Historial de migraciones:${NC}"
    ${KUBECTL} exec -n "$NAMESPACE" "$API_POD" -- alembic history
}

ACTION="${1:-help}"
shift || true
case "${ACTION}" in
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
    "diagnose")
        diagnose
        ;;
    "help"|*)
        show_help
        ;;
esac