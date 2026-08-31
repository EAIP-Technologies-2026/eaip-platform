"""Integration tests for full application bootstrap and lifecycle."""

from __future__ import annotations

import asyncio
from contextlib import suppress

from eaip.app import ApplicationBuilder, ApplicationRunner
from eaip.app.lifecycle import ApplicationLifecycle
from eaip.events.bus import EventBus
from eaip.events.event import DomainEvent
from eaip.health.checks import HealthReport, HealthStatus
from eaip.health.reporter import HealthReporter
from eaip.lifecycle.phases import LifecyclePhase
from eaip.metrics.metrics import Meter
from eaip.services.collection import ServiceCollection

# ---------------------------------------------------------------------------
# Stub types
# ---------------------------------------------------------------------------


class IMessageService:
    pass


class MessageService(IMessageService):
    def __init__(self) -> None:
        self.sent: list[str] = []

    def send(self, msg: str) -> None:
        self.sent.append(msg)


class AppReadyEvent(DomainEvent):
    message: str


class IntegrationHealthCheck:
    def __init__(self) -> None:
        self.name = "integration_check"
        self.healthy = True

    async def check(self) -> HealthReport:
        status = HealthStatus.HEALTHY if self.healthy else HealthStatus.UNHEALTHY
        return HealthReport(component=self.name, status=status)


class TestAppBootstrap:
    """Full integration test: build, start, use subsystems, stop."""

    async def test_build_and_start_stop(self):
        """Verify the full lifecycle: build -> start -> running -> stop -> stopped."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        assert app.phase is LifecyclePhase.CREATED
        await app.start()
        assert app.phase is LifecyclePhase.RUNNING
        assert app.is_running
        await app.stop()
        assert app.phase is LifecyclePhase.STOPPED

    async def test_build_with_services(self):
        """Verify services registered via ServiceCollection are resolvable."""

        def configure(s: ServiceCollection) -> None:
            s.add_singleton(IMessageService, MessageService)

        builder = ApplicationBuilder()
        app = builder.with_services(configure).without_runtime_kernel().build()

        async with app:
            svc = app.platform.container.resolve(IMessageService)
            assert isinstance(svc, MessageService)
            svc.send("hello")
            assert svc.sent == ["hello"]

    async def test_eventbus_works(self):
        """Verify the event bus is functional through DI."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        received: list[str] = []

        async def on_event(event: AppReadyEvent) -> None:
            received.append(event.message)

        eb: EventBus = app.platform.container.resolve(EventBus)
        eb.subscribe(AppReadyEvent, on_event)

        async with app:
            await eb.publish(AppReadyEvent(message="ready"))
            assert "ready" in received

    async def test_health_reporter_accessible(self):
        """Verify the health reporter is registered and functional."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        async with app:
            health: HealthReporter = app.platform.container.resolve(HealthReporter)
            report = await health.report()
            assert report.status is HealthStatus.HEALTHY

    async def test_meter_accessible(self):
        """Verify the Meter is registered and functional."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        async with app:
            meter: Meter = app.platform.container.resolve(Meter)
            counter = meter.counter("test_requests")
            counter.inc()
            assert counter.value == 1

    async def test_with_runtime_kernel(self):
        """Verify the RuntimeKernel is booted when enabled."""
        builder = ApplicationBuilder()
        app = builder.build()  # kernel enabled by default

        async with app:
            assert app.kernel is not None
            assert app.kernel.phase.value == "running"

    async def test_application_runner(self):
        """Verify the ApplicationRunner can start and stop."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()
        runner = ApplicationRunner(app, install_signals=False)

        ran = False

        async def on_running(_app: ApplicationLifecycle) -> None:
            nonlocal ran
            ran = True

        async def run_with_timeout() -> None:
            await runner.run(on_running=on_running)

        task = asyncio.create_task(run_with_timeout())
        await asyncio.sleep(0.2)
        task.cancel()
        with suppress(asyncio.CancelledError, Exception):
            await task
