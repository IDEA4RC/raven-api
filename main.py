"""
Main FastAPI application instance.
"""

import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.api.routes import api_router
from app.config.settings import settings
from app.utils.telemetry import setup_telemetry

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

# Configurar telemetría para OpenTelemetry
if settings.ENABLE_TELEMETRY:
    setup_telemetry(app)

# Configurar métricas de Prometheus
if settings.ENABLE_PROMETHEUS:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Middleware for structured logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Validar que no haya barras adicionales al final (excepto la ruta raíz)
    if request.url.path != "/" and request.url.path.endswith("/"):
        from fastapi import HTTPException
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=400,
            content={"detail": "URL cannot end with trailing slash"}
        )
    
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
