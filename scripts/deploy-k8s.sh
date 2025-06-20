#!/bin/bash
set -e

echo "🚀 Deploying RAVEN API to Kubernetes..."

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para mostrar el progreso
show_progress() {
    echo -e "${BLUE}▶️  $1${NC}"
}

show_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

show_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

show_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar que kubectl está disponible
if ! command -v kubectl &> /dev/null; then
    show_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Verificar conexión al cluster
if ! kubectl cluster-info &> /dev/null; then
    show_error "Cannot connect to Kubernetes cluster"
    exit 1
fi

show_success "Connected to Kubernetes cluster"

# Crear namespace si no existe
show_progress "Creating namespace raven-api..."
kubectl create namespace raven-api --dry-run=client -o yaml | kubectl apply -f -

# Aplicar configuraciones en orden
show_progress "1. Applying secrets..."
kubectl apply -n raven-api -f kubernetes/secrets.yaml

show_progress "2. Applying ConfigMap..."
kubectl apply -n raven-api -f kubernetes/configmap.yaml

show_progress "3. Deploying PostgreSQL..."
kubectl apply -n raven-api -f kubernetes/postgres-deployment.yaml

show_progress "4. Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n raven-api --timeout=120s

show_progress "5. Initializing database..."
kubectl apply -n raven-api -f kubernetes/configmap.yaml
kubectl wait --for=condition=complete job/raven-api-db-init -n raven-api --timeout=120s || true

show_progress "6. Deploying RAVEN API..."
kubectl apply -n raven-api -f kubernetes/deployment.yaml
kubectl apply -n raven-api -f kubernetes/service.yaml

show_progress "7. Waiting for API to be ready..."
kubectl wait --for=condition=ready pod -l app=raven-api -n raven-api --timeout=120s

# Aplicar configuraciones de Istio si están disponibles
if kubectl get crd gateways.networking.istio.io &> /dev/null; then
    show_progress "8. Configuring Istio Gateway and VirtualService..."
    kubectl apply -n raven-api -f kubernetes/gateway.yaml
    kubectl apply -n raven-api -f kubernetes/virtual-service.yaml
    show_success "Istio configuration applied"
else
    show_warning "Istio not detected, skipping Gateway configuration"
fi

# Mostrar información del despliegue
echo
show_success "🎉 Deployment completed!"
echo
echo "📊 Deployment status:"
kubectl get pods,svc,pvc -n raven-api

echo
echo "🌐 To access the API:"
echo "   - Health endpoint: /raven-api/v1/health/"
echo "   - Documentation: /docs"

# Obtener información de acceso
if kubectl get service raven-api -n raven-api -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null; then
    EXTERNAL_IP=$(kubectl get service raven-api -n raven-api -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    echo "   - URL externa: http://$EXTERNAL_IP:8000/raven-api/v1/health/"
elif kubectl get service raven-api -n raven-api -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null; then
    EXTERNAL_HOST=$(kubectl get service raven-api -n raven-api -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    echo "   - URL externa: http://$EXTERNAL_HOST:8000/raven-api/v1/health/"
else
    NODE_PORT=$(kubectl get service raven-api -n raven-api -o jsonpath='{.spec.ports[0].nodePort}')
    if [ ! -z "$NODE_PORT" ]; then
        echo "   - NodePort: http://<node-ip>:$NODE_PORT/raven-api/v1/health/"
    else
        echo "   - ClusterIP: kubectl port-forward service/raven-api 8000:80 -n raven-api"
        echo "     Then access: http://localhost:8000/raven-api/v1/health/"
    fi
fi

echo
echo "🔧 Useful commands:"
echo "   - View logs: kubectl logs -f deployment/raven-api -n raven-api"
echo "   - View status: kubectl get pods -n raven-api -w"
echo "   - Scale: kubectl scale deployment raven-api --replicas=3 -n raven-api"
echo "   - Port-forward: kubectl port-forward service/raven-api 8000:80 -n raven-api"

show_success "Deployment complete! 🚀"
