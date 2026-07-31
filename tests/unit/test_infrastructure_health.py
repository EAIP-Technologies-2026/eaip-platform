"""Tests for :mod:`eaip.infrastructure.health` — aggregate and database health checks."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus, callable_check
from eaip.infrastructure.health import DatabaseHealthCheck, InfrastructureHealthService


async def _ok() -> dict[str, object]:
    return {"status": "healthy", "ping": True}


async def _down() -> dict[str, object]:
    return {"status": "unhealthy", "error": "boom"}


def _down_check(name: str = "b") -> HealthCheck:
    async def _impl() -> HealthReport:
        return HealthReport(component=name, status=HealthStatus.UNHEALTHY)

    return callable_check(name, _impl)


class TestDatabaseHealthCheck:
    async def test_healthy(self) -> None:
        check = DatabaseHealthCheck(provider_name="neon", db_health_fn=_ok)
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY
        assert report.details["provider"] == "neon"
        assert report.details["ping"] is True
        assert report.criticality is not None

    async def test_local_provider_is_skipped(self) -> None:
        check = DatabaseHealthCheck(provider_name="local", db_health_fn=_ok)
        report = await check.check()
        assert report.status is HealthStatus.SKIPPED
        assert report.configured is False
        assert report.details["provider"] == "local"
        assert report.details["skipped"] is True

    async def test_unhealthy(self) -> None:
        check = DatabaseHealthCheck(provider_name="neon", db_health_fn=_down)
        report = await check.check()
        assert report.status is HealthStatus.UNHEALTHY
        assert report.details["provider"] == "neon"
        assert report.details["error"] == "boom"

    async def test_not_initialized_is_unhealthy(self) -> None:
        async def _not_init() -> dict[str, object]:
            return {"status": "not_initialized", "provider": "neon"}

        check = DatabaseHealthCheck(provider_name="neon", db_health_fn=_not_init)
        report = await check.check()
        assert report.status is HealthStatus.UNHEALTHY

    async def test_exception_is_unhealthy(self) -> None:
        async def _raise() -> dict[str, object]:
            raise RuntimeError("nope")

        check = DatabaseHealthCheck(provider_name="neon", db_health_fn=_raise)
        report = await check.check()
        assert report.status is HealthStatus.UNHEALTHY
        assert "database check failed" in report.message


class TestInfrastructureHealthService:
    async def test_empty_is_healthy(self) -> None:
        service = InfrastructureHealthService()
        report = await service.check()
        assert report.status is HealthStatus.HEALTHY
        assert report.message == "no backends registered"

    async def test_aggregates_children(self) -> None:
        service = InfrastructureHealthService()
        service.register("a", DatabaseHealthCheck(provider_name="local", db_health_fn=_ok))
        service.register("b", _down_check())
        report = await service.check()
        assert report.status is HealthStatus.UNHEALTHY
        assert len(report.children) == 2

    async def test_register_connection_snapshot_healthy(self) -> None:
        service = InfrastructureHealthService()
        service.register_connection("cache", True, {"mode": "in-memory"})
        report = await service.check()
        assert report.status is HealthStatus.HEALTHY
        assert report.children[0].details["mode"] == "in-memory"

    async def test_register_connection_snapshot_unhealthy(self) -> None:
        service = InfrastructureHealthService()
        service.register_connection("cache", False)
        report = await service.check()
        assert report.status is HealthStatus.UNHEALTHY

    async def test_register_connection_is_snapshot(self) -> None:
        service = InfrastructureHealthService()
        service.register_connection("db", True)
        report = await service.check()
        assert report.status is HealthStatus.HEALTHY


__all__: list[str] = []
