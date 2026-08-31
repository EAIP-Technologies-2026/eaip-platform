"""Health check for the cross-region replicator."""

from __future__ import annotations

from eaip.crossreg.replicator import CrossRegionReplicator
from eaip.health.checks import HealthReport, HealthStatus


class CrossRegHealthCheck:
    name: str = "crossreg"

    def __init__(self, replicator: CrossRegionReplicator) -> None:
        self._replicator = replicator

    async def check(self) -> HealthReport:
        details: dict[str, object] = {}
        try:
            rules = await self._replicator.list_rules()
            details["rule_count"] = len(rules)
            enabled = [r for r in rules if r.enabled]
            details["enabled_rule_count"] = len(enabled)
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Replicator unavailable: {exc}",
                details={"error": str(exc)},
            )
        try:
            statuses = await self._replicator.list_statuses()
            details["status_count"] = len(statuses)
            failed = [s for s in statuses if s.items_failed > 0]
            details["failed_replications"] = len(failed)
        except Exception as exc:
            details["status_error"] = str(exc)

        status = HealthStatus.HEALTHY
        messages: list[str] = []
        failed_val = details.get("failed_replications")
        if isinstance(failed_val, int) and failed_val > 0:
            status = HealthStatus.DEGRADED
            messages.append(f"{details['failed_replications']} replication(s) with failures")

        return HealthReport(
            component=self.name,
            status=status,
            message="; ".join(messages) if messages else "Cross-region replicator healthy",
            details=details,
        )
