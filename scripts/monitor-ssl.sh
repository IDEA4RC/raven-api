#!/bin/bash

# Script para monitorear el estado de los certificados SSL
# Útil para verificar el progreso de la emisión de certificados con Let's Encrypt

echo "🔐 Estado de Certificados SSL - RAVEN API"
echo "=========================================="
echo ""

# Verificar cert-manager
echo "📋 Estado de cert-manager:"
kubectl get pods -n cert-manager
echo ""

# Estado del ClusterIssuer
echo "🏭 ClusterIssuer:"
kubectl get clusterissuer
echo ""

# Estado del Certificate
echo "📜 Certificate:"
kubectl get certificate -n istio-system
echo ""

# Detalles del Certificate
echo "🔍 Detalles del Certificate raven-api-tls:"
echo "----------------------------------------"
kubectl describe certificate raven-api-tls -n istio-system 2>/dev/null || echo "Certificate no encontrado"
echo ""

# Estado de CertificateRequest
echo "📝 CertificateRequest:"
kubectl get certificaterequest -n istio-system 2>/dev/null || echo "No hay CertificateRequest activos"
echo ""

# Estado del secreto TLS
echo "🔐 Secreto TLS:"
kubectl get secret raven-api-tls-secret -n istio-system 2>/dev/null || echo "Secreto TLS no encontrado (aún no se ha emitido el certificado)"
echo ""

# Si el secreto existe, mostrar detalles
if kubectl get secret raven-api-tls-secret -n istio-system >/dev/null 2>&1; then
    echo "🔍 Detalles del certificado:"
    kubectl get secret raven-api-tls-secret -n istio-system -o yaml | grep -A 5 -B 5 "tls.crt\|tls.key" || true
fi
echo ""

# Estado del Gateway
echo "🌐 Gateway:"
kubectl get gateway
echo ""

# Logs recientes de cert-manager
echo "📋 Logs recientes de cert-manager (últimas 10 líneas):"
echo "---------------------------------------------------"
kubectl logs -n cert-manager -l app=cert-manager --tail=10 2>/dev/null || echo "No se pudieron obtener los logs"
echo ""

# Instrucciones
echo "💡 Comandos útiles:"
echo "==================="
echo "Ver logs completos de cert-manager:"
echo "  kubectl logs -n cert-manager -l app=cert-manager -f"
echo ""
echo "Ver eventos del namespace istio-system:"
echo "  kubectl get events -n istio-system --sort-by='.lastTimestamp'"
echo ""
echo "Eliminar y recrear el certificate si hay problemas:"
echo "  kubectl delete certificate raven-api-tls -n istio-system"
echo "  kubectl apply -f kubernetes/certificate-prod.yaml"
echo ""
echo "Verificar conectividad HTTPS:"
echo "  curl -I https://orchestrator.idea.lst.tfo.upm.es"
