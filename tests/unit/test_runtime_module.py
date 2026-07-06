"""Unit tests for :mod:`eaip.runtime.module`."""

from __future__ import annotations

import pytest

from eaip.health.checks import HealthStatus
from eaip.runtime.module import BaseRuntimeModule, RuntimeModule


class _Minimal(BaseRuntimeModule):
    """Minimal concrete module for testing."""

    module_name = "minimal"

    async def on_start(self, host: object, ctx: object) -> None:  # type: ignore[override]
        pass


class _WithDeps(BaseRuntimeModule):
    module_name = "dependent"
    module_dependencies = ("minimal",)

    async def on_start(self, host: object, ctx: object) -> None:  # type: ignore[override]
        pass


class _AutoName(BaseRuntimeModule):
    # No module_name set — falls back to class qualname.

    async def on_start(self, host: object, ctx: object) -> None:  # type: ignore[override]
        pass


# ---------------------------------------------------------------------------
# Protocol satisfaction
# ---------------------------------------------------------------------------


def test_base_module_satisfies_protocol() -> None:
    m = _Minimal()
    assert isinstance(m, RuntimeModule)


def test_non_module_does_not_satisfy_protocol() -> None:
    class _Nope:
        pass

    assert not isinstance(_Nope(), RuntimeModule)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


def test_name_from_class_attribute() -> None:
    m = _Minimal()
    assert m.name == "minimal"


def test_name_falls_back_to_qualname() -> None:
    m = _AutoName()
    assert "_AutoName" in m.name


def test_dependencies_default_empty() -> None:
    m = _Minimal()
    assert m.dependencies == ()


def test_dependencies_declared() -> None:
    m = _WithDeps()
    assert m.dependencies == ("minimal",)


# ---------------------------------------------------------------------------
# Default implementations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_stop_default_is_noop() -> None:
    m = _Minimal()
    # Should not raise.
    await m.on_stop(object(), object())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_check_health_returns_healthy() -> None:
    m = _Minimal()
    report = await m.check_health()
    assert report.status is HealthStatus.HEALTHY
    assert report.component == "minimal"


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------


def test_repr_contains_name() -> None:
    m = _Minimal()
    assert "minimal" in repr(m)
