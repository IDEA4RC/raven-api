#!/bin/bash
set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

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

echo "🔍 Verificando configuración de Kubernetes para RAVEN API..."
echo

# Verificar kubectl
if ! command -v kubectl &> /dev/null; then
    show_error "kubectl no está instalado"
    exit 1
else
    show_success "kubectl encontrado"
    kubectl version --client --short 2>/dev/null || true
fi

# Verificar conexión al cluster
show_progress "Verificando conexión al cluster..."
if kubectl cluster-info &> /dev/null; then
    show_success "Conectado al cluster de Kubernetes"
    echo "   Cluster: $(kubectl config current-context)"
else
    show_error "No se puede conectar al cluster de Kubernetes"
    exit 1
fi

# Verificar nodos
show_progress "Verificando nodos del cluster..."
NODE_COUNT=$(kubectl get nodes --no-headers | wc -l)
READY_NODES=$(kubectl get nodes --no-headers | grep " Ready " | wc -l)
echo "   Nodos total: $NODE_COUNT"
echo "   Nodos listos: $READY_NODES"

if [ "$READY_NODES" -eq "$NODE_COUNT" ] && [ "$NODE_COUNT" -gt 0 ]; then
    show_success "Todos los nodos están listos"
else
    show_warning "Algunos nodos pueden no estar listos"
fi

# Verificar storage class
show_progress "Verificando storage classes..."
if kubectl get storageclass &> /dev/null; then
    DEFAULT_SC=$(kubectl get storageclass -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}')
    if [ ! -z "$DEFAULT_SC" ]; then
        show_success "Storage class por defecto encontrado: $DEFAULT_SC"
    else
        show_warning "No hay storage class por defecto configurado"
        echo "   Storage classes disponibles:"
        kubectl get storageclass --no-headers | awk '{print "     - " $1}'
    fi
else
    show_warning "No se encontraron storage classes"
fi

# Verificar Istio
show_progress "Verificando Istio..."
if kubectl get namespace istio-system &> /dev/null; then
    if kubectl get pods -n istio-system | grep -q "Running"; then
        show_success "Istio está instalado y funcionando"
        echo "   Componentes de Istio:"
        kubectl get pods -n istio-system --no-headers | awk '{print "     - " $1 ": " $3}'
    else
        show_warning "Istio está instalado pero algunos pods no están corriendo"
    fi
else
    show_warning "Istio no está instalado (opcional)"
fi

# Verificar LoadBalancer support
show_progress "Verificando soporte para LoadBalancer..."
LB_SERVICES=$(kubectl get services --all-namespaces --field-selector spec.type=LoadBalancer --no-headers 2>/dev/null | wc -l)
if [ "$LB_SERVICES" -gt 0 ]; then
    show_success "Soporte para LoadBalancer detectado"
else
    show_warning "No se detectó soporte para LoadBalancer (usará NodePort o port-forward)"
fi

# Verificar registry (para microk8s)
show_progress "Verificando registry de contenedores..."
if kubectl get service registry -n container-registry &> /dev/null; then
    show_success "Registry local de MicroK8s encontrado"
    echo "   Endpoint: localhost:32000"
elif kubectl get configmap -n kube-system | grep -q "microk8s"; then
    show_warning "MicroK8s detectado pero registry no habilitado"
    echo "   Para habilitar: microk8s enable registry"
else
    show_warning "Registry local no detectado (usará registry externo)"
fi

# Verificar recursos disponibles
show_progress "Verificando recursos del cluster..."
echo "   Recursos por nodo:"
kubectl describe nodes | grep -A 4 "Allocatable:" | grep -E "(cpu|memory)" | head -8 | while read line; do
    echo "     $line"
done

# Verificar namespace de destino
show_progress "Verificando namespace raven-api..."
if kubectl get namespace raven-api &> /dev/null; then
    show_warning "Namespace raven-api ya existe"
    echo "   Recursos existentes:"
    kubectl get all -n raven-api --no-headers 2>/dev/null | awk '{print "     - " $1}' | head -10 || echo "     (ninguno)"
else
    show_success "Namespace raven-api listo para crear"
fi

echo
echo "📋 Resumen de la verificación:"
echo "   - Cluster: $(show_success "✓ Conectado")"
echo "   - Nodos: $(show_success "✓ $READY_NODES/$NODE_COUNT listos")"
echo "   - Storage: $(if [ ! -z "$DEFAULT_SC" ]; then show_success "✓ Disponible"; else show_warning "⚠ Revisar"; fi)"
echo "   - Registry: $(if kubectl get service registry -n container-registry &> /dev/null; then show_success "✓ Local"; else show_warning "⚠ Externo"; fi)"
echo "   - Istio: $(if kubectl get namespace istio-system &> /dev/null; then show_success "✓ Instalado"; else show_warning "⚠ No instalado"; fi)"

echo
echo "🚀 Siguiente paso:"
echo "   ./scripts/build-docker.sh"
echo "   ./scripts/deploy-k8s.sh"
