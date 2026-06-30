"""Tests for :mod:`eaip.health`."""

from __future__ import annotations

import pytest

from eaip.exceptions.domain import DuplicateRegistrationError
from eaip.health import (
    HealthCheck,
    HealthReport,
    HealthReporter,
    HealthStatus,
    callable_check,
)


def _check(name: str, status: HealthStatus) -> HealthCheck:
    async def _impl() -> HealthReport:
        return HealthReport(component=name, status=status)

    return callable_check(name, _impl)


@pytest.mark.asyncio
async def test_empty_reporter_is_healthy() -> None:
    r = HealthReporter(name="p")
    report = await r.report()
    assert report.status is HealthStatus.HEALTHY
    assert report.children == ()


@pytest.mark.asyncio
async def test_rollup_picks_worst() -> None:
    r = HealthReporter()
    r.register(_check("a", HealthStatus.HEALTHY))
    r.register(_check("b", HealthStatus.DEGRADED))
    r.register(_check("c", HealthStatus.UNHEALTHY))
    report = await r.report()
    assert report.status is HealthStatus.UNHEALTHY
    assert len(report.children) == 3


@pytest.mark.asyncio
async def test_failing_check_is_reported_unhealthy() -> None:
    async def boom() -> HealthReport:
        raise RuntimeError("nope")

    r = HealthReporter()
    r.register(callable_check("crashy", boom))
    report = await r.report()
    assert report.status is HealthStatus.UNHEALTHY
    assert report.children[0].component == "crashy"


def test_duplicate_check_rejected() -> None:
    r = HealthReporter()
    r.register(_check("a", HealthStatus.HEALTHY))
    with pytest.raises(DuplicateRegistrationError):
        r.register(_check("a", HealthStatus.HEALTHY))


def test_status_numeric_ordering() -> None:
    assert HealthStatus.HEALTHY.numeric < HealthStatus.DEGRADED.numeric < HealthStatus.UNHEALTHY.numeric
