"""Marketplace health check — implements the HealthCheck protocol."""

from __future__ import annotations

from eaip.health.checks import HealthReport, HealthStatus


class MarketplaceHealthCheck:
    """Health check for the marketplace subsystem."""

    name: str = "marketplace"

    def __init__(self, package_count: int = 0, active_installations: int = 0) -> None:
        self._package_count = package_count
        self._active_installations = active_installations

    @property
    def package_count(self) -> int:
        return self._package_count

    @property
    def active_installations(self) -> int:
        return self._active_installations

    async def check(self) -> HealthReport:
        details = {
            "package_count": self._package_count,
            "active_installations": self._active_installations,
        }
        if self._package_count > 0 and self._active_installations > 0:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=(
                    f"{self._package_count} package(s), {self._active_installations} installation(s)."
                ),
                details=details,
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message="Marketplace has no packages or no active installations.",
            details=details,
        )


__all__ = ["MarketplaceHealthCheck"]
