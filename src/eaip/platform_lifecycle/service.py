"""PlatformLifecycleService — state machine, upgrades, migrations, maintenance, reports."""

from __future__ import annotations

from datetime import datetime

from eaip.logging.context import get_logger
from eaip.platform_lifecycle.exceptions import (
    PlatformLifecycleStateError,
    PlatformLifecycleTransitionError,
    PlatformMaintenanceError,
    PlatformMigrationError,
    PlatformUpgradeError,
)
from eaip.platform_lifecycle.models import (
    PlatformLifecycleAuditEntry,
    PlatformLifecycleConfig,
    PlatformLifecycleDashboard,
    PlatformLifecycleEvent,
    PlatformLifecyclePhase,
    PlatformLifecyclePolicy,
    PlatformLifecycleReport,
    PlatformLifecycleSchedule,
    PlatformLifecycleState,
    PlatformLifecycleTransition,
    PlatformMaintenanceWindow,
    PlatformMigration,
    PlatformMigrationStatus,
    PlatformUpgrade,
    PlatformUpgradeStatus,
)
from eaip.shared.time import utc_now

_ALLOWED_TRANSITIONS: dict[PlatformLifecyclePhase, set[PlatformLifecyclePhase]] = {
    PlatformLifecyclePhase.CREATED: {
        PlatformLifecyclePhase.INITIALIZING,
        PlatformLifecyclePhase.FAILED,
    },
    PlatformLifecyclePhase.INITIALIZING: {
        PlatformLifecyclePhase.STARTING,
        PlatformLifecyclePhase.FAILED,
    },
    PlatformLifecyclePhase.STARTING: {
        PlatformLifecyclePhase.RUNNING,
        PlatformLifecyclePhase.FAILED,
    },
    PlatformLifecyclePhase.RUNNING: {
        PlatformLifecyclePhase.STOPPING,
        PlatformLifecyclePhase.MAINTENANCE,
        PlatformLifecyclePhase.UPGRADING,
        PlatformLifecyclePhase.MIGRATING,
        PlatformLifecyclePhase.FAILED,
    },
    PlatformLifecyclePhase.STOPPING: {
        PlatformLifecyclePhase.STOPPED,
        PlatformLifecyclePhase.FAILED,
    },
    PlatformLifecyclePhase.STOPPED: {
        PlatformLifecyclePhase.STARTING,
        PlatformLifecyclePhase.ARCHIVED,
        PlatformLifecyclePhase.FAILED,
    },
    PlatformLifecyclePhase.FAILED: {
        PlatformLifecyclePhase.STARTING,
        PlatformLifecyclePhase.STOPPED,
    },
    PlatformLifecyclePhase.MAINTENANCE: {
        PlatformLifecyclePhase.RUNNING,
        PlatformLifecyclePhase.FAILED,
    },
    PlatformLifecyclePhase.UPGRADING: {
        PlatformLifecyclePhase.RUNNING,
        PlatformLifecyclePhase.FAILED,
    },
    PlatformLifecyclePhase.MIGRATING: {
        PlatformLifecyclePhase.RUNNING,
        PlatformLifecyclePhase.FAILED,
    },
    PlatformLifecyclePhase.ARCHIVED: set(),
}


class PlatformLifecycleService:
    """Central service for platform lifecycle management."""

    def __init__(self, config: PlatformLifecycleConfig | None = None) -> None:
        """Initialize the lifecycle service."""
        self._config = config or PlatformLifecycleConfig()
        self._state = PlatformLifecycleState(phase=PlatformLifecyclePhase.CREATED)
        self._transitions: dict[str, PlatformLifecycleTransition] = {}
        self._upgrades: dict[str, PlatformUpgrade] = {}
        self._migrations: dict[str, PlatformMigration] = {}
        self._maintenance_windows: dict[str, PlatformMaintenanceWindow] = {}
        self._events: list[PlatformLifecycleEvent] = []
        self._policies: dict[str, PlatformLifecyclePolicy] = {}
        self._schedules: dict[str, PlatformLifecycleSchedule] = {}
        self._audit_entries: list[PlatformLifecycleAuditEntry] = []
        self._reports: dict[str, PlatformLifecycleReport] = {}
        self._log = get_logger("eaip.platform_lifecycle.service")

    @property
    def config(self) -> PlatformLifecycleConfig:
        """Return the lifecycle configuration."""
        return self._config

    @property
    def state(self) -> PlatformLifecycleState:
        """Return the current lifecycle state."""
        return self._state

    # ── State Machine ─────────────────────────────────────────────────────────

    async def transition_to(
        self,
        target: PlatformLifecyclePhase,
        reason: str = "",
        triggered_by: str = "",
    ) -> PlatformLifecycleState:
        """Transition the platform to a new lifecycle phase."""
        current = self._state.phase
        allowed = _ALLOWED_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise PlatformLifecycleTransitionError(
                f"Cannot transition from {current.value} to {target.value}",
                context={
                    "current": current.value,
                    "target": target.value,
                },
            )
        transition = PlatformLifecycleTransition(
            id=f"tr_{int(utc_now().timestamp())}",
            from_phase=current,
            to_phase=target,
            reason=reason,
            triggered_by=triggered_by,
        )
        self._transitions[transition.id] = transition
        self._state = PlatformLifecycleState(
            phase=target,
            previous_phase=current,
            message=reason,
        )
        self._log.info(
            "lifecycle.transition",
            from_phase=current.value,
            to_phase=target.value,
            reason=reason,
        )
        return self._state

    async def get_transition(self, transition_id: str) -> PlatformLifecycleTransition:
        """Retrieve a transition by ID."""
        transition = self._transitions.get(transition_id)
        if transition is None:
            raise PlatformLifecycleStateError(f"Transition '{transition_id}' not found")
        return transition

    async def list_transitions(self) -> list[PlatformLifecycleTransition]:
        """List all recorded transitions."""
        return list(self._transitions.values())

    # ── Upgrades ───────────────────────────────────────────────────────────────

    async def start_upgrade(self, from_version: str, to_version: str) -> PlatformUpgrade:
        """Start a platform upgrade."""
        if self._state.phase is not PlatformLifecyclePhase.RUNNING:
            raise PlatformUpgradeError(
                "Cannot start upgrade: platform is not in RUNNING phase",
                context={"phase": self._state.phase.value},
            )
        upgrade = PlatformUpgrade(
            id=f"upg_{int(utc_now().timestamp())}",
            from_version=from_version,
            to_version=to_version,
            status=PlatformUpgradeStatus.IN_PROGRESS,
            started_at=utc_now(),
        )
        self._upgrades[upgrade.id] = upgrade
        self._log.info(
            "lifecycle.upgrade.started",
            upgrade_id=upgrade.id,
            from_version=from_version,
            to_version=to_version,
        )
        return upgrade

    async def complete_upgrade(self, upgrade_id: str) -> PlatformUpgrade:
        """Complete a platform upgrade."""
        upgrade = self._upgrades.get(upgrade_id)
        if upgrade is None:
            raise PlatformUpgradeError(f"Upgrade '{upgrade_id}' not found")
        updated = upgrade.model_copy(
            update={
                "status": PlatformUpgradeStatus.COMPLETED,
                "completed_at": utc_now(),
            },
            deep=True,
        )
        self._upgrades[upgrade_id] = updated
        self._log.info("lifecycle.upgrade.completed", upgrade_id=upgrade_id)
        return updated

    async def fail_upgrade(self, upgrade_id: str, reason: str) -> PlatformUpgrade:
        """Mark a platform upgrade as failed."""
        upgrade = self._upgrades.get(upgrade_id)
        if upgrade is None:
            raise PlatformUpgradeError(f"Upgrade '{upgrade_id}' not found")
        updated = upgrade.model_copy(
            update={
                "status": PlatformUpgradeStatus.FAILED,
                "message": reason,
                "completed_at": utc_now(),
            },
            deep=True,
        )
        self._upgrades[upgrade_id] = updated
        self._log.warning("lifecycle.upgrade.failed", upgrade_id=upgrade_id, reason=reason)
        return updated

    async def rollback_upgrade(self, upgrade_id: str, reason: str) -> PlatformUpgrade:
        """Roll back a platform upgrade."""
        upgrade = self._upgrades.get(upgrade_id)
        if upgrade is None:
            raise PlatformUpgradeError(f"Upgrade '{upgrade_id}' not found")
        updated = upgrade.model_copy(
            update={
                "status": PlatformUpgradeStatus.ROLLED_BACK,
                "message": reason,
                "completed_at": utc_now(),
            },
            deep=True,
        )
        self._upgrades[upgrade_id] = updated
        self._log.info("lifecycle.upgrade.rolled_back", upgrade_id=upgrade_id, reason=reason)
        return updated

    async def get_upgrade(self, upgrade_id: str) -> PlatformUpgrade:
        """Retrieve an upgrade by ID."""
        upgrade = self._upgrades.get(upgrade_id)
        if upgrade is None:
            raise PlatformUpgradeError(f"Upgrade '{upgrade_id}' not found")
        return upgrade

    async def list_upgrades(self) -> list[PlatformUpgrade]:
        """List all upgrades."""
        return list(self._upgrades.values())

    # ── Migrations ─────────────────────────────────────────────────────────────

    async def start_migration(
        self, from_environment: str, to_environment: str
    ) -> PlatformMigration:
        """Start a platform migration."""
        if self._state.phase is not PlatformLifecyclePhase.RUNNING:
            raise PlatformMigrationError(
                "Cannot start migration: platform is not in RUNNING phase",
                context={"phase": self._state.phase.value},
            )
        migration = PlatformMigration(
            id=f"mig_{int(utc_now().timestamp())}",
            from_environment=from_environment,
            to_environment=to_environment,
            status=PlatformMigrationStatus.IN_PROGRESS,
            started_at=utc_now(),
        )
        self._migrations[migration.id] = migration
        self._log.info(
            "lifecycle.migration.started",
            migration_id=migration.id,
            from_env=from_environment,
            to_env=to_environment,
        )
        return migration

    async def complete_migration(self, migration_id: str) -> PlatformMigration:
        """Complete a platform migration."""
        migration = self._migrations.get(migration_id)
        if migration is None:
            raise PlatformMigrationError(f"Migration '{migration_id}' not found")
        updated = migration.model_copy(
            update={
                "status": PlatformMigrationStatus.COMPLETED,
                "completed_at": utc_now(),
            },
            deep=True,
        )
        self._migrations[migration_id] = updated
        self._log.info("lifecycle.migration.completed", migration_id=migration_id)
        return updated

    async def fail_migration(self, migration_id: str, reason: str) -> PlatformMigration:
        """Mark a platform migration as failed."""
        migration = self._migrations.get(migration_id)
        if migration is None:
            raise PlatformMigrationError(f"Migration '{migration_id}' not found")
        updated = migration.model_copy(
            update={
                "status": PlatformMigrationStatus.FAILED,
                "message": reason,
                "completed_at": utc_now(),
            },
            deep=True,
        )
        self._migrations[migration_id] = updated
        self._log.warning("lifecycle.migration.failed", migration_id=migration_id, reason=reason)
        return updated

    async def rollback_migration(self, migration_id: str, reason: str) -> PlatformMigration:
        """Roll back a platform migration."""
        migration = self._migrations.get(migration_id)
        if migration is None:
            raise PlatformMigrationError(f"Migration '{migration_id}' not found")
        updated = migration.model_copy(
            update={
                "status": PlatformMigrationStatus.ROLLED_BACK,
                "message": reason,
                "completed_at": utc_now(),
            },
            deep=True,
        )
        self._migrations[migration_id] = updated
        self._log.info("lifecycle.migration.rolled_back", migration_id=migration_id, reason=reason)
        return updated

    async def get_migration(self, migration_id: str) -> PlatformMigration:
        """Retrieve a migration by ID."""
        migration = self._migrations.get(migration_id)
        if migration is None:
            raise PlatformMigrationError(f"Migration '{migration_id}' not found")
        return migration

    async def list_migrations(self) -> list[PlatformMigration]:
        """List all migrations."""
        return list(self._migrations.values())

    # ── Maintenance Windows ────────────────────────────────────────────────────

    async def schedule_maintenance(
        self,
        description: str,
        scheduled_start: datetime,
        scheduled_end: datetime,
    ) -> PlatformMaintenanceWindow:
        """Schedule a maintenance window."""
        if scheduled_start >= scheduled_end:
            raise PlatformMaintenanceError("Maintenance window start must be before end")
        window = PlatformMaintenanceWindow(
            id=f"mw_{int(utc_now().timestamp())}",
            description=description,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
        )
        self._maintenance_windows[window.id] = window
        self._log.info(
            "lifecycle.maintenance.scheduled",
            window_id=window.id,
            description=description,
        )
        return window

    async def start_maintenance_window(self, window_id: str) -> PlatformMaintenanceWindow:
        """Start a maintenance window."""
        window = self._maintenance_windows.get(window_id)
        if window is None:
            raise PlatformMaintenanceError(f"Maintenance window '{window_id}' not found")
        updated = window.model_copy(
            update={"status": "active", "actual_start": utc_now()},
            deep=True,
        )
        self._maintenance_windows[window_id] = updated
        self._log.info("lifecycle.maintenance.started", window_id=window_id)
        return updated

    async def end_maintenance_window(self, window_id: str) -> PlatformMaintenanceWindow:
        """End a maintenance window."""
        window = self._maintenance_windows.get(window_id)
        if window is None:
            raise PlatformMaintenanceError(f"Maintenance window '{window_id}' not found")
        updated = window.model_copy(
            update={"status": "completed", "actual_end": utc_now()},
            deep=True,
        )
        self._maintenance_windows[window_id] = updated
        self._log.info("lifecycle.maintenance.ended", window_id=window_id)
        return updated

    async def get_maintenance_window(self, window_id: str) -> PlatformMaintenanceWindow:
        """Retrieve a maintenance window by ID."""
        window = self._maintenance_windows.get(window_id)
        if window is None:
            raise PlatformMaintenanceError(f"Maintenance window '{window_id}' not found")
        return window

    async def list_maintenance_windows(self) -> list[PlatformMaintenanceWindow]:
        """List all maintenance windows."""
        return list(self._maintenance_windows.values())

    # ── Reports ────────────────────────────────────────────────────────────────

    async def generate_report(self, report_type: str) -> PlatformLifecycleReport:
        """Generate a lifecycle report."""
        report = PlatformLifecycleReport(
            id=f"rpt_{int(utc_now().timestamp())}",
            report_type=report_type,
            summary=f"Generated {report_type} report",
        )
        self._reports[report.id] = report
        self._log.info("lifecycle.report.generated", report_id=report.id, report_type=report_type)
        return report

    async def get_report(self, report_id: str) -> PlatformLifecycleReport:
        """Retrieve a report by ID."""
        report = self._reports.get(report_id)
        if report is None:
            raise PlatformLifecycleStateError(f"Report '{report_id}' not found")
        return report

    async def list_reports(self) -> list[PlatformLifecycleReport]:
        """List all reports."""
        return list(self._reports.values())

    # ── Policies ───────────────────────────────────────────────────────────────

    async def add_policy(self, policy: PlatformLifecyclePolicy) -> PlatformLifecyclePolicy:
        """Register a lifecycle policy."""
        self._policies[policy.id] = policy
        self._log.info("lifecycle.policy.added", policy_id=policy.id, name=policy.name)
        return policy

    async def get_policy(self, policy_id: str) -> PlatformLifecyclePolicy:
        """Retrieve a policy by ID."""
        policy = self._policies.get(policy_id)
        if policy is None:
            raise PlatformLifecycleStateError(f"Policy '{policy_id}' not found")
        return policy

    async def list_policies(self) -> list[PlatformLifecyclePolicy]:
        """List all policies."""
        return list(self._policies.values())

    # ── Schedules ──────────────────────────────────────────────────────────────

    async def add_schedule(self, schedule: PlatformLifecycleSchedule) -> PlatformLifecycleSchedule:
        """Register a lifecycle schedule."""
        self._schedules[schedule.id] = schedule
        self._log.info(
            "lifecycle.schedule.added",
            schedule_id=schedule.id,
            operation=schedule.operation,
        )
        return schedule

    async def get_schedule(self, schedule_id: str) -> PlatformLifecycleSchedule:
        """Retrieve a schedule by ID."""
        schedule = self._schedules.get(schedule_id)
        if schedule is None:
            raise PlatformLifecycleStateError(f"Schedule '{schedule_id}' not found")
        return schedule

    async def list_schedules(self) -> list[PlatformLifecycleSchedule]:
        """List all schedules."""
        return list(self._schedules.values())

    # ── Audit ──────────────────────────────────────────────────────────────────

    async def log_audit_entry(
        self, entry: PlatformLifecycleAuditEntry
    ) -> PlatformLifecycleAuditEntry:
        """Log an audit entry."""
        self._audit_entries.append(entry)
        self._log.info("lifecycle.audit.logged", entry_id=entry.id, action=entry.action)
        return entry

    async def list_audit_entries(self) -> list[PlatformLifecycleAuditEntry]:
        """List all audit entries."""
        return list(self._audit_entries)

    # ── Events ─────────────────────────────────────────────────────────────────

    async def record_event(self, event: PlatformLifecycleEvent) -> PlatformLifecycleEvent:
        """Record a lifecycle event."""
        self._events.append(event)
        self._log.info("lifecycle.event.recorded", event_id=event.id, event_type=event.event_type)
        return event

    async def list_events(self) -> list[PlatformLifecycleEvent]:
        """List all recorded events."""
        return list(self._events)

    # ── Dashboard ──────────────────────────────────────────────────────────────

    async def get_dashboard(self) -> PlatformLifecycleDashboard:
        """Build and return a dashboard summary."""
        return PlatformLifecycleDashboard(
            current_phase=self._state.phase,
            overall_health=(
                "healthy" if self._state.phase is PlatformLifecyclePhase.RUNNING else "degraded"
            ),
            active_upgrades=sum(
                1 for u in self._upgrades.values() if u.status is PlatformUpgradeStatus.IN_PROGRESS
            ),
            active_migrations=sum(
                1
                for m in self._migrations.values()
                if m.status is PlatformMigrationStatus.IN_PROGRESS
            ),
            active_maintenance_windows=sum(
                1 for w in self._maintenance_windows.values() if w.status == "active"
            ),
            component_count=0,
            unhealthy_components=0,
        )


__all__ = ["PlatformLifecycleService"]
