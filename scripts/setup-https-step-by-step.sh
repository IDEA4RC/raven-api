#!/bin/bash

# Script paso a paso para configurar HTTPS con Let's Encrypt
# Primero prueba con staging, luego permite cambiar a producción

set -e

echo "🔐 Configuración HTTPS para RAVEN API - Paso a Paso"
echo "===================================================="
echo ""

# Función para esperar entrada del usuario
wait_for_user() {
    echo "Presiona Enter para continuar..."
    read
}

# Paso 1: Verificar cert-manager
echo "PASO 1: Verificando cert-manager..."
echo "-----------------------------------"
kubectl get pods -n cert-manager
echo ""
if ! kubectl get pods -n cert-manager | grep -q "Running"; then
    echo "❌ Error: cert-manager no está ejecutándose correctamente"
    exit 1
fi
echo "✅ cert-manager está funcionando"
wait_for_user

# Paso 2: Aplicar ClusterIssuer
echo "PASO 2: Aplicando ClusterIssuer..."
echo "----------------------------------"
kubectl apply -f kubernetes/cluster-issuer.yaml
echo "✅ ClusterIssuer aplicado"
sleep 5
kubectl get clusterissuer
wait_for_user

# Paso 3: Probar con certificado de staging
echo "PASO 3: Probando con certificado de STAGING..."
echo "----------------------------------------------"
echo "⚠️ Primero vamos a probar con Let's Encrypt staging para evitar límites de rate"
kubectl apply -f kubernetes/certificate-staging.yaml
echo "✅ Certificate de staging aplicado"
echo ""

echo "Esperando 30 segundos para que se procese..."
sleep 30

echo "Estado del certificate de staging:"
kubectl get certificate -n istio-system
echo ""
kubectl describe certificate raven-api-tls-staging -n istio-system
wait_for_user

# Paso 4: Verificar que el certificado de staging funcione
echo "PASO 4: Verificando certificado de staging..."
echo "--------------------------------------------"
kubectl get secret raven-api-tls-staging-secret -n istio-system 2>/dev/null || echo "Secreto de staging aún no creado"

echo ""
echo "Si ves errores, revisa los logs:"
echo "kubectl logs -n cert-manager -l app=cert-manager --tail=20"
echo ""
echo "¿El certificado de staging se creó correctamente? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "✅ ¡Perfecto! Continuando con producción..."
else
    echo "❌ Hay problemas con staging. Revisa los logs y configuración."
    echo "Comandos útiles:"
    echo "kubectl describe certificate raven-api-tls-staging -n istio-system"
    echo "kubectl get events -n istio-system --sort-by='.lastTimestamp'"
    echo "kubectl logs -n cert-manager -l app=cert-manager"
    exit 1
fi

# Paso 5: Aplicar certificado de producción
echo ""
echo "PASO 5: Aplicando certificado de PRODUCCIÓN..."
echo "----------------------------------------------"
echo "⚠️ Ahora vamos a crear el certificado de producción"
kubectl apply -f kubernetes/certificate-prod.yaml
echo "✅ Certificate de producción aplicado"

echo "Esperando 30 segundos para que se procese..."
sleep 30

kubectl get certificate -n istio-system
echo ""
kubectl describe certificate raven-api-tls -n istio-system
wait_for_user

# Paso 6: Aplicar Gateway con HTTPS
echo "PASO 6: Desplegando Gateway con HTTPS..."
echo "----------------------------------------"
kubectl apply -f kubernetes/gateway-https.yaml
echo "✅ Gateway con HTTPS aplicado"
echo ""
kubectl get gateway
wait_for_user

# Paso 7: Verificación final
echo "PASO 7: Verificación final..."
echo "----------------------------"
echo "Estado de certificates:"
kubectl get certificate -n istio-system
echo ""

echo "Estado de secretos TLS:"
kubectl get secret -n istio-system | grep tls || echo "No se encontraron secretos TLS"
echo ""

echo "Esperando 60 segundos adicionales para que todo se propague..."
sleep 60

echo ""
echo "🎉 Configuración completada!"
echo "============================"
echo ""
echo "🔍 Para verificar que todo funciona:"
echo "curl -I https://orchestrator.idea.lst.tfo.upm.es"
echo ""
echo "📊 Para monitorear el estado:"
echo "./scripts/monitor-ssl.sh"
echo ""
echo "🐛 Si hay problemas, revisa:"
echo "kubectl logs -n cert-manager -l app=cert-manager"
echo "kubectl get events -n istio-system --sort-by='.lastTimestamp'"
