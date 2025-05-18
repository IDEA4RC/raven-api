#!/bin/bash
# Script completo para desplegar RAVEN API en MicroK8s con Istio

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin Color

echo -e "${GREEN}🚀 Iniciando proceso completo de despliegue de RAVEN API${NC}"

# 1. Verificar y habilitar el registro de MicroK8s
echo -e "${YELLOW}📋 Paso 1: Verificando registro de MicroK8s...${NC}"
./scripts/check-registry.sh

# 2. Verificar y habilitar Istio
echo -e "${YELLOW}📋 Paso 2: Verificando Istio...${NC}"
./scripts/check-istio.sh

# 3. Realizar el despliegue de la API
echo -e "${YELLOW}📋 Paso 3: Desplegando RAVEN API...${NC}"
./scripts/deploy.sh

# 4. Verificar el estado del despliegue
echo -e "${YELLOW}📋 Paso 4: Verificando estado final del despliegue...${NC}"
NAMESPACE="raven"
KUBECTL_CMD="microk8s kubectl"

echo -e "${YELLOW}🔍 Pods:${NC}"
$KUBECTL_CMD get pods -n $NAMESPACE

echo -e "${YELLOW}🔍 Servicios:${NC}"
$KUBECTL_CMD get services -n $NAMESPACE

echo -e "${YELLOW}🔍 Virtual Services:${NC}"
$KUBECTL_CMD get virtualservices -n $NAMESPACE

echo -e "${YELLOW}🔍 Gateways:${NC}"
$KUBECTL_CMD get gateways -n $NAMESPACE

# 5. Mostrar la URL de acceso
echo -e "${GREEN}✅ Despliegue completado.${NC}"
echo -e "${GREEN}📊 La API debería estar accesible en: https://host02.idea.lst.tfo.upm.es/raven-api/v1/health/${NC}"

# 6. Instrucciones para solución de problemas
echo -e "${YELLOW}ℹ️ Si encuentras problemas con el despliegue:${NC}"
echo -e "   - Verifica los logs de los pods: ${KUBECTL_CMD} logs -n ${NAMESPACE} <nombre-del-pod>"
echo -e "   - Comprueba el estado de los pods: ${KUBECTL_CMD} describe pod -n ${NAMESPACE} <nombre-del-pod>"
echo -e "   - Asegúrate de que la imagen Docker se construyó correctamente"
echo -e "   - Verifica que el gateway de Istio esté configurado adecuadamente"
