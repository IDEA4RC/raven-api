#!/bin/bash
# Script para verificar el acceso a la RAVEN API

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin Color

HOST="orchestrator.idea.lst.tfo.upm.es"
API_PATH="/raven-api/v1/health/"
HTTP_URL="http://$HOST$API_PATH"
HTTPS_URL="https://$HOST$API_PATH"

echo -e "${YELLOW}🔍 Verificando acceso a la RAVEN API...${NC}"

# Verificar si el host está en /etc/hosts o es accesible por DNS
echo -e "${YELLOW}ℹ️ Verificando resolución de nombre para $HOST...${NC}"
if ping -c 1 $HOST &>/dev/null; then
    echo -e "${GREEN}✅ El host $HOST es accesible.${NC}"
else
    echo -e "${RED}❌ No se puede resolver el host $HOST.${NC}"
    echo -e "${YELLOW}ℹ️ Verifica que hayas configurado la entrada en /etc/hosts o el DNS correctamente.${NC}"
    exit 1
fi

# Probar acceso HTTP
echo -e "${YELLOW}ℹ️ Probando acceso HTTP...${NC}"
if curl -s -o /dev/null -w "%{http_code}" $HTTP_URL | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✅ API accesible vía HTTP.${NC}"
    echo -e "${YELLOW}ℹ️ Respuesta completa:${NC}"
    curl -v $HTTP_URL
else
    echo -e "${RED}❌ No se puede acceder a la API vía HTTP.${NC}"
    echo -e "${YELLOW}ℹ️ Intentando consulta con más detalles:${NC}"
    curl -v $HTTP_URL
fi

# Probar acceso HTTPS
echo -e "${YELLOW}ℹ️ Probando acceso HTTPS...${NC}"
if curl -s -k -o /dev/null -w "%{http_code}" $HTTPS_URL | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✅ API accesible vía HTTPS (ignorando validación de certificado).${NC}"
    echo -e "${YELLOW}ℹ️ Respuesta completa:${NC}"
    curl -k -v $HTTPS_URL
else
    echo -e "${RED}❌ No se puede acceder a la API vía HTTPS.${NC}"
    echo -e "${YELLOW}ℹ️ Intentando consulta con más detalles:${NC}"
    curl -k -v $HTTPS_URL
fi

echo -e "${YELLOW}ℹ️ Si ninguna de las pruebas tuvo éxito, verifica:${NC}"
echo -e "1. Que el clúster esté correctamente expuesto a Internet"
echo -e "2. Que los servicios y pods de la API estén funcionando correctamente"
echo -e "3. Que la configuración de Istio (Gateway y VirtualService) sea correcta"
echo -e "4. Que no haya restricciones de firewall bloqueando el acceso"
