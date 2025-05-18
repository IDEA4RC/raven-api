#!/bin/bash
# Script para configurar MetalLB en MicroK8s

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin Color

echo -e "${YELLOW}🔍 Habilitando MetalLB en MicroK8s...${NC}"

# Determinar la interfaz de red primaria y su rango de direcciones IP
INTERFACE=$(ip route | grep default | awk '{print $5}')
IP_RANGE=$(ip -4 addr show $INTERFACE | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1 | sed 's/\.[0-9]*$/.200-\0.250/')

echo -e "${YELLOW}ℹ️ Interface de red primaria: $INTERFACE${NC}"
echo -e "${YELLOW}ℹ️ Rango de IPs para MetalLB: $IP_RANGE${NC}"

# Habilitar el complemento MetalLB en MicroK8s
microk8s enable metallb:$IP_RANGE

echo -e "${GREEN}✅ MetalLB habilitado en MicroK8s con rango de IPs: $IP_RANGE${NC}"

# Verificar los servicios de tipo LoadBalancer
echo -e "${YELLOW}🔍 Verificando servicios de tipo LoadBalancer...${NC}"
microk8s kubectl get svc -A -o wide | grep LoadBalancer

echo -e "${YELLOW}ℹ️ Para exponer el Gateway de Istio, ejecuta:${NC}"
echo -e "microk8s kubectl apply -f kubernetes/istio-ingress-lb.yaml"

echo -e "${GREEN}✅ Configuración de MetalLB completada.${NC}"
