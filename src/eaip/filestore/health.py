"""File store health check — implements the HealthCheck protocol."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class FileStoreHealthCheck:
    """Health check for the file store subsystem."""

    name: str = "filestore"

    def __init__(self, asset_count: int = 0, provider_available: bool = True) -> None:
        """Initialize with asset count and provider availability."""
        self._asset_count = asset_count
        self._provider_available = provider_available

    @property
    def asset_count(self) -> int:
        """Return the number of assets."""
        return self._asset_count

    @property
    def provider_available(self) -> bool:
        """Return whether the storage provider is available."""
        return self._provider_available

    async def check(self) -> HealthReport:
        """Run the health check and return a report."""
        details = {
            "asset_count": self._asset_count,
            "provider_available": self._provider_available,
        }
        if self._provider_available:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=f"{self._asset_count} asset(s), provider available.",
                details=details,
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message="Storage provider unavailable.",
            details=details,
        )


__all__ = ["FileStoreHealthCheck"]
