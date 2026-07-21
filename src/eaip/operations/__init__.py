"""Platform Operations Console — maintenance, backup, migration, health."""

from __future__ import annotations

from eaip.operations.backup import BackupManager
from eaip.operations.events import (
    BackupCreated,
    BackupRestored,
    BackupVerified,
    ComponentHealthChanged,
    HealthSnapshotCaptured,
    MaintenanceCompleted,
    MaintenanceScheduled,
    MaintenanceStarted,
    MigrationCompleted,
    MigrationCreated,
    MigrationRolledBack,
    MigrationStarted,
)
from eaip.operations.exceptions import (
    BackupNotFoundError,
    BackupRestoreError,
    MaintenanceActiveError,
    MigrationError,
    MigrationValidationError,
    OperationsError,
    SnapshotError,
)
from eaip.operations.health import OperationsHealthCheck
from eaip.operations.health_dashboard import HealthDashboard
from eaip.operations.integration import OperationsRuntimeModule
from eaip.operations.maintenance import MaintenanceManager
from eaip.operations.migration import MigrationService
from eaip.operations.models import (
    BackupComponent,
    BackupManifest,
    MaintenanceWindow,
    MigrationPlan,
    MigrationStep,
    OperationsConfig,
    SystemHealthSnapshot,
)

__all__ = [
    "BackupComponent",
    "BackupCreated",
    "BackupManager",
    "BackupManifest",
    "BackupNotFoundError",
    "BackupRestoreError",
    "BackupRestored",
    "BackupVerified",
    "ComponentHealthChanged",
    "HealthDashboard",
    "HealthSnapshotCaptured",
    "MaintenanceActiveError",
    "MaintenanceCompleted",
    "MaintenanceManager",
    "MaintenanceScheduled",
    "MaintenanceStarted",
    "MaintenanceWindow",
    "MigrationCompleted",
    "MigrationCreated",
    "MigrationError",
    "MigrationPlan",
    "MigrationRolledBack",
    "MigrationService",
    "MigrationStarted",
    "MigrationStep",
    "MigrationValidationError",
    "OperationsConfig",
    "OperationsError",
    "OperationsHealthCheck",
    "OperationsRuntimeModule",
    "SnapshotError",
    "SystemHealthSnapshot",
]
