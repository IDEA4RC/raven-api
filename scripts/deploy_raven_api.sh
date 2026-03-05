#!/bin/bash
# deploy_raven_api.sh
# Script completo para Git Bash: limpia, build, push, despliega y port-forward
set -e

IMAGE_NAME="sgonzmart/raven-api-dev:1.0.4"
NAMESPACE="raven-api"
DEPLOYMENT_NAME="raven-api"

echo "🧹 Eliminando contenedores locales de raven-api..."
docker ps -a -q --filter "name=raven-api" | xargs -r docker rm -f || true

echo "🧹 Borrando imagen local antigua $IMAGE_NAME..."
docker rmi -f $IMAGE_NAME || true

echo "📦 Construyendo imagen $IMAGE_NAME sin cache..."
docker build --no-cache -t $IMAGE_NAME .

echo "🚀 Pusheando la imagen al registry..."
docker push $IMAGE_NAME

echo "🔧 Actualizando Deployment con la imagen reconstruida..."
kubectl set image deployment/$DEPLOYMENT_NAME raven-api=$IMAGE_NAME -n $NAMESPACE --record

echo "⏳ Forzando recreación completa del Deployment..."
kubectl rollout restart deployment/$DEPLOYMENT_NAME -n $NAMESPACE

echo "⏳ Esperando a que todos los pods estén listos..."
kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE

# --- Port-forward ---
echo "🛑 Matando port-forwards antiguos..."
pkill -f "kubectl.*port-forward.*raven-api" || true
pkill -f "kubectl.*port-forward.*pgadmin" || true

echo "🚪 Iniciando port-forward Istio Ingress Gateway (8080:80, 8443:443)..."
kubectl -n istio-system port-forward svc/istio-ingressgateway 8080:80 8443:443 &

echo "🚪 Iniciando port-forward PgAdmin (8081:80)..."
kubectl -n $NAMESPACE port-forward svc/pgadmin-service 8081:80 &

echo "✅ Deploy completo. Usa CTRL+C para detener los port-forwards."
wait