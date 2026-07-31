"""Infrastructure health — aggregate health checks for all platform backends.

Provides a single :class:`InfrastructureHealthService` that probes every
configured backend (cache, repository, vector store, LLM, etc.) and returns
a consolidated :class:`HealthReport`.
"""

from __future__ import annotations

from typing import Any

from eaip.health.checks import (
    DependencyClass,
    HealthCheck,
    HealthReport,
    HealthStatus,
    callable_check,
)

_LOCAL_DB_PROVIDERS = {"local", "sqlite", "memory"}


class InfrastructureHealthService(HealthCheck):
    """Aggregate health check for all platform backends.

    Probes each registered backend and produces a consolidated report.
    Backends that are not configured report as ``HEALTHY`` with a
    "not configured" message.
    """

    name: str = "infrastructure"
    criticality: DependencyClass = DependencyClass.CRITICAL
    configured: bool = True

    def __init__(self) -> None:
        self._backends: dict[str, HealthCheck] = {}

    def register(self, name: str, check: HealthCheck) -> None:
        """Register a backend health check.

        Args:
            name: Backend name (e.g. ``"cache"``, ``"database"``).
            check: A :class:`HealthCheck` instance.
        """
        self._backends[name] = check

    def register_connection(
        self,
        name: str,
        is_connected: bool,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Register a simple connectivity check.

        Args:
            name: Backend name.
            is_connected: Whether the backend is connected.
            details: Optional details dict.
        """
        check_name = name
        check_details = details or {}

        async def _check() -> HealthReport:
            if is_connected:
                return HealthReport(
                    component=check_name,
                    status=HealthStatus.HEALTHY,
                    message=f"{check_name} connected",
                    details=check_details,
                )
            return HealthReport(
                component=check_name,
                status=HealthStatus.UNHEALTHY,
                message=f"{check_name} not connected",
                details=check_details,
            )

        self._backends[name] = callable_check(name, _check)

    async def check(self) -> HealthReport:
        """Run all registered backend checks.

        Returns:
            A consolidated :class:`HealthReport`.
        """
        if not self._backends:
            return HealthReport(
                component="infrastructure",
                status=HealthStatus.HEALTHY,
                message="no backends registered",
            )

        children: list[HealthReport] = []
        for name, check in sorted(self._backends.items()):
            try:
                report = await check.check()
                children.append(report)
            except Exception as exc:
                children.append(
                    HealthReport(
                        component=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"check raised: {exc}",
                    )
                )

        worst = max((c.status for c in children), key=lambda s: s.numeric)
        return HealthReport(
            component="infrastructure",
            status=worst,
            message=f"{len(children)} backend(s) checked",
            children=tuple(children),
            criticality=self.criticality,
            configured=self.configured,
        )


class DatabaseHealthCheck(HealthCheck):
    """Health check that reports the active database provider and connection status.

    The provider is classified as a required dependency. When the configured
    provider is an in-process provider (``local``, ``sqlite``, ``memory``) no
    external database is expected, so the check reports ``SKIPPED`` rather
    than ``UNHEALTHY``.
    """

    name: str = "database"
    criticality: DependencyClass = DependencyClass.REQUIRED

    def __init__(self, provider_name: str, db_health_fn: Any) -> None:
        self._provider_name = provider_name
        self._db_health_fn = db_health_fn
        self.configured: bool = provider_name not in _LOCAL_DB_PROVIDERS

    async def check(self) -> HealthReport:
        try:
            result = await self._db_health_fn()
            if self._provider_name in _LOCAL_DB_PROVIDERS:
                return HealthReport(
                    component="database",
                    status=HealthStatus.SKIPPED,
                    message=(
                        f"database provider: {self._provider_name}; no external database configured"
                    ),
                    details={
                        "provider": self._provider_name,
                        "skipped": True,
                        **result,
                    },
                    criticality=self.criticality,
                    configured=self.configured,
                )
            status = (
                HealthStatus.HEALTHY
                if result.get("status") == "healthy"
                else HealthStatus.UNHEALTHY
            )
            return HealthReport(
                component="database",
                status=status,
                message=f"database provider: {self._provider_name}",
                details={
                    "provider": self._provider_name,
                    **result,
                },
                criticality=self.criticality,
                configured=self.configured,
            )
        except Exception as exc:
            return HealthReport(
                component="database",
                status=HealthStatus.UNHEALTHY,
                message=f"database check failed: {exc}",
                details={"provider": self._provider_name},
                criticality=self.criticality,
                configured=self.configured,
            )


__all__ = ["DatabaseHealthCheck", "InfrastructureHealthService"]
