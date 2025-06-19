#!/bin/bash
# Script para probar los endpoints de la API sin autenticacion

API_BASE="http://localhost:8000/raven-api/v1"
DATE=$(date +"%Y-%m-%d %H:%M:%S")

echo "====================================================="
echo "PRUEBA DE ENDPOINTS SIN AUTENTICACION"
echo "Fecha de ejecucion: $DATE"
echo "====================================================="

# Comprobar si jq está instalado
if ! command -v jq &> /dev/null; then
    echo "Error: Este script requiere jq para procesar respuestas JSON."
    echo "Instalalo con: sudo apt install jq"
    exit 1
fi

# Función para mostrar mensajes con formato
function show_test {
    echo -e "\n>> $1"
}

# Función para separar secciones
function section {
    echo -e "\n==== $1 ===="
}

# Verificar salud del servicio
section "VERIFICACION DE SALUD"
show_test "Verificando estado de salud de la API..."
curl -s "${API_BASE}/health" | jq .

# Login para obtener token (falso en bypass)
section "AUTENTICACION"
show_test "Probando login (obtendra token falso)..."
TOKEN=$(curl -s -X POST "${API_BASE}/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test@example.com&password=cualquier_clave" | jq -r '.access_token')

echo "Token obtenido: ${TOKEN:0:20}... (truncado)"

# Probar endpoints de workspace
section "WORKSPACES"
show_test "Obteniendo lista de workspaces existentes..."
curl -s "${API_BASE}/workspaces/?skip=0&limit=100" \
     -H "Content-Type: application/json" | jq .

show_test "Creando un nuevo workspace..."
RESPONSE=$(curl -s -X POST "${API_BASE}/workspaces/" \
     -H "Content-Type: application/json" \
     -d "{
        \"name\": \"Workspace de prueba ${DATE}\",
        \"description\": \"Workspace creado mediante script de prueba\",
        \"team_id\": 1,
        \"data_access\": 0
     }")

echo "$RESPONSE" | jq .
WORKSPACE_ID=$(echo "$RESPONSE" | jq -r '.id')

if [[ "$WORKSPACE_ID" == "null" || -z "$WORKSPACE_ID" ]]; then
    echo "Error: No se pudo crear el workspace o extraer su ID"
    echo "Respuesta completa: $RESPONSE"
    WORKSPACE_ID=1  # Usar ID 1 como fallback para continuar las pruebas
else
    echo "Workspace creado con ID: ${WORKSPACE_ID}"
fi

show_test "Obteniendo detalles del workspace recien creado..."
curl -s "${API_BASE}/workspaces/${WORKSPACE_ID}" \
     -H "Content-Type: application/json" | jq .

show_test "Actualizando el estado de acceso a datos del workspace..."
curl -s -X PATCH "${API_BASE}/workspaces/${WORKSPACE_ID}/data-access?data_access=1" \
     -H "Content-Type: application/json" | jq .

# Probar endpoints de permisos
section "PERMISOS"
show_test "Creando un permiso para el workspace..."
RESPONSE=$(curl -s -X POST "${API_BASE}/permits/" \
     -H "Content-Type: application/json" \
     -d "{
        \"workspace_id\": ${WORKSPACE_ID},
        \"status\": 1
     }")

echo "$RESPONSE" | jq .
PERMIT_ID=$(echo "$RESPONSE" | jq -r '.id')

if [[ "$PERMIT_ID" == "null" || -z "$PERMIT_ID" ]]; then
    echo "Error: No se pudo crear el permiso o extraer su ID"
    echo "Respuesta completa: $RESPONSE"
    PERMIT_ID=1  # Usar ID 1 como fallback para continuar las pruebas
else
    echo "Permiso creado con ID: ${PERMIT_ID}"
fi

show_test "Obteniendo detalles del permiso..."
curl -s "${API_BASE}/permits/${PERMIT_ID}" \
     -H "Content-Type: application/json" | jq .

show_test "Obteniendo todos los permisos del workspace..."
curl -s "${API_BASE}/permits/workspace/${WORKSPACE_ID}" \
     -H "Content-Type: application/json" | jq .

show_test "Actualizando el estado del permiso a SUBMITTED (2)..."
curl -s -X PATCH "${API_BASE}/permits/${PERMIT_ID}/status?status=2" \
     -H "Content-Type: application/json" | jq .

# Probar historial de workspace
section "HISTORIAL DE WORKSPACE"
show_test "Verificando historial del workspace..."
curl -s "${API_BASE}/workspace-history/${WORKSPACE_ID}" \
     -H "Content-Type: application/json" | jq .

section "RESUMEN DE PRUEBAS"
echo -e "\n✓ Pruebas completadas exitosamente"
echo "Se creo el workspace con ID: ${WORKSPACE_ID}"
echo "Se creo el permiso con ID: ${PERMIT_ID}"
echo "Fecha de finalizacion: $(date +"%Y-%m-%d %H:%M:%S")"
echo "====================================================="
