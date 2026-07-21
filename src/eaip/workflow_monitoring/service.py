"""WorkflowMonitorService — CRUD monitors, evaluate alerts, dashboards."""

from __future__ import annotations

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now
from eaip.workflow_monitoring.exceptions import (
    WorkflowMonitorAlertError,
    WorkflowMonitorConfigError,
    WorkflowMonitorDashboardError,
    WorkflowMonitorNotFoundError,
)
from eaip.workflow_monitoring.models import (
    MonitorThreshold,
    WorkflowMonitorAlert,
    WorkflowMonitorConfig,
    WorkflowMonitorDashboard,
    WorkflowMonitorSnapshot,
    WorkflowMonitorStatus,
)


class WorkflowMonitorService:
    """Central service for managing workflow monitors, alerts, and dashboards."""

    def __init__(self) -> None:
        """Initialize WorkflowMonitorService with empty in-memory stores."""
        self._configs: dict[str, WorkflowMonitorConfig] = {}
        self._alerts: dict[str, WorkflowMonitorAlert] = {}
        self._snapshots: dict[str, WorkflowMonitorSnapshot] = {}
        self._dashboards: dict[str, WorkflowMonitorDashboard] = {}
        self._log = get_logger("eaip.workflow_monitoring.service")

    # -- Config CRUD -----------------------------------------------------------

    async def create_config(self, config: WorkflowMonitorConfig) -> WorkflowMonitorConfig:
        """Create a new workflow monitor configuration."""
        if config.id in self._configs:
            raise WorkflowMonitorConfigError(f"config already exists: {config.id!r}")
        self._configs[config.id] = config
        self._log.info("monitor.config.created", config_id=config.id, workflow=config.workflow_name)
        return config

    async def get_config(self, config_id: str) -> WorkflowMonitorConfig:
        """Get a workflow monitor configuration by ID."""
        config = self._configs.get(config_id)
        if config is None:
            raise WorkflowMonitorNotFoundError(config_id)
        return config

    async def update_config(self, config_id: str, **updates: object) -> WorkflowMonitorConfig:
        """Update a workflow monitor configuration."""
        config = await self.get_config(config_id)
        updated = config.model_copy(update={k: v for k, v in updates.items() if v is not None})
        self._configs[config_id] = updated
        self._log.info("monitor.config.updated", config_id=config_id)
        return updated

    async def delete_config(self, config_id: str) -> None:
        """Delete a workflow monitor configuration."""
        if config_id not in self._configs:
            raise WorkflowMonitorNotFoundError(config_id)
        del self._configs[config_id]
        self._log.info("monitor.config.deleted", config_id=config_id)

    async def list_configs(
        self, status: WorkflowMonitorStatus | None = None
    ) -> list[WorkflowMonitorConfig]:
        """List all monitor configurations, optionally filtered by status."""
        cfgs = list(self._configs.values())
        if status is not None:
            cfgs = [c for c in cfgs if c.status == status]
        return cfgs

    # -- Alert evaluation ------------------------------------------------------

    async def evaluate_alerts(
        self, config_id: str, metrics: dict[str, float]
    ) -> list[WorkflowMonitorAlert]:
        """Evaluate metric values against configured thresholds and trigger alerts."""
        config = await self.get_config(config_id)
        triggered: list[WorkflowMonitorAlert] = []

        for threshold in config.thresholds:
            if not threshold.enabled:
                continue
            current = metrics.get(threshold.metric_name)
            if current is None:
                continue

            breached = self._check_threshold(current, threshold)
            if not breached:
                continue

            alert = WorkflowMonitorAlert(
                id=f"alert_{utc_now().timestamp():.0f}_{threshold.id}",
                config_id=config_id,
                severity=threshold.severity,
                metric_name=threshold.metric_name,
                current_value=current,
                threshold_value=threshold.value,
                message=(
                    f"{threshold.metric_name} "
                    f"{self._operator_label(threshold.operator)} "
                    f"{threshold.value} (current={current})"
                ),
            )
            self._alerts[alert.id] = alert
            triggered.append(alert)

        self._log.info(
            "monitor.alerts.evaluated",
            config_id=config_id,
            triggered=len(triggered),
            metrics=len(metrics),
        )
        return triggered

    async def resolve_alert(self, alert_id: str) -> WorkflowMonitorAlert:
        """Mark an alert as resolved."""
        alert = self._alerts.get(alert_id)
        if alert is None:
            raise WorkflowMonitorAlertError(f"alert not found: {alert_id!r}")
        resolved = alert.model_copy(update={"resolved_at": utc_now()})
        self._alerts[alert_id] = resolved
        self._log.info("monitor.alert.resolved", alert_id=alert_id)
        return resolved

    async def list_alerts(
        self, config_id: str | None = None, unresolved_only: bool = False
    ) -> list[WorkflowMonitorAlert]:
        """List alerts, optionally filtered by config or unresolved status."""
        result = list(self._alerts.values())
        if config_id is not None:
            result = [a for a in result if a.config_id == config_id]
        if unresolved_only:
            result = [a for a in result if a.resolved_at is None]
        return sorted(result, key=lambda a: a.triggered_at, reverse=True)

    # -- Snapshots -------------------------------------------------------------

    async def take_snapshot(
        self, config_id: str, metrics: dict[str, float] | None = None
    ) -> WorkflowMonitorSnapshot:
        """Capture a point-in-time snapshot of a workflow monitor."""
        config = await self.get_config(config_id)
        snapshot = WorkflowMonitorSnapshot(
            id=f"snap_{utc_now().timestamp():.0f}_{config_id}",
            config_id=config_id,
            status=config.status,
            metrics=metrics or {},
            healthy=config.status is WorkflowMonitorStatus.ACTIVE,
        )
        self._snapshots[snapshot.id] = snapshot
        self._log.info("monitor.snapshot.taken", config_id=config_id, snapshot_id=snapshot.id)
        return snapshot

    async def list_snapshots(
        self, config_id: str, limit: int = 20
    ) -> list[WorkflowMonitorSnapshot]:
        """List recent snapshots for a given monitor config."""
        all_snaps = [s for s in self._snapshots.values() if s.config_id == config_id]
        return sorted(all_snaps, key=lambda s: s.timestamp, reverse=True)[:limit]

    # -- Dashboards ------------------------------------------------------------

    async def create_dashboard(
        self, dashboard: WorkflowMonitorDashboard
    ) -> WorkflowMonitorDashboard:
        """Create a new monitoring dashboard."""
        if dashboard.id in self._dashboards:
            raise WorkflowMonitorDashboardError(f"dashboard already exists: {dashboard.id!r}")
        self._dashboards[dashboard.id] = dashboard
        self._log.info("monitor.dashboard.created", dashboard_id=dashboard.id)
        return dashboard

    async def get_dashboard(self, dashboard_id: str) -> WorkflowMonitorDashboard:
        """Get a monitoring dashboard by ID."""
        dashboard = self._dashboards.get(dashboard_id)
        if dashboard is None:
            raise WorkflowMonitorDashboardError(dashboard_id)
        return dashboard

    async def list_dashboards(self) -> list[WorkflowMonitorDashboard]:
        """List all monitoring dashboards."""
        return list(self._dashboards.values())

    async def delete_dashboard(self, dashboard_id: str) -> None:
        """Delete a monitoring dashboard."""
        if dashboard_id not in self._dashboards:
            raise WorkflowMonitorDashboardError(dashboard_id)
        del self._dashboards[dashboard_id]
        self._log.info("monitor.dashboard.deleted", dashboard_id=dashboard_id)

    # -- Internal helpers ------------------------------------------------------

    def _check_threshold(self, current: float, threshold: MonitorThreshold) -> bool:
        """Check whether a metric value breaches a threshold."""
        if threshold.operator == "gt":
            return current > threshold.value
        if threshold.operator == "lt":
            return current < threshold.value
        if threshold.operator == "gte":
            return current >= threshold.value
        if threshold.operator == "lte":
            return current <= threshold.value
        if threshold.operator == "eq":
            return current == threshold.value
        return False

    @staticmethod
    def _operator_label(op: str) -> str:
        """Return a human-readable label for a comparison operator."""
        labels = {"gt": ">", "lt": "<", "gte": ">=", "lte": "<=", "eq": "=="}
        return labels.get(op, op)


__all__ = ["WorkflowMonitorService"]
