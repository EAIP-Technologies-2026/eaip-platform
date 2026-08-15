"""Tests for the tracing provider setup (setup_telemetry, get_tracer, get_meter)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from eaip.settings.core_settings import TelemetrySettings
from eaip.tracing.provider import (
    force_flush,
    get_meter,
    get_tracer,
    setup_telemetry,
    shutdown_telemetry,
)

if TYPE_CHECKING:
    from opentelemetry.metrics import Meter
    from opentelemetry.trace import Tracer


class TestSetupTelemetry:
    def test_setup_tracer_provider(self) -> None:
        setup_telemetry(TelemetrySettings())
        tracer = get_tracer()
        assert isinstance(tracer, object)
        tracer_provider = get_tracer()
        assert tracer_provider is not None

    def test_setup_tracer_provider_tracing_disabled(self) -> None:
        settings = TelemetrySettings(tracing_enabled=False)
        setup_telemetry(settings)
        tracer = get_tracer()
        assert tracer is not None

    def test_setup_meter_provider(self) -> None:
        settings = TelemetrySettings(metrics_enabled=True)
        setup_telemetry(settings)
        meter = get_meter()
        assert meter is not None

    def test_setup_no_metrics(self) -> None:
        settings = TelemetrySettings(metrics_enabled=False)
        setup_telemetry(settings)
        meter = get_meter()
        assert meter is not None

    def test_otlp_endpoint_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("EAIP_TELEMETRY_OTLP_ENDPOINT", "http://custom:4318")
        settings = TelemetrySettings()
        assert settings.otlp_endpoint == "http://custom:4318"
        setup_telemetry(settings)
        tracer = get_tracer()
        assert tracer is not None


class TestTracer:
    def test_get_tracer_default_name(self) -> None:
        setup_telemetry(TelemetrySettings())
        tracer = get_tracer()
        assert isinstance(tracer, object)

    def test_get_tracer_custom_name(self) -> None:
        setup_telemetry(TelemetrySettings())
        tracer = get_tracer("myapp")
        assert isinstance(tracer, object)

    def test_get_tracer_returns_valid_tracer(self) -> None:
        setup_telemetry(TelemetrySettings())
        tracer: Tracer = get_tracer()
        with tracer.start_as_current_span("test") as span:
            span.set_attribute("test.key", "value")
            assert span.is_recording()


class TestMeter:
    def test_get_meter_default_name(self) -> None:
        setup_telemetry(TelemetrySettings(metrics_enabled=True))
        meter = get_meter()
        assert isinstance(meter, object)

    def test_get_meter_creates_instruments(self) -> None:
        setup_telemetry(TelemetrySettings(metrics_enabled=True))
        meter: Meter = get_meter()
        counter = meter.create_counter("test_counter", unit="1")
        assert counter is not None
        counter.add(1)
        counter.add(2)


class TestForceFlush:
    def test_force_flush_no_provider(self) -> None:
        force_flush()

    def test_force_flush_after_setup(self) -> None:
        setup_telemetry(TelemetrySettings())
        force_flush()


class TestShutdownTelemetry:
    def test_shutdown_no_provider(self) -> None:
        shutdown_telemetry()

    def test_shutdown_after_setup(self) -> None:
        setup_telemetry(TelemetrySettings())
        shutdown_telemetry()


class TestIdempotency:
    def test_setup_called_twice(self) -> None:
        setup_telemetry(TelemetrySettings())
        setup_telemetry(TelemetrySettings())
        tracer = get_tracer()
        assert tracer is not None

    def test_shutdown_twice(self) -> None:
        setup_telemetry(TelemetrySettings())
        shutdown_telemetry()
        shutdown_telemetry()

    def test_force_flush_after_shutdown(self) -> None:
        setup_telemetry(TelemetrySettings())
        shutdown_telemetry()
        force_flush()
