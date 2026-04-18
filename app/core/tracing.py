"""OpenTelemetry-трассировка.

Активируется только при выставленной OTEL_EXPORTER_OTLP_ENDPOINT —
иначе вызов setup_tracing() ничего не делает, и зависимость от
otel не напрягает локальную разработку.

Автоинструментация FastAPI + SQLAlchemy — span'ы HTTP и DB уходят в
один trace_id, коррелирующийся с нашим request_id через атрибут.
"""

from __future__ import annotations

import os

from app.core.logging import get_logger

_log = get_logger("tracing")


def setup_tracing(app, engine) -> None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        _log.info("otel_disabled", reason="OTEL_EXPORTER_OTLP_ENDPOINT not set")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError as exc:
        _log.warning("otel_libraries_missing", error=str(exc))
        return

    resource = Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", "serviceflow-backend"),
            "service.version": "0.1.0",
            "deployment.environment": os.getenv("ENV", "dev"),
        }
    )

    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine)

    _log.info("otel_enabled", endpoint=endpoint)
