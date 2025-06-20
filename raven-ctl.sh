#!/bin/bash
# Script maestro para RAVEN API: despliegue, gestión y exposición

# Configuración
NAMESPACE="raven-api"
IMAGE_NAME="raven-api"
IMAGE_TAG="latest"
REGISTRY="localhost:32000"  # Registro local de MicroK8s
KUBECTL_CMD="microk8s kubectl"  # Usar microk8s kubectl directamente
HOST="orchestrator.idea.lst.tfo.upm.es"

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
    echo -e "  ${GREEN}verify${NC}           - Verificar el acceso a la API desde diferentes URLs"
    echo -e "  ${GREEN}status${NC}           - Verificar estado del despliegue"
    echo -e "  ${GREEN}restart${NC}          - Reiniciar el despliegue (útil para solucionar problemas)"
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
    echo -e "  $0 verify                   # Verificar acceso a la API"
    echo -e "  $0 restart                  # Reiniciar el despliegue"
    echo -e "  $0 status                   # Verificar estado"
    echo -e "  $0 cleanup                  # Eliminar el despliegue"
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
    
    # Verificar si la API está desplegada
    if ! ${KUBECTL_CMD} get deployment -n ${NAMESPACE} raven-api &>/dev/null; then
        echo -e "${RED}❌ La API no está desplegada. Ejecuta primero 'deploy'.${NC}"
        exit 1
    fi
    
    # Verificar el estado del despliegue
    READY_REPLICAS=$(${KUBECTL_CMD} get deployment -n ${NAMESPACE} raven-api -o jsonpath='{.status.readyReplicas}')
    if [ -z "$READY_REPLICAS" ] || [ "$READY_REPLICAS" -eq 0 ]; then
        echo -e "${RED}⚠️ El despliegue no está listo. Verificando estado...${NC}"
        ${KUBECTL_CMD} get pods -n ${NAMESPACE} -l app=raven-api
        ${KUBECTL_CMD} describe deployment -n ${NAMESPACE} raven-api
        echo -e "${YELLOW}ℹ️ Espera a que el despliegue esté listo o verifica los errores.${NC}"
        read -p "¿Deseas continuar de todos modos? (S/N): " CONTINUE_ANYWAY
        if [[ ! $CONTINUE_ANYWAY =~ ^[Ss]$ ]]; then
            exit 1
        fi
    else
        echo -e "${GREEN}✅ El despliegue está listo. Continuando...${NC}"
    fi
    
    # Verificar si el servicio istio-ingressgateway existe
    if ! ${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway &>/dev/null; then
        echo -e "${RED}❌ No se encontró el servicio Istio Ingress Gateway.${NC}"
        exit 1
    fi
    
    # Obtener interfaces de red e IPs del servidor
    echo -e "${YELLOW}ℹ️ Interfaces de red disponibles:${NC}"
    ip -o addr show | grep inet | grep -v "127.0.0.1" | awk '{print $2, $4}' | column -t
    
    # Autodetectar la IP principal del servidor (excluyendo IPs locales y de Docker)
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    echo -e "${YELLOW}ℹ️ IP principal detectada: $SERVER_IP${NC}"
    read -p "¿Usar esta IP? De lo contrario, introduce la IP que deseas usar: " CUSTOM_IP
    
    if [ ! -z "$CUSTOM_IP" ]; then
        SERVER_IP=$CUSTOM_IP
        echo -e "${YELLOW}ℹ️ Usando IP personalizada: $SERVER_IP${NC}"
    fi
    
    # Obtener el tipo actual de servicio
    INGRESS_TYPE=$(${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway -o jsonpath='{.spec.type}')
    echo -e "${YELLOW}ℹ️ El tipo actual del Istio Ingress Gateway es: $INGRESS_TYPE${NC}"
    
    # Si no es LoadBalancer, ofrecer opciones para cambiarlo
    if [ "$INGRESS_TYPE" != "LoadBalancer" ]; then
        echo -e "${YELLOW}ℹ️ Se recomienda cambiar a tipo LoadBalancer para exponer la API.${NC}"
        echo -e "${YELLOW}ℹ️ Opciones disponibles:${NC}"
        echo -e "1. Configurar MetalLB con la IP fija del servidor ($SERVER_IP)"
        echo -e "2. Cambiar a NodePort"
        echo -e "3. Mantener como $INGRESS_TYPE"
        
        read -p "Elige una opción (1-3): " EXPOSE_OPTION
        
        case $EXPOSE_OPTION in
            1)
                # Configurar MetalLB con la IP fija del servidor
                echo -e "${YELLOW}🔄 Configurando MetalLB con IP fija...${NC}"
                
                # Crear un rango que incluya solo la IP del servidor
                IP_RANGE="$SERVER_IP-$SERVER_IP"
                
                echo -e "${YELLOW}ℹ️ Rango de IPs para MetalLB: $IP_RANGE${NC}"
                
                # Verificar si MetalLB ya está habilitado
                microk8s status | grep -q "metallb" && METALLB_ENABLED=true || METALLB_ENABLED=false
                
                if [ "$METALLB_ENABLED" = true ]; then
                    echo -e "${YELLOW}ℹ️ MetalLB ya está habilitado. Reconfigurando...${NC}"
                    # Para reconfigurar MetalLB, primero lo deshabilitamos
                    microk8s disable metallb
                    sleep 2
                fi
                
                # Habilitar el complemento MetalLB con la nueva configuración
                echo -e "${YELLOW}🔄 Habilitando MetalLB con el rango: $IP_RANGE${NC}"
                microk8s enable metallb:$IP_RANGE
                
                # Cambiar el servicio a LoadBalancer
                ${KUBECTL_CMD} patch svc istio-ingressgateway -n istio-system -p '{"spec": {"type": "LoadBalancer"}}'
                
                echo -e "${YELLOW}⏳ Esperando a que se asigne la IP al servicio...${NC}"
                
                # Esperar con un timeout y verificar la asignación de IP
                COUNTER=0
                MAX_TRIES=30
                while [ $COUNTER -lt $MAX_TRIES ]; do
                    EXTERNAL_IP=$(${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
                    
                    if [ ! -z "$EXTERNAL_IP" ]; then
                        echo -e "${GREEN}✅ IP asignada: $EXTERNAL_IP${NC}"
                        break
                    fi
                    
                    echo -n "."
                    sleep 2
                    COUNTER=$((COUNTER+1))
                    
                    # Cada 5 intentos, mostrar el estado del servicio
                    if [ $((COUNTER % 5)) -eq 0 ]; then
                        echo -e "\n${YELLOW}ℹ️ Estado actual del servicio (intento $COUNTER de $MAX_TRIES):${NC}"
                        ${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway -o wide
                    fi
                done
                echo # Nueva línea para mejorar formato
                
                # Si después de los intentos no se asignó IP, recargar el servicio
                if [ -z "$EXTERNAL_IP" ]; then
                    echo -e "${YELLOW}⚠️ No se asignó IP automáticamente. Intentando forzar la asignación...${NC}"
                    # Forzar la actualización del servicio
                    ${KUBECTL_CMD} patch svc istio-ingressgateway -n istio-system -p '{"spec": {"type": "ClusterIP"}}'
                    sleep 3
                    ${KUBECTL_CMD} patch svc istio-ingressgateway -n istio-system -p '{"spec": {"type": "LoadBalancer"}}'
                    
                    echo -e "${YELLOW}⏳ Esperando nuevamente la asignación de IP...${NC}"
                    sleep 10
                fi
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
    else
        # Si ya es LoadBalancer pero no tiene IP externa, configurar MetalLB
        EXTERNAL_IP=$(${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        
        if [ -z "$EXTERNAL_IP" ]; then
            echo -e "${YELLOW}⚠️ El servicio ya es de tipo LoadBalancer pero no tiene IP asignada.${NC}"
            echo -e "${YELLOW}ℹ️ ¿Deseas configurar MetalLB con la IP fija del servidor? (S/N): ${NC}"
            read -p "" CONFIGURE_METALLB
            
            if [[ $CONFIGURE_METALLB =~ ^[Ss]$ ]]; then
                # Configurar MetalLB con la IP fija
                IP_RANGE="$SERVER_IP-$SERVER_IP"
                echo -e "${YELLOW}ℹ️ Configurando MetalLB con rango: $IP_RANGE${NC}"
                
                # Verificar si MetalLB ya está habilitado
                microk8s status | grep -q "metallb" && METALLB_ENABLED=true || METALLB_ENABLED=false
                
                if [ "$METALLB_ENABLED" = true ]; then
                    echo -e "${YELLOW}ℹ️ MetalLB ya está habilitado. Reconfigurando...${NC}"
                    microk8s disable metallb
                    sleep 2
                fi
                
                # Habilitar MetalLB con la nueva configuración
                microk8s enable metallb:$IP_RANGE
                
                # Recargar el servicio para aplicar la nueva configuración
                ${KUBECTL_CMD} patch svc istio-ingressgateway -n istio-system -p '{"spec": {"type": "ClusterIP"}}' 
                sleep 3
                ${KUBECTL_CMD} patch svc istio-ingressgateway -n istio-system -p '{"spec": {"type": "LoadBalancer"}}'
                
                echo -e "${YELLOW}⏳ Esperando a que se asigne la IP al servicio...${NC}"
                sleep 10
            fi
        fi
    fi
    
    # Verificar nuevamente la IP externa después de los cambios
    EXTERNAL_IP=$(${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    # Si aún no tiene IP asignada, mostrar detalles del servicio y usar IP del servidor
    if [ -z "$EXTERNAL_IP" ]; then
        echo -e "${YELLOW}⚠️ El servicio sigue sin tener una IP externa asignada.${NC}"
        echo -e "${YELLOW}ℹ️ Detalles del servicio:${NC}"
        ${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway -o wide
        
        # Extraer puertos NodePort si están disponibles
        HTTP_PORT=$(${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')
        HTTPS_PORT=$(${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')
        
        if [ ! -z "$HTTP_PORT" ]; then
            echo -e "${YELLOW}ℹ️ Puertos NodePort detectados - HTTP: $HTTP_PORT, HTTPS: $HTTPS_PORT${NC}"
            echo -e "${YELLOW}ℹ️ Puedes acceder a la API con: http://$SERVER_IP:$HTTP_PORT/raven-api/v1/${NC}"
        fi
        
        # Usar la IP del servidor como alternativa
        echo -e "${YELLOW}ℹ️ Como alternativa, puedes usar la IP del servidor: $SERVER_IP${NC}"
        echo -e "${YELLOW}ℹ️ Configura tu DNS o archivo hosts para apuntar $HOST a $SERVER_IP${NC}"
        EXTERNAL_IP=$SERVER_IP
    else
        echo -e "${GREEN}✅ MetalLB ha asignado correctamente la IP: $EXTERNAL_IP${NC}"
    fi
    
    # Mostrar información de acceso
    echo -e "${GREEN}✅ API expuesta con éxito.${NC}"
    echo -e "${YELLOW}ℹ️ Para acceder localmente, agrega esta línea a tu archivo /etc/hosts:${NC}"
    echo -e "${GREEN}$EXTERNAL_IP $HOST${NC}"
    echo -e "${YELLOW}ℹ️ La API será accesible en: http://$HOST/raven-api/v1/${NC}"
    
    # Verificar si el hostname ya está en /etc/hosts
    if grep -q "$HOST" /etc/hosts; then
        echo -e "${YELLOW}ℹ️ El hostname ya existe en /etc/hosts. Considera actualizarlo si es necesario.${NC}"
    else
        echo -e "${YELLOW}ℹ️ Para agregar automáticamente la entrada a /etc/hosts, ejecuta:${NC}"
        echo -e "sudo sh -c \"echo '$EXTERNAL_IP $HOST' >> /etc/hosts\""
    fi
    
    # Verificar acceso a la API
    echo -e "${YELLOW}ℹ️ ¿Deseas verificar el acceso a la API? (S/N): ${NC}"
    read -p "" VERIFY_ACCESS
    
    if [[ $VERIFY_ACCESS =~ ^[Ss]$ ]]; then
        echo -e "${YELLOW}⏳ Verificando acceso a la API...${NC}"
        # Intentar con el hostname
        echo -e "${YELLOW}ℹ️ Intentando acceder con el hostname...${NC}"
        curl -s -o /dev/null -w "%{http_code}" http://$HOST/raven-api/v1/health/ || echo "Falló la conexión"
        
        # Intentar con la IP directamente
        echo -e "${YELLOW}ℹ️ Intentando acceder con la IP...${NC}"
        curl -s -o /dev/null -w "%{http_code}" -H "Host: $HOST" http://$EXTERNAL_IP/raven-api/v1/health/ || echo "Falló la conexión"
        
        # Verificar si hay puertos NodePort y probar también
        if [ ! -z "$HTTP_PORT" ]; then
            echo -e "${YELLOW}ℹ️ Intentando acceder con NodePort...${NC}"
            curl -s -o /dev/null -w "%{http_code}" -H "Host: $HOST" http://$SERVER_IP:$HTTP_PORT/raven-api/v1/health/ || echo "Falló la conexión"
        fi
        
        echo -e "${YELLOW}ℹ️ Si ves un código 200, la API está accesible correctamente.${NC}"
        echo -e "${YELLOW}ℹ️ Si ves otro código o un error, puede que haya problemas de acceso o configuración.${NC}"
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
        
        # Verificar el endpoint de salud primero dentro del pod
        echo -e "${YELLOW}ℹ️ Intentando verificar el endpoint de salud...${NC}"
        
        # Verificar si curl está disponible en el contenedor
        if ${KUBECTL_CMD} exec -n ${NAMESPACE} ${POD_NAME} -c raven-api -- which curl &>/dev/null; then
            echo -e "${YELLOW}ℹ️ Usando curl dentro del pod...${NC}"
            HEALTH_CHECK=$(${KUBECTL_CMD} exec -n ${NAMESPACE} ${POD_NAME} -c raven-api -- curl -s http://localhost:8000/raven-api/v1/health/)
            INTERNAL_CHECK_SUCCESS=true
        # Verificar si wget está disponible como alternativa
        elif ${KUBECTL_CMD} exec -n ${NAMESPACE} ${POD_NAME} -c raven-api -- which wget &>/dev/null; then
            echo -e "${YELLOW}ℹ️ Usando wget dentro del pod...${NC}"
            HEALTH_CHECK=$(${KUBECTL_CMD} exec -n ${NAMESPACE} ${POD_NAME} -c raven-api -- wget -q -O - http://localhost:8000/raven-api/v1/health/)
            INTERNAL_CHECK_SUCCESS=true
        else
            echo -e "${YELLOW}⚠️ No se encontró herramientas (curl/wget) en el pod para verificar la salud.${NC}"
            INTERNAL_CHECK_SUCCESS=false
            
            # Intentar con Python si está disponible
            if ${KUBECTL_CMD} exec -n ${NAMESPACE} ${POD_NAME} -c raven-api -- which python &>/dev/null; then
                echo -e "${YELLOW}ℹ️ Intentando con Python...${NC}"
                PYTHON_CMD='import urllib.request; response = urllib.request.urlopen("http://localhost:8000/raven-api/v1/health/"); print(response.read().decode("utf-8"))'
                HEALTH_CHECK=$(${KUBECTL_CMD} exec -n ${NAMESPACE} ${POD_NAME} -c raven-api -- python -c "${PYTHON_CMD}" 2>/dev/null)
                if [ ! -z "$HEALTH_CHECK" ]; then
                    INTERNAL_CHECK_SUCCESS=true
                fi
            fi
            
            # Si todos los métodos anteriores fallan
            if [ "$INTERNAL_CHECK_SUCCESS" != true ]; then
                echo -e "${YELLOW}ℹ️ Intentando verificar externamente...${NC}"
                # Obtener la IP del servicio interno
                SERVICE_IP=$(${KUBECTL_CMD} get svc -n ${NAMESPACE} raven-api -o jsonpath='{.spec.clusterIP}')
                if [ ! -z "$SERVICE_IP" ]; then
                    # Usar kubectl port-forward para conectar con el servicio
                    echo -e "${YELLOW}ℹ️ Iniciando port-forward al servicio...${NC}"
                    ${KUBECTL_CMD} port-forward -n ${NAMESPACE} svc/raven-api 8888:80 &>/dev/null &
                    PF_PID=$!
                    sleep 2
                    
                    # Verificar el endpoint de salud a través del port-forward
                    if command -v curl &>/dev/null; then
                        HEALTH_CHECK=$(curl -s http://localhost:8888/raven-api/v1/health/)
                        INTERNAL_CHECK_SUCCESS=true
                    elif command -v wget &>/dev/null; then
                        HEALTH_CHECK=$(wget -q -O - http://localhost:8888/raven-api/v1/health/)
                        INTERNAL_CHECK_SUCCESS=true
                    fi
                    
                    # Detener el port-forward
                    kill $PF_PID 2>/dev/null
                    wait $PF_PID 2>/dev/null
                fi
            fi
        fi
        
        # Mostrar los resultados de la verificación
        if [ "$INTERNAL_CHECK_SUCCESS" = true ] && [ ! -z "$HEALTH_CHECK" ]; then
            echo -e "${GREEN}✅ Respuesta del endpoint de salud:${NC}"
            echo $HEALTH_CHECK
        else
            echo -e "${YELLOW}⚠️ No se pudo verificar el endpoint de salud internamente.${NC}"
            echo -e "${YELLOW}ℹ️ Se recomienda ejecutar './raven-ctl.sh verify' para verificar el acceso externo.${NC}"
        fi
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

# Función para verificar el acceso a la API
verify_api_access() {
    echo -e "${YELLOW}🔍 Verificando acceso a la RAVEN API...${NC}"
    
    # Verificar si la API está desplegada
    if ! ${KUBECTL_CMD} get deployment -n ${NAMESPACE} raven-api &>/dev/null; then
        echo -e "${RED}❌ La API no está desplegada. Ejecuta primero 'deploy'.${NC}"
        exit 1
    fi
    
    # Verificar el estado del despliegue
    TOTAL_PODS=$(${KUBECTL_CMD} get pods -n ${NAMESPACE} -l app=raven-api -o name | wc -l)
    READY_PODS=$(${KUBECTL_CMD} get pods -n ${NAMESPACE} -l app=raven-api -o jsonpath='{range .items[*]}{.status.containerStatuses[?(@.name=="raven-api")].ready}{"\n"}{end}' | grep -c "true")
    
    if [ "$READY_PODS" -lt "$TOTAL_PODS" ]; then
        echo -e "${YELLOW}⚠️ No todos los pods están listos ($READY_PODS/$TOTAL_PODS). Algunos servicios pueden no estar disponibles.${NC}"
        echo -e "${YELLOW}ℹ️ Detalles de los pods:${NC}"
        ${KUBECTL_CMD} get pods -n ${NAMESPACE} -l app=raven-api
        echo -e "${YELLOW}ℹ️ Se continuará con la verificación de acceso, pero podrían haber errores.${NC}"
    else
        echo -e "${GREEN}✅ Todos los pods están listos ($READY_PODS/$TOTAL_PODS).${NC}"
    fi
    
    # Obtener la IP del servidor
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    # Obtener la IP externa del servicio istio-ingressgateway
    EXTERNAL_IP=$(${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    # Si no hay IP externa, usar la IP del servidor
    if [ -z "$EXTERNAL_IP" ]; then
        echo -e "${YELLOW}⚠️ No se encontró IP externa en el servicio.${NC}"
        EXTERNAL_IP=$SERVER_IP
        
        # Verificar si hay puertos NodePort
        HTTP_PORT=$(${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')
        HTTPS_PORT=$(${KUBECTL_CMD} get svc -n istio-system istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')
    fi
    
    # Crear tabla de IPs y endpoints a probar
    echo -e "${YELLOW}ℹ️ Probando acceso a la API desde varias URLs...${NC}"
    echo -e "┌─────────────────────────────────────────────────────┬────────┐"
    echo -e "│ URL                                                 │ Estado │"
    echo -e "├─────────────────────────────────────────────────────┼────────┤"
    
    # Probar hostname normal (requiere entrada en /etc/hosts)
    STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$HOST/raven-api/v1/health/ 2>/dev/null || echo "ERROR")
    if [ "$STATUS_CODE" = "200" ]; then
        STATUS="${GREEN}✅ OK${NC}"
    else
        STATUS="${RED}❌ $STATUS_CODE${NC}"
    fi
    echo -e "│ http://$HOST/raven-api/v1/health/              │ $STATUS │"
    
    # Probar https si está configurado
    if ${KUBECTL_CMD} get secret -n istio-system raven-api-cert &>/dev/null; then
        STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -k https://$HOST/raven-api/v1/health/ 2>/dev/null || echo "ERROR")
        if [ "$STATUS_CODE" = "200" ]; then
            STATUS="${GREEN}✅ OK${NC}"
        else
            STATUS="${RED}❌ $STATUS_CODE${NC}"
        fi
        echo -e "│ https://$HOST/raven-api/v1/health/ (inseguro)  │ $STATUS │"
    fi
    
    # Probar IP externa directa
    STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: $HOST" http://$EXTERNAL_IP/raven-api/v1/health/ 2>/dev/null || echo "ERROR")
    if [ "$STATUS_CODE" = "200" ]; then
        STATUS="${GREEN}✅ OK${NC}"
    else
        STATUS="${RED}❌ $STATUS_CODE${NC}"
    fi
    echo -e "│ http://$EXTERNAL_IP/ (con Host: $HOST)       │ $STATUS │"
    
    # Probar NodePort si está disponible
    if [ ! -z "$HTTP_PORT" ]; then
        STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: $HOST" http://$SERVER_IP:$HTTP_PORT/raven-api/v1/health/ 2>/dev/null || echo "ERROR")
        if [ "$STATUS_CODE" = "200" ]; then
            STATUS="${GREEN}✅ OK${NC}"
        else
            STATUS="${RED}❌ $STATUS_CODE${NC}"
        fi
        echo -e "│ http://$SERVER_IP:$HTTP_PORT/ (NodePort)         │ $STATUS │"
    fi
    
    # Probar el servicio de Kubernetes directamente (port-forward)
    echo -e "│ Port-forward al servicio interno                   │ ${YELLOW}⏳${NC} │"
    ${KUBECTL_CMD} port-forward -n ${NAMESPACE} svc/raven-api 8899:80 &>/dev/null &
    PF_PID=$!
    sleep 3
    
    STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8899/raven-api/v1/health/ 2>/dev/null || echo "ERROR")
    kill $PF_PID 2>/dev/null
    wait $PF_PID 2>/dev/null
    
    if [ "$STATUS_CODE" = "200" ]; then
        STATUS="${GREEN}✅ OK${NC}"
    else
        STATUS="${RED}❌ $STATUS_CODE${NC}"
    fi
    echo -e "│ Port-forward al servicio interno                   │ $STATUS │"
    
    echo -e "└─────────────────────────────────────────────────────┴────────┘"
    
    # Verificar si alguna prueba tuvo éxito y mostrar la respuesta
    RESPONSE=""
    
    if curl -s http://$HOST/raven-api/v1/health/ 2>/dev/null | grep -q "status"; then
        RESPONSE=$(curl -s http://$HOST/raven-api/v1/health/)
        ACCESS_METHOD="hostname directo (http://$HOST/)"
    elif curl -s -k https://$HOST/raven-api/v1/health/ 2>/dev/null | grep -q "status"; then
        RESPONSE=$(curl -s -k https://$HOST/raven-api/v1/health/)
        ACCESS_METHOD="HTTPS (https://$HOST/)"
    elif curl -s -H "Host: $HOST" http://$EXTERNAL_IP/raven-api/v1/health/ 2>/dev/null | grep -q "status"; then
        RESPONSE=$(curl -s -H "Host: $HOST" http://$EXTERNAL_IP/raven-api/v1/health/)
        ACCESS_METHOD="IP directa (http://$EXTERNAL_IP/ con Host: $HOST)"
    elif [ ! -z "$HTTP_PORT" ] && curl -s -H "Host: $HOST" http://$SERVER_IP:$HTTP_PORT/raven-api/v1/health/ 2>/dev/null | grep -q "status"; then
        RESPONSE=$(curl -s -H "Host: $HOST" http://$SERVER_IP:$HTTP_PORT/raven-api/v1/health/)
        ACCESS_METHOD="NodePort (http://$SERVER_IP:$HTTP_PORT/)"
    elif curl -s http://localhost:8899/raven-api/v1/health/ 2>/dev/null | grep -q "status"; then
        ${KUBECTL_CMD} port-forward -n ${NAMESPACE} svc/raven-api 8899:80 &>/dev/null &
        PF_PID=$!
        sleep 2
        RESPONSE=$(curl -s http://localhost:8899/raven-api/v1/health/)
        kill $PF_PID 2>/dev/null
        wait $PF_PID 2>/dev/null
        ACCESS_METHOD="port-forward al servicio interno"
    fi
    
    if [ ! -z "$RESPONSE" ]; then
        echo -e "${GREEN}✅ La API es accesible via $ACCESS_METHOD${NC}"
        echo -e "${YELLOW}ℹ️ Respuesta del endpoint de salud:${NC}"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    else
        echo -e "${RED}❌ No se pudo acceder al endpoint de salud.${NC}"
        
        # Ofrecer sugerencias de solución de problemas
        echo -e "${YELLOW}ℹ️ Sugerencias de solución de problemas:${NC}"
        echo -e "1. Verifica que el namespace '$NAMESPACE' existe y tiene los recursos correctos:"
        echo -e "   ${KUBECTL_CMD} get all -n $NAMESPACE"
        echo -e "2. Verifica que los pods están en estado 'Running':"
        echo -e "   ${KUBECTL_CMD} get pods -n $NAMESPACE"
        echo -e "3. Revisa los logs de los pods:"
        echo -e "   ${KUBECTL_CMD} logs -n $NAMESPACE deployment/raven-api"
        echo -e "4. Verifica la configuración del VirtualService y Gateway:"
        echo -e "   ${KUBECTL_CMD} get virtualservice,gateway -n $NAMESPACE -o yaml"
        echo -e "5. Asegúrate de que la entrada en /etc/hosts es correcta para $HOST"
        echo -e "6. Si usas HTTPS, verifica que el certificado esté creado correctamente"
        echo -e "7. Intenta reiniciar el deployment:"
        echo -e "   ${KUBECTL_CMD} rollout restart deployment -n $NAMESPACE raven-api"
        
        # Verificar específicamente los pods con problemas
        PODS_WITH_ISSUES=$(${KUBECTL_CMD} get pods -n ${NAMESPACE} | grep -v "2/2" | grep -v "NAME" | awk '{print $1}')
        if [ ! -z "$PODS_WITH_ISSUES" ]; then
            echo -e "\n${YELLOW}ℹ️ Detalles de los pods con problemas:${NC}"
            for POD in $PODS_WITH_ISSUES; do
                echo -e "${YELLOW}🔍 Estado del pod $POD:${NC}"
                ${KUBECTL_CMD} describe pod -n ${NAMESPACE} $POD | grep -A 5 "State:"
                
                echo -e "${YELLOW}📜 Últimas líneas de logs:${NC}"
                ${KUBECTL_CMD} logs -n ${NAMESPACE} $POD -c raven-api --tail=10
                echo
            done
        fi
    fi
}

# Función para reiniciar el despliegue
restart_deployment() {
    echo -e "${YELLOW}🔄 Reiniciando despliegue de RAVEN API...${NC}"
    
    # Verificar si la API está desplegada
    if ! ${KUBECTL_CMD} get deployment -n ${NAMESPACE} raven-api &>/dev/null; then
        echo -e "${RED}❌ La API no está desplegada. Ejecuta primero 'deploy'.${NC}"
        exit 1
    fi
    
    # Reiniciar el despliegue
    ${KUBECTL_CMD} rollout restart deployment -n ${NAMESPACE} raven-api
    
    echo -e "${YELLOW}⏳ Esperando a que los pods se reinicien...${NC}"
    ${KUBECTL_CMD} rollout status deployment -n ${NAMESPACE} raven-api --timeout=120s
    
    echo -e "${GREEN}✅ Despliegue reiniciado. Ejecutando verificación de estado...${NC}"
    check_status
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
        verify)
            verify_api_access
            ;;
        restart)
            restart_deployment
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
