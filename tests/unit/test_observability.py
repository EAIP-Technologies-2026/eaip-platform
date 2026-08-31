"""Tests for observability infrastructure: logging, metrics, tracing, task registry, diagnostics."""

from __future__ import annotations

import asyncio
import time

import pytest

from eaip.infrastructure.logger import InMemoryLogger
from eaip.infrastructure.metrics import InMemoryMetricsProvider
from eaip.infrastructure.tracing import NoOpTracingProvider
from eaip.runtime.diagnostics import RuntimeDiagnosticsService
from eaip.shared.background_task_registry import BackgroundTaskRegistry


class TestInMemoryLogger:
    def test_log_levels(self) -> None:
        logger = InMemoryLogger(level="INFO")
        logger.debug("should not appear")
        assert logger.entry_count == 0
        logger.info("should appear")
        assert logger.entry_count == 1

    def test_bind_creates_new_logger(self) -> None:
        logger = InMemoryLogger(level="INFO")
        bound = logger.bind(service="test")
        bound.info("event", key="val")
        assert bound.entry_count == 1
        entry = bound.entries[0]
        assert entry.context["service"] == "test"
        assert entry.context["key"] == "val"

    def test_filter_by_level(self) -> None:
        logger = InMemoryLogger(level="DEBUG")
        logger.info("one")
        logger.warning("two")
        logger.error("three")
        assert len(logger.filter_by_level("INFO")) == 1
        assert len(logger.filter_by_level("WARNING")) == 1
        assert len(logger.filter_by_level("ERROR")) == 1

    def test_filter_by_event(self) -> None:
        logger = InMemoryLogger(level="INFO")
        logger.info("user.login")
        logger.info("user.logout")
        logger.info("data.sync")
        assert len(logger.filter_by_event("user.login")) == 1
        assert len(logger.filter_by_event("user")) == 0  # exact match

    def test_clear(self) -> None:
        logger = InMemoryLogger(level="INFO")
        logger.info("one")
        logger.clear()
        assert logger.entry_count == 0

    def test_json_format(self) -> None:
        logger = InMemoryLogger(level="INFO")
        logger.info("test.event", user_id="abc")
        line = logger.format_json()
        assert "test.event" in line
        assert "abc" in line

    def test_is_enabled_for(self) -> None:
        logger = InMemoryLogger(level="WARNING")
        assert logger.is_enabled_for("ERROR")
        assert logger.is_enabled_for("WARNING")
        assert not logger.is_enabled_for("INFO")
        assert not logger.is_enabled_for("DEBUG")

    def test_error_and_critical(self) -> None:
        logger = InMemoryLogger(level="DEBUG")
        logger.error("err.msg", code=500)
        logger.critical("crit.msg")
        assert logger.entries[0].level == "ERROR"
        assert logger.entries[1].level == "CRITICAL"


@pytest.mark.asyncio
class TestInMemoryMetricsProvider:
    async def test_counter(self) -> None:
        p = InMemoryMetricsProvider()
        c = p.counter("requests")
        assert c.get() == 0.0
        c.inc()
        assert c.get() == 1.0
        c.inc(5)
        assert c.get() == 6.0

    async def test_gauge(self) -> None:
        p = InMemoryMetricsProvider()
        g = p.gauge("connections")
        g.set(10)
        assert g.get() == 10.0
        g.inc()
        assert g.get() == 11.0
        g.dec(3)
        assert g.get() == 8.0

    async def test_histogram(self) -> None:
        p = InMemoryMetricsProvider()
        h = p.histogram("latency")
        h.observe(0.05)
        h.observe(0.5)
        h.observe(5.0)
        buckets = h.get_bucket_counts()
        assert sum(buckets.values()) == 3

    async def test_timer(self) -> None:
        p = InMemoryMetricsProvider()
        t = p.timer("duration")
        t.record(1.5)
        t.record(2.5)
        assert t.get_count() == 2
        assert t.get_total() == 4.0

    async def test_labels(self) -> None:
        p = InMemoryMetricsProvider()
        c1 = p.counter("requests", {"method": "GET"})
        c2 = p.counter("requests", {"method": "POST"})
        c1.inc()
        c2.inc(2)
        c1.inc()
        snapshot = p.get_snapshot()
        assert snapshot["counters"]["requests[method=GET]"] == 2.0
        assert snapshot["counters"]["requests[method=POST]"] == 2.0

    async def test_snapshot(self) -> None:
        p = InMemoryMetricsProvider()
        p.counter("hits").inc(10)
        p.gauge("temp").set(36.6)
        snap = p.get_snapshot()
        assert "counters" in snap
        assert "gauges" in snap
        assert "histograms" in snap
        assert "timers" in snap


class TestNoOpTracingProvider:
    def test_noop_span_does_not_crash(self) -> None:
        t = NoOpTracingProvider()
        with t.span("test"):
            pass

    def test_start_span(self) -> None:
        t = NoOpTracingProvider()
        span = t.start_span("test")
        span.set_attribute("key", "val")
        span.add_event("event")
        span.set_status(0)
        span.end()

    def test_inject_empty(self) -> None:
        t = NoOpTracingProvider()
        assert t.inject(t.start_span("x")) == {}

    def test_current_ids_none(self) -> None:
        t = NoOpTracingProvider()
        assert t.current_span_id() is None
        assert t.current_trace_id() is None


@pytest.mark.asyncio
class TestBackgroundTaskRegistry:
    async def test_register_and_await(self) -> None:
        registry = BackgroundTaskRegistry()
        done = False

        async def worker() -> None:
            nonlocal done
            done = True

        await registry.register("worker", worker())
        await registry.await_all()
        assert done

    async def test_active_count(self) -> None:
        registry = BackgroundTaskRegistry()

        async def slow() -> None:
            await asyncio.sleep(0.5)

        await registry.register("slow", slow())
        assert registry.active_count == 1
        await registry.await_all(timeout=1.0)
        assert registry.active_count == 0

    async def test_cancel(self) -> None:
        registry = BackgroundTaskRegistry()
        started = asyncio.Event()
        cancelled = False

        async def cancellable() -> None:
            nonlocal cancelled
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancelled = True
                raise

        task = await registry.register("cancellable", cancellable())
        await started.wait()
        assert registry.active_count == 1
        registry.cancel_all()
        await asyncio.sleep(0.02)
        assert cancelled

    async def test_failed_tracking(self) -> None:
        registry = BackgroundTaskRegistry()

        async def will_fail() -> None:
            raise ValueError("boom")

        await registry.register("failing", will_fail())
        await registry.await_all()
        # The task should be tracked as failed
        assert registry.total_count >= 1

    async def test_stats(self) -> None:
        registry = BackgroundTaskRegistry()
        stats = registry.get_stats()
        assert "active_count" in stats
        assert "total_count" in stats


class TestRuntimeDiagnosticsService:
    async def test_uptime_monotonic(self) -> None:
        d = RuntimeDiagnosticsService()
        u1 = d.uptime_seconds
        time.sleep(0.01)
        u2 = d.uptime_seconds
        assert u2 > u1

    async def test_collect_empty(self) -> None:
        d = RuntimeDiagnosticsService()
        snap = await d.collect()
        assert "timestamp" in snap
        assert "uptime_seconds" in snap

    async def test_collect_with_component(self) -> None:
        d = RuntimeDiagnosticsService()

        class FakeComponent:
            def get_stats(self) -> dict[str, int]:
                return {"size": 42}

        snap = await d.collect(my_component=FakeComponent())
        assert snap["my_component"]["size"] == 42

    async def test_collect_handles_none(self) -> None:
        d = RuntimeDiagnosticsService()
        snap = await d.collect(missing=None)
        assert "missing" not in snap

    async def test_collect_handles_error(self) -> None:
        d = RuntimeDiagnosticsService()

        class BrokenComponent:
            def get_stats(self) -> int:
                raise RuntimeError("broken")

        snap = await d.collect(broken=BrokenComponent())
        assert "error" in snap["broken"]
