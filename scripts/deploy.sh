#!/bin/bash
# Script para construir e implementar en Kubernetes con Istio

# Configuración
NAMESPACE="raven"
IMAGE_NAME="raven-api"
IMAGE_TAG="latest"
REGISTRY="localhost:32000"  # Registro local de MicroK8s
KUBECTL_CMD="microk8s kubectl"  # Usar microk8s kubectl directamente

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin Color

echo -e "${GREEN}🚀 Iniciando despliegue de RAVEN API en Kubernetes con Istio${NC}"

# Construir la imagen Docker (sin usar caché)
echo -e "${YELLOW}📦 Construyendo imagen Docker (sin caché)...${NC}"
docker build --no-cache -t ${IMAGE_NAME}:${IMAGE_TAG} .

# Etiquetar la imagen para el registro local de MicroK8s
echo -e "${YELLOW}🏷️ Etiquetando imagen para el registro local de MicroK8s...${NC}"
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}

# Enviar la imagen al registro local de MicroK8s
echo -e "${YELLOW}📤 Enviando imagen al registro local...${NC}"
docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}

# Verificar si se especificó un registro
if [ -z "$REGISTRY" ]; then
    echo -e "${RED}❌ Error: No se ha especificado un registro. Usando imagen local.${NC}"
    # Nota: En este caso podríamos manejar el flujo de otra manera si se requiere
fi

# Verificar la disponibilidad de microk8s kubectl
if ! command -v microk8s &> /dev/null; then
    echo -e "${RED}❌ Error: microk8s no está instalado o no está en el PATH.${NC}"
    echo -e "${YELLOW}ℹ️ Por favor, instala microk8s o asegúrate de que esté en tu PATH.${NC}"
    exit 1
fi

# Verificar si el namespace existe, si no, crearlo
if ! ${KUBECTL_CMD} get namespace ${NAMESPACE} &> /dev/null; then
    echo -e "${YELLOW}🌐 Creando namespace ${NAMESPACE}...${NC}"
    ${KUBECTL_CMD} create namespace ${NAMESPACE}
    
    # Habilitar inyección de Istio
    echo -e "${YELLOW}🔧 Habilitando inyección de Istio en el namespace...${NC}"
    ${KUBECTL_CMD} label namespace ${NAMESPACE} istio-injection=enabled
else
    # Asegurarse de que la inyección de Istio esté habilitada
    echo -e "${YELLOW}🏷️ Asegurando que la inyección de Istio esté habilitada...${NC}"
    ${KUBECTL_CMD} label namespace ${NAMESPACE} istio-injection=enabled --overwrite
fi

# Aplicar manifiestos de Kubernetes
echo -e "${YELLOW}📄 Aplicando manifiestos de Kubernetes...${NC}"

# Aplicar primero los secretos
echo -e "${YELLOW}🔑 Aplicando secretos...${NC}"
${KUBECTL_CMD} apply -f kubernetes/secrets.yaml -n ${NAMESPACE}

# Aplicar el resto de recursos
echo -e "${YELLOW}🚢 Aplicando deployment...${NC}"
${KUBECTL_CMD} apply -f kubernetes/deployment.yaml -n ${NAMESPACE}

echo -e "${YELLOW}🔄 Aplicando service...${NC}"
${KUBECTL_CMD} apply -f kubernetes/service.yaml -n ${NAMESPACE}

echo -e "${YELLOW}🚪 Aplicando gateway...${NC}"
${KUBECTL_CMD} apply -f kubernetes/gateway.yaml -n ${NAMESPACE}

echo -e "${YELLOW}🌐 Aplicando virtual service...${NC}"
${KUBECTL_CMD} apply -f kubernetes/virtual-service.yaml -n ${NAMESPACE}

# Verificar el estado del despliegue
echo -e "${YELLOW}🔍 Verificando estado del despliegue...${NC}"
${KUBECTL_CMD} get pods -n ${NAMESPACE}

# Esperar a que todos los pods estén listos
echo -e "${YELLOW}⏳ Esperando a que los pods estén listos...${NC}"
${KUBECTL_CMD} wait --for=condition=ready pod -l app=raven-api -n ${NAMESPACE} --timeout=120s

# Inicializar la base de datos con datos de ejemplo
echo -e "${YELLOW}🗃️ Inicializando la base de datos con datos de ejemplo...${NC}"
POD_NAME=$(${KUBECTL_CMD} get pods -n ${NAMESPACE} -l app=raven-api -o jsonpath="{.items[0].metadata.name}")
${KUBECTL_CMD} exec -n ${NAMESPACE} ${POD_NAME} -- python -m scripts.seed_db

echo -e "${GREEN}✅ Despliegue completado. Verifica el estado con '${KUBECTL_CMD} get pods -n ${NAMESPACE}'${NC}"
echo -e "${GREEN}📊 Puedes monitorear el servicio con las herramientas de Istio (Kiali, Jaeger, etc.)${NC}"
