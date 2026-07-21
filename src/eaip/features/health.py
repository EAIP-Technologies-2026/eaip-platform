"""Health check for the feature flag & experimentation engine."""

from __future__ import annotations

from eaip.features.manager import FeatureManager
from eaip.health.checks import HealthReport, HealthStatus


class FeatureHealthCheck:
    """Health check for feature flag services.

    Implements the :class:`eaip.health.checks.HealthCheck` protocol.
    """

    name: str = "features"

    def __init__(self, manager: FeatureManager) -> None:
        self._manager = manager

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        try:
            flags = await self._manager.list_flags()
            details["flag_count"] = len(flags)
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Feature manager unavailable: {exc}",
                details={"error": str(exc)},
            )

        enabled = sum(1 for f in flags if f.enabled)
        details["enabled_flag_count"] = enabled

        status = HealthStatus.HEALTHY
        messages: list[str] = []

        if enabled > 100:
            status = HealthStatus.DEGRADED
            messages.append(f"{enabled} enabled flags exceed recommended threshold")

        return HealthReport(
            component=self.name,
            status=status,
            message="; ".join(messages) if messages else "Feature flag engine healthy",
            details=details,
        )


__all__ = ["FeatureHealthCheck"]
