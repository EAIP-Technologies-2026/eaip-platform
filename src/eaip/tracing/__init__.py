"""OpenTelemetry Telemetry Baseline — tracing, metrics, and export.

Provides the OTel integration for the EAIP platform:

- ``setup_telemetry()`` — configures the global tracer and meter providers.
- ``traced()`` — async function decorator that creates OTel spans.
- ``scoped_telemetry_context()`` — bridges OTel trace context to ``RuntimeContext``.
- ``get_tracer()``, ``get_meter()`` — access named tracer/meter instances.
- ``force_flush()``, ``shutdown_telemetry()`` — lifecycle management.
"""

from __future__ import annotations

from eaip.settings.core_settings import TelemetrySettings
from eaip.tracing.context import current_trace_context, scoped_telemetry_context
from eaip.tracing.decorators import traced
from eaip.tracing.provider import (
    force_flush,
    get_meter,
    get_tracer,
    setup_telemetry,
    shutdown_telemetry,
)

__all__ = [
    "TelemetrySettings",
    "current_trace_context",
    "force_flush",
    "get_meter",
    "get_tracer",
    "scoped_telemetry_context",
    "setup_telemetry",
    "shutdown_telemetry",
    "traced",
]
