#!/bin/bash
set -e

echo "🚀 Desplegando RAVEN API en Kubernetes..."

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
    show_error "kubectl no está instalado o no está en el PATH"
    exit 1
fi

# Verificar conexión al cluster
if ! kubectl cluster-info &> /dev/null; then
    show_error "No se puede conectar al cluster de Kubernetes"
    exit 1
fi

show_success "Conectado al cluster de Kubernetes"

# Crear namespace si no existe
show_progress "Creando namespace raven-api..."
kubectl create namespace raven-api --dry-run=client -o yaml | kubectl apply -f -

# Aplicar configuraciones en orden
show_progress "1. Aplicando secrets..."
kubectl apply -n raven-api -f kubernetes/secrets.yaml

show_progress "2. Aplicando ConfigMap..."
kubectl apply -n raven-api -f kubernetes/configmap.yaml

show_progress "3. Desplegando PostgreSQL..."
kubectl apply -n raven-api -f kubernetes/postgres-deployment.yaml

show_progress "4. Esperando a que PostgreSQL esté listo..."
kubectl wait --for=condition=ready pod -l app=postgres -n raven-api --timeout=120s

show_progress "5. Inicializando base de datos..."
kubectl apply -n raven-api -f kubernetes/configmap.yaml
kubectl wait --for=condition=complete job/raven-api-db-init -n raven-api --timeout=120s || true

show_progress "6. Desplegando RAVEN API..."
kubectl apply -n raven-api -f kubernetes/deployment.yaml
kubectl apply -n raven-api -f kubernetes/service.yaml

show_progress "7. Esperando a que la API esté lista..."
kubectl wait --for=condition=ready pod -l app=raven-api -n raven-api --timeout=120s

# Aplicar configuraciones de Istio si están disponibles
if kubectl get crd gateways.networking.istio.io &> /dev/null; then
    show_progress "8. Configurando Istio Gateway y VirtualService..."
    kubectl apply -n raven-api -f kubernetes/gateway.yaml
    kubectl apply -n raven-api -f kubernetes/virtual-service.yaml
    show_success "Istio configuration applied"
else
    show_warning "Istio not detected, skipping Gateway configuration"
fi

# Mostrar información del despliegue
echo
show_success "🎉 Despliegue completado!"
echo
echo "📊 Estado del despliegue:"
kubectl get pods,svc,pvc -n raven-api

echo
echo "🌐 Para acceder a la API:"
echo "   - Endpoint de salud: /raven-api/v1/health/"
echo "   - Documentación: /docs"

# Obtener información de acceso
if kubectl get service raven-api-service -n raven-api -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null; then
    EXTERNAL_IP=$(kubectl get service raven-api-service -n raven-api -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    echo "   - URL externa: http://$EXTERNAL_IP:8000/raven-api/v1/health/"
elif kubectl get service raven-api-service -n raven-api -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null; then
    EXTERNAL_HOST=$(kubectl get service raven-api-service -n raven-api -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    echo "   - URL externa: http://$EXTERNAL_HOST:8000/raven-api/v1/health/"
else
    NODE_PORT=$(kubectl get service raven-api-service -n raven-api -o jsonpath='{.spec.ports[0].nodePort}')
    if [ ! -z "$NODE_PORT" ]; then
        echo "   - NodePort: http://<node-ip>:$NODE_PORT/raven-api/v1/health/"
    fi
fi

echo
echo "🔧 Comandos útiles:"
echo "   - Ver logs: kubectl logs -f deployment/raven-api -n raven-api"
echo "   - Ver estado: kubectl get pods -n raven-api -w"
echo "   - Escalar: kubectl scale deployment raven-api --replicas=3 -n raven-api"
echo "   - Port-forward: kubectl port-forward service/raven-api-service 8000:8000 -n raven-api"

show_success "Despliegue completo! 🚀"
