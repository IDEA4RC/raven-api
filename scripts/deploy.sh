#!/bin/bash
# Script to build and deploy to Kubernetes with Istio

# Configuration
NAMESPACE="raven"
IMAGE_NAME="raven-api"
IMAGE_TAG="latest"
REGISTRY="" 

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting deployment of RAVEN API in Kubernetes with Istio${NC}"

# Building the image
echo -e "${YELLOW}🔨 Building the Docker image...${NC}"
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

# Create namespace if it doesn't exist
echo -e "${YELLOW}🌍 Creating namespace if it doesn't exist...${NC}"
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Label namespace for Istio injection
echo -e "${YELLOW}🏷️ Enabling Istio injection for namespace...${NC}"
kubectl label namespace ${NAMESPACE} istio-injection=enabled --overwrite

# Apply secrets first
echo -e "${YELLOW}🔑 Applying secrets...${NC}"
kubectl apply -f kubernetes/secrets.yaml -n ${NAMESPACE}

# Apply the rest of the Kubernetes resources
echo -e "${YELLOW}🚢 Applying deployment...${NC}"
kubectl apply -f kubernetes/deployment.yaml -n ${NAMESPACE}

echo -e "${YELLOW}🔄 Applying service...${NC}"
kubectl apply -f kubernetes/service.yaml -n ${NAMESPACE}

echo -e "${YELLOW}🚪 Applying gateway...${NC}"
kubectl apply -f kubernetes/gateway.yaml -n ${NAMESPACE}

echo -e "${YELLOW}🌐 Applying virtual service...${NC}"
kubectl apply -f kubernetes/virtual-service.yaml -n ${NAMESPACE}

# Verify the deployment status
echo -e "${YELLOW}🔍 Verifying deployment status...${NC}"
kubectl get pods -n ${NAMESPACE}

echo -e "${GREEN}✅ Deployment completed. Verify the status with 'kubectl get pods -n ${NAMESPACE}'${NC}"
echo -e "${GREEN}📊 You can monitor the service with Istio tools (Kiali, Jaeger, etc.)${NC}"

# Build Docker image
echo -e "${YELLOW}📦 Building Docker image...${NC}"
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

# Check if a registry was specified
if [ ! -z "$REGISTRY" ]; then
    # Tag image for the registry
    echo -e "${YELLOW}🏷️  Tagging image for registry...${NC}"
    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
    
    # Push image to registry
    echo -e "${YELLOW}📤 Pushing image to registry...${NC}"
    docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
fi

# Check if the namespace exists, if not, create it
if ! kubectl get namespace ${NAMESPACE} &> /dev/null; then
    echo -e "${YELLOW}🌐 Creating namespace ${NAMESPACE}...${NC}"
    kubectl create namespace ${NAMESPACE}
    
    # Enable Istio injection
    echo -e "${YELLOW}🔧 Enabling Istio injection in namespace...${NC}"
    kubectl label namespace ${NAMESPACE} istio-injection=enabled
fi

# Apply Kubernetes manifests
echo -e "${YELLOW}📄 Applying Kubernetes manifests...${NC}"

# Apply secrets first
echo -e "${YELLOW}🔑 Applying secrets...${NC}"
kubectl apply -f kubernetes/secrets.yaml -n ${NAMESPACE}

# Apply the rest of the resources
echo -e "${YELLOW}🚢 Applying deployment...${NC}"
kubectl apply -f kubernetes/deployment.yaml -n ${NAMESPACE}

echo -e "${YELLOW}🔄 Aplicando service...${NC}"
kubectl apply -f kubernetes/service.yaml -n ${NAMESPACE}

echo -e "${YELLOW}🚪 Aplicando gateway...${NC}"
kubectl apply -f kubernetes/gateway.yaml -n ${NAMESPACE}

echo -e "${YELLOW}🌐 Aplicando virtual service...${NC}"
kubectl apply -f kubernetes/virtual-service.yaml -n ${NAMESPACE}

# Verificar el estado del despliegue
echo -e "${YELLOW}🔍 Verificando estado del despliegue...${NC}"
kubectl get pods -n ${NAMESPACE}

# Esperar a que todos los pods estén listos
echo -e "${YELLOW}⏳ Esperando a que los pods estén listos...${NC}"
kubectl wait --for=condition=ready pod -l app=raven-api -n ${NAMESPACE} --timeout=120s

# Inicializar la base de datos con datos de ejemplo
echo -e "${YELLOW}🗃️ Inicializando la base de datos con datos de ejemplo...${NC}"
POD_NAME=$(kubectl get pods -n ${NAMESPACE} -l app=raven-api -o jsonpath="{.items[0].metadata.name}")
kubectl exec -n ${NAMESPACE} ${POD_NAME} -- python -m scripts.seed_db

echo -e "${GREEN}✅ Despliegue completado. Verifica el estado con 'kubectl get pods -n ${NAMESPACE}'${NC}"
echo -e "${GREEN}📊 Puedes monitorear el servicio con las herramientas de Istio (Kiali, Jaeger, etc.)${NC}"
