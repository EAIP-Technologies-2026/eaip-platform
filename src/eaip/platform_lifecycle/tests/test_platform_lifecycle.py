"""Tests for platform lifecycle models, events, exceptions, service, integration, and health."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from eaip.platform_lifecycle.events import (
    PlatformComponentStatusChanged,
    PlatformDeprecationNoticeIssued,
    PlatformHealthSummaryGenerated,
    PlatformLifecycleAuditLogged,
    PlatformLifecyclePhaseChanged,
    PlatformLifecyclePolicyApplied,
    PlatformLifecycleReportGenerated,
    PlatformLifecycleStateTransitioned,
    PlatformMaintenanceWindowEnded,
    PlatformMaintenanceWindowStarted,
    PlatformMigrationCompleted,
    PlatformMigrationFailed,
    PlatformMigrationRolledBack,
    PlatformMigrationStarted,
    PlatformUpgradeCompleted,
    PlatformUpgradeFailed,
    PlatformUpgradeRolledBack,
    PlatformUpgradeStarted,
    PlatformVersionUpdated,
)
from eaip.platform_lifecycle.exceptions import (
    PlatformComponentError,
    PlatformLifecycleConfigError,
    PlatformLifecycleError,
    PlatformLifecycleStateError,
    PlatformLifecycleTransitionError,
    PlatformMaintenanceError,
    PlatformMigrationError,
    PlatformUpgradeError,
)
from eaip.platform_lifecycle.health import PlatformLifecycleHealthCheck
from eaip.platform_lifecycle.integration import PlatformLifecycleRuntimeModule
from eaip.platform_lifecycle.models import (
    ComponentStatus,
    PlatformComponent,
    PlatformDeprecationNotice,
    PlatformHealthSummary,
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
    PlatformVersionInfo,
)
from eaip.platform_lifecycle.service import PlatformLifecycleService
from eaip.shared.time import utc_now

# ── Models ───────────────────────────────────────────────────────────────────


class TestPlatformLifecyclePhase:
    def test_values(self) -> None:
        assert PlatformLifecyclePhase.CREATED.value == "created"
        assert PlatformLifecyclePhase.INITIALIZING.value == "initializing"
        assert PlatformLifecyclePhase.STARTING.value == "starting"
        assert PlatformLifecyclePhase.RUNNING.value == "running"
        assert PlatformLifecyclePhase.STOPPING.value == "stopping"
        assert PlatformLifecyclePhase.STOPPED.value == "stopped"
        assert PlatformLifecyclePhase.FAILED.value == "failed"
        assert PlatformLifecyclePhase.MAINTENANCE.value == "maintenance"
        assert PlatformLifecyclePhase.UPGRADING.value == "upgrading"
        assert PlatformLifecyclePhase.MIGRATING.value == "migrating"
        assert PlatformLifecyclePhase.ARCHIVED.value == "archived"


class TestPlatformUpgradeStatus:
    def test_values(self) -> None:
        assert PlatformUpgradeStatus.PENDING.value == "pending"
        assert PlatformUpgradeStatus.IN_PROGRESS.value == "in_progress"
        assert PlatformUpgradeStatus.COMPLETED.value == "completed"
        assert PlatformUpgradeStatus.FAILED.value == "failed"
        assert PlatformUpgradeStatus.ROLLED_BACK.value == "rolled_back"


class TestPlatformMigrationStatus:
    def test_values(self) -> None:
        assert PlatformMigrationStatus.PENDING.value == "pending"
        assert PlatformMigrationStatus.IN_PROGRESS.value == "in_progress"
        assert PlatformMigrationStatus.COMPLETED.value == "completed"
        assert PlatformMigrationStatus.FAILED.value == "failed"
        assert PlatformMigrationStatus.ROLLED_BACK.value == "rolled_back"


class TestComponentStatus:
    def test_values(self) -> None:
        assert ComponentStatus.HEALTHY.value == "healthy"
        assert ComponentStatus.DEGRADED.value == "degraded"
        assert ComponentStatus.UNHEALTHY.value == "unhealthy"
        assert ComponentStatus.OFFLINE.value == "offline"


class TestPlatformLifecycleState:
    def test_defaults(self) -> None:
        s = PlatformLifecycleState(phase=PlatformLifecyclePhase.CREATED)
        assert s.phase is PlatformLifecyclePhase.CREATED
        assert s.previous_phase is None
        assert s.message == ""

    def test_frozen(self) -> None:
        s = PlatformLifecycleState(phase=PlatformLifecyclePhase.RUNNING)
        with pytest.raises(ValidationError):
            s.phase = PlatformLifecyclePhase.STOPPED


class TestPlatformLifecycleTransition:
    def test_minimal(self) -> None:
        t = PlatformLifecycleTransition(
            id="tr_1",
            from_phase=PlatformLifecyclePhase.CREATED,
            to_phase=PlatformLifecyclePhase.INITIALIZING,
        )
        assert t.reason == ""
        assert t.triggered_by == ""

    def test_frozen(self) -> None:
        t = PlatformLifecycleTransition(
            id="tr_1",
            from_phase=PlatformLifecyclePhase.CREATED,
            to_phase=PlatformLifecyclePhase.INITIALIZING,
        )
        with pytest.raises(ValidationError):
            t.reason = "test"


class TestPlatformUpgrade:
    def test_minimal(self) -> None:
        u = PlatformUpgrade(id="upg_1", from_version="1.0", to_version="2.0")
        assert u.status is PlatformUpgradeStatus.PENDING
        assert u.started_at is None
        assert u.message == ""

    def test_frozen(self) -> None:
        u = PlatformUpgrade(id="upg_1", from_version="1.0", to_version="2.0")
        with pytest.raises(ValidationError):
            u.from_version = "3.0"


class TestPlatformMigration:
    def test_minimal(self) -> None:
        m = PlatformMigration(id="mig_1", from_environment="dev", to_environment="prod")
        assert m.status is PlatformMigrationStatus.PENDING
        assert m.started_at is None

    def test_frozen(self) -> None:
        m = PlatformMigration(id="mig_1", from_environment="dev", to_environment="prod")
        with pytest.raises(ValidationError):
            m.from_environment = "staging"


class TestPlatformHealthSummary:
    def test_defaults(self) -> None:
        h = PlatformHealthSummary()
        assert h.overall_status == "healthy"
        assert h.total_components == 0
        assert h.healthy_count == 0

    def test_frozen(self) -> None:
        h = PlatformHealthSummary()
        with pytest.raises(ValidationError):
            h.overall_status = "degraded"


class TestPlatformComponent:
    def test_minimal(self) -> None:
        c = PlatformComponent(id="comp_1", name="api-gateway")
        assert c.status is ComponentStatus.HEALTHY
        assert c.version == ""

    def test_frozen(self) -> None:
        c = PlatformComponent(id="comp_1", name="api-gateway")
        with pytest.raises(ValidationError):
            c.name = "auth-service"


class TestPlatformLifecycleConfig:
    def test_defaults(self) -> None:
        c = PlatformLifecycleConfig()
        assert c.health_check_interval_seconds == 60
        assert c.auto_rollback_enabled is True
        assert c.audit_retention_days == 365

    def test_frozen(self) -> None:
        c = PlatformLifecycleConfig()
        with pytest.raises(ValidationError):
            c.health_check_interval_seconds = 120


class TestPlatformLifecycleEvent:
    def test_minimal(self) -> None:
        e = PlatformLifecycleEvent(id="evt_1", event_type="test.event")
        assert e.data == {}

    def test_frozen(self) -> None:
        e = PlatformLifecycleEvent(id="evt_1", event_type="test.event")
        with pytest.raises(ValidationError):
            e.event_type = "changed"


class TestPlatformLifecyclePolicy:
    def test_minimal(self) -> None:
        p = PlatformLifecyclePolicy(id="pol_1", name="auto-rollback")
        assert p.enabled is True
        assert p.description == ""

    def test_frozen(self) -> None:
        p = PlatformLifecyclePolicy(id="pol_1", name="auto-rollback")
        with pytest.raises(ValidationError):
            p.enabled = False


class TestPlatformLifecycleSchedule:
    def test_minimal(self) -> None:
        s = PlatformLifecycleSchedule(id="sch_1", operation="upgrade", cron_expression="0 0 * * 0")
        assert s.enabled is True

    def test_frozen(self) -> None:
        s = PlatformLifecycleSchedule(id="sch_1", operation="upgrade", cron_expression="0 0 * * 0")
        with pytest.raises(ValidationError):
            s.cron_expression = "0 0 * * 1"


class TestPlatformLifecycleAuditEntry:
    def test_minimal(self) -> None:
        a = PlatformLifecycleAuditEntry(id="aud_1", action="upgrade")
        assert a.actor == "system"

    def test_frozen(self) -> None:
        a = PlatformLifecycleAuditEntry(id="aud_1", action="upgrade")
        with pytest.raises(ValidationError):
            a.action = "rollback"


class TestPlatformLifecycleReport:
    def test_minimal(self) -> None:
        r = PlatformLifecycleReport(id="rpt_1", report_type="monthly")
        assert r.summary == ""

    def test_frozen(self) -> None:
        r = PlatformLifecycleReport(id="rpt_1", report_type="monthly")
        with pytest.raises(ValidationError):
            r.report_type = "weekly"


class TestPlatformVersionInfo:
    def test_minimal(self) -> None:
        v = PlatformVersionInfo(version="1.0.0")
        assert v.build == ""

    def test_frozen(self) -> None:
        v = PlatformVersionInfo(version="1.0.0")
        with pytest.raises(ValidationError):
            v.version = "2.0.0"


class TestPlatformDeprecationNotice:
    def test_minimal(self) -> None:
        d = PlatformDeprecationNotice(
            id="dep_1",
            component="v1-api",
            message="API v1 is deprecated",
            deprecation_date=utc_now(),
        )
        assert d.removal_date is None

    def test_frozen(self) -> None:
        d = PlatformDeprecationNotice(
            id="dep_1",
            component="v1-api",
            message="API v1 is deprecated",
            deprecation_date=utc_now(),
        )
        with pytest.raises(ValidationError):
            d.component = "v2-api"


class TestPlatformMaintenanceWindow:
    def test_minimal(self) -> None:
        now = utc_now()
        m = PlatformMaintenanceWindow(
            id="mw_1",
            description="Scheduled maintenance",
            scheduled_start=now,
            scheduled_end=now + timedelta(hours=2),
        )
        assert m.status == "scheduled"

    def test_frozen(self) -> None:
        now = utc_now()
        m = PlatformMaintenanceWindow(
            id="mw_1",
            description="Scheduled maintenance",
            scheduled_start=now,
            scheduled_end=now + timedelta(hours=2),
        )
        with pytest.raises(ValidationError):
            m.status = "active"


class TestPlatformLifecycleDashboard:
    def test_defaults(self) -> None:
        d = PlatformLifecycleDashboard(current_phase=PlatformLifecyclePhase.RUNNING)
        assert d.overall_health == "healthy"
        assert d.active_upgrades == 0

    def test_frozen(self) -> None:
        d = PlatformLifecycleDashboard(current_phase=PlatformLifecyclePhase.RUNNING)
        with pytest.raises(ValidationError):
            d.current_phase = PlatformLifecyclePhase.FAILED


# ── Events ────────────────────────────────────────────────────────────────────


class TestPlatformLifecyclePhaseChanged:
    def test_event_type(self) -> None:
        e = PlatformLifecyclePhaseChanged(
            previous_phase=PlatformLifecyclePhase.CREATED,
            new_phase=PlatformLifecyclePhase.RUNNING,
        )
        assert e.event_type == "eaip.platform_lifecycle.phase.changed"


class TestPlatformLifecycleStateTransitioned:
    def test_event_type(self) -> None:
        e = PlatformLifecycleStateTransitioned(
            transition_id="tr_1",
            from_phase=PlatformLifecyclePhase.CREATED,
            to_phase=PlatformLifecyclePhase.INITIALIZING,
        )
        assert e.event_type == "eaip.platform_lifecycle.state.transitioned"


class TestPlatformUpgradeStarted:
    def test_event_type(self) -> None:
        e = PlatformUpgradeStarted(upgrade_id="upg_1", from_version="1.0", to_version="2.0")
        assert e.event_type == "eaip.platform_lifecycle.upgrade.started"


class TestPlatformUpgradeCompleted:
    def test_event_type(self) -> None:
        e = PlatformUpgradeCompleted(upgrade_id="upg_1", from_version="1.0", to_version="2.0")
        assert e.event_type == "eaip.platform_lifecycle.upgrade.completed"


class TestPlatformUpgradeFailed:
    def test_event_type(self) -> None:
        e = PlatformUpgradeFailed(
            upgrade_id="upg_1", from_version="1.0", to_version="2.0", reason="error"
        )
        assert e.event_type == "eaip.platform_lifecycle.upgrade.failed"


class TestPlatformUpgradeRolledBack:
    def test_event_type(self) -> None:
        e = PlatformUpgradeRolledBack(
            upgrade_id="upg_1", from_version="1.0", to_version="2.0", reason="timeout"
        )
        assert e.event_type == "eaip.platform_lifecycle.upgrade.rolled_back"


class TestPlatformMigrationStarted:
    def test_event_type(self) -> None:
        e = PlatformMigrationStarted(
            migration_id="mig_1", from_environment="dev", to_environment="prod"
        )
        assert e.event_type == "eaip.platform_lifecycle.migration.started"


class TestPlatformMigrationCompleted:
    def test_event_type(self) -> None:
        e = PlatformMigrationCompleted(
            migration_id="mig_1", from_environment="dev", to_environment="prod"
        )
        assert e.event_type == "eaip.platform_lifecycle.migration.completed"


class TestPlatformMigrationFailed:
    def test_event_type(self) -> None:
        e = PlatformMigrationFailed(
            migration_id="mig_1",
            from_environment="dev",
            to_environment="prod",
            reason="error",
        )
        assert e.event_type == "eaip.platform_lifecycle.migration.failed"


class TestPlatformMigrationRolledBack:
    def test_event_type(self) -> None:
        e = PlatformMigrationRolledBack(
            migration_id="mig_1",
            from_environment="dev",
            to_environment="prod",
            reason="timeout",
        )
        assert e.event_type == "eaip.platform_lifecycle.migration.rolled_back"


class TestPlatformHealthSummaryGenerated:
    def test_event_type(self) -> None:
        e = PlatformHealthSummaryGenerated(
            total_components=5,
            healthy_count=3,
            degraded_count=1,
            unhealthy_count=1,
            offline_count=0,
        )
        assert e.event_type == "eaip.platform_lifecycle.health_summary.generated"


class TestPlatformComponentStatusChanged:
    def test_event_type(self) -> None:
        e = PlatformComponentStatusChanged(
            component_id="comp_1",
            component_name="api-gateway",
            previous_status=ComponentStatus.HEALTHY,
            new_status=ComponentStatus.DEGRADED,
        )
        assert e.event_type == "eaip.platform_lifecycle.component.status_changed"


class TestPlatformLifecyclePolicyApplied:
    def test_event_type(self) -> None:
        e = PlatformLifecyclePolicyApplied(policy_id="pol_1", policy_name="auto-rollback")
        assert e.event_type == "eaip.platform_lifecycle.policy.applied"


class TestPlatformMaintenanceWindowStarted:
    def test_event_type(self) -> None:
        now = utc_now()
        e = PlatformMaintenanceWindowStarted(
            window_id="mw_1",
            description="Scheduled maintenance",
            scheduled_start=now,
            scheduled_end=now + timedelta(hours=2),
        )
        assert e.event_type == "eaip.platform_lifecycle.maintenance_window.started"


class TestPlatformMaintenanceWindowEnded:
    def test_event_type(self) -> None:
        now = utc_now()
        e = PlatformMaintenanceWindowEnded(
            window_id="mw_1",
            description="Scheduled maintenance",
            actual_start=now,
            actual_end=now + timedelta(hours=1),
        )
        assert e.event_type == "eaip.platform_lifecycle.maintenance_window.ended"


class TestPlatformDeprecationNoticeIssued:
    def test_event_type(self) -> None:
        e = PlatformDeprecationNoticeIssued(
            notice_id="dep_1",
            component="v1-api",
            message="Deprecated",
            deprecation_date=utc_now(),
        )
        assert e.event_type == "eaip.platform_lifecycle.deprecation_notice.issued"


class TestPlatformLifecycleReportGenerated:
    def test_event_type(self) -> None:
        e = PlatformLifecycleReportGenerated(report_id="rpt_1", report_type="monthly")
        assert e.event_type == "eaip.platform_lifecycle.report.generated"


class TestPlatformLifecycleAuditLogged:
    def test_event_type(self) -> None:
        e = PlatformLifecycleAuditLogged(entry_id="aud_1", action="upgrade", actor="admin")
        assert e.event_type == "eaip.platform_lifecycle.audit.logged"


class TestPlatformVersionUpdated:
    def test_event_type(self) -> None:
        e = PlatformVersionUpdated(version="2.0.0")
        assert e.event_type == "eaip.platform_lifecycle.version.updated"


# ── Exceptions ────────────────────────────────────────────────────────────────


class TestExceptions:
    def test_platform_lifecycle_error(self) -> None:
        e = PlatformLifecycleError("test error")
        assert "test error" in str(e)

    def test_platform_lifecycle_state_error(self) -> None:
        e = PlatformLifecycleStateError("invalid state")
        assert isinstance(e, PlatformLifecycleError)

    def test_platform_lifecycle_transition_error(self) -> None:
        e = PlatformLifecycleTransitionError("invalid transition")
        assert isinstance(e, PlatformLifecycleError)

    def test_platform_upgrade_error(self) -> None:
        e = PlatformUpgradeError("upgrade failed")
        assert isinstance(e, PlatformLifecycleError)

    def test_platform_migration_error(self) -> None:
        e = PlatformMigrationError("migration failed")
        assert isinstance(e, PlatformLifecycleError)

    def test_platform_component_error(self) -> None:
        e = PlatformComponentError("component error")
        assert isinstance(e, PlatformLifecycleError)

    def test_platform_maintenance_error(self) -> None:
        e = PlatformMaintenanceError("maintenance error")
        assert isinstance(e, PlatformLifecycleError)

    def test_platform_lifecycle_config_error(self) -> None:
        e = PlatformLifecycleConfigError("config error")
        assert isinstance(e, PlatformLifecycleError)


# ── Service ───────────────────────────────────────────────────────────────────


class TestPlatformLifecycleService:
    @pytest.fixture
    def service(self) -> PlatformLifecycleService:
        return PlatformLifecycleService()

    @pytest.mark.asyncio
    async def test_initial_state(self, service: PlatformLifecycleService) -> None:
        assert service.state.phase is PlatformLifecyclePhase.CREATED

    @pytest.mark.asyncio
    async def test_valid_transition(self, service: PlatformLifecycleService) -> None:
        state = await service.transition_to(PlatformLifecyclePhase.INITIALIZING)
        assert state.phase is PlatformLifecyclePhase.INITIALIZING
        assert state.previous_phase is PlatformLifecyclePhase.CREATED

    @pytest.mark.asyncio
    async def test_invalid_transition(self, service: PlatformLifecycleService) -> None:
        with pytest.raises(PlatformLifecycleTransitionError):
            await service.transition_to(PlatformLifecyclePhase.RUNNING)

    @pytest.mark.asyncio
    async def test_transition_not_found(self, service: PlatformLifecycleService) -> None:
        with pytest.raises(PlatformLifecycleStateError):
            await service.get_transition("nonexistent")

    @pytest.mark.asyncio
    async def test_list_transitions(self, service: PlatformLifecycleService) -> None:
        await service.transition_to(PlatformLifecyclePhase.INITIALIZING)
        transitions = await service.list_transitions()
        assert len(transitions) == 1

    @pytest.mark.asyncio
    async def test_start_upgrade(self, service: PlatformLifecycleService) -> None:
        await service.transition_to(PlatformLifecyclePhase.INITIALIZING)
        await service.transition_to(PlatformLifecyclePhase.STARTING)
        await service.transition_to(PlatformLifecyclePhase.RUNNING)
        upgrade = await service.start_upgrade("1.0", "2.0")
        assert upgrade.status is PlatformUpgradeStatus.IN_PROGRESS
        assert upgrade.from_version == "1.0"

    @pytest.mark.asyncio
    async def test_start_upgrade_not_running(self, service: PlatformLifecycleService) -> None:
        with pytest.raises(PlatformUpgradeError):
            await service.start_upgrade("1.0", "2.0")

    @pytest.mark.asyncio
    async def test_complete_upgrade(self, service: PlatformLifecycleService) -> None:
        await service.transition_to(PlatformLifecyclePhase.INITIALIZING)
        await service.transition_to(PlatformLifecyclePhase.STARTING)
        await service.transition_to(PlatformLifecyclePhase.RUNNING)
        upgrade = await service.start_upgrade("1.0", "2.0")
        completed = await service.complete_upgrade(upgrade.id)
        assert completed.status is PlatformUpgradeStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_fail_upgrade(self, service: PlatformLifecycleService) -> None:
        await service.transition_to(PlatformLifecyclePhase.INITIALIZING)
        await service.transition_to(PlatformLifecyclePhase.STARTING)
        await service.transition_to(PlatformLifecyclePhase.RUNNING)
        upgrade = await service.start_upgrade("1.0", "2.0")
        failed = await service.fail_upgrade(upgrade.id, "connection lost")
        assert failed.status is PlatformUpgradeStatus.FAILED
        assert failed.message == "connection lost"

    @pytest.mark.asyncio
    async def test_rollback_upgrade(self, service: PlatformLifecycleService) -> None:
        await service.transition_to(PlatformLifecyclePhase.INITIALIZING)
        await service.transition_to(PlatformLifecyclePhase.STARTING)
        await service.transition_to(PlatformLifecyclePhase.RUNNING)
        upgrade = await service.start_upgrade("1.0", "2.0")
        rolled_back = await service.rollback_upgrade(upgrade.id, "timeout")
        assert rolled_back.status is PlatformUpgradeStatus.ROLLED_BACK

    @pytest.mark.asyncio
    async def test_upgrade_not_found(self, service: PlatformLifecycleService) -> None:
        with pytest.raises(PlatformUpgradeError):
            await service.complete_upgrade("nonexistent")

    @pytest.mark.asyncio
    async def test_list_upgrades(self, service: PlatformLifecycleService) -> None:
        await service.transition_to(PlatformLifecyclePhase.INITIALIZING)
        await service.transition_to(PlatformLifecyclePhase.STARTING)
        await service.transition_to(PlatformLifecyclePhase.RUNNING)
        await service.start_upgrade("1.0", "2.0")
        upgrades = await service.list_upgrades()
        assert len(upgrades) == 1

    @pytest.mark.asyncio
    async def test_start_migration(self, service: PlatformLifecycleService) -> None:
        await service.transition_to(PlatformLifecyclePhase.INITIALIZING)
        await service.transition_to(PlatformLifecyclePhase.STARTING)
        await service.transition_to(PlatformLifecyclePhase.RUNNING)
        migration = await service.start_migration("dev", "prod")
        assert migration.status is PlatformMigrationStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_start_migration_not_running(self, service: PlatformLifecycleService) -> None:
        with pytest.raises(PlatformMigrationError):
            await service.start_migration("dev", "prod")

    @pytest.mark.asyncio
    async def test_complete_migration(self, service: PlatformLifecycleService) -> None:
        await service.transition_to(PlatformLifecyclePhase.INITIALIZING)
        await service.transition_to(PlatformLifecyclePhase.STARTING)
        await service.transition_to(PlatformLifecyclePhase.RUNNING)
        migration = await service.start_migration("dev", "prod")
        completed = await service.complete_migration(migration.id)
        assert completed.status is PlatformMigrationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_fail_migration(self, service: PlatformLifecycleService) -> None:
        await service.transition_to(PlatformLifecyclePhase.INITIALIZING)
        await service.transition_to(PlatformLifecyclePhase.STARTING)
        await service.transition_to(PlatformLifecyclePhase.RUNNING)
        migration = await service.start_migration("dev", "prod")
        failed = await service.fail_migration(migration.id, "timeout")
        assert failed.status is PlatformMigrationStatus.FAILED

    @pytest.mark.asyncio
    async def test_rollback_migration(self, service: PlatformLifecycleService) -> None:
        await service.transition_to(PlatformLifecyclePhase.INITIALIZING)
        await service.transition_to(PlatformLifecyclePhase.STARTING)
        await service.transition_to(PlatformLifecyclePhase.RUNNING)
        migration = await service.start_migration("dev", "prod")
        rolled_back = await service.rollback_migration(migration.id, "error")
        assert rolled_back.status is PlatformMigrationStatus.ROLLED_BACK

    @pytest.mark.asyncio
    async def test_migration_not_found(self, service: PlatformLifecycleService) -> None:
        with pytest.raises(PlatformMigrationError):
            await service.complete_migration("nonexistent")

    @pytest.mark.asyncio
    async def test_list_migrations(self, service: PlatformLifecycleService) -> None:
        await service.transition_to(PlatformLifecyclePhase.INITIALIZING)
        await service.transition_to(PlatformLifecyclePhase.STARTING)
        await service.transition_to(PlatformLifecyclePhase.RUNNING)
        await service.start_migration("dev", "prod")
        migrations = await service.list_migrations()
        assert len(migrations) == 1

    @pytest.mark.asyncio
    async def test_schedule_maintenance(self, service: PlatformLifecycleService) -> None:
        now = utc_now()
        window = await service.schedule_maintenance(
            "Scheduled maintenance",
            now + timedelta(hours=1),
            now + timedelta(hours=3),
        )
        assert window.status == "scheduled"
        assert window.description == "Scheduled maintenance"

    @pytest.mark.asyncio
    async def test_schedule_maintenance_invalid_dates(
        self, service: PlatformLifecycleService
    ) -> None:
        now = utc_now()
        with pytest.raises(PlatformMaintenanceError):
            await service.schedule_maintenance("bad", now, now - timedelta(hours=1))

    @pytest.mark.asyncio
    async def test_start_maintenance_window(self, service: PlatformLifecycleService) -> None:
        now = utc_now()
        window = await service.schedule_maintenance("test", now, now + timedelta(hours=2))
        started = await service.start_maintenance_window(window.id)
        assert started.status == "active"
        assert started.actual_start is not None

    @pytest.mark.asyncio
    async def test_end_maintenance_window(self, service: PlatformLifecycleService) -> None:
        now = utc_now()
        window = await service.schedule_maintenance("test", now, now + timedelta(hours=2))
        await service.start_maintenance_window(window.id)
        ended = await service.end_maintenance_window(window.id)
        assert ended.status == "completed"

    @pytest.mark.asyncio
    async def test_maintenance_window_not_found(self, service: PlatformLifecycleService) -> None:
        with pytest.raises(PlatformMaintenanceError):
            await service.start_maintenance_window("nonexistent")

    @pytest.mark.asyncio
    async def test_generate_report(self, service: PlatformLifecycleService) -> None:
        report = await service.generate_report("monthly")
        assert report.report_type == "monthly"
        assert report.summary == "Generated monthly report"

    @pytest.mark.asyncio
    async def test_generate_and_get_report(self, service: PlatformLifecycleService) -> None:
        report = await service.generate_report("weekly")
        fetched = await service.get_report(report.id)
        assert fetched.id == report.id

    @pytest.mark.asyncio
    async def test_report_not_found(self, service: PlatformLifecycleService) -> None:
        with pytest.raises(PlatformLifecycleStateError):
            await service.get_report("nonexistent")

    @pytest.mark.asyncio
    async def test_list_reports(self, service: PlatformLifecycleService) -> None:
        await service.generate_report("daily")
        await service.generate_report("weekly")
        reports = await service.list_reports()
        assert len(reports) == 2

    @pytest.mark.asyncio
    async def test_add_and_get_policy(self, service: PlatformLifecycleService) -> None:
        policy = PlatformLifecyclePolicy(id="pol_1", name="auto-rollback")
        await service.add_policy(policy)
        fetched = await service.get_policy("pol_1")
        assert fetched.name == "auto-rollback"

    @pytest.mark.asyncio
    async def test_policy_not_found(self, service: PlatformLifecycleService) -> None:
        with pytest.raises(PlatformLifecycleStateError):
            await service.get_policy("nonexistent")

    @pytest.mark.asyncio
    async def test_add_and_get_schedule(self, service: PlatformLifecycleService) -> None:
        schedule = PlatformLifecycleSchedule(
            id="sch_1", operation="upgrade", cron_expression="0 0 * * 0"
        )
        await service.add_schedule(schedule)
        fetched = await service.get_schedule("sch_1")
        assert fetched.operation == "upgrade"

    @pytest.mark.asyncio
    async def test_schedule_not_found(self, service: PlatformLifecycleService) -> None:
        with pytest.raises(PlatformLifecycleStateError):
            await service.get_schedule("nonexistent")

    @pytest.mark.asyncio
    async def test_log_audit_entry(self, service: PlatformLifecycleService) -> None:
        entry = PlatformLifecycleAuditEntry(id="aud_1", action="upgrade", actor="admin")
        await service.log_audit_entry(entry)
        entries = await service.list_audit_entries()
        assert len(entries) == 1

    @pytest.mark.asyncio
    async def test_record_event(self, service: PlatformLifecycleService) -> None:
        event = PlatformLifecycleEvent(id="evt_1", event_type="test.event")
        await service.record_event(event)
        events = await service.list_events()
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_get_dashboard(self, service: PlatformLifecycleService) -> None:
        dashboard = await service.get_dashboard()
        assert dashboard.current_phase is PlatformLifecyclePhase.CREATED

    @pytest.mark.asyncio
    async def test_get_dashboard_after_transition(self, service: PlatformLifecycleService) -> None:
        await service.transition_to(PlatformLifecyclePhase.INITIALIZING)
        dashboard = await service.get_dashboard()
        assert dashboard.current_phase is PlatformLifecyclePhase.INITIALIZING


# ── Health ────────────────────────────────────────────────────────────────────


class TestPlatformLifecycleHealthCheck:
    @pytest.mark.asyncio
    async def test_check_returns_healthy(self) -> None:
        check = PlatformLifecycleHealthCheck()
        report = await check.check()
        assert report.component == "platform_lifecycle"
        assert report.status.value == "healthy"
        assert "healthy" in report.message


# ── Integration ───────────────────────────────────────────────────────────────


class TestPlatformLifecycleRuntimeModule:
    def test_name(self) -> None:
        module = PlatformLifecycleRuntimeModule()
        assert module.name == "platform_lifecycle"

    def test_service_property(self) -> None:
        module = PlatformLifecycleRuntimeModule()
        assert isinstance(module.service, PlatformLifecycleService)

    def test_health_check_property(self) -> None:
        module = PlatformLifecycleRuntimeModule()
        assert isinstance(module.health_check, PlatformLifecycleHealthCheck)

    @pytest.mark.asyncio
    async def test_start_and_stop(self) -> None:
        module = PlatformLifecycleRuntimeModule()
        kernel = MagicMock()
        await module.start(kernel)
        kernel.platform.health.register.assert_called_once()
        await module.stop(kernel)
