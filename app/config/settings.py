"""
Configurations and environment variables
"""

from typing import List, Optional, Union, Dict, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings
from secrets import token_urlsafe


class Settings(BaseSettings):
    # General configuration
    PROJECT_NAME: str = "RAVEN API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/raven-api/v1"
    ENVIRONMENT: str = "development"
    
    # CORS origins can be provided as CSV string or JSON/array via env
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Normalize CORS origins to a list of strings."""
        if not v:
            return []
        if isinstance(v, list):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        # Handle comma-separated string
        if "," in v:
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        # Single value string
        return [v.strip()] if str(v).strip() else []

    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins as a normalized list"""
        return self.assemble_cors_origins(self.BACKEND_CORS_ORIGINS)
    
    # Database
    DATABASE_URI: str = "postgresql://raven_user:raven_password@localhost:5432/raven_db"
    
    # JWT
    # IMPORTANT: Provide via environment in production
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Keycloak
    KEYCLOAK_SERVER_URL: str = ""
    KEYCLOAK_REALM: str = "idea4rc"
    KEYCLOAK_CLIENT_ID: str = "raven"
    KEYCLOAK_CLIENT_SECRET: str = ""
    KEYCLOAK_PUBLIC_KEY: Optional[str] = None
    KEYCLOAK_ADMIN_USERNAME: str = ""
    KEYCLOAK_ADMIN_PASSWORD: str = ""
    
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

    def model_post_init(self, __context: Dict[str, Any]) -> None:
        # Generate a dev-only secret key if none provided (not for production)
        if not self.SECRET_KEY:
            self.SECRET_KEY = token_urlsafe(32)


settings = Settings()
