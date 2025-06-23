#!/bin/bash

# Script para configurar HTTPS con cert-manager y Let's Encrypt
# Este script despliega el certificado SSL y actualiza el Gateway de Istio

set -e

echo "🔐 Configurando HTTPS para RAVEN API..."

# Verificar que cert-manager esté instalado
echo "📋 Verificando cert-manager..."
if ! kubectl get pods -n cert-manager | grep -q "Running"; then
    echo "❌ Error: cert-manager no está ejecutándose correctamente"
    echo "Ejecuta primero: kubectl get pods -n cert-manager"
    exit 1
fi

# Aplicar ClusterIssuer si no existe
echo "🏗️ Aplicando ClusterIssuer..."
kubectl apply -f kubernetes/cluster-issuer.yaml

# Esperar a que el ClusterIssuer esté listo
echo "⏳ Esperando a que el ClusterIssuer esté listo..."
sleep 10
kubectl get clusterissuer

# Aplicar el Certificate
echo "📜 Creando Certificate para Let's Encrypt..."
kubectl apply -f kubernetes/certificate-prod.yaml

# Verificar el estado del Certificate
echo "🔍 Verificando el estado del Certificate..."
sleep 5
kubectl describe certificate raven-api-tls -n istio-system

# Aplicar el Gateway con HTTPS
echo "🌐 Desplegando Gateway con HTTPS..."
kubectl apply -f kubernetes/gateway-https.yaml

# Verificar el estado del secreto TLS
echo "🔐 Verificando el secreto TLS..."
sleep 10
kubectl get secret raven-api-tls-secret -n istio-system || echo "⚠️ Secreto TLS aún no creado, puede tardar unos minutos..."

# Mostrar el estado final
echo "✅ Configuración HTTPS desplegada!"
echo ""
echo "📊 Estado actual:"
echo "=================="
kubectl get certificate -n istio-system
echo ""
kubectl get secret raven-api-tls-secret -n istio-system || echo "Secreto TLS pendiente..."
echo ""
kubectl get gateway

echo ""
echo "🔍 Para monitorear el progreso del certificado:"
echo "kubectl describe certificate raven-api-tls -n istio-system"
echo "kubectl get certificaterequest -n istio-system"
echo "kubectl logs -n cert-manager -l app=cert-manager"
echo ""
echo "🌐 Una vez listo, tu API estará disponible en:"
echo "https://orchestrator.idea.lst.tfo.upm.es"
