"""OpenTelemetry-backed :class:`TracingProvider` implementation.

Provides production-grade distributed tracing behind the existing
:class:`TracingProvider` port.

Usage::

    from eaip.infrastructure.otel_tracing import OTelTracingProvider

    tracer = OTelTracingProvider(service_name="eaip")
    with tracer.span("process") as span:
        span.set_attribute("key", "value")
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from eaip.ports.tracing import Span, TracingProvider


class _OTelSpan(Span):
    """Wraps an OpenTelemetry span to match the EAIP Span protocol."""

    def __init__(self, span: Any) -> None:
        self._span = span

    def set_attribute(self, key: str, value: Any) -> None:
        self._span.set_attribute(key, value)

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self._span.add_event(name, attributes or {})

    def set_status(self, code: int, description: str = "") -> None:
        from opentelemetry.trace import Status, StatusCode

        self._span.set_status(Status(StatusCode(code), description))

    def end(self) -> None:
        self._span.end()


class OTelTracingProvider(TracingProvider):
    """Production tracing provider backed by OpenTelemetry.

    Exports traces via OTLP to any OpenTelemetry-compatible backend.
    """

    def __init__(
        self,
        service_name: str = "eaip",
        otlp_endpoint: str = "http://localhost:4318",
        sampling_ratio: float = 1.0,
    ) -> None:
        self._service_name = service_name
        self._otlp_endpoint = otlp_endpoint
        self._sampling_ratio = sampling_ratio
        self._tracer: Any = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": self._service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=f"{self._otlp_endpoint}/v1/traces")
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        self._tracer = trace.get_tracer(self._service_name)
        self._initialized = True

    def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> Span:
        self._ensure_initialized()
        span = self._tracer.start_span(name)
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)
        return _OTelSpan(span)

    @contextmanager
    def span(self, name: str, attributes: dict[str, Any] | None = None) -> Iterator[Span]:
        self._ensure_initialized()
        with self._tracer.start_as_current_span(name) as span:
            if attributes:
                for k, v in attributes.items():
                    span.set_attribute(k, v)
            yield _OTelSpan(span)

    def inject(self, span: Span) -> dict[str, str]:
        from opentelemetry import propagate

        carrier: dict[str, str] = {}
        if isinstance(span, _OTelSpan):
            propagate.inject(carrier, span._span)
        return carrier

    def current_span_id(self) -> str | None:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span:
            ctx = span.get_span_context()
            if ctx:
                return hex(ctx.span_id)
        return None

    def current_trace_id(self) -> str | None:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span:
            ctx = span.get_span_context()
            if ctx:
                return hex(ctx.trace_id)
        return None


__all__ = ["OTelTracingProvider"]
