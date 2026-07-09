"""Tests for ApplicationBuilder."""

from __future__ import annotations

from eaip.app.builder import ApplicationBuilder
from eaip.app.lifecycle import ApplicationLifecycle
from eaip.events.bus import EventBus
from eaip.health.reporter import HealthReporter
from eaip.lifecycle.manager import LifecycleManager
from eaip.metrics.metrics import Meter
from eaip.services.collection import ServiceCollection
from eaip.settings.core_settings import PlatformSettings

# ---------------------------------------------------------------------------
# Stub service types
# ---------------------------------------------------------------------------


class IMyService:
    pass


class MyService(IMyService):
    pass


class TestApplicationBuilder:
    def test_build_returns_lifecycle(self):
        builder = ApplicationBuilder()
        app = builder.build()
        assert isinstance(app, ApplicationLifecycle)

    def test_build_creates_platform(self):
        builder = ApplicationBuilder()
        app = builder.build()
        assert app.platform is not None

    def test_build_creates_runtime_kernel_by_default(self):
        builder = ApplicationBuilder()
        app = builder.build()
        assert app.kernel is not None

    def test_without_runtime_kernel(self):
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()
        assert app.kernel is None

    def test_with_services_registers_in_container(self):
        builder = ApplicationBuilder()
        app = builder.with_services(lambda s: s.add_singleton(IMyService, MyService)).build()
        resolved = app.platform.container.resolve(IMyService)
        assert isinstance(resolved, MyService)

    def test_with_settings(self):
        settings = PlatformSettings()
        builder = ApplicationBuilder()
        app = builder.with_settings(settings).build()
        assert app.platform.settings is settings

    def test_with_services_singleton_lifetime(self):
        builder = ApplicationBuilder()
        app = builder.with_services(lambda s: s.add_singleton(IMyService, MyService)).build()
        c1 = app.platform.container.resolve(IMyService)
        c2 = app.platform.container.resolve(IMyService)
        assert c1 is c2

    def test_default_meter_registered(self):
        builder = ApplicationBuilder()
        app = builder.build()
        meter = app.platform.container.try_resolve(Meter)
        assert meter is not None
        assert isinstance(meter, Meter)

    def test_default_health_reporter_registered(self):
        builder = ApplicationBuilder()
        app = builder.build()
        health = app.platform.container.try_resolve(HealthReporter)
        assert health is not None

    def test_eventbus_registered(self):
        builder = ApplicationBuilder()
        app = builder.build()
        eb = app.platform.container.try_resolve(EventBus)
        assert eb is not None

    def test_lifecycle_manager_registered(self):
        builder = ApplicationBuilder()
        app = builder.build()
        lm = app.platform.container.try_resolve(LifecycleManager)
        assert lm is not None

    def test_platform_settings_registered(self):
        builder = ApplicationBuilder()
        app = builder.build()
        ps = app.platform.container.try_resolve(PlatformSettings)
        assert ps is not None

    async def test_built_app_starts_and_stops(self):
        builder = ApplicationBuilder()
        app = builder.build()
        async with app:
            assert app.is_running
        assert not app.is_running

    def test_descriptors_property(self):
        services = ServiceCollection()
        services.add_singleton(IMyService, MyService)
        assert len(services.descriptors) == 1
        assert services.descriptors[0].service_type is IMyService
