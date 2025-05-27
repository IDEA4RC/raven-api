#!/bin/bash
# Script para obtener la IP externa del ingress gateway y configurar host localmente

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin Color

KUBECTL_CMD="microk8s kubectl"
HOSTNAME="orchestrator.idea.lst.tfo.upm.es"

echo -e "${YELLOW}🔍 Obteniendo la IP externa del Istio Ingress Gateway...${NC}"

# Comprobar si existe el servicio de tipo LoadBalancer
if $KUBECTL_CMD get svc -n istio-system istio-ingressgateway-lb &>/dev/null; then
    # Obtener la IP externa del LoadBalancer
    EXTERNAL_IP=$($KUBECTL_CMD get svc -n istio-system istio-ingressgateway-lb -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ -z "$EXTERNAL_IP" ]; then
        echo -e "${RED}❌ No se pudo obtener la IP externa del LoadBalancer.${NC}"
        echo -e "${YELLOW}ℹ️ Verificando si existe asignación de IP...${NC}"
        $KUBECTL_CMD get svc -n istio-system istio-ingressgateway-lb -o wide
    else
        echo -e "${GREEN}✅ IP externa del LoadBalancer: $EXTERNAL_IP${NC}"
    fi
elif $KUBECTL_CMD get svc -n istio-system istio-ingressgateway-nodeport &>/dev/null; then
    # Es un NodePort, obtener la IP del nodo
    NODE_IP=$(hostname -I | awk '{print $1}')
    NODE_PORT=$($KUBECTL_CMD get svc -n istio-system istio-ingressgateway-nodeport -o jsonpath='{.spec.ports[?(@.name=="http")].nodePort}')
    EXTERNAL_IP="$NODE_IP:$NODE_PORT"
    echo -e "${GREEN}✅ NodePort accesible en: $EXTERNAL_IP${NC}"
else
    # Verificar si existe el ingressgateway por defecto
    if $KUBECTL_CMD get svc -n istio-system istio-ingressgateway &>/dev/null; then
        # Obtener el tipo de servicio
        SERVICE_TYPE=$($KUBECTL_CMD get svc -n istio-system istio-ingressgateway -o jsonpath='{.spec.type}')
        
        if [ "$SERVICE_TYPE" == "LoadBalancer" ]; then
            EXTERNAL_IP=$($KUBECTL_CMD get svc -n istio-system istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
            if [ -z "$EXTERNAL_IP" ]; then
                echo -e "${RED}❌ No se pudo obtener la IP externa del LoadBalancer.${NC}"
                echo -e "${YELLOW}ℹ️ Verificando detalles del servicio...${NC}"
                $KUBECTL_CMD get svc -n istio-system istio-ingressgateway -o wide
            else
                echo -e "${GREEN}✅ IP externa del LoadBalancer: $EXTERNAL_IP${NC}"
            fi
        elif [ "$SERVICE_TYPE" == "NodePort" ]; then
            NODE_IP=$(hostname -I | awk '{print $1}')
            NODE_PORT=$($KUBECTL_CMD get svc -n istio-system istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http")].nodePort}')
            EXTERNAL_IP="$NODE_IP:$NODE_PORT"
            echo -e "${GREEN}✅ NodePort accesible en: $EXTERNAL_IP${NC}"
        else
            echo -e "${RED}❌ El servicio istio-ingressgateway es de tipo $SERVICE_TYPE, no es accesible externamente.${NC}"
            EXTERNAL_IP=""
        fi
    else
        echo -e "${RED}❌ No se encontró ningún servicio de Istio Ingress Gateway.${NC}"
        echo -e "${YELLOW}ℹ️ Es posible que necesites configurar uno manualmente.${NC}"
        EXTERNAL_IP=""
    fi
fi

# Si se encontró una IP externa, mostrar configuración de hosts
if [ ! -z "$EXTERNAL_IP" ]; then
    echo -e "${YELLOW}ℹ️ Para acceder localmente, agrega esta línea a tu archivo /etc/hosts:${NC}"
    echo -e "${GREEN}$EXTERNAL_IP $HOSTNAME${NC}"
    
    echo -e "${YELLOW}ℹ️ Si deseas agregar esta entrada automáticamente, ejecuta:${NC}"
    echo -e "sudo sh -c \"echo '$EXTERNAL_IP $HOSTNAME' >> /etc/hosts\""
    
    echo -e "${YELLOW}ℹ️ Para una configuración DNS adecuada en un entorno de producción:${NC}"
    echo -e "1. Configurar un registro A en tu servidor DNS que apunte $HOSTNAME a $EXTERNAL_IP"
    echo -e "2. Para HTTPS, configurar certificados SSL para $HOSTNAME"
fi

echo -e "${GREEN}✅ Verificación completada.${NC}"
