"""
Script to run the API with uvicorn
Includes configuration for environments with Istio
"""

import os
import uvicorn

if __name__ == "__main__":
    # Configuration for environments with Istio
    # In Kubernetes, ports are remapped by the Service
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    # Determine if we're in a development environment
    is_dev = os.getenv("ENV", "dev").lower() == "dev"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=is_dev,
        proxy_headers=True,  # Important for Istio/proxy
        forwarded_allow_ips="*"  # Trust X-Forwarded-* headers
    )
