#!/bin/bash
# port-forward-all.sh

echo "Iniciando port-forward de Istio Ingress Gateway (8080 y 8443)..."
kubectl -n istio-system port-forward svc/istio-ingressgateway 8080:80 8443:443 &

echo "Iniciando port-forward de PgAdmin (8081)..."
kubectl -n raven-api port-forward svc/pgadmin-service 8081:80 &

echo "✅ Ambos port-forward están activos. Usa CTRL+C para detenerlos."
wait