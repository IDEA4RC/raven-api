"""
Telemetry and observability configuration using OpenTelemetry
"""

import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

from app.config.settings import settings


def setup_telemetry(app):
    """
    Configure telemetry and tracing for the application.
    Will only be configured if ENABLE_TELEMETRY is active.
    """
    if not settings.ENABLE_TELEMETRY:
        return

    # Create a resource with service metadata
    resource = Resource.create({
        "service.name": settings.PROJECT_NAME,
        "service.version": settings.VERSION,
        "deployment.environment": settings.ENVIRONMENT,
    })

    # Configure a sampler (1.0 = 100% of requests)
    sampler = TraceIdRatioBased(settings.TELEMETRY_SAMPLING_RATE)

    # Create a trace provider
    tracer_provider = TracerProvider(
        resource=resource,
        sampler=sampler
    )
    
    # Configure OTLP exporter to send traces to the backend
    # (Jaeger or any other OTLP-compatible system)
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.TELEMETRY_ENDPOINT
    )
    
    # Configure the processor that will send the spans
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)
    
    # Set the global trace provider
    trace.set_tracer_provider(tracer_provider)
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
