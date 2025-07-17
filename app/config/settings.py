"""
Configurations and environment variables
"""

from typing import List, Optional, Union, Dict, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # General configuration
    PROJECT_NAME: str = "RAVEN API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/raven-api/v1"
    ENVIRONMENT: str = "development"
    
    # CORS origins as string, will be converted to list
    BACKEND_CORS_ORIGINS: str = ""

    @field_validator("BACKEND_CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: str) -> List[str]:
        """Convert CORS origins string to list"""
        if not v:
            return []
        
        # Handle comma-separated values
        if "," in v:
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        
        # Handle single value
        return [v.strip()] if v.strip() else []

    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins as a list"""
        return self.BACKEND_CORS_ORIGINS
    
    # Database
    DATABASE_URI: str = "postgresql://raven_user:raven_password@localhost:5432/raven_db"
    
    # JWT
    SECRET_KEY: str = "YOUR_SECRET_KEY_HERE"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Keycloak
    KEYCLOAK_SERVER_URL: str = "https://idea4rc-keykloak.development-iti.com"
    KEYCLOAK_REALM: str = "idea4rc"
    KEYCLOAK_CLIENT_ID: str = "raven"
    KEYCLOAK_CLIENT_SECRET: str = "EfesLqjtooH49AYUU2U4ZkJKfQGFuUwx"
    KEYCLOAK_PUBLIC_KEY: Optional[str] = None
    KEYCLOAK_ADMIN_USERNAME: str = "admin"
    KEYCLOAK_ADMIN_PASSWORD: str = "admin"
    
    # Telemetry
    ENABLE_TELEMETRY: bool = False
    TELEMETRY_ENDPOINT: str = "http://jaeger-collector:4317"
    TELEMETRY_SAMPLING_RATE: float = 1.0  # Percentage of traces to collect (1.0 = 100%)
    
    # Prometheus
    ENABLE_PROMETHEUS: bool = False
    METRICS_PORT: int = 8000
    
    # Host URL (para configurar endpoints externos)
    HOST_URL: str = "https://orchestrator.idea.lst.tfo.upm.es"

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore"  # Allow extra fields in .env file
    }


settings = Settings()
