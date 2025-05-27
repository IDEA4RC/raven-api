#!/bin/bash
# Script para generar un certificado TLS autofirmado para Istio

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin Color

KUBECTL_CMD="microk8s kubectl"
NAMESPACE="istio-system"
HOST="orchestrator.idea.lst.tfo.upm.es"
CERT_NAME="raven-api-cert"

echo -e "${YELLOW}🔒 Generando certificado TLS autofirmado para $HOST...${NC}"

# Crear directorio temporal para los certificados
TEMP_DIR=$(mktemp -d)
cd $TEMP_DIR

# Generar clave privada
echo -e "${YELLOW}ℹ️ Generando clave privada...${NC}"
openssl genrsa -out key.pem 2048

# Generar solicitud de certificado
echo -e "${YELLOW}ℹ️ Generando solicitud de certificado...${NC}"
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
echo -e "${YELLOW}ℹ️ Generando certificado autofirmado...${NC}"
openssl x509 -req -in csr.pem -signkey key.pem -out cert.pem -days 365 -extfile csr.conf -extensions req_ext

# Verificar el certificado
echo -e "${YELLOW}ℹ️ Verificando el certificado generado...${NC}"
openssl x509 -in cert.pem -text -noout | grep -A1 "Subject Alternative Name"

# Crear secreto de Kubernetes con el certificado
echo -e "${YELLOW}ℹ️ Creando secreto de Kubernetes con el certificado...${NC}"
$KUBECTL_CMD create -n $NAMESPACE secret tls $CERT_NAME --key=key.pem --cert=cert.pem --dry-run=client -o yaml > tls-secret.yaml

echo -e "${YELLOW}ℹ️ Aplicando el secreto al clúster...${NC}"
$KUBECTL_CMD apply -f tls-secret.yaml

# Limpiar archivos temporales
cd - > /dev/null
rm -rf $TEMP_DIR

echo -e "${GREEN}✅ Certificado TLS autofirmado creado y configurado correctamente.${NC}"
echo -e "${YELLOW}⚠️ NOTA: Este es un certificado autofirmado para pruebas.${NC}"
echo -e "${YELLOW}ℹ️ Para producción, debes usar un certificado válido de una CA reconocida.${NC}"

echo -e "${YELLOW}ℹ️ Ahora puedes aplicar el gateway con soporte HTTPS:${NC}"
echo -e "$KUBECTL_CMD apply -f kubernetes/gateway-with-https.yaml -n raven"
