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
MONITORING_NAMESPACE="monitoring"
DOMAIN="orchestrator.idea.lst.tfo.upm.es"
IP_ADDRESS="138.4.10.238"

echo -e "${CYAN}🚀 Despliegue RAVEN API con HTTPS + PGAdmin + Observabilidad${NC}"
echo -e "${CYAN}=========================================================${NC}"
echo ""
echo -e "${GREEN}Dominio base:${NC} https://${DOMAIN}"

# Resolver de kubectl (usa kubectl si existe o microk8s kubectl como fallback)
KUBECTL=""
resolve_kubectl() {
    if command -v kubectl >/dev/null 2>&1; then
        KUBECTL="kubectl"
        return
    fi
    if command -v microk8s >/dev/null 2>&1; then
        KUBECTL="microk8s kubectl"
        return
    fi
}
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
    
    # Resolver kubectl
    resolve_kubectl
    if [ -z "${KUBECTL}" ]; then
        show_error "kubectl no está disponible. Instala kubectl o usa microk8s."
        echo "Sugerencia: en Ubuntu con snap: sudo snap install kubectl --classic"
        echo "Alternativa: usa 'microk8s kubectl' instalando MicroK8s."
        exit 1
    fi
    
    # Verificar conexión al cluster
    if ! ${KUBECTL} cluster-info &> /dev/null; then
        show_error "No se puede conectar al cluster de Kubernetes"
        exit 1
    fi
    
    # Verificar Istio
    if ! ${KUBECTL} get namespace istio-system &> /dev/null; then
        show_error "Istio no está instalado"
        exit 1
    fi
    
    # Verificar cert-manager
    if ! ${KUBECTL} get namespace cert-manager &> /dev/null; then
        show_error "cert-manager no está instalado"
        exit 1
    fi
    
    show_success "Prerrequisitos verificados"
}

    # Verificar prerrequisitos (modo local, sin cert-manager)
    check_prerequisites_local() {
        show_step "Verificando prerrequisitos (modo local, sin cert-manager)..."

        # Resolver kubectl
        resolve_kubectl
        if [ -z "${KUBECTL}" ]; then
            show_error "kubectl no está disponible. Instala kubectl o usa microk8s."
            echo "Sugerencia: en Ubuntu con snap: sudo snap install kubectl --classic"
            echo "Alternativa: usa 'microk8s kubectl' instalando MicroK8s."
            exit 1
        fi

        # Verificar conexión al cluster
        if ! ${KUBECTL} cluster-info &> /dev/null; then
            show_error "No se puede conectar al cluster de Kubernetes"
            exit 1
        fi

        # Verificar Istio
        if ! ${KUBECTL} get namespace istio-system &> /dev/null; then
            show_error "Istio no está instalado"
            exit 1
        fi

        show_success "Prerrequisitos locales verificados"
    }

# Crear namespace si no existe
create_namespace() {
    show_step "Creando namespaces..."
    ${KUBECTL} create namespace ${NAMESPACE} --dry-run=client -o yaml | ${KUBECTL} apply -f -
    ${KUBECTL} create namespace ${MONITORING_NAMESPACE} --dry-run=client -o yaml | ${KUBECTL} apply -f -
    show_success "Namespaces ${NAMESPACE} y ${MONITORING_NAMESPACE} listos"
}

# Desplegar cert-manager recursos
deploy_cert_manager() {
    show_step "Configurando cert-manager..."
    
    # ClusterIssuer para Let's Encrypt
    ${KUBECTL} apply -f kubernetes/cluster-issuer.yaml

    # Certificate
    ${KUBECTL} apply -f kubernetes/certificate.yaml

    show_success "cert-manager configurado"
}

# Desplegar aplicación
deploy_app() {
    show_step "Desplegando aplicación RAVEN API..."
    
    # Secrets
    ${KUBECTL} apply -f kubernetes/api-secrets.yaml -n ${NAMESPACE}

    # PostgreSQL
    ${KUBECTL} apply -f kubernetes/postgres-deployment.yaml -n ${NAMESPACE}
    
    # RAVEN API
    ${KUBECTL} apply -f kubernetes/deployment.yaml -n ${NAMESPACE}
    ${KUBECTL} apply -f kubernetes/service.yaml -n ${NAMESPACE}
    
    show_success "Aplicación desplegada"
}

# Desplegar PGAdmin
deploy_pgadmin() {
    show_step "Desplegando PGAdmin..."
    ${KUBECTL} apply -f kubernetes/pgadmin-deploy.yaml -n ${NAMESPACE}

    show_success "PGAdmin desplegado"
}

# Desplegar Jaeger
deploy_jaeger() {
    show_step "Desplegando Jaeger..."

    ${KUBECTL} apply -f kubernetes/jaeger-deploy.yaml -n ${MONITORING_NAMESPACE}

    show_success "Jaeger desplegado"
}

# Desplegar Prometheus
deploy_prometheus() {
    show_step "Desplegando Prometheus..."
    
    ${KUBECTL} apply -f kubernetes/prometheus-deploy.yaml -n ${MONITORING_NAMESPACE}

    show_success "Prometheus desplegado"
}

# Desplegar Grafana
deploy_grafana() {
    show_step "Desplegando Grafana..."

    ${KUBECTL} apply -f kubernetes/grafana-deploy.yaml -n ${MONITORING_NAMESPACE}

    show_success "Grafana desplegado"
}

# Configurar red (Gateway + VirtualService)
deploy_networking() {
    show_step "Configurando red (Gateway + VirtualService)..."

    # Aplicar Gateway desde archivo
    ${KUBECTL} apply -f kubernetes/gateway.yaml
    
    # Aplicar VirtualService desde archivo
    ${KUBECTL} apply -f kubernetes/virtual-service.yaml

    show_success "Red configurada"
}

# Configurar red (Gateway HTTP-only para entorno local)
deploy_networking_local() {
        show_step "Configurando red local (Gateway HTTP sin TLS)..."

        # Crear/actualizar un Gateway sin TLS (solo HTTP 80)
        cat <<EOF | ${KUBECTL} apply -f -
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
    name: raven-gateway
    namespace: default
spec:
    selector:
        istio: ingressgateway
    servers:
    - port:
            number: 80
            name: http
            protocol: HTTP
        hosts:
        - "${DOMAIN}"
        - "vantage.${DOMAIN}"
        - "pgadmin.${DOMAIN}"
        - "jaeger.${DOMAIN}"
        - "prometheus.${DOMAIN}"
        - "grafana.${DOMAIN}"
EOF

        # Aplicar VirtualService desde archivo (paths y rutas)
        ${KUBECTL} apply -f kubernetes/virtual-service.yaml

        show_success "Red local configurada"
}

# Despliegue local (sin certificados)
deploy_local() {
        check_prerequisites_local
        create_namespace
        # No cert-manager ni certificados en local
        deploy_app
        deploy_pgadmin
        deploy_jaeger
        deploy_prometheus
        deploy_grafana
        deploy_networking_local
        sleep 10
        verify_deployment

        echo ""
        echo -e "${CYAN}💡 Acceso local (HTTP):${NC}"
        echo -e "   Salud API vía NodePort o LB: http://${IP_ADDRESS}/raven-api/v1/health/"
        echo -e "   Swagger (si usas Host header o DNS local): http://${DOMAIN}/docs"
}

# Esperar a que el certificado esté listo
wait_for_certificate() {
    show_step "Esperando certificado SSL..."
    
    local max_attempts=30
    local attempts=0
    
    while [ $attempts -lt $max_attempts ]; do
        if ${KUBECTL} get certificate raven-api-tls -n istio-system -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' | grep -q "True"; then
            # shellcheck disable=SC2016
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
    ${KUBECTL} get pods -n ${NAMESPACE}
    echo ""
    
    echo "Pods en namespace ${MONITORING_NAMESPACE}:"
    ${KUBECTL} get pods -n ${MONITORING_NAMESPACE}
    echo ""
    
    # Verificar servicios
    echo "Servicios en namespace ${NAMESPACE}:"
    ${KUBECTL} get svc -n ${NAMESPACE}
    echo ""
    
    echo "Servicios en namespace ${MONITORING_NAMESPACE}:"
    ${KUBECTL} get svc -n ${MONITORING_NAMESPACE}
    echo ""
    
    # Verificar Gateway y VirtualService
    echo "Gateway y VirtualServices:"
    ${KUBECTL} get gateway,virtualservice
    echo ""
    
    # Verificar certificado
    echo "Estado del certificado:"
    ${KUBECTL} get certificate -n istio-system
    echo ""
    
    show_success "Verificación completada"
}

# Mostrar información final
show_final_info() {
    echo ""
    echo -e "${CYAN}🎉 ¡Despliegue completado!${NC}"
    echo -e "${CYAN}=========================${NC}"
    echo ""
    echo -e "${GREEN}🌐 URLs disponibles:${NC}"
    echo -e "   API:         https://${DOMAIN}"
    echo -e "   PGAdmin:     https://pgadmin.${DOMAIN}"
    echo -e "   Jaeger:      https://jaeger.${DOMAIN}"
    echo -e "   Prometheus:  https://prometheus.${DOMAIN}"
    echo -e "   Grafana:     https://grafana.${DOMAIN}"
    echo ""
    echo -e "${GREEN}🔐 Credenciales:${NC}"
    echo -e "   PGAdmin:     admin@${DOMAIN} / admin123"
    echo -e "   Grafana:     admin / admin123"
    echo ""
    echo -e "${GREEN}🔧 Configuración PGAdmin:${NC}"
    echo -e "   Host:        postgres-service.${NAMESPACE}.svc.cluster.local"
    echo -e "   Port:        5432"
    echo -e "   Database:    raven_db"
    echo -e "   Username:    raven_user"
    echo -e "   Password:    raven_password"
    echo ""
    echo -e "${GREEN}📊 Comandos útiles:${NC}"
    echo -e "   Ver pods API:        ${KUBECTL} get pods -n ${NAMESPACE}"
    echo -e "   Ver pods monitor:    ${KUBECTL} get pods -n ${MONITORING_NAMESPACE}"
    echo -e "   Ver logs API:        ${KUBECTL} logs -n ${NAMESPACE} -l app=raven-api -f"
    echo -e "   Ver logs DB:         ${KUBECTL} logs -n ${NAMESPACE} -l app=postgres -f"
    echo -e "   Ver logs Jaeger:     ${KUBECTL} logs -n ${MONITORING_NAMESPACE} -l app=jaeger -f"
    echo -e "   Estado SSL:          ${KUBECTL} get certificate -n istio-system"
    echo ""
    echo -e "${GREEN}🔧 Scripts disponibles:${NC}"
    echo -e "   Migrar BD:       ./scripts/migrate.sh migrate"
    echo -e "   Limpiar BD:      ./scripts/migrate.sh clean"
    echo -e "   Health check:    python scripts/health_check.py"
    echo ""
    echo -e "${YELLOW}💡 Notas importantes:${NC}"
    echo -e "   • Si el certificado SSL no está listo aún, puede tardar unos minutos"
    echo -e "   • Configurar DNS para los subdominios: pgadmin, jaeger, prometheus, grafana"
    echo -e "   • Prometheus recogerá métricas automáticamente de pods anotados"
    echo -e "   • Jaeger está configurado para recibir trazas OTLP en puerto 4317"
}

# Función principal
main() {
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            create_namespace
            deploy_cert_manager
            deploy_app
            deploy_pgadmin
            deploy_jaeger
            deploy_prometheus
            deploy_grafana
            wait_for_certificate
            deploy_networking
            sleep 15  # Dar tiempo para que se propague
            verify_deployment
            show_final_info
            ;;
        "deploy-local")
            deploy_local
            ;;
        "clean")
            show_step "Limpiando recursos..."
            resolve_kubectl
            ${KUBECTL} delete namespace ${NAMESPACE} --ignore-not-found=true || true
            ${KUBECTL} delete namespace ${MONITORING_NAMESPACE} --ignore-not-found=true || true
            ${KUBECTL} delete gateway raven-gateway --ignore-not-found=true || true
            ${KUBECTL} delete virtualservice raven-api-vs --ignore-not-found=true || true
            ${KUBECTL} delete certificate raven-api-tls -n istio-system --ignore-not-found=true || true
            ${KUBECTL} delete clusterissuer letsencrypt-prod --ignore-not-found=true || true
            show_success "Recursos limpiados"
            ;;
        "status")
            verify_deployment
            ;;
        "monitoring")
            show_step "Desplegando solo stack de monitoreo..."
            create_namespace
            deploy_jaeger
            deploy_prometheus
            deploy_grafana
            show_success "Stack de monitoreo desplegado"
            ;;
        "pgadmin")
            show_step "Desplegando solo PGAdmin..."
            create_namespace
            deploy_pgadmin
            show_success "PGAdmin desplegado"
            ;;
        "help")
            echo "Uso: $0 [deploy|deploy-local|clean|status|monitoring|pgadmin|help]"
            echo ""
            echo "Comandos:"
            echo "  deploy     - Desplegar todo (por defecto)"
            echo "  deploy-local - Desplegar entorno local sin TLS/certificados"
            echo "  clean      - Limpiar todos los recursos"
            echo "  status     - Verificar estado del despliegue"
            echo "  monitoring - Desplegar solo Jaeger + Prometheus + Grafana"
            echo "  pgadmin    - Desplegar solo PGAdmin"
            echo "  help       - Mostrar esta ayuda"
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
