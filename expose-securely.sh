#!/bin/bash
# Script maestro para exponer la RAVEN API a Internet de manera segura

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin Color

echo -e "${GREEN}🌐 Iniciando proceso para exponer la RAVEN API a Internet de manera segura${NC}"

# 1. Exponer el clúster a Internet (MetalLB o NodePort)
echo -e "${YELLOW}📋 Paso 1: Exponiendo el clúster a Internet...${NC}"
./expose-to-internet.sh

# 2. Generar certificado TLS para HTTPS
echo -e "${YELLOW}📋 Paso 2: Generando certificado TLS para HTTPS...${NC}"
./scripts/generate-tls-cert.sh

# 3. Aplicar el Gateway con soporte HTTPS
echo -e "${YELLOW}📋 Paso 3: Aplicando Gateway con soporte HTTPS...${NC}"
microk8s kubectl apply -f kubernetes/gateway-with-https.yaml -n raven

# 4. Esperar a que los cambios se apliquen
echo -e "${YELLOW}📋 Paso 4: Esperando a que los cambios se apliquen...${NC}"
sleep 10

# 5. Verificar el acceso a la API
echo -e "${YELLOW}📋 Paso 5: Verificando el acceso a la API...${NC}"
./scripts/verify-api-access.sh

echo -e "${GREEN}✅ Proceso completado.${NC}"
echo -e "${GREEN}ℹ️ La RAVEN API debería estar expuesta de manera segura en:${NC}"
echo -e "${GREEN}https://orchestrator.idea.lst.tfo.upm.es/raven-api/v1/${NC}"
