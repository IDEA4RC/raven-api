#!/bin/bash
# deploy_raven_api.sh
# Script completo para Git Bash: limpia, build, push, despliega y port-forward



docker build -t sgonzmart/raven-api-dev:latest .

docker push sgonzmart/raven-api-dev:latest


NAMESPACE="raven-api"

echo "📌 Obteniendo pod actual..."
OLD_POD=$(kubectl get pods -n $NAMESPACE -l app=raven-api -o jsonpath='{.items[0].metadata.name}')

echo "🔄 Reiniciando deployment..."
kubectl rollout restart deployment raven-api -n $NAMESPACE

echo "⏳ Esperando a que el pod viejo termine ($OLD_POD)..."
kubectl wait --for=delete pod/$OLD_POD -n $NAMESPACE --timeout=120s

echo "⏳ Esperando al nuevo pod..."
NEW_POD=""
while [ -z "$NEW_POD" ]; do
    NEW_POD=$(kubectl get pods -n $NAMESPACE -l app=raven-api -o jsonpath='{.items[?(@.metadata.name!="'$OLD_POD'")].metadata.name}')
    sleep 2
done
echo "📌 Nuevo pod detectado: $NEW_POD"


echo "⏳ Esperando a que el nuevo pod esté ready..."
kubectl wait --for=condition=ready pod/$NEW_POD -n $NAMESPACE --timeout=120s
echo "✅ Nuevo pod listo."


echo "Iniciando port-forward de Istio Ingress Gateway (8080 y 8443)..."
kubectl -n istio-system port-forward svc/istio-ingressgateway 8080:80 8443:443 &

echo "Iniciando port-forward de PgAdmin (8081)..."
kubectl -n raven-api port-forward svc/pgadmin-service 8081:80 &

echo "✅ Ambos port-forward están activos. Usa CTRL+C para detenerlos."
wait