#!/bin/bash

# Script de despliegue completo para RAVEN API con HTTPS
# Automatiza todo el proceso de configuración

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuración
NAMESPACE="raven-api"
DOMAIN="orchestrator.idea.lst.tfo.upm.es"
IP_ADDRESS="138.4.10.238"

echo -e "${CYAN}🚀 Despliegue RAVEN API con HTTPS${NC}"
echo -e "${CYAN}====================================${NC}"
echo ""
# Función para mostrar progreso
show_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

# Función para mostrar éxito
show_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Función para mostrar advertencia
show_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Función para mostrar error
show_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Función para esperar entrada del usuario
wait_for_user() {
    echo -e "${YELLOW}Presiona Enter para continuar...${NC}"
    read
}

# Verificar prerrequisitos
check_prerequisites() {
    show_step "Verificando prerrequisitos..."
    
    # Verificar kubectl
    if ! command -v kubectl &> /dev/null; then
        show_error "kubectl no está instalado"
        exit 1
    fi
    
    # Verificar conexión al cluster
    if ! kubectl cluster-info &> /dev/null; then
        show_error "No se puede conectar al cluster de Kubernetes"
        exit 1
    fi
    
    # Verificar Istio
    if ! kubectl get namespace istio-system &> /dev/null; then
        show_error "Istio no está instalado"
        exit 1
    fi
    
    # Verificar cert-manager
    if ! kubectl get namespace cert-manager &> /dev/null; then
        show_error "cert-manager no está instalado"
        exit 1
    fi
    
    show_success "Prerrequisitos verificados"
}

# Crear namespace si no existe
create_namespace() {
    show_step "Creando namespace ${NAMESPACE}..."
    kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    show_success "Namespace ${NAMESPACE} listo"
}

# Desplegar cert-manager recursos
deploy_cert_manager() {
    show_step "Configurando cert-manager..."
    
    # ClusterIssuer para Let's Encrypt
    cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@${DOMAIN}
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: istio
EOF

    # Certificate
    cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: raven-api-tls
  namespace: istio-system
spec:
  secretName: raven-api-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
    group: cert-manager.io
  dnsNames:
  - ${DOMAIN}
  duration: 2160h  # 90 días
  renewBefore: 360h  # Renovar 15 días antes
  usages:
  - digital signature
  - key encipherment
EOF

    show_success "cert-manager configurado"
}

# Desplegar aplicación
deploy_app() {
    show_step "Desplegando aplicación RAVEN API..."
    
    # Secrets
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: raven-api-secrets
  namespace: ${NAMESPACE}
type: Opaque
stringData:
  database-uri: "postgresql://raven_user:raven_password@postgres-service:5432/raven_db"
  secret-key: "$(openssl rand -hex 32)"
  postgres-user: "raven_user"
  postgres-password: "raven_password"
  postgres-db: "raven_db"
EOF

    # PostgreSQL
    kubectl apply -f kubernetes/postgres-deployment.yaml -n ${NAMESPACE}
    
    # RAVEN API
    kubectl apply -f kubernetes/deployment.yaml -n ${NAMESPACE}
    kubectl apply -f kubernetes/service.yaml -n ${NAMESPACE}
    
    show_success "Aplicación desplegada"
}

# Configurar red (Gateway + VirtualService)
deploy_networking() {
    show_step "Configurando red (Gateway + VirtualService)..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: raven-gateway
  namespace: default
spec:
  selector:
    istio: ingressgateway
  servers:
  # HTTP - redirige a HTTPS
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "${DOMAIN}"
    - "${IP_ADDRESS}"
    tls:
      httpsRedirect: true
  # HTTPS - certificado válido
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - "${DOMAIN}"
    tls:
      mode: SIMPLE
      credentialName: raven-api-tls-secret
---
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: raven-api-vs
  namespace: default
spec:
  hosts:
  - "${DOMAIN}"
  - "${IP_ADDRESS}"
  gateways:
  - raven-gateway
  http:
  - match:
    - uri:
        prefix: /
    route:
    - destination:
        host: raven-api.${NAMESPACE}.svc.cluster.local
        port:
          number: 80
EOF

    show_success "Red configurada"
}

# Esperar a que el certificado esté listo
wait_for_certificate() {
    show_step "Esperando certificado SSL..."
    
    local max_attempts=30
    local attempts=0
    
    while [ $attempts -lt $max_attempts ]; do
        if kubectl get certificate raven-api-tls -n istio-system -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' | grep -q "True"; then
            show_success "Certificado SSL listo"
            return 0
        fi
        
        echo -n "."
        sleep 10
        attempts=$((attempts + 1))
    done
    
    show_warning "El certificado está tardando más de lo esperado. Continuando..."
}

# Verificar despliegue
verify_deployment() {
    show_step "Verificando despliegue..."
    
    # Verificar pods
    echo "Pods en namespace ${NAMESPACE}:"
    kubectl get pods -n ${NAMESPACE}
    echo ""
    
    # Verificar servicios
    echo "Servicios en namespace ${NAMESPACE}:"
    kubectl get svc -n ${NAMESPACE}
    echo ""
    
    # Verificar Gateway y VirtualService
    echo "Gateway y VirtualService:"
    kubectl get gateway,virtualservice
    echo ""
    
    # Verificar certificado
    echo "Estado del certificado:"
    kubectl get certificate -n istio-system
    echo ""
    
    show_success "Verificación completada"
}

# Mostrar información final
show_final_info() {
    echo ""
    echo -e "${CYAN}🎉 ¡Despliegue completado!${NC}"
    echo -e "${CYAN}=========================${NC}"
    echo ""
    echo -e "${GREEN}🌐 URL de la API:${NC}"
    echo -e "   HTTPS: https://${DOMAIN}"
    echo -e "   HTTP:  http://${DOMAIN} (redirige a HTTPS)"
    echo ""
    echo -e "${GREEN}📊 Comandos útiles:${NC}"
    echo -e "   Ver pods:        kubectl get pods -n ${NAMESPACE}"
    echo -e "   Ver logs API:    kubectl logs -n ${NAMESPACE} -l app=raven-api -f"
    echo -e "   Ver logs DB:     kubectl logs -n ${NAMESPACE} -l app=postgres -f"
    echo -e "   Estado SSL:      kubectl get certificate -n istio-system"
    echo ""
    echo -e "${GREEN}🔧 Scripts disponibles:${NC}"
    echo -e "   Migrar BD:       ./scripts/migrate.sh migrate"
    echo -e "   Limpiar BD:      ./scripts/migrate.sh clean"
    echo -e "   Health check:    python scripts/health_check.py"
    echo ""
    echo -e "${YELLOW}💡 Nota: Si el certificado SSL no está listo aún, puede tardar unos minutos.${NC}"
}

# Función principal
main() {
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            create_namespace
            deploy_cert_manager
            deploy_app
            wait_for_certificate
            deploy_networking
            sleep 10  # Dar tiempo para que se propague
            verify_deployment
            show_final_info
            ;;
        "clean")
            show_step "Limpiando recursos..."
            kubectl delete namespace ${NAMESPACE} --ignore-not-found=true
            kubectl delete gateway raven-gateway --ignore-not-found=true
            kubectl delete virtualservice raven-api-vs --ignore-not-found=true
            kubectl delete certificate raven-api-tls -n istio-system --ignore-not-found=true
            kubectl delete clusterissuer letsencrypt-prod --ignore-not-found=true
            show_success "Recursos limpiados"
            ;;
        "status")
            verify_deployment
            ;;
        "help")
            echo "Uso: $0 [deploy|clean|status|help]"
            echo ""
            echo "Comandos:"
            echo "  deploy  - Desplegar todo (por defecto)"
            echo "  clean   - Limpiar todos los recursos"
            echo "  status  - Verificar estado del despliegue"
            echo "  help    - Mostrar esta ayuda"
            ;;
        *)
            show_error "Comando desconocido: $1"
            echo "Usa '$0 help' para ver los comandos disponibles"
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"
