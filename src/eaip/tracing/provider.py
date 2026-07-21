"""OpenTelemetry provider setup — tracer, meter, and export pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.metrics import (
    get_meter as _get_meter,
    get_meter_provider as _get_mp,
    set_meter_provider as _set_mp,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio
from opentelemetry.trace import get_tracer as _get_tracer, get_tracer_provider, set_tracer_provider

from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from opentelemetry.metrics import Meter
    from opentelemetry.trace import Tracer

    from eaip.settings.core_settings import TelemetrySettings


_log = get_logger("eaip.tracing.provider")


def _build_resource(settings: TelemetrySettings) -> Resource:
    return Resource.create(
        {
            "service.name": settings.service_name,
            "service.version": "0.0.2",
        }
    )


def setup_telemetry(settings: TelemetrySettings) -> None:
    """Configure the global OTel trace and metric providers.

    Called once during platform bootstrap.
    """
    resource = _build_resource(settings)

    if settings.tracing_enabled:
        sampler = ParentBasedTraceIdRatio(settings.sampling_ratio)
        tracer_provider = TracerProvider(resource=resource, sampler=sampler)
        span_exporter = OTLPSpanExporter(
            endpoint=f"{settings.otlp_endpoint}/v1/traces",
        )
        tracer_provider.add_span_processor(
            BatchSpanProcessor(span_exporter),
        )
        set_tracer_provider(tracer_provider)
        _log.info("telemetry.tracing.enabled", endpoint=settings.otlp_endpoint)
    else:
        _log.info("telemetry.tracing.disabled")

    if settings.metrics_enabled:
        metric_exporter = OTLPMetricExporter(
            endpoint=f"{settings.otlp_endpoint}/v1/metrics",
        )
        reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=30_000)
        meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
        _set_mp(meter_provider)
        _log.info("telemetry.metrics.enabled", endpoint=settings.otlp_endpoint)
    else:
        _log.info("telemetry.metrics.disabled")


def force_flush() -> None:
    """Force-flush any pending telemetry data."""
    try:
        tracer_provider = get_tracer_provider()
        if isinstance(tracer_provider, TracerProvider):
            tracer_provider.force_flush()
    except Exception:
        _log.warning("telemetry.force_flush.trace_failed")
    try:
        mp = _get_mp()
        if isinstance(mp, MeterProvider):
            mp.force_flush()
    except Exception:
        _log.warning("telemetry.force_flush.metrics_failed")


def shutdown_telemetry() -> None:
    """Shut down the telemetry pipeline."""
    try:
        tracer_provider = get_tracer_provider()
        if isinstance(tracer_provider, TracerProvider):
            tracer_provider.shutdown()
    except Exception:
        _log.warning("telemetry.shutdown.trace_failed")
    try:
        mp = _get_mp()
        if isinstance(mp, MeterProvider):
            mp.shutdown()
    except Exception:
        _log.warning("telemetry.shutdown.metrics_failed")


def get_tracer(name: str = "eaip") -> Tracer:
    """Return a named tracer."""
    return _get_tracer(name)


def get_meter(name: str = "eaip") -> Meter:
    """Return a named meter."""
    return _get_meter(name)


__all__ = [
    "force_flush",
    "get_meter",
    "get_tracer",
    "setup_telemetry",
    "shutdown_telemetry",
]
