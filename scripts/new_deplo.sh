#!/bin/bash
set -e

IMAGE="sgonzmart/raven-api-dev:1.0.5"
NS="raven-api"

docker build -t $IMAGE .
docker push $IMAGE

kubectl set image deployment/raven-api raven-api=$IMAGE -n $NS
kubectl rollout status deployment/raven-api -n $NS