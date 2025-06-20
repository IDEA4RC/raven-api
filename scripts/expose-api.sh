#!/bin/bash
set -e

echo "🌐 Exposing RAVEN API to Internet..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions for output
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

# Check if API is deployed
if ! kubectl get deployment raven-api -n raven-api &>/dev/null; then
    show_error "RAVEN API is not deployed. Run './scripts/deploy-k8s.sh' first"
    exit 1
fi

# Get current service type
CURRENT_TYPE=$(kubectl get service raven-api -n raven-api -o jsonpath='{.spec.type}')
echo "Current service type: $CURRENT_TYPE"

# Show options
echo
echo "Choose how to expose the API to Internet:"
echo "1. LoadBalancer (recommended for cloud providers)"
echo "2. NodePort (works on any cluster)"
echo "3. Ingress (requires ingress controller)"
echo "4. Istio Gateway (if Istio is available)"
echo

read -p "Select option (1-4): " OPTION

case $OPTION in
    1)
        # LoadBalancer
        show_progress "Configuring LoadBalancer service..."
        kubectl patch service raven-api -n raven-api -p '{"spec": {"type": "LoadBalancer"}}'
        
        show_progress "Waiting for external IP assignment..."
        echo "This may take a few minutes depending on your cloud provider..."
        
        # Wait for external IP with timeout
        COUNTER=0
        MAX_TRIES=60
        while [ $COUNTER -lt $MAX_TRIES ]; do
            EXTERNAL_IP=$(kubectl get service raven-api -n raven-api -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
            EXTERNAL_HOST=$(kubectl get service raven-api -n raven-api -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
            
            if [ ! -z "$EXTERNAL_IP" ] || [ ! -z "$EXTERNAL_HOST" ]; then
                break
            fi
            
            echo -n "."
            sleep 5
            COUNTER=$((COUNTER+1))
        done
        echo
        
        if [ ! -z "$EXTERNAL_IP" ]; then
            show_success "External IP assigned: $EXTERNAL_IP"
            echo "🌐 API accessible at: http://$EXTERNAL_IP/raven-api/v1/health/"
        elif [ ! -z "$EXTERNAL_HOST" ]; then
            show_success "External hostname assigned: $EXTERNAL_HOST"
            echo "🌐 API accessible at: http://$EXTERNAL_HOST/raven-api/v1/health/"
        else
            show_warning "External IP not assigned yet. Check your cloud provider's load balancer configuration."
            kubectl get service raven-api -n raven-api
        fi
        ;;
    
    2)
        # NodePort
        show_progress "Configuring NodePort service..."
        kubectl patch service raven-api -n raven-api -p '{"spec": {"type": "NodePort"}}'
        
        # Get node port
        sleep 2
        NODE_PORT=$(kubectl get service raven-api -n raven-api -o jsonpath='{.spec.ports[0].nodePort}')
        
        # Get node IPs
        echo "Node IPs:"
        kubectl get nodes -o wide | awk 'NR>1 {print "  - " $6}'
        
        show_success "NodePort configured: $NODE_PORT"
        echo "🌐 API accessible at: http://<any-node-ip>:$NODE_PORT/raven-api/v1/health/"
        echo
        echo "💡 Replace <any-node-ip> with any of the node IPs listed above"
        ;;
    
    3)
        # Ingress
        show_progress "Creating Ingress configuration..."
        
        # Create ingress manifest
        cat > /tmp/raven-api-ingress.yaml << EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: raven-api-ingress
  namespace: raven-api
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: raven-api.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: raven-api
            port:
              number: 80
EOF
        
        # Apply ingress
        kubectl apply -f /tmp/raven-api-ingress.yaml
        rm /tmp/raven-api-ingress.yaml
        
        # Get ingress info
        sleep 2
        INGRESS_IP=$(kubectl get ingress raven-api-ingress -n raven-api -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
        
        if [ ! -z "$INGRESS_IP" ]; then
            show_success "Ingress configured with IP: $INGRESS_IP"
            echo "🌐 Add this to your /etc/hosts file:"
            echo "$INGRESS_IP raven-api.local"
            echo "🌐 Then access: http://raven-api.local/raven-api/v1/health/"
        else
            show_success "Ingress configured"
            echo "🌐 Check ingress controller for external access:"
            kubectl get ingress raven-api-ingress -n raven-api
        fi
        ;;
    
    4)
        # Istio Gateway
        if ! kubectl get crd gateways.networking.istio.io &> /dev/null; then
            show_error "Istio is not installed in this cluster"
            exit 1
        fi
        
        show_progress "Configuring Istio Gateway for external access..."
        
        # Check if gateway already exists and is properly configured
        if kubectl get gateway raven-gateway -n raven-api &>/dev/null; then
            show_success "Istio Gateway already configured"
        else
            show_error "Istio Gateway not found. Make sure to run deploy-k8s.sh first"
            exit 1
        fi
        
        # Get Istio ingress gateway external IP
        ISTIO_IP=$(kubectl get service istio-ingressgateway -n istio-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
        ISTIO_HOST=$(kubectl get service istio-ingressgateway -n istio-system -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
        
        if [ ! -z "$ISTIO_IP" ]; then
            show_success "Istio Gateway accessible via IP: $ISTIO_IP"
            echo "🌐 API accessible at: http://$ISTIO_IP/raven-api/v1/health/"
        elif [ ! -z "$ISTIO_HOST" ]; then
            show_success "Istio Gateway accessible via hostname: $ISTIO_HOST"
            echo "🌐 API accessible at: http://$ISTIO_HOST/raven-api/v1/health/"
        else
            # Check if it's NodePort
            ISTIO_PORT=$(kubectl get service istio-ingressgateway -n istio-system -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}' 2>/dev/null)
            if [ ! -z "$ISTIO_PORT" ]; then
                echo "Istio Gateway uses NodePort: $ISTIO_PORT"
                echo "Node IPs:"
                kubectl get nodes -o wide | awk 'NR>1 {print "  - " $6}'
                echo "🌐 API accessible at: http://<any-node-ip>:$ISTIO_PORT/raven-api/v1/health/"
            else
                show_warning "Istio Gateway external access not configured"
                kubectl get service istio-ingressgateway -n istio-system
            fi
        fi
        ;;
    
    *)
        show_error "Invalid option selected"
        exit 1
        ;;
esac

echo
echo "🔧 Additional commands:"
echo "   - Check service: kubectl get service raven-api -n raven-api"
echo "   - Check endpoints: kubectl get endpoints raven-api -n raven-api"
echo "   - Test API: curl -v http://<external-ip>/raven-api/v1/health/"

show_success "Exposure configuration complete! 🚀"
