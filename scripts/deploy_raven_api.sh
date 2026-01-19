#!/bin/bash
# deploy_raven_api.sh
# Script completo para Git Bash: limpia, build, push, despliega y port-forward

set -e

IMAGE_NAME="sgonzmart/raven-api-dev:1.0.2"
NAMESPACE="raven-api"
DEPLOYMENT_NAME="raven-api"


echo "🧹 Eliminando pods antiguos de raven-api..."
kubectl delete pod -n $NAMESPACE -l app=raven-api || true

echo "🧹 Limpiando contenedores locales de raven-api..."
docker ps -a -q --filter "name=raven-api" | xargs -r docker rm -f

echo "🧹 Borrando imágenes locales antiguas de raven-api-dev..."
docker images "sgonzmart/raven-api-dev" -q | xargs -r docker rmi -f

echo "📦 Construyendo la imagen $IMAGE_NAME..."
docker build -t $IMAGE_NAME .

echo "🚀 Pusheando la imagen al registry..."
docker push $IMAGE_NAME

echo "🔧 Actualizando Deployment con la nueva imagen..."
kubectl set image deployment/$DEPLOYMENT_NAME raven-api=$IMAGE_NAME -n $NAMESPACE

echo "⏳ Esperando a que el pod se levante..."
while true; do
    READY=$(kubectl get pods -n $NAMESPACE -l app=raven-api -o jsonpath='{.items[0].status.containerStatuses[0].ready}' 2>/dev/null || echo "false")
    if [ "$READY" == "true" ]; then
        echo "✅ Pod raven-api está listo!"
        break
    fi
    echo "⏳ Esperando..."
    sleep 5
done

echo "🚪 Iniciando port-forward (opcional)..."

echo "Iniciando port-forward de Istio Ingress Gateway (8080 y 8443)..."
kubectl -n istio-system port-forward svc/istio-ingressgateway 8080:80 8443:443 &

echo "Iniciando port-forward de PgAdmin (8081)..."
kubectl -n raven-api port-forward svc/pgadmin-service 8081:80 &

echo "✅ Ambos port-forward están activos. Usa CTRL+C para detenerlos."
wait