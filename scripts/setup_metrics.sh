#!/bin/bash
# setup_metrics.sh
# One-time setup for the metrics database.
# Uses scp to copy yamls to the VM, then applies them via SSH.
# Run from your local machine (Windows Git Bash) from the raven-api directory.
set -e

VM_USER="dcarvajal"
VM_HOST="138.4.10.238"
NAMESPACE="raven-api"

echo "Copying yaml files to VM..."
scp kubernetes/api-secrets.yaml ${VM_USER}@${VM_HOST}:/tmp/api-secrets.yaml
scp kubernetes/configmap.yaml ${VM_USER}@${VM_HOST}:/tmp/configmap.yaml
scp kubernetes/metrics-db-deployment.yaml ${VM_USER}@${VM_HOST}:/tmp/metrics-db-deployment.yaml

echo "Applying secrets..."
ssh -t ${VM_USER}@${VM_HOST} "sudo microk8s kubectl apply -f /tmp/api-secrets.yaml -n ${NAMESPACE}"

echo "Applying configmap..."
ssh -t ${VM_USER}@${VM_HOST} "sudo microk8s kubectl apply -f /tmp/configmap.yaml -n ${NAMESPACE}"

echo "Deploying metrics PostgreSQL..."
ssh -t ${VM_USER}@${VM_HOST} "sudo microk8s kubectl apply -f /tmp/metrics-db-deployment.yaml -n ${NAMESPACE}"

echo "Waiting for metrics-postgres to be ready..."
ssh -t ${VM_USER}@${VM_HOST} "sudo microk8s kubectl rollout status deployment/metrics-postgres -n ${NAMESPACE}"

echo "Cleaning up temp files..."
ssh ${VM_USER}@${VM_HOST} "rm /tmp/api-secrets.yaml /tmp/configmap.yaml /tmp/metrics-db-deployment.yaml"

echo "Done. Metrics database is up."
