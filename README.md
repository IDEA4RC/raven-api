# RAVEN API

API for the RAVEN platform developed with FastAPI.

## Description

This project implements a RESTful API for the RAVEN platform using FastAPI, SQLAlchemy, and Pydantic. The API is structured following best practices to facilitate its maintenance and scalability.

## Requirements

- Python 3.11+
- uv (modern package manager for Python)
- Docker (for container building)
- Kubernetes and Istio (for deployment)

## Installation with uv

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/raven-api.git
   cd raven-api
   ```

2. Install uv if you don't have it:
   ```bash
   pip install uv
   ```

3. Create a virtual environment and install dependencies with uv:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with appropriate values
   ```

5. Initialize the database:
   ```bash
   python -m app.db.init_db
   ```

## Execution

To run the API in development mode:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.
Interactive documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
raven-api/
│
├── app/                    # Main package
│   ├── api/                # Route and endpoint definitions
│   │   └── endpoints/      # Endpoints organized by resource
│   ├── config/             # Project configuration
│   ├── db/                 # Database configuration
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas for validation
│   ├── services/           # Business logic
│   └── utils/              # Utilities and helper functions
│
├── kubernetes/             # Kubernetes and Istio manifests
│   ├── deployment.yaml     # Deployment definition
│   ├── service.yaml        # Service definition
│   ├── gateway.yaml        # Istio Gateway
│   ├── secrets.yaml        # Secrets for configuration
│   └── virtual-service.yaml # Istio VirtualService
│
├── migrations/             # Database migrations
├── tests/                  # Unit and integration tests
├── .env.example            # Environment variables template
├── Dockerfile              # Definition for building the image
├── main.py                 # Application entry point
├── pyproject.toml          # Configuration for uv and tools
└── requirements.txt        # Project dependencies
```

## Tests

To run tests with uv:

```bash
uv run pytest
```

## Building the Docker Image

To build the Docker image for the application:

```bash
docker build -t raven-api:latest .
```

## Deployment on Kubernetes with Istio

1. Make sure you have a Kubernetes cluster with Istio installed.

2. Apply the Kubernetes manifests:

   ```bash
   # Create namespace and enable Istio injection
   kubectl create namespace raven
   kubectl label namespace raven istio-injection=enabled
   
   # Apply secrets first
   kubectl apply -f kubernetes/secrets.yaml -n raven
   
   # Apply the rest of the resources
   kubectl apply -f kubernetes/deployment.yaml -n raven
   kubectl apply -f kubernetes/service.yaml -n raven
   kubectl apply -f kubernetes/gateway.yaml -n raven
   kubectl apply -f kubernetes/virtual-service.yaml -n raven
   ```

3. Verify the deployment:

   ```bash
   kubectl get pods -n raven
   kubectl get svc -n raven
   kubectl get virtualservice -n raven
   kubectl get gateway -n raven
   ```

## Monitoring with Istio

Once deployed with Istio, you can use the integrated tools for monitoring:

- **Kiali**: For service mesh visualization
- **Jaeger/Zipkin**: For distributed tracing
- **Prometheus/Grafana**: For metrics and dashboards

## License



Copyright 2025 Universidad Politécnica de Madrid
Copyright 2025 RAVEN Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.