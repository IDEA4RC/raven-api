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
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    BACKEND_CORS_ORIGINS: List[str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database
    DATABASE_URI: str = "sqlite:///./raven.db"
    
    # JWT
    SECRET_KEY: str = "YOUR_SECRET_KEY_HERE"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Keycloak
    KEYCLOAK_SERVER_URL: str = "http://keycloak:8080/auth"
    KEYCLOAK_REALM: str = "raven"
    KEYCLOAK_CLIENT_ID: str = "raven-api"
    KEYCLOAK_CLIENT_SECRET: str = "client-secret"
    KEYCLOAK_ADMIN_USERNAME: str = "admin"
    KEYCLOAK_ADMIN_PASSWORD: str = "admin"
    
    # Telemetry
    ENABLE_TELEMETRY: bool = False
    TELEMETRY_ENDPOINT: str = "http://jaeger-collector:4317"
    TELEMETRY_SAMPLING_RATE: float = 1.0  # Percentage of traces to collect (1.0 = 100%)
    
    # Prometheus
    ENABLE_PROMETHEUS: bool = False
    METRICS_PORT: int = 8000

    model_config = {
        "case_sensitive": True,
        "env_file": ".env"
    }


settings = Settings()
