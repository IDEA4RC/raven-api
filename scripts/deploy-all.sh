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
    show_step "Creando namespaces..."
    kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace ${MONITORING_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    show_success "Namespaces ${NAMESPACE} y ${MONITORING_NAMESPACE} listos"
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
  - pgadmin.${DOMAIN}
  - jaeger.${DOMAIN}
  - prometheus.${DOMAIN}
  - grafana.${DOMAIN}
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
  # Telemetry configuration
  enable-telemetry: "true"
  telemetry-endpoint: "http://jaeger-collector.${MONITORING_NAMESPACE}.svc.cluster.local:4317"
  telemetry-sampling-rate: "1.0"
  # Prometheus configuration
  enable-prometheus: "true"
  metrics-port: "8000"
EOF

    # PostgreSQL
    kubectl apply -f kubernetes/postgres-deployment.yaml -n ${NAMESPACE}
    
    # RAVEN API
    kubectl apply -f kubernetes/deployment.yaml -n ${NAMESPACE}
    kubectl apply -f kubernetes/service.yaml -n ${NAMESPACE}
    
    show_success "Aplicación desplegada"
}

# Desplegar PGAdmin
deploy_pgadmin() {
    show_step "Desplegando PGAdmin..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: pgadmin-secret
  namespace: ${NAMESPACE}
type: Opaque
stringData:
  pgadmin-password: "admin123"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pgadmin
  namespace: ${NAMESPACE}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: pgadmin
  template:
    metadata:
      labels:
        app: pgadmin
    spec:
      containers:
      - name: pgadmin
        image: dpage/pgadmin4:latest
        ports:
        - containerPort: 80
        env:
        - name: PGADMIN_DEFAULT_EMAIL
          value: "admin@${DOMAIN}"
        - name: PGADMIN_DEFAULT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: pgadmin-secret
              key: pgadmin-password
        - name: PGADMIN_DISABLE_POSTFIX
          value: "true"
        volumeMounts:
        - name: pgadmin-data
          mountPath: /var/lib/pgadmin
      volumes:
      - name: pgadmin-data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: pgadmin-service
  namespace: ${NAMESPACE}
spec:
  selector:
    app: pgadmin
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF

    show_success "PGAdmin desplegado"
}

# Desplegar Jaeger
deploy_jaeger() {
    show_step "Desplegando Jaeger..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger
  namespace: ${MONITORING_NAMESPACE}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jaeger
  template:
    metadata:
      labels:
        app: jaeger
    spec:
      containers:
      - name: jaeger
        image: jaegertracing/all-in-one:latest
        ports:
        - containerPort: 16686  # UI
        - containerPort: 14250  # gRPC
        - containerPort: 14268  # HTTP
        - containerPort: 4317   # OTLP gRPC
        - containerPort: 4318   # OTLP HTTP
        env:
        - name: COLLECTOR_OTLP_ENABLED
          value: "true"
        - name: COLLECTOR_ZIPKIN_HOST_PORT
          value: ":9411"
---
apiVersion: v1
kind: Service
metadata:
  name: jaeger-service
  namespace: ${MONITORING_NAMESPACE}
spec:
  selector:
    app: jaeger
  ports:
  - name: ui
    port: 16686
    targetPort: 16686
  - name: grpc
    port: 14250
    targetPort: 14250
  - name: http
    port: 14268
    targetPort: 14268
  - name: otlp-grpc
    port: 4317
    targetPort: 4317
  - name: otlp-http
    port: 4318
    targetPort: 4318
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: jaeger-collector
  namespace: ${MONITORING_NAMESPACE}
spec:
  selector:
    app: jaeger
  ports:
  - name: otlp-grpc
    port: 4317
    targetPort: 4317
  - name: otlp-http
    port: 4318
    targetPort: 4318
  type: ClusterIP
EOF

    show_success "Jaeger desplegado"
}

# Desplegar Prometheus
deploy_prometheus() {
    show_step "Desplegando Prometheus..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: ${MONITORING_NAMESPACE}
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    scrape_configs:
    - job_name: 'prometheus'
      static_configs:
      - targets: ['localhost:9090']
    
    - job_name: 'raven-api'
      static_configs:
      - targets: ['raven-api.${NAMESPACE}.svc.cluster.local:8000']
      metrics_path: '/metrics'
      scrape_interval: 10s
    
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: ${MONITORING_NAMESPACE}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        args:
        - '--config.file=/etc/prometheus/prometheus.yml'
        - '--storage.tsdb.path=/prometheus/'
        - '--web.console.libraries=/etc/prometheus/console_libraries'
        - '--web.console.templates=/etc/prometheus/consoles'
        - '--web.enable-lifecycle'
        volumeMounts:
        - name: prometheus-config
          mountPath: /etc/prometheus/
        - name: prometheus-data
          mountPath: /prometheus/
      volumes:
      - name: prometheus-config
        configMap:
          name: prometheus-config
      - name: prometheus-data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus-service
  namespace: ${MONITORING_NAMESPACE}
spec:
  selector:
    app: prometheus
  ports:
  - port: 9090
    targetPort: 9090
  type: ClusterIP
EOF

    show_success "Prometheus desplegado"
}

# Desplegar Grafana
deploy_grafana() {
    show_step "Desplegando Grafana..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: grafana-secret
  namespace: ${MONITORING_NAMESPACE}
type: Opaque
stringData:
  admin-password: "admin123"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-datasources
  namespace: ${MONITORING_NAMESPACE}
data:
  datasources.yaml: |
    apiVersion: 1
    datasources:
    - name: Prometheus
      type: prometheus
      access: proxy
      url: http://prometheus-service:9090
      isDefault: true
    - name: Jaeger
      type: jaeger
      access: proxy
      url: http://jaeger-service:16686
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: ${MONITORING_NAMESPACE}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: grafana-secret
              key: admin-password
        - name: GF_INSTALL_PLUGINS
          value: "grafana-piechart-panel,grafana-clock-panel"
        volumeMounts:
        - name: grafana-datasources
          mountPath: /etc/grafana/provisioning/datasources
        - name: grafana-data
          mountPath: /var/lib/grafana
      volumes:
      - name: grafana-datasources
        configMap:
          name: grafana-datasources
      - name: grafana-data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: grafana-service
  namespace: ${MONITORING_NAMESPACE}
spec:
  selector:
    app: grafana
  ports:
  - port: 3000
    targetPort: 3000
  type: ClusterIP
EOF

    show_success "Grafana desplegado"
}

# Configurar red (Gateway + VirtualService)
deploy_networking() {
    show_step "Configurando red (Gateway + VirtualServices)..."

    kubectl apply -f kubernetes/virtual-service.yaml
    
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
    - "pgadmin.${DOMAIN}"
    - "jaeger.${DOMAIN}"
    - "prometheus.${DOMAIN}"
    - "grafana.${DOMAIN}"
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
    - "pgadmin.${DOMAIN}"
    - "jaeger.${DOMAIN}"
    - "prometheus.${DOMAIN}"
    - "grafana.${DOMAIN}"
    tls:
      mode: SIMPLE
      credentialName: raven-api-tls-secret
---
# PGAdmin
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: pgadmin-vs
  namespace: default
spec:
  hosts:
  - "pgadmin.${DOMAIN}"
  gateways:
  - raven-gateway
  http:
  - match:
    - uri:
        prefix: /
    route:
    - destination:
        host: pgadmin-service.${NAMESPACE}.svc.cluster.local
        port:
          number: 80
---
# Jaeger
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: jaeger-vs
  namespace: default
spec:
  hosts:
  - "jaeger.${DOMAIN}"
  gateways:
  - raven-gateway
  http:
  - match:
    - uri:
        prefix: /
    route:
    - destination:
        host: jaeger-service.${MONITORING_NAMESPACE}.svc.cluster.local
        port:
          number: 16686
---
# Prometheus
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: prometheus-vs
  namespace: default
spec:
  hosts:
  - "prometheus.${DOMAIN}"
  gateways:
  - raven-gateway
  http:
  - match:
    - uri:
        prefix: /
    route:
    - destination:
        host: prometheus-service.${MONITORING_NAMESPACE}.svc.cluster.local
        port:
          number: 9090
---
# Grafana
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: grafana-vs
  namespace: default
spec:
  hosts:
  - "grafana.${DOMAIN}"
  gateways:
  - raven-gateway
  http:
  - match:
    - uri:
        prefix: /
    route:
    - destination:
        host: grafana-service.${MONITORING_NAMESPACE}.svc.cluster.local
        port:
          number: 3000
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
    
    echo "Pods en namespace ${MONITORING_NAMESPACE}:"
    kubectl get pods -n ${MONITORING_NAMESPACE}
    echo ""
    
    # Verificar servicios
    echo "Servicios en namespace ${NAMESPACE}:"
    kubectl get svc -n ${NAMESPACE}
    echo ""
    
    echo "Servicios en namespace ${MONITORING_NAMESPACE}:"
    kubectl get svc -n ${MONITORING_NAMESPACE}
    echo ""
    
    # Verificar Gateway y VirtualService
    echo "Gateway y VirtualServices:"
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
    echo -e "   Ver pods API:        kubectl get pods -n ${NAMESPACE}"
    echo -e "   Ver pods monitor:    kubectl get pods -n ${MONITORING_NAMESPACE}"
    echo -e "   Ver logs API:        kubectl logs -n ${NAMESPACE} -l app=raven-api -f"
    echo -e "   Ver logs DB:         kubectl logs -n ${NAMESPACE} -l app=postgres -f"
    echo -e "   Ver logs Jaeger:     kubectl logs -n ${MONITORING_NAMESPACE} -l app=jaeger -f"
    echo -e "   Estado SSL:          kubectl get certificate -n istio-system"
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
        "clean")
            show_step "Limpiando recursos..."
            kubectl delete namespace ${NAMESPACE} --ignore-not-found=true
            kubectl delete namespace ${MONITORING_NAMESPACE} --ignore-not-found=true
            kubectl delete gateway raven-gateway --ignore-not-found=true
            kubectl delete virtualservice raven-api-vs pgadmin-vs jaeger-vs prometheus-vs grafana-vs --ignore-not-found=true
            kubectl delete certificate raven-api-tls -n istio-system --ignore-not-found=true
            kubectl delete clusterissuer letsencrypt-prod --ignore-not-found=true
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
            echo "Uso: $0 [deploy|clean|status|monitoring|pgadmin|help]"
            echo ""
            echo "Comandos:"
            echo "  deploy     - Desplegar todo (por defecto)"
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
