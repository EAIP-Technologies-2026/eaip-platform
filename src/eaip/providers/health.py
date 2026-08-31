"""Provider health monitoring — checks provider liveness and updates status."""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING

import httpx

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.logging.context import get_logger
from eaip.providers.models import ProviderInstance, ProviderStatus

if TYPE_CHECKING:
    from eaip.providers.registry import ProviderRegistry


class ProviderHealthCheck(HealthCheck):
    """Health check that probes all registered providers.

    Reports DEGRADED if any provider is unavailable,
    UNHEALTHY if all providers are unavailable.
    """

    name: str = "providers"

    def __init__(self, registry: ProviderRegistry) -> None:
        """Initialize the ProviderHealthCheck.

        Args:
            registry: The provider registry to check.
        """
        self._registry = registry
        self._log = get_logger("eaip.providers.health")

    async def check(self) -> HealthReport:
        """Probe each provider and aggregate their health status."""
        providers = self._registry.all()
        if not providers:
            return HealthReport(
                component="providers",
                status=HealthStatus.HEALTHY,
                message="No providers registered",
                details={"total": 0, "available": 0, "unavailable": 0},
            )

        results = await asyncio.gather(
            *[self._probe(p) for p in providers],
            return_exceptions=True,
        )

        available = sum(1 for r in results if r is True)
        unavailable = sum(1 for r in results if r is False)
        total = len(providers)

        for prov, ok in zip(providers, results, strict=False):
            old_status = prov.status
            new_status = ProviderStatus.AVAILABLE if ok is True else ProviderStatus.UNAVAILABLE
            if old_status != new_status:
                updated = prov.model_copy(
                    update={"status": new_status, "metadata": {**prov.metadata}}
                )
                self._registry.register(updated, replace=True)

        if available == 0 and total > 0:
            return HealthReport(
                component="providers",
                status=HealthStatus.UNHEALTHY,
                message=f"All {total} providers unavailable",
                details={"total": total, "available": 0, "unavailable": total},
            )
        if unavailable > 0:
            return HealthReport(
                component="providers",
                status=HealthStatus.DEGRADED,
                message=f"{available}/{total} providers available",
                details={"total": total, "available": available, "unavailable": unavailable},
            )
        return HealthReport(
            component="providers",
            status=HealthStatus.HEALTHY,
            message=f"All {total} providers available",
            details={"total": total, "available": available, "unavailable": 0},
        )

    async def _probe(self, instance: ProviderInstance) -> bool:
        """Probe a single provider endpoint for liveness."""
        try:
            probe_url = instance.endpoint.rstrip("/")
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(probe_url, headers={"Accept": "application/json"})
                return resp.status_code < 500  # noqa: PLR2004
        except Exception:
            return False


class ProviderHealthMonitor:
    """Periodically runs health checks on all providers.

    Args:
        registry: The provider registry.
        interval_seconds: How often to run health checks.
    """

    def __init__(
        self,
        registry: ProviderRegistry,
        interval_seconds: float = 30.0,
    ) -> None:
        """Initialize the ProviderHealthMonitor.

        Args:
            registry: The provider registry to monitor.
            interval_seconds: How often to run health checks.
        """
        self._registry = registry
        self._interval = interval_seconds
        self._check = ProviderHealthCheck(registry)
        self._task: asyncio.Task[None] | None = None
        self._log = get_logger("eaip.providers.monitor")

    async def start(self) -> None:
        """Start the periodic health monitoring."""
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop the periodic health monitoring."""
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _run(self) -> None:
        while True:
            try:
                await asyncio.sleep(self._interval)
                report = await self._check.check()
                self._log.info(
                    "provider.monitor.report",
                    status=report.status.value,
                    details=report.details,
                )
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self._log.error("provider.monitor.error", error=repr(exc))


__all__ = ["ProviderHealthCheck", "ProviderHealthMonitor"]
