#!/bin/bash

# Script completo y simplificado para desplegar RAVEN API con HTTPS
# Consolida todo el proceso en comandos simples

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuración
NAMESPACE="raven-api"
DOMAIN="orchestrator.idea.lst.tfo.upm.es"
IP="138.4.10.238"

show_help() {
    echo -e "${BLUE}🚀 RAVEN API - Despliegue Simplificado${NC}"
    echo "===================================="
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos principales:"
    echo "  all       - Desplegar todo desde cero"
    echo "  app       - Solo desplegar la aplicación"
    echo "  ssl       - Solo configurar HTTPS"
    echo "  gateway   - Solo configurar gateway"
    echo ""
    echo "Comandos de gestión:"
    echo "  status    - Ver estado completo"
    echo "  logs      - Ver logs en tiempo real"
    echo "  restart   - Reiniciar aplicación"
    echo "  clean     - Limpiar todo"
    echo ""
    echo "Comandos de base de datos:"
    echo "  migrate   - Ejecutar migraciones"
    echo "  db-reset  - Resetear base de datos"
    echo ""
    echo "Ejemplo de uso típico:"
    echo "  $0 all      # Primera vez"
    echo "  $0 status   # Verificar estado"
    echo "  $0 logs     # Ver logs"
}

# Verificar dependencias básicas
check_deps() {
    if ! kubectl cluster-info &>/dev/null; then
        echo -e "${RED}❌ No hay conexión a Kubernetes${NC}"
        exit 1
    fi
    
    if ! kubectl get pods -n cert-manager | grep -q Running; then
        echo -e "${RED}❌ cert-manager no está funcionando${NC}"
        exit 1
    fi
}

# Crear manifiesto unificado para la aplicación
create_app_manifest() {
    cat > /tmp/raven-app.yaml <<EOF
# Namespace
apiVersion: v1
kind: Namespace
metadata:
  name: $NAMESPACE
---
# Secret
apiVersion: v1
kind: Secret
metadata:
  name: raven-api-secrets
  namespace: $NAMESPACE
type: Opaque
stringData:
  database-uri: "postgresql://raven_user:raven_password@postgres-service:5432/raven_db"
  secret-key: "$(openssl rand -base64 32)"
  postgres-user: "raven_user"
  postgres-password: "$(openssl rand -base64 16)"
  postgres-db: "raven_db"
---
# PostgreSQL Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-deployment
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: raven-api-secrets
              key: postgres-db
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: raven-api-secrets
              key: postgres-user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: raven-api-secrets
              key: postgres-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        emptyDir: {}
---
# PostgreSQL Service
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: $NAMESPACE
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
---
# RAVEN API Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: raven-api-deployment
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: raven-api
  template:
    metadata:
      labels:
        app: raven-api
    spec:
      containers:
      - name: raven-api
        image: aalonso/raven-api:latest
        env:
        - name: DATABASE_URI
          valueFrom:
            secretKeyRef:
              name: raven-api-secrets
              key: database-uri
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: raven-api-secrets
              key: secret-key
        ports:
        - containerPort: 8000
---
# RAVEN API Service
apiVersion: v1
kind: Service
metadata:
  name: raven-api
  namespace: $NAMESPACE
spec:
  selector:
    app: raven-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
EOF
}

# Crear manifiesto para SSL
create_ssl_manifest() {
    cat > /tmp/raven-ssl.yaml <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: aalonso@lst.tfo.upm.es
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: istio
---
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
  dnsNames:
  - $DOMAIN
  duration: 2160h
  renewBefore: 360h
EOF
}

# Crear manifiesto para Gateway
create_gateway_manifest() {
    cat > /tmp/raven-gateway.yaml <<EOF
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: raven-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "$DOMAIN"
    - "$IP"
    tls:
      httpsRedirect: true
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - "$DOMAIN"
    tls:
      mode: SIMPLE
      credentialName: raven-api-tls-secret
---
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: raven-api-vs
spec:
  hosts:
  - "$DOMAIN"
  - "$IP"
  gateways:
  - raven-gateway
  http:
  - match:
    - uri:
        prefix: /
    route:
    - destination:
        host: raven-api.$NAMESPACE.svc.cluster.local
        port:
          number: 80
EOF
}

# Comandos principales
deploy_all() {
    echo -e "${BLUE}🚀 Desplegando RAVEN API completo...${NC}"
    check_deps
    deploy_app
    deploy_ssl
    deploy_gateway
    echo -e "${GREEN}✅ Despliegue completo terminado${NC}"
    show_status
}

deploy_app() {
    echo -e "${BLUE}📦 Desplegando aplicación...${NC}"
    create_app_manifest
    kubectl apply -f /tmp/raven-app.yaml
    echo -e "${YELLOW}⏳ Esperando a que los pods estén listos...${NC}"
    kubectl wait --for=condition=available --timeout=300s deployment/raven-api-deployment -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=300s deployment/postgres-deployment -n $NAMESPACE
    echo -e "${GREEN}✅ Aplicación desplegada${NC}"
}

deploy_ssl() {
    echo -e "${BLUE}🔐 Configurando SSL...${NC}"
    create_ssl_manifest
    kubectl apply -f /tmp/raven-ssl.yaml
    echo -e "${YELLOW}⏳ Esperando certificado SSL (puede tardar 2-3 minutos)...${NC}"
    
    # Esperar hasta 5 minutos por el certificado
    for i in {1..30}; do
        if kubectl get certificate raven-api-tls -n istio-system -o jsonpath='{.status.conditions[0].status}' 2>/dev/null | grep -q "True"; then
            echo -e "${GREEN}✅ Certificado SSL emitido${NC}"
            return 0
        fi
        sleep 10
        echo -n "."
    done
    
    echo -e "${YELLOW}⚠️ Certificado SSL aún pendiente, continuando...${NC}"
}

deploy_gateway() {
    echo -e "${BLUE}🌐 Configurando Gateway...${NC}"
    create_gateway_manifest
    kubectl apply -f /tmp/raven-gateway.yaml
    echo -e "${GREEN}✅ Gateway configurado${NC}"
}

show_status() {
    echo -e "${BLUE}📊 Estado de RAVEN API:${NC}"
    echo "======================"
    echo ""
    
    echo -e "${BLUE}Pods:${NC}"
    kubectl get pods -n $NAMESPACE 2>/dev/null | grep -E "(NAME|raven|postgres)" || echo "Sin pods"
    echo ""
    
    echo -e "${BLUE}Servicios:${NC}"
    kubectl get svc -n $NAMESPACE 2>/dev/null || echo "Sin servicios"
    echo ""
    
    echo -e "${BLUE}Certificado SSL:${NC}"
    if kubectl get certificate raven-api-tls -n istio-system &>/dev/null; then
        ssl_status=$(kubectl get certificate raven-api-tls -n istio-system -o jsonpath='{.status.conditions[0].status}' 2>/dev/null)
        if [ "$ssl_status" = "True" ]; then
            echo -e "${GREEN}✅ SSL activo${NC}"
        else
            echo -e "${YELLOW}⏳ SSL pendiente${NC}"
        fi
    else
        echo -e "${RED}❌ SSL no configurado${NC}"
    fi
    echo ""
    
    echo -e "${BLUE}URLs:${NC}"
    echo "🌐 https://$DOMAIN"
    echo "🌐 http://$DOMAIN (→ HTTPS)"
}

show_logs() {
    echo -e "${BLUE}📋 Logs de RAVEN API:${NC}"
    kubectl logs -f -l app=raven-api -n $NAMESPACE --tail=50
}

restart_app() {
    echo -e "${BLUE}🔄 Reiniciando...${NC}"
    kubectl rollout restart deployment/raven-api-deployment -n $NAMESPACE
    kubectl rollout status deployment/raven-api-deployment -n $NAMESPACE
    echo -e "${GREEN}✅ Reiniciado${NC}"
}

run_migrations() {
    echo -e "${BLUE}🔄 Ejecutando migraciones...${NC}"
    pod=$(kubectl get pods -n $NAMESPACE -l app=raven-api -o jsonpath='{.items[0].metadata.name}')
    kubectl exec -n $NAMESPACE $pod -- python -c "from alembic import command; from alembic.config import Config; cfg = Config('alembic.ini'); command.upgrade(cfg, 'head')"
    echo -e "${GREEN}✅ Migraciones completadas${NC}"
}

clean_all() {
    echo -e "${YELLOW}⚠️ Limpiando RAVEN API...${NC}"
    read -p "¿Confirmar limpieza completa? (escribe 'SI'): " confirm
    if [ "$confirm" = "SI" ]; then
        kubectl delete namespace $NAMESPACE 2>/dev/null || true
        kubectl delete gateway raven-gateway 2>/dev/null || true
        kubectl delete virtualservice raven-api-vs 2>/dev/null || true
        kubectl delete certificate raven-api-tls -n istio-system 2>/dev/null || true
        kubectl delete clusterissuer letsencrypt-prod 2>/dev/null || true
        echo -e "${GREEN}✅ Limpieza completa${NC}"
    fi
}

# Procesar comando
case "${1:-help}" in
    all) deploy_all ;;
    app) deploy_app ;;
    ssl) deploy_ssl ;;
    gateway) deploy_gateway ;;
    status) show_status ;;
    logs) show_logs ;;
    restart) restart_app ;;
    migrate) run_migrations ;;
    db-reset) 
        echo "Ejecuta: kubectl exec -n $NAMESPACE deployment/raven-api-deployment -- python scripts/db_manager.py reset --confirm"
        ;;
    clean) clean_all ;;
    help|*) show_help ;;
esac
