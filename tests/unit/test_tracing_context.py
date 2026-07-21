"""Tests for the OTel-to-RuntimeContext bridge."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from opentelemetry import trace

from eaip.runtime.context import current_context
from eaip.settings.core_settings import TelemetrySettings
from eaip.tracing.context import current_trace_context, scoped_telemetry_context
from eaip.tracing.provider import setup_telemetry

if TYPE_CHECKING:
    from collections.abc import Generator

pytestmark = pytest.mark.usefixtures("_setup_otel")


@pytest.fixture(autouse=True)
def _setup_otel() -> Generator[None]:
    setup_telemetry(TelemetrySettings())
    yield


def _tracer():
    return trace.get_tracer("test")


class TestCurrentTraceContext:
    def test_no_active_span_returns_empty(self) -> None:
        ctx = current_trace_context()
        assert ctx == {}

    def test_with_active_span_returns_trace_ids(self) -> None:
        tracer = _tracer()
        with tracer.start_as_current_span("test"):
            ctx = current_trace_context()
            assert "trace_id" in ctx
            assert "span_id" in ctx
            assert isinstance(ctx["trace_id"], str)
            assert isinstance(ctx["span_id"], str)
            assert len(ctx["trace_id"]) == 32
            assert len(ctx["span_id"]) == 16

    def test_different_spans_produce_different_ids(self) -> None:
        tracer = _tracer()
        ids: list[dict[str, str]] = []

        with tracer.start_as_current_span("parent"):
            ids.append(current_trace_context())
            with tracer.start_as_current_span("child"):
                ids.append(current_trace_context())

        assert ids[0]["trace_id"] == ids[1]["trace_id"]
        assert ids[0]["span_id"] != ids[1]["span_id"]

    def test_outside_span_inside_span(self) -> None:
        tracer = _tracer()
        outside = current_trace_context()
        with tracer.start_as_current_span("inner"):
            inside = current_trace_context()
        assert outside == {}
        assert inside != {}


class TestScopedTelemetryContext:
    async def test_merges_trace_context_into_runtime_context(self) -> None:
        tracer = _tracer()
        with tracer.start_as_current_span("test"), scoped_telemetry_context():
            ctx = current_context()
            assert "trace_id" in ctx.labels
            assert "span_id" in ctx.labels

    async def test_merges_extra_labels(self) -> None:
        tracer = _tracer()
        with (
            tracer.start_as_current_span("test"),
            scoped_telemetry_context(labels={"tenant_id": "acme"}),
        ):
            ctx = current_context()
            assert ctx.labels["tenant_id"] == "acme"
            assert "trace_id" in ctx.labels

    async def test_trace_context_takes_precedence_over_labels(self) -> None:
        tracer = _tracer()
        with tracer.start_as_current_span("test"):
            span_id_from_trace = current_trace_context()["span_id"]
            with scoped_telemetry_context(labels={"span_id": "override"}):
                ctx = current_context()
                assert ctx.labels["span_id"] == span_id_from_trace

    async def test_forwards_labels_and_tenant(self) -> None:
        tracer = _tracer()
        with (
            tracer.start_as_current_span("test"),
            scoped_telemetry_context(labels={"user_id": "usr-1"}, tenant_id="tnt-1"),
        ):
            ctx = current_context()
            assert ctx.labels["user_id"] == "usr-1"
            assert ctx.tenant_id == "tnt-1"

    async def test_no_labels_no_trace_context(self) -> None:
        with scoped_telemetry_context():
            ctx = current_context()
            assert ctx.labels == {}

    async def test_no_active_span_still_works(self) -> None:
        with scoped_telemetry_context(labels={"request_id": "abc"}):
            ctx = current_context()
            assert ctx.labels.get("request_id") == "abc"
            assert "trace_id" not in ctx.labels

    async def test_context_restored_after_exit(self) -> None:
        tracer = _tracer()
        with tracer.start_as_current_span("test"), scoped_telemetry_context():
            inside = current_context()
            assert "trace_id" in inside.labels

        after = current_context()
        assert "trace_id" not in after.labels

    async def test_multiple_calls_nest_correctly(self) -> None:
        tracer = _tracer()
        with (
            tracer.start_as_current_span("outer"),
            scoped_telemetry_context(labels={"a": "1"}),
            scoped_telemetry_context(labels={"b": "2"}),
        ):
            ctx = current_context()
            assert ctx.labels.get("a") == "1"
            assert ctx.labels.get("b") == "2"
            assert "trace_id" in ctx.labels
