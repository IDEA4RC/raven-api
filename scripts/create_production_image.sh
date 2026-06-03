#!/bin/bash
set -e
docker build --no-cache -t sgonzmart/raven-api .
docker push sgonzmart/raven-api
