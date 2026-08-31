"""Platform Health — snapshots, metrics, dashboards, and alerting."""

from __future__ import annotations

from eaip.phealth.events import (
    AlertResolved,
    AlertTriggered,
    MetricThresholdBreached,
    SnapshotTaken,
)
from eaip.phealth.exceptions import (
    HealthMetricNotFoundError,
    PlatformHealthError,
)
from eaip.phealth.health import PlatformHealthHealthCheck
from eaip.phealth.integration import PlatformHealthRuntimeModule
from eaip.phealth.models import (
    HealthAlert,
    HealthDashboard,
    HealthMetric,
    HealthSnapshot,
)

__all__ = [
    "AlertResolved",
    "AlertTriggered",
    "HealthAlert",
    "HealthDashboard",
    "HealthMetric",
    "HealthMetricNotFoundError",
    "HealthSnapshot",
    "MetricThresholdBreached",
    "PlatformHealthError",
    "PlatformHealthHealthCheck",
    "PlatformHealthRuntimeModule",
    "SnapshotTaken",
]
