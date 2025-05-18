#!/bin/bash
# Script para exponer el clúster MicroK8s a Internet

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin Color

KUBECTL_CMD="microk8s kubectl"
NAMESPACE="raven"

echo -e "${GREEN}🌐 Iniciando proceso para exponer la RAVEN API a Internet${NC}"

# 1. Verificar si Istio está habilitado
echo -e "${YELLOW}📋 Paso 1: Verificando si Istio está habilitado...${NC}"
if ! microk8s status | grep -q "istio: enabled"; then
    echo -e "${YELLOW}⚠️ Istio no está habilitado. Habilitándolo...${NC}"
    microk8s enable istio
    echo -e "${GREEN}✅ Istio habilitado correctamente.${NC}"
else
    echo -e "${GREEN}✅ Istio ya está habilitado.${NC}"
fi

# 2. Verificar el tipo de servicio del ingress gateway de Istio
echo -e "${YELLOW}📋 Paso 2: Verificando el Istio Ingress Gateway...${NC}"
if ! $KUBECTL_CMD get svc -n istio-system istio-ingressgateway &>/dev/null; then
    echo -e "${RED}❌ No se encontró el servicio Istio Ingress Gateway.${NC}"
    echo -e "${YELLOW}ℹ️ Es posible que Istio no se haya instalado correctamente.${NC}"
    exit 1
fi

INGRESS_TYPE=$($KUBECTL_CMD get svc -n istio-system istio-ingressgateway -o jsonpath='{.spec.type}')
echo -e "${YELLOW}ℹ️ El tipo actual del Istio Ingress Gateway es: $INGRESS_TYPE${NC}"

# 3. Configurar MetalLB si es necesario para LoadBalancer
if [ "$INGRESS_TYPE" != "LoadBalancer" ]; then
    echo -e "${YELLOW}📋 Paso 3: El Ingress Gateway no es de tipo LoadBalancer.${NC}"
    echo -e "${YELLOW}ℹ️ Tienes estas opciones para exponer tu servicio:${NC}"
    echo -e "1. Utilizar MetalLB para habilitar soporte de LoadBalancer (recomendado)"
    echo -e "2. Cambiar el servicio a NodePort"
    echo -e "3. Dejar como está ($INGRESS_TYPE) y configurar manualmente el acceso externo"
    
    read -p "Elige una opción (1, 2, 3): " OPTION
    
    case $OPTION in
        1)
            echo -e "${YELLOW}🔄 Habilitando MetalLB...${NC}"
            ./scripts/setup-metallb.sh
            
            echo -e "${YELLOW}🔄 Cambiando el tipo de servicio de Istio Ingress Gateway a LoadBalancer...${NC}"
            $KUBECTL_CMD patch svc istio-ingressgateway -n istio-system -p '{"spec": {"type": "LoadBalancer"}}'
            ;;
        2)
            echo -e "${YELLOW}🔄 Cambiando el tipo de servicio de Istio Ingress Gateway a NodePort...${NC}"
            $KUBECTL_CMD patch svc istio-ingressgateway -n istio-system -p '{"spec": {"type": "NodePort"}}'
            ;;
        3)
            echo -e "${YELLOW}ℹ️ Manteniendo la configuración actual.${NC}"
            ;;
        *)
            echo -e "${RED}❌ Opción no válida.${NC}"
            exit 1
            ;;
    esac
else
    echo -e "${GREEN}✅ El Istio Ingress Gateway ya es de tipo LoadBalancer.${NC}"
fi

# 4. Esperar a que el servicio esté listo
echo -e "${YELLOW}📋 Paso 4: Esperando a que el servicio esté listo...${NC}"
sleep 5  # Esperar un momento para que los cambios se apliquen

# 5. Obtener la IP externa del servicio
echo -e "${YELLOW}📋 Paso 5: Obteniendo la IP externa del servicio...${NC}"
./scripts/get-external-ip.sh

# 6. Verificar que la API sea accesible
echo -e "${YELLOW}📋 Paso 6: Verificando que la API sea accesible...${NC}"
echo -e "${YELLOW}ℹ️ Después de configurar DNS o el archivo /etc/hosts, la API debería estar accesible en:${NC}"
echo -e "${GREEN}https://host02.idea.lst.tfo.upm.es/raven-api/v1/health/${NC}"

# 7. Instrucciones adicionales
echo -e "${YELLOW}ℹ️ Instrucciones adicionales:${NC}"
echo -e "1. Si estás en un entorno de producción, necesitarás configurar un registro DNS adecuado"
echo -e "2. Para HTTPS, deberás configurar certificados TLS en el Gateway de Istio"
echo -e "3. Para monitorizar el tráfico, puedes usar las herramientas de Istio (Kiali, Jaeger, etc.)"

echo -e "${GREEN}✅ Proceso completado.${NC}"
