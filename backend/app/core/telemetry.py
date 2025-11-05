"""
OpenTelemetry configuration for distributed tracing and observability.

This module sets up OpenTelemetry instrumentation for FastAPI, including:
- Automatic instrumentation for HTTP requests
- OTLP exporter for sending traces to a collector
- Resource detection and service identification
"""

import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


def configure_opentelemetry(app) -> None:
	"""
	Configure OpenTelemetry instrumentation for the FastAPI application.

	Args:
	    app: FastAPI application instance
	"""
	settings = get_settings()

	if not settings.enable_opentelemetry:
		logger.info("OpenTelemetry is disabled")
		return

	try:
		# Create resource with service information
		resource = Resource.create(
			{
				"service.name": settings.service_name,
				"service.version": "1.0.0",
				"deployment.environment": settings.environment,
			}
		)

		# Create tracer provider
		tracer_provider = TracerProvider(resource=resource)

		# Add OTLP exporter if endpoint is configured
		if settings.otlp_endpoint:
			otlp_exporter = OTLPSpanExporter(
				endpoint=settings.otlp_endpoint,
				insecure=True,  # Use insecure for local dev
			)
			tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
			logger.info(f"OTLP exporter configured: {settings.otlp_endpoint}")

		# Add console exporter for development
		if settings.environment == "development":
			console_exporter = ConsoleSpanExporter()
			tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
			logger.info("Console span exporter enabled for development")

		# Set global tracer provider
		trace.set_tracer_provider(tracer_provider)

		# Instrument FastAPI
		FastAPIInstrumentor.instrument_app(app)

		logger.info(f"✅ OpenTelemetry configured for service: {settings.service_name}")

	except Exception as e:
		logger.error(f"Failed to configure OpenTelemetry: {e}", exc_info=True)
		logger.warning("Application will continue without OpenTelemetry")


def get_tracer(name: str) -> trace.Tracer:
	"""
	Get a tracer instance for manual instrumentation.

	Args:
	    name: Name of the tracer (typically __name__)

	Returns:
	    Tracer instance
	"""
	return trace.get_tracer(name)


def create_span(name: str, tracer: Optional[trace.Tracer] = None, **attributes) -> trace.Span:
	"""
	Create a new span for manual instrumentation.

	Args:
	    name: Name of the span
	    tracer: Optional tracer instance (creates default if None)
	    **attributes: Additional span attributes

	Returns:
	    Span context manager

	Example:
	    with create_span("my_operation", user_id=123) as span:
	        # Your code here
	        span.set_attribute("result", "success")
	"""
	if tracer is None:
		tracer = get_tracer(__name__)

	span = tracer.start_span(name)

	# Set attributes
	for key, value in attributes.items():
		span.set_attribute(key, value)

	return span
