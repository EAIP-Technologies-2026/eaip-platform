"""Health Check Aggregator — dependency graphs, status pages, snapshots, and health history."""

from __future__ import annotations

from eaip.healthagg.aggregator import HealthAggregator
from eaip.healthagg.dependencies import DependencyGraph
from eaip.healthagg.events import (
    ComponentStatusChanged,
    DependencyImpactDetected,
    HealthCheckCompleted,
    HealthDegraded,
    HealthRestored,
    SnapshotCaptured,
    StatusPageCreated,
    StatusPageUpdated,
)
from eaip.healthagg.exceptions import (
    ComponentNotFoundError,
    DependencyNotFoundError,
    HealthAggError,
    SnapshotNotFoundError,
    StatusPageNotFoundError,
)
from eaip.healthagg.health import HealthAggHealthCheck
from eaip.healthagg.integration import HealthAggRuntimeModule
from eaip.healthagg.models import (
    HealthAggregationConfig,
    HealthDependency,
    HealthSnapshot,
    HealthStatusPage,
)
from eaip.healthagg.status_page import StatusPageService

__all__ = [
    "ComponentNotFoundError",
    "ComponentStatusChanged",
    "DependencyGraph",
    "DependencyImpactDetected",
    "DependencyNotFoundError",
    "HealthAggError",
    "HealthAggHealthCheck",
    "HealthAggregationConfig",
    "HealthAggregator",
    "HealthCheckCompleted",
    "HealthDegraded",
    "HealthDependency",
    "HealthRestored",
    "HealthSnapshot",
    "HealthStatusPage",
    "SnapshotCaptured",
    "SnapshotNotFoundError",
    "StatusPageCreated",
    "StatusPageNotFoundError",
    "StatusPageService",
    "StatusPageUpdated",
]
