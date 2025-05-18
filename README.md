# RAVEN API

API for the RAVEN platform developed with FastAPI.

## Description

This project implements a RESTful API for the RAVEN platform using FastAPI, SQLAlchemy, and Pydantic. The API is structured following best practices to facilitate its maintenance and scalability.

## Requirements

- Python 3.11+
- pip (package manager for Python)
- Docker (for container building)
- MicroK8s or Kubernetes with Istio (for deployment)
- OpenSSL (for TLS certificate generation)

## Installation with pip

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/raven-api.git
   cd raven-api
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with appropriate values
   ```

4. Initialize the database:
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
│   ├── gateway.yaml        # Istio Gateway configuration
│   ├── gateway-with-https.yaml # Istio Gateway with HTTPS support
│   ├── secrets.yaml        # Secrets for configuration
│   └── virtual-service.yaml # Istio VirtualService configuration
│
├── scripts/                # Utility scripts
│   ├── check-istio.sh      # Check and enable Istio
│   ├── check-registry.sh   # Check and enable MicroK8s registry
│   ├── deploy.sh           # Deployment script
│   ├── generate-tls-cert.sh # Generate TLS certificates
│   ├── seed_db.py          # Database seeder
│   └── verify-api-access.sh # API accessibility verification
│
├── migrations/             # Database migrations
├── tests/                  # Unit and integration tests
├── .env.example            # Environment variables template
├── docker-entrypoint.sh    # Docker entry point script
├── Dockerfile              # Definition for building the image
├── main.py                 # Application entry point
├── raven-ctl.sh            # Main control script for RAVEN API
├── pyproject.toml          # Configuration for Python tools
└── requirements.txt        # Project dependencies
```

## Tests

To run tests:

```bash
pytest
```

## Building the Docker Image

To build the Docker image for the application:

```bash
docker build -t raven-api:latest .
```

## Deployment on Kubernetes with Istio

### Using the Control Script (Recommended)

The project includes a comprehensive control script (`raven-ctl.sh`) that simplifies the deployment, exposure, and management of the RAVEN API on Kubernetes with Istio.

1. Make sure you have a MicroK8s or Kubernetes cluster with Istio installed.

2. Make the control script executable:

   ```bash
   chmod +x raven-ctl.sh
   ```

3. Use the script with different commands:

   ```bash
   # Display help and available commands
   ./raven-ctl.sh help
   
   # Deploy the API (builds and deploys the application)
   ./raven-ctl.sh deploy
   
   # Expose the API to the internet (HTTP)
   ./raven-ctl.sh expose
   
   # Configure HTTPS with TLS certificate
   ./raven-ctl.sh secure
   
   # Check the status of the deployment
   ./raven-ctl.sh status
   
   # Clean up the deployment
   ./raven-ctl.sh cleanup
   ```

4. The script supports various options:

   ```bash
   # Skip image building
   ./raven-ctl.sh deploy --skip-build
   
   # Build without using Docker cache
   ./raven-ctl.sh deploy --no-cache
   
   # Specify a custom registry
   ./raven-ctl.sh deploy --registry=myregistry.example.com
   
   # Specify a custom hostname
   ./raven-ctl.sh expose --hostname=api.example.com
   ```

### Manual Deployment

If you prefer to deploy manually, follow these steps:

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

## Exposing the API to the Internet

To expose the RAVEN API to the internet, you can use the control script:

```bash
# Expose with HTTP
./raven-ctl.sh expose

# Configure HTTPS
./raven-ctl.sh secure
```

The script will guide you through the following options:

1. **Using MetalLB (recommended for local environments)**: Configures MetalLB to provide LoadBalancer capabilities.
2. **Using NodePort**: Exposes the API through a specific port on the nodes.
3. **Manual configuration**: For advanced scenarios or cloud environments.

After exposure, the script will provide the necessary information to access the API, including:
- External IP or hostname
- Required DNS configuration
- How to test the accessibility

## Security Considerations

When deploying to production:

1. Use valid TLS certificates from a trusted CA instead of self-signed certificates.
2. Configure proper access controls and authentication.
3. Secure sensitive environment variables using Kubernetes secrets.
4. Consider implementing network policies to restrict traffic.

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