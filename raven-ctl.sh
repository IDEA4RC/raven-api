#!/bin/bash
# Script maestro para RAVEN API: despliegue, gestión y exposición

# Configuración
NAMESPACE="raven"
IMAGE_NAME="raven-api"
IMAGE_TAG="latest"
REGISTRY="localhost:32000"  # Registro local de MicroK8s
KUBECTL_CMD="microk8s kubectl"  # Usar microk8s kubectl directamente
HOST="host01.idea.lst.tfo.upm.es"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # Sin Color

# Función para mostrar la ayuda
show_help() {
    echo -e "${BLUE}=== RAVEN API Control Script ===${NC}"
    echo -e "Uso: $0 [comando] [opciones]"
    echo -e ""
    echo -e "Comandos disponibles:"
    echo -e "  ${GREEN}deploy${NC}           - Desplegar la RAVEN API en Kubernetes"
    echo -e "  ${GREEN}expose${NC}           - Exponer la API a Internet (HTTP)"
    echo -e "  ${GREEN}secure${NC}           - Configurar HTTPS para la API"
    echo -e "  ${GREEN}status${NC}           - Verificar estado del despliegue"
    echo -e "  ${GREEN}cleanup${NC}          - Eliminar el despliegue"
    echo -e "  ${GREEN}help${NC}             - Mostrar esta ayuda"
    echo -e ""
    echo -e "Opciones:"
    echo -e "  ${YELLOW}--skip-build${NC}      - Omitir la construcción de la imagen"
    echo -e "  ${YELLOW}--no-cache${NC}        - Construir imagen sin usar caché"
    echo -e "  ${YELLOW}--registry=URL${NC}    - Especificar un registro de imágenes personalizado"
    echo -e "  ${YELLOW}--hostname=HOST${NC}   - Especificar un hostname personalizado"
    echo -e ""
    echo -e "Ejemplos:"
    echo -e "  $0 deploy                   # Desplegar la API"
    echo -e "  $0 deploy --skip-build      # Desplegar sin reconstruir la imagen"
    echo -e "  $0 expose                   # Exponer la API a Internet"
    echo -e "  $0 secure                   # Configurar HTTPS"
    echo -e "  $0 status                   # Verificar estado"
}

# Función para verificar prerrequisitos
check_prerequisites() {
    echo -e "${YELLOW}🔍 Verificando prerrequisitos...${NC}"
    
    # Verificar MicroK8s
    if ! command -v microk8s &> /dev/null; then
        echo -e "${RED}❌ MicroK8s no está instalado.${NC}"
        exit 1
    fi
    
    # Verificar registro
    if ! microk8s status | grep -q "registry: enabled"; then
        echo -e "${YELLOW}⚠️ El registro de MicroK8s no está habilitado.${NC}"
        echo -e "${YELLOW}ℹ️ Habilitando...${NC}"
        microk8s enable registry
    fi
    
    # Verificar Istio
    if ! microk8s status | grep -q "istio: enabled"; then
        echo -e "${YELLOW}⚠️ Istio no está habilitado.${NC}"
        echo -e "${YELLOW}ℹ️ Habilitando...${NC}"
        microk8s enable istio
    fi
    
    echo -e "${GREEN}✅ Prerrequisitos verificados.${NC}"
}

# Función para construir y enviar imagen Docker
build_image() {
    local no_cache=$1
    
    echo -e "${YELLOW}📦 Construyendo imagen Docker...${NC}"
    
    # Construir con o sin caché
    if [ "$no_cache" = true ]; then
        echo -e "${YELLOW}ℹ️ Construyendo sin caché...${NC}"
        docker build --no-cache -t ${IMAGE_NAME}:${IMAGE_TAG} .
    else
        docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
    fi
    
    # Etiquetar la imagen para el registro
    echo -e "${YELLOW}🏷️ Etiquetando imagen para el registro...${NC}"
    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
    
    # Enviar la imagen al registro
    echo -e "${YELLOW}📤 Enviando imagen al registro...${NC}"
    docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
    
    echo -e "${GREEN}✅ Imagen construida y enviada al registro.${NC}"
}

# Función para desplegar la API en Kubernetes
deploy_api() {
    echo -e "${YELLOW}🚢 Desplegando RAVEN API en Kubernetes...${NC}"
    
    # Verificar si el namespace existe, si no, crearlo
    if ! ${KUBECTL_CMD} get namespace ${NAMESPACE} &> /dev/null; then
        echo -e "${YELLOW}🌐 Creando namespace ${NAMESPACE}...${NC}"
        ${KUBECTL_CMD} create namespace ${NAMESPACE}
        
        # Habilitar inyección de Istio
        echo -e "${YELLOW}🔧 Habilitando inyección de Istio en el namespace...${NC}"
        ${KUBECTL_CMD} label namespace ${NAMESPACE} istio-injection=enabled
    else
        # Asegurarse de que la inyección de Istio esté habilitada
        echo -e "${YELLOW}🏷️ Asegurando que la inyección de Istio esté habilitada...${NC}"
        ${KUBECTL_CMD} label namespace ${NAMESPACE} istio-injection=enabled --overwrite
    fi
    
    # Aplicar manifiestos de Kubernetes
    echo -e "${YELLOW}📄 Aplicando manifiestos de Kubernetes...${NC}"
    
    # Aplicar primero los secretos
    echo -e "${YELLOW}🔑 Aplicando secretos...${NC}"
    ${KUBECTL_CMD} apply -f kubernetes/secrets.yaml -n ${NAMESPACE}
    
    # Aplicar el resto de recursos
    echo -e "${YELLOW}🚢 Aplicando deployment...${NC}"
    ${KUBECTL_CMD} apply -f kubernetes/deployment.yaml -n ${NAMESPACE}
    
    echo -e "${YELLOW}🔄 Aplicando service...${NC}"
    ${KUBECTL_CMD} apply -f kubernetes/service.yaml -n ${NAMESPACE}
    
    echo -e "${YELLOW}🚪 Aplicando gateway...${NC}"
    ${KUBECTL_CMD} apply -f kubernetes/gateway.yaml -n ${NAMESPACE}
    
    echo -e "${YELLOW}🌐 Aplicando virtual service...${NC}"
    ${KUBECTL_CMD} apply -f kubernetes/virtual-service.yaml -n ${NAMESPACE}
    
    # Esperar a que todos los pods estén listos
    echo -e "${YELLOW}⏳ Esperando a que los pods estén listos...${NC}"
    ${KUBECTL_CMD} wait --for=condition=ready pod -l app=raven-api -n ${NAMESPACE} --timeout=120s
    
    # Inicializar la base de datos con datos de ejemplo
    echo -e "${YELLOW}🗃️ Inicializando la base de datos con datos de ejemplo...${NC}"
    POD_NAME=$(${KUBECTL_CMD} get pods -n ${NAMESPACE} -l app=raven-api -o jsonpath="{.items[0].metadata.name}")
    ${KUBECTL_CMD} exec -n ${NAMESPACE} ${POD_NAME} -- python -m scripts.seed_db
    
    echo -e "${GREEN}✅ Despliegue completado.${NC}"
}

# Función para exponer la API a Internet
expose_api() {
    echo -e "${YELLOW}🌐 Exponiendo la RAVEN API a Internet...${NC}"
    
    # Verificar si el servicio istio-ingressgateway existe
    if ! ${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway &>/dev/null; then
        echo -e "${RED}❌ No se encontró el servicio Istio Ingress Gateway.${NC}"
        exit 1
    fi
    
    # Obtener el tipo actual de servicio
    INGRESS_TYPE=$(${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway -o jsonpath='{.spec.type}')
    echo -e "${YELLOW}ℹ️ El tipo actual del Istio Ingress Gateway es: $INGRESS_TYPE${NC}"
    
    # Si no es LoadBalancer, ofrecer opciones para cambiarlo
    if [ "$INGRESS_TYPE" != "LoadBalancer" ]; then
        echo -e "${YELLOW}ℹ️ Se recomienda cambiar a tipo LoadBalancer para exponer la API.${NC}"
        echo -e "${YELLOW}ℹ️ Opciones disponibles:${NC}"
        echo -e "1. Configurar MetalLB (recomendado para entornos locales)"
        echo -e "2. Cambiar a NodePort"
        echo -e "3. Mantener como $INGRESS_TYPE"
        
        read -p "Elige una opción (1-3): " EXPOSE_OPTION
        
        case $EXPOSE_OPTION in
            1)
                # Configurar MetalLB
                echo -e "${YELLOW}🔄 Configurando MetalLB...${NC}"
                
                # Determinar la interfaz de red primaria y su rango de direcciones IP
                INTERFACE=$(ip route | grep default | awk '{print $5}')
                IP_RANGE=$(ip -4 addr show $INTERFACE | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1 | sed 's/\.[0-9]*$/.200-\0.250/')
                
                echo -e "${YELLOW}ℹ️ Interface de red primaria: $INTERFACE${NC}"
                echo -e "${YELLOW}ℹ️ Rango de IPs para MetalLB: $IP_RANGE${NC}"
                
                # Habilitar el complemento MetalLB
                microk8s enable metallb:$IP_RANGE
                
                # Cambiar el servicio a LoadBalancer
                ${KUBECTL_CMD} patch svc istio-ingressgateway -n istio-system -p '{"spec": {"type": "LoadBalancer"}}'
                ;;
            2)
                # Cambiar a NodePort
                echo -e "${YELLOW}🔄 Cambiando el servicio a NodePort...${NC}"
                ${KUBECTL_CMD} patch svc istio-ingressgateway -n istio-system -p '{"spec": {"type": "NodePort"}}'
                ;;
            3)
                echo -e "${YELLOW}ℹ️ Manteniendo configuración actual.${NC}"
                ;;
            *)
                echo -e "${RED}❌ Opción no válida.${NC}"
                return 1
                ;;
        esac
    fi
    
    # Esperar a que el servicio esté listo
    echo -e "${YELLOW}⏳ Esperando a que el servicio esté listo...${NC}"
    sleep 5
    
    # Obtener y mostrar información de acceso
    echo -e "${YELLOW}🔍 Obteniendo información de acceso...${NC}"
    
    # Obtener tipo actualizado
    INGRESS_TYPE=$(${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway -o jsonpath='{.spec.type}')
    
    if [ "$INGRESS_TYPE" == "LoadBalancer" ]; then
        # Obtener la IP externa
        EXTERNAL_IP=$(${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        
        if [ -z "$EXTERNAL_IP" ]; then
            echo -e "${YELLOW}⚠️ Esperando asignación de IP externa...${NC}"
            echo -e "${YELLOW}ℹ️ Esto puede tardar unos minutos. Verificando detalles del servicio:${NC}"
            ${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway -o wide
        else
            echo -e "${GREEN}✅ API expuesta en LoadBalancer con IP: $EXTERNAL_IP${NC}"
            echo -e "${YELLOW}ℹ️ Para acceder localmente, agrega esta línea a tu archivo /etc/hosts:${NC}"
            echo -e "${GREEN}$EXTERNAL_IP $HOST${NC}"
        fi
    elif [ "$INGRESS_TYPE" == "NodePort" ]; then
        # Para NodePort, obtener la IP del nodo y el puerto
        NODE_IP=$(hostname -I | awk '{print $1}')
        NODE_PORT=$(${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')
        
        echo -e "${GREEN}✅ API expuesta en NodePort: $NODE_IP:$NODE_PORT${NC}"
        echo -e "${YELLOW}ℹ️ Para acceder localmente, agrega esta línea a tu archivo /etc/hosts:${NC}"
        echo -e "${GREEN}$NODE_IP $HOST${NC}"
        echo -e "${YELLOW}ℹ️ Y accede mediante: http://$HOST:$NODE_PORT${NC}"
    else
        echo -e "${YELLOW}ℹ️ La API está expuesta con tipo de servicio: $INGRESS_TYPE${NC}"
        echo -e "${YELLOW}ℹ️ Este tipo de servicio puede requerir configuración adicional.${NC}"
    fi
    
    echo -e "${GREEN}✅ Proceso de exposición completado.${NC}"
}

# Función para configurar HTTPS
configure_https() {
    echo -e "${YELLOW}🔒 Configurando HTTPS para la RAVEN API...${NC}"
    
    # Generar certificado TLS autofirmado
    echo -e "${YELLOW}ℹ️ Generando certificado TLS autofirmado...${NC}"
    
    # Crear directorio temporal para los certificados
    TEMP_DIR=$(mktemp -d)
    pushd $TEMP_DIR > /dev/null
    
    # Generar clave privada
    openssl genrsa -out key.pem 2048
    
    # Generar solicitud de certificado
    cat > csr.conf << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn

[dn]
CN = $HOST
O = RAVEN API
OU = IDEA4RC
L = Madrid
C = ES

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = $HOST
EOF
    
    openssl req -new -key key.pem -out csr.pem -config csr.conf
    
    # Generar certificado autofirmado
    openssl x509 -req -in csr.pem -signkey key.pem -out cert.pem -days 365 -extfile csr.conf -extensions req_ext
    
    # Crear secreto de Kubernetes
    CERT_NAME="raven-api-cert"
    ${KUBECTL_CMD} create -n istio-system secret tls ${CERT_NAME} --key=key.pem --cert=cert.pem --dry-run=client -o yaml | ${KUBECTL_CMD} apply -f -
    
    # Limpiar archivos temporales
    popd > /dev/null
    rm -rf $TEMP_DIR
    
    # Aplicar Gateway con HTTPS
    cat > kubernetes/gateway-https.yaml << EOF
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
    - "$HOST"
    tls:
      httpsRedirect: true
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - "$HOST"
    tls:
      mode: SIMPLE
      credentialName: ${CERT_NAME}
EOF
    
    # Aplicar el Gateway con HTTPS
    ${KUBECTL_CMD} apply -f kubernetes/gateway-https.yaml -n ${NAMESPACE}
    
    echo -e "${GREEN}✅ HTTPS configurado correctamente.${NC}"
    echo -e "${YELLOW}⚠️ NOTA: Este es un certificado autofirmado para pruebas.${NC}"
    echo -e "${YELLOW}ℹ️ Para entornos de producción, deberías usar un certificado válido.${NC}"
    echo -e "${GREEN}ℹ️ La API ahora debería estar accesible en https://$HOST/raven-api/v1/${NC}"
}

# Función para verificar el estado del despliegue
check_status() {
    echo -e "${YELLOW}🔍 Verificando estado del despliegue...${NC}"
    
    echo -e "${YELLOW}ℹ️ Pods:${NC}"
    ${KUBECTL_CMD} get pods -n ${NAMESPACE}
    
    echo -e "${YELLOW}ℹ️ Servicios:${NC}"
    ${KUBECTL_CMD} get services -n ${NAMESPACE}
    
    echo -e "${YELLOW}ℹ️ Virtual Services:${NC}"
    ${KUBECTL_CMD} get virtualservices -n ${NAMESPACE}
    
    echo -e "${YELLOW}ℹ️ Gateways:${NC}"
    ${KUBECTL_CMD} get gateways -n ${NAMESPACE}
    
    # Verificar si los pods están funcionando correctamente
    if ${KUBECTL_CMD} get pods -n ${NAMESPACE} | grep -q "Running"; then
        echo -e "${GREEN}✅ Los pods están en ejecución.${NC}"
        
        # Obtener el primer pod para verificar la salud
        POD_NAME=$(${KUBECTL_CMD} get pods -n ${NAMESPACE} -l app=raven-api -o jsonpath="{.items[0].metadata.name}")
        
        # Verificar el endpoint de salud
        echo -e "${YELLOW}ℹ️ Verificando endpoint de salud dentro del pod...${NC}"
        HEALTH_CHECK=$(${KUBECTL_CMD} exec -n ${NAMESPACE} ${POD_NAME} -c raven-api -- curl -s http://localhost:8000/raven-api/v1/health/)
        
        echo -e "${YELLOW}ℹ️ Respuesta del endpoint de salud:${NC}"
        echo $HEALTH_CHECK
    else
        echo -e "${RED}❌ Algunos pods no están en estado 'Running'.${NC}"
        echo -e "${YELLOW}ℹ️ Verificando logs para diagnosticar problemas...${NC}"
        
        # Obtener los pods con problemas
        PODS_WITH_ISSUES=$(${KUBECTL_CMD} get pods -n ${NAMESPACE} | grep -v "Running" | grep -v "NAME" | awk '{print $1}')
        
        for POD in $PODS_WITH_ISSUES; do
            echo -e "${YELLOW}ℹ️ Logs del pod $POD:${NC}"
            ${KUBECTL_CMD} logs -n ${NAMESPACE} $POD
            
            echo -e "${YELLOW}ℹ️ Descripción del pod $POD:${NC}"
            ${KUBECTL_CMD} describe pod -n ${NAMESPACE} $POD
        done
    fi
    
    # Verificar configuración de acceso externo
    echo -e "${YELLOW}ℹ️ Configuración de acceso externo:${NC}"
    ${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway -o wide
}

# Función para limpiar el despliegue
cleanup() {
    echo -e "${YELLOW}🧹 Limpiando despliegue de RAVEN API...${NC}"
    
    read -p "¿Estás seguro de que deseas eliminar todo el despliegue? (S/N): " CONFIRM
    if [[ $CONFIRM =~ ^[Ss]$ ]]; then
        echo -e "${YELLOW}ℹ️ Eliminando recursos de Kubernetes...${NC}"
        
        # Eliminar recursos de la API
        ${KUBECTL_CMD} delete -f kubernetes/virtual-service.yaml -n ${NAMESPACE} --ignore-not-found
        ${KUBECTL_CMD} delete -f kubernetes/gateway.yaml -n ${NAMESPACE} --ignore-not-found
        ${KUBECTL_CMD} delete -f kubernetes/service.yaml -n ${NAMESPACE} --ignore-not-found
        ${KUBECTL_CMD} delete -f kubernetes/deployment.yaml -n ${NAMESPACE} --ignore-not-found
        ${KUBECTL_CMD} delete -f kubernetes/secrets.yaml -n ${NAMESPACE} --ignore-not-found
        
        # Verificar si existe el gateway HTTPS y eliminarlo
        if [ -f kubernetes/gateway-https.yaml ]; then
            ${KUBECTL_CMD} delete -f kubernetes/gateway-https.yaml -n ${NAMESPACE} --ignore-not-found
        fi
        
        # Eliminar el namespace
        read -p "¿Deseas eliminar también el namespace '$NAMESPACE'? (S/N): " CONFIRM_NS
        if [[ $CONFIRM_NS =~ ^[Ss]$ ]]; then
            ${KUBECTL_CMD} delete namespace ${NAMESPACE}
            echo -e "${GREEN}✅ Namespace eliminado.${NC}"
        fi
        
        # Eliminar certificado TLS
        read -p "¿Deseas eliminar el certificado TLS en istio-system? (S/N): " CONFIRM_CERT
        if [[ $CONFIRM_CERT =~ ^[Ss]$ ]]; then
            ${KUBECTL_CMD} delete secret raven-api-cert -n istio-system --ignore-not-found
            echo -e "${GREEN}✅ Certificado TLS eliminado.${NC}"
        fi
        
        echo -e "${GREEN}✅ Limpieza completada.${NC}"
    else
        echo -e "${YELLOW}ℹ️ Operación cancelada.${NC}"
    fi
}

# Procesar argumentos
parse_args() {
    # Variables por defecto
    SKIP_BUILD=false
    NO_CACHE=false
    
    # Procesar opciones
    for arg in "$@"; do
        case $arg in
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --no-cache)
                NO_CACHE=true
                shift
                ;;
            --registry=*)
                REGISTRY="${arg#*=}"
                shift
                ;;
            --hostname=*)
                HOST="${arg#*=}"
                shift
                ;;
            *)
                # Ignorar otros argumentos
                ;;
        esac
    done
}

# Función principal
main() {
    # Si no hay comando, mostrar ayuda
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    # Obtener el comando principal
    COMMAND=$1
    shift
    
    # Procesar argumentos
    parse_args "$@"
    
    # Ejecutar el comando correspondiente
    case $COMMAND in
        deploy)
            check_prerequisites
            if [ "$SKIP_BUILD" != true ]; then
                build_image $NO_CACHE
            fi
            deploy_api
            ;;
        expose)
            check_prerequisites
            expose_api
            ;;
        secure)
            check_prerequisites
            configure_https
            ;;
        status)
            check_status
            ;;
        cleanup)
            cleanup
            ;;
        help)
            show_help
            ;;
        *)
            echo -e "${RED}❌ Comando no reconocido: $COMMAND${NC}"
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar la función principal con todos los argumentos
main "$@"
