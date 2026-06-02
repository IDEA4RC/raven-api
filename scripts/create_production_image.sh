#!/bin/bash
set -e
docker build -t sgonzmart/raven-api .
docker push sgonzmart/raven-api
