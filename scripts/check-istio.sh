#!/bin/bash
# Script para verificar y habilitar Istio en MicroK8s

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin Color

echo -e "${YELLOW}🔍 Verificando estado de Istio en MicroK8s...${NC}"

# Verificar si Istio está habilitado
if ! microk8s status | grep -q "istio: enabled"; then
    echo -e "${YELLOW}⚠️ Istio no está habilitado en MicroK8s.${NC}"
    echo -e "${YELLOW}🔄 Habilitando Istio...${NC}"
    
    # Habilitar Istio en MicroK8s
    microk8s enable istio
    
    echo -e "${GREEN}✅ Istio habilitado correctamente en MicroK8s.${NC}"
else
    echo -e "${GREEN}✅ Istio ya está habilitado en MicroK8s.${NC}"
fi

# Verificar los componentes de Istio
echo -e "${YELLOW}🔍 Verificando componentes de Istio...${NC}"
microk8s kubectl get pods -n istio-system
