#!/bin/bash
set -e

echo "🌐 Setting up MetalLB LoadBalancer for RAVEN API..."

# Colors for output
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

# Check if running on MicroK8s
if command -v microk8s &> /dev/null; then
    show_progress "Detected MicroK8s environment"
    KUBECTL_CMD="microk8s kubectl"
    
    # Check if MetalLB is enabled
    if ! microk8s status | grep -q "metallb.*enabled"; then
        show_progress "Enabling MetalLB addon..."
        
        # Get server IP
        SERVER_IP=$(hostname -I | awk '{print $1}')
        echo "Detected server IP: $SERVER_IP"
        
        read -p "Enter IP range for MetalLB (default: $SERVER_IP-$SERVER_IP): " IP_RANGE
        if [ -z "$IP_RANGE" ]; then
            IP_RANGE="$SERVER_IP-$SERVER_IP"
        fi
        
        echo "Configuring MetalLB with IP range: $IP_RANGE"
        microk8s enable metallb:$IP_RANGE
        
        # Wait for MetalLB to be ready
        show_progress "Waiting for MetalLB to be ready..."
        sleep 10
    else
        show_success "MetalLB already enabled"
    fi
else
    KUBECTL_CMD="kubectl"
    
    # Check if MetalLB is installed manually
    if ! $KUBECTL_CMD get namespace metallb-system &>/dev/null; then
        show_error "MetalLB not detected. Please install MetalLB or use a different exposure method."
        echo "For manual installation: https://metallb.universe.tf/installation/"
        exit 1
    fi
fi

# Change service to LoadBalancer
show_progress "Converting service to LoadBalancer type..."
$KUBECTL_CMD patch service raven-api -n raven-api -p '{"spec": {"type": "LoadBalancer"}}'

# Wait for external IP
show_progress "Waiting for external IP assignment..."
COUNTER=0
MAX_TRIES=30
while [ $COUNTER -lt $MAX_TRIES ]; do
    EXTERNAL_IP=$($KUBECTL_CMD get service raven-api -n raven-api -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    
    if [ ! -z "$EXTERNAL_IP" ]; then
        break
    fi
    
    echo -n "."
    sleep 2
    COUNTER=$((COUNTER+1))
done
echo

if [ ! -z "$EXTERNAL_IP" ]; then
    show_success "External IP assigned: $EXTERNAL_IP"
    echo
    echo "🌐 RAVEN API is now accessible from Internet:"
    echo "   - Health endpoint: http://$EXTERNAL_IP/raven-api/v1/health/"
    echo "   - API documentation: http://$EXTERNAL_IP/docs"
    echo "   - API base URL: http://$EXTERNAL_IP/raven-api/v1/"
    echo
    echo "🧪 Test the API:"
    echo "   curl -v http://$EXTERNAL_IP/raven-api/v1/health/"
    
    # Test the endpoint
    show_progress "Testing API endpoint..."
    if curl -s --max-time 10 "http://$EXTERNAL_IP/raven-api/v1/health/" | grep -q "status"; then
        show_success "API is responding correctly!"
    else
        show_warning "API might not be fully ready yet. Try again in a few seconds."
    fi
else
    show_error "Failed to get external IP. Check MetalLB configuration."
    echo "Service status:"
    $KUBECTL_CMD get service raven-api -n raven-api
    echo
    echo "MetalLB status:"
    if command -v microk8s &> /dev/null; then
        microk8s status | grep metallb
    else
        $KUBECTL_CMD get pods -n metallb-system
    fi
fi

echo
echo "🔧 Useful commands:"
echo "   - Check service: $KUBECTL_CMD get service raven-api -n raven-api"
echo "   - Check MetalLB logs: $KUBECTL_CMD logs -n metallb-system -l app=metallb"
echo "   - Reset service type: $KUBECTL_CMD patch service raven-api -n raven-api -p '{\"spec\": {\"type\": \"ClusterIP\"}}'"

show_success "MetalLB configuration complete! 🚀"
