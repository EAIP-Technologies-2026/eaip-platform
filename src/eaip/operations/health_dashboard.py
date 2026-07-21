"""Health dashboard — snapshots, metrics, and reporting."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from eaip.logging.context import get_logger
from eaip.operations.models import SystemHealthSnapshot


class HealthDashboard:
    """Captures and reports system health snapshots."""

    def __init__(self) -> None:
        """Initialize the health dashboard."""
        self._snapshots: list[SystemHealthSnapshot] = []
        self._log = get_logger("eaip.operations.health_dashboard")

    async def capture_snapshot(self) -> SystemHealthSnapshot:
        """Capture a system health snapshot.

        Returns:
            The captured health snapshot.
        """
        snapshot_id = f"snap-{datetime.now(UTC).timestamp():.0f}"
        snapshot = SystemHealthSnapshot(
            id=snapshot_id,
            timestamp=datetime.now(UTC),
            overall_status="healthy",
            component_statuses={},
            metrics={},
            active_alerts=(),
            version_info={"platform": "1.0.0"},
            uptime_seconds=0.0,
        )
        self._snapshots.append(snapshot)
        self._log.info("health.snapshot.captured", snapshot_id=snapshot_id)
        return snapshot

    async def get_latest_snapshot(self) -> SystemHealthSnapshot | None:
        """Get the most recent health snapshot.

        Returns:
            The latest snapshot, or None if no snapshots exist.
        """
        if not self._snapshots:
            return None
        return self._snapshots[-1]

    async def get_snapshot_history(self, limit: int = 10) -> list[SystemHealthSnapshot]:
        """Get snapshot history up to a limit.

        Args:
            limit: Maximum number of snapshots to return.

        Returns:
            A list of recent snapshots.
        """
        return list(self._snapshots[-limit:])

    async def get_component_health(self, component: str) -> dict[str, Any]:
        """Get health information for a specific component.

        Args:
            component: The component name.

        Returns:
            A dict with component health data.
        """
        latest = await self.get_latest_snapshot()
        if latest is None:
            return {"component": component, "status": "unknown", "available": False}
        status = latest.component_statuses.get(component, "unknown")
        return {"component": component, "status": status, "available": status == "healthy"}

    async def get_system_metrics(self) -> dict[str, float]:
        """Get aggregated system metrics.

        Returns:
            A dict of metric names to values.
        """
        latest = await self.get_latest_snapshot()
        if latest is None:
            return {}
        return dict(latest.metrics)

    async def generate_health_report(self) -> dict[str, Any]:
        """Generate a comprehensive health report.

        Returns:
            A dict with overall health status, component statuses,
            metrics, and total uptime.
        """
        latest = await self.get_latest_snapshot()
        if latest is None:
            return {
                "status": "unknown",
                "components": {},
                "metrics": {},
                "uptime_seconds": 0.0,
                "alerts": [],
                "snapshots_available": 0,
            }
        return {
            "status": latest.overall_status,
            "components": dict(latest.component_statuses),
            "metrics": dict(latest.metrics),
            "uptime_seconds": latest.uptime_seconds,
            "alerts": list(latest.active_alerts),
            "snapshots_available": len(self._snapshots),
            "version_info": dict(latest.version_info),
        }


__all__ = ["HealthDashboard"]
