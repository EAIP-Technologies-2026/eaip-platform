"""Unit tests for :mod:`eaip.runtime.health`."""

from __future__ import annotations

import pytest

from eaip.health.checks import HealthCheck, HealthStatus
from eaip.lifecycle import LifecycleManager
from eaip.runtime.health import RuntimeDiagnostics, RuntimeHealthCheck
from eaip.runtime.hooks import ObservabilityHooks
from eaip.runtime.loader import ModuleLoader
from eaip.runtime.module import BaseRuntimeModule


class _HealthyModule(BaseRuntimeModule):
    module_name = "healthy-mod"

    async def on_start(self, host: object, ctx: object) -> None:  # type: ignore[override]
        pass


class _SickModule(BaseRuntimeModule):
    module_name = "sick-mod"

    async def on_start(self, host: object, ctx: object) -> None:  # type: ignore[override]
        pass

    async def check_health(self) -> object:  # type: ignore[override]
        raise RuntimeError("sick!")


class _NoCheckModule:
    """Does not implement check_health."""


def test_satisfies_health_check_protocol() -> None:
    check = RuntimeHealthCheck(name="test", module=_HealthyModule())
    assert isinstance(check, HealthCheck)


def test_name_property() -> None:
    check = RuntimeHealthCheck(name="my-check", module=_HealthyModule())
    assert check.name == "my-check"


@pytest.mark.asyncio
async def test_healthy_module_returns_healthy_report() -> None:
    check = RuntimeHealthCheck(name="healthy", module=_HealthyModule())
    report = await check.check()
    assert report.status is HealthStatus.HEALTHY


@pytest.mark.asyncio
async def test_raising_module_returns_unhealthy() -> None:
    check = RuntimeHealthCheck(name="sick", module=_SickModule())
    report = await check.check()
    assert report.status is HealthStatus.UNHEALTHY
    assert "sick!" in report.message


@pytest.mark.asyncio
async def test_no_check_health_returns_degraded() -> None:
    check = RuntimeHealthCheck(name="no-health", module=_NoCheckModule())  # type: ignore[arg-type]
    report = await check.check()
    assert report.status is HealthStatus.DEGRADED


# ---------------------------------------------------------------------------
# RuntimeDiagnostics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_diagnostics_no_sources() -> None:
    diag = RuntimeDiagnostics()
    report = await diag.diagnose()
    assert report.component == "runtime.diagnostics"
    assert report.status is HealthStatus.HEALTHY
    assert "no diagnostic sources" in report.message


@pytest.mark.asyncio
async def test_diagnostics_with_loader() -> None:
    loader = ModuleLoader()
    diag = RuntimeDiagnostics(loader=loader)
    report = await diag.diagnose()
    assert report.status is HealthStatus.HEALTHY
    children = {c.component for c in report.children}
    assert "loader" in children


@pytest.mark.asyncio
async def test_diagnostics_with_lifecycle() -> None:
    lifecycle = LifecycleManager()
    diag = RuntimeDiagnostics(lifecycle=lifecycle)
    report = await diag.diagnose()
    assert report.status is HealthStatus.HEALTHY
    children = {c.component for c in report.children}
    assert "lifecycle" in children


@pytest.mark.asyncio
async def test_diagnostics_with_hooks() -> None:
    hooks = ObservabilityHooks()
    diag = RuntimeDiagnostics(hooks=hooks)
    report = await diag.diagnose()
    assert report.status is HealthStatus.HEALTHY
    children = {c.component for c in report.children}
    assert "hooks" in children


@pytest.mark.asyncio
async def test_diagnostics_all_sources() -> None:
    loader = ModuleLoader()
    lifecycle = LifecycleManager()
    hooks = ObservabilityHooks()
    diag = RuntimeDiagnostics(loader=loader, lifecycle=lifecycle, hooks=hooks)
    report = await diag.diagnose()
    assert report.status is HealthStatus.HEALTHY
    assert len(report.children) == 3
