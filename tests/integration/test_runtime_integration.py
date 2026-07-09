"""Integration tests for the assembled runtime — lifecycle, error recovery, concurrency."""

from __future__ import annotations

import asyncio
from contextlib import suppress

import pytest

from eaip.app import ApplicationBuilder, ApplicationLifecycle, ApplicationRunner
from eaip.events.bus import EventBus
from eaip.events.event import DomainEvent
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.health.reporter import HealthReporter
from eaip.lifecycle.phases import LifecyclePhase
from eaip.metrics.metrics import Meter
from eaip.services.collection import ServiceCollection
from eaip.services.descriptors import ServiceLifetime


class IntegrationEvent(DomainEvent):
    value: str


class CustomHealthCheck:
    def __init__(self, name: str = "custom_check") -> None:
        self.name = name
        self._healthy = True

    async def check(self) -> HealthReport:
        status = HealthStatus.HEALTHY if self._healthy else HealthStatus.UNHEALTHY
        return HealthReport(component=self.name, status=status)

    def set_healthy(self, healthy: bool) -> None:
        self._healthy = healthy


class TestRuntimeIntegration:
    """Integration tests for the fully assembled runtime."""

    async def test_bootstrap_with_kernel_and_services(self):
        """Build with kernel + services, verify everything works."""
        builder = ApplicationBuilder()

        def configure(s: ServiceCollection) -> None:
            s.add_factory(dict, lambda _c: {"count": 0}, lifetime=ServiceLifetime.SINGLETON)

        app = builder.with_services(configure).build()

        async with app:
            container = app.platform.container
            state = container.resolve(dict)
            state["count"] += 1

            meter: Meter = container.resolve(Meter)
            meter.counter("boot_count").inc()
            assert meter.counter("boot_count").value == 1

            health: HealthReporter = container.resolve(HealthReporter)
            report = await health.report()
            assert report.status is HealthStatus.HEALTHY

            assert app.kernel is not None
            assert app.kernel.phase.value == "running"

        assert app.phase is LifecyclePhase.STOPPED

    async def test_custom_health_check_registered(self):
        """Register a custom health check via DI and verify it appears in the report."""
        builder = ApplicationBuilder()

        check = CustomHealthCheck("integration_check")

        def configure(s: ServiceCollection) -> None:
            s.add_instance(HealthCheck, check)

        app = builder.with_services(configure).without_runtime_kernel().build()

        async with app:
            health: HealthReporter = app.platform.container.resolve(HealthReporter)
            report = await health.report()
            assert "integration_check" in [c.component for c in (report.children or ())]
            assert report.status is HealthStatus.HEALTHY

            check.set_healthy(False)
            report = await health.report()
            assert report.status is HealthStatus.UNHEALTHY

    async def test_multiple_events_subscribed(self):
        """Verify multiple subscribers on the same event type all receive it."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        received_1: list[str] = []
        received_2: list[str] = []

        async def handler_1(event: IntegrationEvent) -> None:
            received_1.append(event.value)

        async def handler_2(event: IntegrationEvent) -> None:
            received_2.append(event.value)

        async with app:
            eb: EventBus = app.platform.container.resolve(EventBus)
            eb.subscribe(IntegrationEvent, handler_1)
            eb.subscribe(IntegrationEvent, handler_2)

            await eb.publish(IntegrationEvent(value="hello"))

        assert received_1 == ["hello"]
        assert received_2 == ["hello"]

    async def test_application_runner_with_kernel(self):
        """Verify ApplicationRunner works with RuntimeKernel enabled."""
        builder = ApplicationBuilder()
        app = builder.build()
        runner = ApplicationRunner(app, install_signals=False)

        phase_log: list[str] = []

        async def on_running(_app: ApplicationLifecycle) -> None:
            phase_log.append("running")
            phase_log.append(_app.kernel.phase.value)  # type: ignore[union-attr]

        task = asyncio.create_task(runner.run(on_running=on_running))
        await asyncio.sleep(0.1)
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

        assert "running" in phase_log
        assert phase_log.count("running") == 2
        assert app.phase is LifecyclePhase.STOPPED

    async def test_start_failure_sets_failed_phase(self):
        """Verify that a start failure sets FAILED phase on the app lifecycle."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        original_start = app._platform._lifecycle.start

        async def failing_start() -> None:
            raise RuntimeError("start failure")

        app._platform._lifecycle.start = failing_start
        with pytest.raises(RuntimeError, match="start failure"):
            await app.start()

        assert app.phase is LifecyclePhase.FAILED
        app._platform._lifecycle.start = original_start

    async def test_concurrent_health_checks(self):
        """Verify concurrent health checks do not race."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        async with app:
            health: HealthReporter = app.platform.container.resolve(HealthReporter)
            reports = await asyncio.gather(
                *(health.report() for _ in range(10)),
            )
            for report in reports:
                assert report.status is HealthStatus.HEALTHY

    async def test_service_singleton_is_shared(self):
        """Verify singleton services registered via ServiceCollection are shared."""
        builder = ApplicationBuilder()

        def configure(s: ServiceCollection) -> None:
            s.add_factory(list, lambda _c: [], lifetime=ServiceLifetime.SINGLETON)

        app = builder.with_services(configure).without_runtime_kernel().build()

        async with app:
            container = app.platform.container
            lst_1 = container.resolve(list)
            lst_2 = container.resolve(list)
            assert lst_1 is lst_2
            lst_1.append("item")
            assert lst_2 == ["item"]
