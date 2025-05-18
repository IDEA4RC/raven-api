#!/bin/bash
# Script para verificar y habilitar el registro de MicroK8s

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin Color

echo -e "${YELLOW}🔍 Verificando estado del registro de MicroK8s...${NC}"

# Verificar si el registro está habilitado
if ! microk8s status | grep -q "registry: enabled"; then
    echo -e "${YELLOW}⚠️ El registro de MicroK8s no está habilitado.${NC}"
    echo -e "${YELLOW}🔄 Habilitando el registro...${NC}"
    
    # Habilitar el registro de MicroK8s
    microk8s enable registry
    
    echo -e "${GREEN}✅ Registro de MicroK8s habilitado correctamente.${NC}"
else
    echo -e "${GREEN}✅ El registro de MicroK8s ya está habilitado.${NC}"
fi

# Verificar si el puerto 32000 está en uso (donde debería estar el registro)
if nc -z localhost 32000; then
    echo -e "${GREEN}✅ El registro está accesible en localhost:32000${NC}"
else
    echo -e "${RED}❌ No se pudo acceder al registro en localhost:32000${NC}"
    echo -e "${YELLOW}ℹ️ Verifica que el complemento registry de MicroK8s esté funcionando correctamente.${NC}"
fi
