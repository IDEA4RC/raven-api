"""
Main FastAPI application instance.
"""

import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.api.routes import api_router
from app.config.settings import settings
from app.utils.telemetry import setup_telemetry

import logging
import sys

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configuration at application startup
    # Here you can add tasks like database initialization,
    # logging configuration, etc.
    yield
    # Cleanup at application shutdown
    # Close connections, free resources, etc.


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API for the RAVEN platform",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# MODO PRUEBAS: Autenticación desactivada temporalmente
# Para volver a activar la autenticación, restaura los comentarios en:
# - app/api/deps.py
# - app/api/endpoints/auth.py

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    logging.getLogger("app.validation").error(
        "[422] Validation error on %s %s | body: %s | errors: %s",
        request.method, request.url.path, body.decode("utf-8", errors="replace"), exc.errors()
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


# Configurar telemetría para OpenTelemetry
if settings.ENABLE_TELEMETRY:
    setup_telemetry(app)

# Configurar métricas de Prometheus
if settings.ENABLE_PROMETHEUS:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# CORS
cors_origins = settings.cors_origins
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Middleware for structured logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    
    # Log in JSON format for easier processing
    log_data = {
        "request_path": request.url.path,
        "request_method": request.method,
        "status_code": response.status_code,
        "client_host": request.client.host if request.client else None,
    }
    
    # Only print in JSON format for production environments
    if settings.ENVIRONMENT != "development":
        print(json.dumps(log_data))
    
    return response

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/raven-api/v1", tags=["Root"])
async def root():
    return {"message": "Welcome to the RAVEN API v1. For documentation, visit /docs or /redoc."}

# Configurar logging global
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout
)

# Suppress noisy third-party loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
# Access log spam (health probes hit this every ~10s)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


class _V6VerboseFilter(logging.Filter):
    """Drop high-volume development-only log lines from the V6 service."""
    _suppress = frozenset([
        "[V6] Payload to send to Vantage6",
        "[V6] workspace from db",
        "[V6] analysis from db",
        "[V6] cohorts from db",
    ])

    def filter(self, record: logging.LogRecord) -> bool:
        return not any(s in record.msg for s in self._suppress)


logging.getLogger("app.services.vantage_6").addFilter(_V6VerboseFilter())

# Reuse root handlers for uvicorn
logging.getLogger("uvicorn").handlers = logging.getLogger().handlers
logging.getLogger("uvicorn.error").handlers = logging.getLogger().handlers
logging.getLogger("uvicorn.access").handlers = logging.getLogger().handlers
