# Script ultra-rápido para despliegue básico
#!/bin/bash

echo "🚀 RAVEN API - Despliegue Rápido"
echo "================================"

# Configuración rápida
NAMESPACE="raven-api"
DOMAIN="orchestrator.idea.lst.tfo.upm.es"

case "$1" in
  "quick")
    echo "📦 Desplegando aplicación..."
    kubectl apply -f kubernetes/secrets.yaml
    kubectl apply -f kubernetes/postgres-deployment.yaml 
    kubectl apply -f kubernetes/deployment.yaml
    kubectl apply -f kubernetes/service.yaml
    echo "✅ Aplicación desplegada"
    ;;
    
  "ssl")
    echo "🔐 Configurando SSL..."
    kubectl apply -f kubernetes/cluster-issuer.yaml
    kubectl apply -f kubernetes/certificate-prod.yaml
    echo "✅ SSL configurado"
    ;;
    
  "gateway")
    echo "🌐 Configurando acceso web..."
    kubectl apply -f kubernetes/gateway-final-fixed.yaml
    echo "✅ Gateway configurado"
    ;;
    
  "all")
    echo "🔄 Despliegue completo..."
    $0 quick && $0 ssl && $0 gateway
    echo "🎉 Todo listo: https://$DOMAIN"
    ;;
    
  "clean")
    echo "🧹 Limpiando..."
    kubectl delete -f kubernetes/ 2>/dev/null || true
    kubectl delete certificate raven-api-tls -n istio-system 2>/dev/null || true
    echo "✅ Limpio"
    ;;
    
  "status")
    echo "📊 Estado:"
    kubectl get pods -n $NAMESPACE
    kubectl get certificate raven-api-tls -n istio-system
    echo "🌐 URL: https://$DOMAIN"
    ;;
    
  *)
    echo "Uso: $0 [quick|ssl|gateway|all|clean|status]"
    echo ""
    echo "quick   - Solo aplicación"
    echo "ssl     - Solo certificado"  
    echo "gateway - Solo acceso web"
    echo "all     - Todo completo"
    echo "clean   - Limpiar todo"
    echo "status  - Ver estado"
    ;;
esac
