"""Runtime smoke tests — verify the complete platform boots successfully.

These tests exercise the full assembly: ApplicationBuilder -> ApplicationLifecycle
-> Platform -> RuntimeKernel, confirming that every subsystem initialises
correctly and that the application transitions through all lifecycle phases.
"""

from __future__ import annotations

import asyncio
from contextlib import suppress

from eaip.app import ApplicationBuilder, ApplicationLifecycle, ApplicationRunner
from eaip.events.bus import EventBus
from eaip.events.event import DomainEvent
from eaip.health.checks import HealthStatus
from eaip.health.reporter import HealthReporter
from eaip.lifecycle.phases import LifecyclePhase
from eaip.logging.config import is_configured
from eaip.metrics.metrics import Meter
from eaip.services.collection import ServiceCollection
from eaip.services.descriptors import ServiceLifetime
from eaip.settings.core_settings import PlatformSettings


class SmokeEvent(DomainEvent):
    message: str


class TestRuntimeBootstrap:
    """End-to-end smoke tests for the fully assembled runtime."""

    async def test_platform_boots_with_kernel(self):
        """Verify the platform boots successfully with RuntimeKernel enabled."""
        builder = ApplicationBuilder()
        app = builder.build()

        async with app:
            assert app.phase is LifecyclePhase.RUNNING
            assert app.is_running
            assert app.kernel is not None
            assert app.kernel.phase.value == "running"

        assert app.phase is LifecyclePhase.STOPPED
        assert app.kernel.phase.value == "stopped"

    async def test_logging_configured_after_build(self):
        """Verify structured logging is configured by the builder."""
        builder = ApplicationBuilder()
        builder.without_runtime_kernel().build()
        assert is_configured()

    async def test_platform_boots_without_kernel(self):
        """Verify the platform boots successfully without RuntimeKernel."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        async with app:
            assert app.phase is LifecyclePhase.RUNNING
            assert app.kernel is None

        assert app.phase is LifecyclePhase.STOPPED

    async def test_di_container_initialised(self):
        """Verify the DI container is wired and resolves core services."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        async with app:
            container = app.platform.container
            assert container.has(EventBus)
            assert container.has(HealthReporter)
            assert container.has(PlatformSettings)
            assert container.has(Meter)

    async def test_eventbus_functional(self):
        """Verify the event bus dispatches events through DI."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        received: list[str] = []

        async def handler(event: SmokeEvent) -> None:
            received.append(event.message)

        async with app:
            eb = app.platform.container.resolve(EventBus)
            eb.subscribe(SmokeEvent, handler)
            await eb.publish(SmokeEvent(message="smoke"))
            assert "smoke" in received

    async def test_health_subsystem_initialised(self):
        """Verify the health reporter is accessible and reports HEALTHY."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        async with app:
            health = app.platform.container.resolve(HealthReporter)
            report = await health.report()
            assert report.status is HealthStatus.HEALTHY

    async def test_metrics_subsystem_initialised(self):
        """Verify the Meter creates and tracks metrics correctly."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        async with app:
            meter = app.platform.container.resolve(Meter)
            counter = meter.counter("smoke_requests")
            counter.inc()
            counter.inc(2)
            assert counter.value == 3

            gauge = meter.gauge("smoke_temperature")
            gauge.set(98.6)
            assert gauge.value == 98.6

    async def test_application_runner_start_stop(self):
        """Verify ApplicationRunner starts and stops the application."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()
        runner = ApplicationRunner(app, install_signals=False)

        started = False

        async def on_running(_app: ApplicationLifecycle) -> None:
            nonlocal started
            started = True

        task = asyncio.create_task(runner.run(on_running=on_running))
        await asyncio.sleep(0.1)
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

        assert started
        assert app.phase is LifecyclePhase.STOPPED

    async def test_full_kernel_bootstrap_chain(self):
        """Verify the full Platform + RuntimeKernel bootstrap chain."""
        builder = ApplicationBuilder()

        def configure(s: ServiceCollection) -> None:
            s.add_factory(
                dict,
                lambda _c: {"bootstrapped": True},
                lifetime=ServiceLifetime.SINGLETON,
            )

        app = builder.with_services(configure).build()

        async with app:
            assert app.kernel is not None
            container = app.platform.container
            config = container.resolve(dict)
            assert config["bootstrapped"]

    async def test_idempotent_stop(self):
        """Verify stopping an already-stopped application is safe."""
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()

        async with app:
            pass

        await app.stop()
        assert app.phase is LifecyclePhase.STOPPED

    async def test_custom_settings_apply(self):
        """Verify custom PlatformSettings propagate through bootstrap."""
        settings = PlatformSettings()
        settings.core.app_name = "smoke-test-app"
        builder = ApplicationBuilder()

        app = builder.with_settings(settings).without_runtime_kernel().build()

        async with app:
            assert app.platform.name == "smoke-test-app"
            resolved = app.platform.container.resolve(PlatformSettings)
            assert resolved.core.app_name == "smoke-test-app"
