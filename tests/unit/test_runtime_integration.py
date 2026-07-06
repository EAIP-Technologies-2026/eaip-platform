"""Integration tests for Runtime Operations (TC-0008).

Verifies interaction between Runtime Context, Host, Loader, Registry,
Lifecycle, Health, and Hooks.
"""

from __future__ import annotations

import pytest

from eaip.application import build_platform
from eaip.health.checks import HealthReport, HealthStatus
from eaip.runtime.context import RuntimeContext
from eaip.runtime.health import RuntimeDiagnostics, RuntimeHealthCheck
from eaip.runtime.hooks import ObservabilityHooks
from eaip.runtime.host import RuntimeHost
from eaip.runtime.module import BaseRuntimeModule
from eaip.shared.time import utc_now


class _IntegrationModule(BaseRuntimeModule):
    module_name = "integration-mod"

    def __init__(self) -> None:
        self.start_ctx: RuntimeContext | None = None
        self.stop_ctx: RuntimeContext | None = None

    async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        self.start_ctx = ctx

    async def on_stop(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        self.stop_ctx = ctx

    async def check_health(self) -> object:
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="integration module is healthy",
            observed_at=utc_now(),
        )


# ---------------------------------------------------------------------------
# Context + Host + Loader + Hooks + Health
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_context_propagates_through_lifecycle() -> None:
    """RuntimeContext created by the host is received by module hooks."""
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    mod = _IntegrationModule()
    host.add_module(mod)

    await host.start()
    assert mod.start_ctx is not None
    assert mod.start_ctx.run_id is not None
    assert mod.start_ctx.environment == "local"

    await host.stop()
    assert mod.stop_ctx is not None


@pytest.mark.asyncio
async def test_hooks_fire_during_host_lifecycle() -> None:
    """ObservabilityHooks fire at every lifecycle stage of the host."""
    fired: list[str] = []
    hooks = ObservabilityHooks()
    hooks.on_host_starting(lambda **_kw: fired.append("host_starting"))
    hooks.on_host_running(lambda **_kw: fired.append("host_running"))
    hooks.on_host_stopping(lambda **_kw: fired.append("host_stopping"))
    hooks.on_host_stopped(lambda **_kw: fired.append("host_stopped"))
    hooks.on_module_starting(lambda **_kw: fired.append("module_starting"))
    hooks.on_module_started(lambda **_kw: fired.append("module_started"))

    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform, hooks=hooks)
    host.add_module(_IntegrationModule())

    async with host:
        assert "host_starting" in fired
        assert "host_running" in fired
        assert "module_starting" in fired
        assert "module_started" in fired

    assert "host_stopping" in fired
    assert "host_stopped" in fired


@pytest.mark.asyncio
async def test_health_check_registered_during_start() -> None:
    """RuntimeHealthCheck is registered on the platform health reporter."""
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    host.add_module(_IntegrationModule())

    assert "integration-mod" not in platform.health.registered()
    await host.start()
    assert "integration-mod" in platform.health.registered()

    report = await platform.health.report()
    assert report.status.name == "HEALTHY"

    await host.stop()


@pytest.mark.asyncio
async def test_runtime_diagnostics_aggregates_all_sources() -> None:
    """RuntimeDiagnostics reports health from loader, lifecycle, and hooks."""
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    host.add_module(_IntegrationModule())
    await host.start()

    diagnostics = RuntimeDiagnostics(
        loader=host._loader,  # type: ignore[arg-type]
        hooks=host._hooks,
    )
    report = await diagnostics.diagnose()
    assert report.status.name == "HEALTHY"

    child_components = {c.component for c in report.children}
    assert "loader" in child_components
    assert "hooks" in child_components

    await host.stop()


@pytest.mark.asyncio
async def test_module_health_reports_via_health_check() -> None:
    """Module.check_health is reachable through the HealthReporter."""
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    mod = _IntegrationModule()
    host.add_module(mod)
    await host.start()

    health_check = RuntimeHealthCheck(name="integration-mod", module=mod)
    report = await health_check.check()
    assert report.component == "integration-mod"
    assert "healthy" in report.message

    await host.stop()


@pytest.mark.asyncio
async def test_full_lifecycle_with_loader_registry() -> None:
    """Loader correctly registers, the registry is queryable, and lifecycle
    transitions are observable."""
    platform = build_platform(configure_logging=False)
    host = RuntimeHost(platform=platform)
    mod = _IntegrationModule()
    host.add_module(mod)

    assert "integration-mod" in host.module_names
    assert host.get_module("integration-mod") is mod
    assert not host.is_running

    await host.start()
    assert host.is_running

    await host.stop()
    assert not host.is_running
