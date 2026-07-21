"""Tests for SLA Engine — models, events, exceptions, service, health, integration."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.events.event import DomainEvent
from eaip.sla_engine.events import (
    SlaBreached,
    SlaDefinitionCreated,
    SlaDefinitionDeleted,
    SlaDefinitionUpdated,
    SlaMonitorCompleted,
    SlaMonitorStarted,
    SlaPolicyEvaluated,
    SlaStatusUpdated,
    SlaViolationLogged,
    SlaWarningTriggered,
)
from eaip.sla_engine.exceptions import (
    SlaBreachError,
    SlaConfigError,
    SlaDefinitionNotFoundError,
    SlaError,
    SlaMonitorNotFoundError,
    SlaPolicyError,
    SlaViolationError,
)
from eaip.sla_engine.health import SlaHealthCheck
from eaip.sla_engine.integration import SlaRuntimeModule
from eaip.sla_engine.models import (
    SlaDashboard,
    SlaDefinition,
    SlaMonitor,
    SlaPolicy,
    SlaStatus,
    SlaViolation,
)
from eaip.sla_engine.service import SlaService

# ── Models ────────────────────────────────────────────────────────────────────


class TestSlaStatus:
    def test_values(self) -> None:
        assert SlaStatus.ACTIVE.value == "active"
        assert SlaStatus.WARNING.value == "warning"
        assert SlaStatus.BREACHED.value == "breached"
        assert SlaStatus.PAUSED.value == "paused"
        assert SlaStatus.COMPLETED.value == "completed"

    def test_valid_members(self) -> None:
        assert len(SlaStatus) == 5


class TestSlaPolicy:
    def test_defaults(self) -> None:
        p = SlaPolicy()
        assert p.warning_threshold == 0.0
        assert p.breach_threshold == 0.0
        assert p.evaluation_interval_seconds == 60.0
        assert p.max_violations == 0
        assert p.auto_resolve is True
        assert p.notify_on_warning is True
        assert p.notify_on_breach is True
        assert p.metadata == {}

    def test_custom(self) -> None:
        p = SlaPolicy(warning_threshold=80.0, breach_threshold=95.0, max_violations=3)
        assert p.warning_threshold == 80.0
        assert p.breach_threshold == 95.0
        assert p.max_violations == 3

    def test_frozen(self) -> None:
        p = SlaPolicy()
        with pytest.raises(ValueError):
            p.warning_threshold = 50.0


class TestSlaDefinition:
    def test_required_fields(self) -> None:
        d = SlaDefinition(id="sla_1", name="Uptime 99.9%")
        assert d.id == "sla_1"
        assert d.name == "Uptime 99.9%"
        assert d.description == ""
        assert d.target_metric == ""
        assert d.target_value == 0.0
        assert d.operator == "gte"
        assert d.window_seconds == 300.0
        assert isinstance(d.policy, SlaPolicy)
        assert d.enabled is True
        assert d.version == "1.0.0"

    def test_with_values(self) -> None:
        d = SlaDefinition(
            id="sla_2",
            name="Response Time",
            target_metric="response_time_ms",
            target_value=200.0,
            operator="lte",
            window_seconds=600.0,
            tags=("critical", "api"),
        )
        assert d.target_metric == "response_time_ms"
        assert d.target_value == 200.0
        assert d.operator == "lte"
        assert d.window_seconds == 600.0
        assert d.tags == ("critical", "api")

    def test_frozen(self) -> None:
        d = SlaDefinition(id="sla_1", name="Test")
        with pytest.raises(ValueError):
            d.name = "changed"


class TestSlaViolation:
    def test_defaults(self) -> None:
        v = SlaViolation(id="v1", definition_id="sla_1")
        assert v.definition_name == ""
        assert v.metric == ""
        assert v.actual_value == 0.0
        assert v.threshold == 0.0
        assert v.severity == "warning"
        assert isinstance(v.timestamp, datetime)
        assert v.acknowledged is False
        assert v.resolved is False

    def test_with_values(self) -> None:
        v = SlaViolation(
            id="v1",
            definition_id="sla_1",
            definition_name="Uptime",
            metric="uptime_pct",
            actual_value=95.0,
            threshold=99.9,
            severity="breach",
        )
        assert v.definition_name == "Uptime"
        assert v.actual_value == 95.0
        assert v.threshold == 99.9
        assert v.severity == "breach"

    def test_frozen(self) -> None:
        v = SlaViolation(id="v1", definition_id="sla_1")
        with pytest.raises(ValueError):
            v.severity = "critical"


class TestSlaMonitor:
    def test_defaults(self) -> None:
        m = SlaMonitor(id="m1", definition_id="sla_1")
        assert m.status is SlaStatus.ACTIVE
        assert m.current_value == 0.0
        assert m.last_evaluated is None
        assert m.violation_count == 0
        assert isinstance(m.started_at, datetime)
        assert m.completed_at is None

    def test_with_status(self) -> None:
        m = SlaMonitor(
            id="m1",
            definition_id="sla_1",
            status=SlaStatus.BREACHED,
            current_value=99.0,
            violation_count=2,
        )
        assert m.status is SlaStatus.BREACHED
        assert m.current_value == 99.0
        assert m.violation_count == 2

    def test_frozen(self) -> None:
        m = SlaMonitor(id="m1", definition_id="sla_1")
        with pytest.raises(ValueError):
            m.status = SlaStatus.BREACHED


class TestSlaDashboard:
    def test_defaults(self) -> None:
        d = SlaDashboard()
        assert d.total_definitions == 0
        assert d.active_monitors == 0
        assert d.breached_count == 0
        assert d.warning_count == 0
        assert d.total_violations == 0
        assert d.unresolved_violations == 0
        assert d.avg_response_time_ms == 0.0
        assert d.compliance_pct == 100.0

    def test_with_values(self) -> None:
        d = SlaDashboard(
            total_definitions=5,
            active_monitors=3,
            breached_count=1,
            compliance_pct=95.5,
        )
        assert d.total_definitions == 5
        assert d.active_monitors == 3
        assert d.breached_count == 1
        assert d.compliance_pct == 95.5


# ── Events ────────────────────────────────────────────────────────────────────


class TestSlaEvents:
    def test_sla_definition_created(self) -> None:
        e = SlaDefinitionCreated(definition_id="sla_1", definition_name="Test", target_metric="cpu")
        assert e.event_type == "eaip.sla_engine.definition.created"
        assert isinstance(e, DomainEvent)
        assert e.definition_id == "sla_1"
        assert e.definition_name == "Test"
        assert e.target_metric == "cpu"

    def test_definition_created_defaults(self) -> None:
        e = SlaDefinitionCreated()
        assert e.definition_id == ""
        assert e.definition_name == ""
        assert e.target_metric == ""

    def test_frozen(self) -> None:
        e = SlaDefinitionCreated()
        with pytest.raises(ValueError):
            e.definition_id = "x"

    def test_sla_definition_updated(self) -> None:
        e = SlaDefinitionUpdated(definition_id="sla_1", definition_name="Test")
        assert e.event_type == "eaip.sla_engine.definition.updated"

    def test_sla_definition_deleted(self) -> None:
        e = SlaDefinitionDeleted(definition_id="sla_1")
        assert e.event_type == "eaip.sla_engine.definition.deleted"

    def test_sla_monitor_started(self) -> None:
        e = SlaMonitorStarted(monitor_id="m1", definition_id="sla_1")
        assert e.event_type == "eaip.sla_engine.monitor.started"

    def test_sla_monitor_completed(self) -> None:
        e = SlaMonitorCompleted(monitor_id="m1", definition_id="sla_1", duration_ms=5000.0)
        assert e.event_type == "eaip.sla_engine.monitor.completed"
        assert e.duration_ms == 5000.0

    def test_sla_breached(self) -> None:
        e = SlaBreached(
            definition_id="sla_1",
            definition_name="Uptime",
            monitor_id="m1",
            actual_value=80.0,
            threshold=99.0,
        )
        assert e.event_type == "eaip.sla_engine.breached"
        assert e.actual_value == 80.0
        assert e.threshold == 99.0

    def test_sla_warning_triggered(self) -> None:
        e = SlaWarningTriggered(
            definition_id="sla_1",
            definition_name="Uptime",
            monitor_id="m1",
            actual_value=90.0,
            threshold=95.0,
        )
        assert e.event_type == "eaip.sla_engine.warning"
        assert e.actual_value == 90.0

    def test_sla_violation_logged(self) -> None:
        e = SlaViolationLogged(
            violation_id="v1",
            definition_id="sla_1",
            definition_name="Uptime",
            metric="uptime_pct",
            actual_value=80.0,
            threshold=99.0,
            severity="breach",
        )
        assert e.event_type == "eaip.sla_engine.violation.logged"
        assert e.severity == "breach"

    def test_sla_status_updated(self) -> None:
        e = SlaStatusUpdated(
            monitor_id="m1",
            definition_id="sla_1",
            previous_status="active",
            new_status="breached",
        )
        assert e.event_type == "eaip.sla_engine.status.updated"
        assert e.previous_status == "active"
        assert e.new_status == "breached"

    def test_sla_policy_evaluated(self) -> None:
        e = SlaPolicyEvaluated(
            definition_id="sla_1",
            definition_name="Uptime",
            monitor_id="m1",
            current_value=80.0,
            breach_detected=True,
        )
        assert e.event_type == "eaip.sla_engine.policy.evaluated"
        assert e.breach_detected is True
        assert e.current_value == 80.0
        assert e.details == {}

    def test_sla_event_union(self) -> None:
        assert issubclass(SlaDefinitionCreated, DomainEvent)
        assert issubclass(SlaBreached, DomainEvent)

    def test_sla_event_full_event_type_names(self) -> None:
        assert SlaDefinitionCreated.event_type == "eaip.sla_engine.definition.created"
        assert SlaDefinitionUpdated.event_type == "eaip.sla_engine.definition.updated"
        assert SlaDefinitionDeleted.event_type == "eaip.sla_engine.definition.deleted"
        assert SlaMonitorStarted.event_type == "eaip.sla_engine.monitor.started"
        assert SlaMonitorCompleted.event_type == "eaip.sla_engine.monitor.completed"
        assert SlaBreached.event_type == "eaip.sla_engine.breached"
        assert SlaWarningTriggered.event_type == "eaip.sla_engine.warning"
        assert SlaViolationLogged.event_type == "eaip.sla_engine.violation.logged"
        assert SlaStatusUpdated.event_type == "eaip.sla_engine.status.updated"
        assert SlaPolicyEvaluated.event_type == "eaip.sla_engine.policy.evaluated"


# ── Exceptions ────────────────────────────────────────────────────────────────


class TestSlaExceptions:
    def test_sla_error(self) -> None:
        e = SlaError("something went wrong")
        assert "something went wrong" in str(e)

    def test_definition_not_found(self) -> None:
        e = SlaDefinitionNotFoundError("sla_1")
        assert "sla_1" in str(e)
        assert e.definition_id == "sla_1"

    def test_monitor_not_found(self) -> None:
        e = SlaMonitorNotFoundError("m1")
        assert "m1" in str(e)
        assert e.monitor_id == "m1"

    def test_violation_error(self) -> None:
        e = SlaViolationError("invalid metric")
        assert "invalid metric" in str(e)

    def test_policy_error(self) -> None:
        e = SlaPolicyError("threshold misconfigured")
        assert "threshold misconfigured" in str(e)

    def test_breach_error(self) -> None:
        e = SlaBreachError("sla_1", 95.0, 99.0)
        assert "sla_1" in str(e)
        assert e.actual_value == 95.0
        assert e.threshold == 99.0

    def test_config_error(self) -> None:
        e = SlaConfigError("invalid window")
        assert "invalid window" in str(e)


# ── Service ───────────────────────────────────────────────────────────────────


class TestSlaService:
    @pytest.fixture
    def service(self) -> SlaService:
        return SlaService()

    @pytest.fixture
    def definition(self) -> SlaDefinition:
        return SlaDefinition(
            id="sla_1", name="Uptime 99.9%", target_metric="uptime_pct", target_value=99.9
        )

    async def test_create_and_get_definition(
        self, service: SlaService, definition: SlaDefinition
    ) -> None:
        created = await service.create_definition(definition)
        assert created.id == "sla_1"
        got = await service.get_definition("sla_1")
        assert got.name == "Uptime 99.9%"

    async def test_get_definition_not_found(self, service: SlaService) -> None:
        with pytest.raises(SlaDefinitionNotFoundError):
            await service.get_definition("nonexistent")

    async def test_update_definition(self, service: SlaService, definition: SlaDefinition) -> None:
        await service.create_definition(definition)
        updated = await service.update_definition("sla_1", description="Updated description")
        assert updated.description == "Updated description"

    async def test_delete_definition(self, service: SlaService, definition: SlaDefinition) -> None:
        await service.create_definition(definition)
        await service.delete_definition("sla_1")
        assert await service.list_definitions() == []

    async def test_delete_definition_not_found(self, service: SlaService) -> None:
        with pytest.raises(SlaDefinitionNotFoundError):
            await service.delete_definition("nonexistent")

    async def test_list_definitions(self, service: SlaService, definition: SlaDefinition) -> None:
        assert await service.list_definitions() == []
        await service.create_definition(definition)
        assert len(await service.list_definitions()) == 1

    async def test_start_monitor(self, service: SlaService, definition: SlaDefinition) -> None:
        await service.create_definition(definition)
        monitor = await service.start_monitor("sla_1")
        assert monitor.definition_id == "sla_1"
        assert monitor.status is SlaStatus.ACTIVE

    async def test_start_monitor_no_definition(self, service: SlaService) -> None:
        with pytest.raises(SlaDefinitionNotFoundError):
            await service.start_monitor("nonexistent")

    async def test_stop_monitor(self, service: SlaService, definition: SlaDefinition) -> None:
        await service.create_definition(definition)
        monitor = await service.start_monitor("sla_1")
        stopped = await service.stop_monitor(monitor.id)
        assert stopped.status is SlaStatus.COMPLETED
        assert stopped.completed_at is not None

    async def test_stop_monitor_not_found(self, service: SlaService) -> None:
        with pytest.raises(SlaMonitorNotFoundError):
            await service.stop_monitor("nonexistent")

    async def test_get_monitor(self, service: SlaService, definition: SlaDefinition) -> None:
        await service.create_definition(definition)
        monitor = await service.start_monitor("sla_1")
        got = await service.get_monitor(monitor.id)
        assert got.id == monitor.id

    async def test_get_monitor_not_found(self, service: SlaService) -> None:
        with pytest.raises(SlaMonitorNotFoundError):
            await service.get_monitor("nonexistent")

    async def test_list_monitors(self, service: SlaService, definition: SlaDefinition) -> None:
        await service.create_definition(definition)
        await service.start_monitor("sla_1")
        assert len(await service.list_monitors()) == 1
        assert len(await service.list_monitors(definition_id="sla_1")) == 1
        assert len(await service.list_monitors(definition_id="other")) == 0

    async def test_evaluate_sla_healthy(
        self, service: SlaService, definition: SlaDefinition
    ) -> None:
        await service.create_definition(definition)
        await service.start_monitor("sla_1")
        result = await service.evaluate_sla("sla_1", 99.95)
        assert result.breach_detected is False
        assert result.warning_detected is False
        assert result.violation_ids == ()

    async def test_evaluate_sla_warning(self, service: SlaService) -> None:
        policy = SlaPolicy(warning_threshold=90.0, breach_threshold=99.0)
        d = SlaDefinition(
            id="sla_2", name="Warning Test", target_metric="cpu", target_value=100.0, policy=policy
        )
        await service.create_definition(d)
        await service.start_monitor("sla_2")
        result = await service.evaluate_sla("sla_2", 95.0)
        assert result.warning_detected is True
        assert result.breach_detected is False
        assert len(result.violation_ids) == 1

    async def test_evaluate_sla_breach(self, service: SlaService) -> None:
        policy = SlaPolicy(warning_threshold=50.0, breach_threshold=80.0)
        d = SlaDefinition(
            id="sla_3", name="Breach Test", target_metric="cpu", target_value=100.0, policy=policy
        )
        await service.create_definition(d)
        await service.start_monitor("sla_3")
        result = await service.evaluate_sla("sla_3", 95.0)
        assert result.breach_detected is True
        assert len(result.violation_ids) == 1

    async def test_evaluate_sla_no_monitor(
        self, service: SlaService, definition: SlaDefinition
    ) -> None:
        await service.create_definition(definition)
        with pytest.raises(SlaMonitorNotFoundError):
            await service.evaluate_sla("sla_1", 99.0)

    async def test_get_violations(self, service: SlaService) -> None:
        policy = SlaPolicy(warning_threshold=50.0, breach_threshold=80.0)
        d = SlaDefinition(
            id="sla_v",
            name="Violation Test",
            target_metric="cpu",
            target_value=100.0,
            policy=policy,
        )
        await service.create_definition(d)
        await service.start_monitor("sla_v")
        await service.evaluate_sla("sla_v", 95.0)
        violations = await service.get_violations()
        assert len(violations) == 1
        assert violations[0].definition_id == "sla_v"

    async def test_get_violations_filtered(self, service: SlaService) -> None:
        d1 = SlaDefinition(id="sla_a", name="A", policy=SlaPolicy(breach_threshold=50.0))
        d2 = SlaDefinition(id="sla_b", name="B", policy=SlaPolicy(breach_threshold=50.0))
        await service.create_definition(d1)
        await service.create_definition(d2)
        await service.start_monitor("sla_a")
        await service.start_monitor("sla_b")
        await service.evaluate_sla("sla_a", 95.0)
        await service.evaluate_sla("sla_b", 95.0)
        assert len(await service.get_violations(definition_id="sla_a")) == 1
        assert len(await service.get_violations(definition_id="sla_b")) == 1

    async def test_monitor_status_updated_on_breach(self, service: SlaService) -> None:
        policy = SlaPolicy(breach_threshold=80.0)
        d = SlaDefinition(
            id="sla_m",
            name="Monitor Status",
            target_metric="cpu",
            target_value=100.0,
            policy=policy,
        )
        await service.create_definition(d)
        monitor = await service.start_monitor("sla_m")
        assert monitor.status is SlaStatus.ACTIVE
        await service.evaluate_sla("sla_m", 95.0)
        updated = await service.get_monitor(monitor.id)
        assert updated.status is SlaStatus.BREACHED


# ── Health Check ──────────────────────────────────────────────────────────────


class TestSlaHealthCheck:
    @pytest.fixture
    def service(self) -> SlaService:
        return SlaService()

    async def test_healthy(self, service: SlaService) -> None:
        check = SlaHealthCheck(service=service)
        report = await check.check()
        assert report.status.value == "healthy"
        assert report.component == "SlaEngine"

    async def test_degraded_on_breach(self, service: SlaService) -> None:
        policy = SlaPolicy(breach_threshold=80.0)
        d = SlaDefinition(
            id="sla_h", name="Health", target_metric="cpu", target_value=100.0, policy=policy
        )
        await service.create_definition(d)
        await service.start_monitor("sla_h")
        await service.evaluate_sla("sla_h", 95.0)
        check = SlaHealthCheck(service=service)
        report = await check.check()
        assert report.status.value == "degraded"

    async def test_healthy_name(self) -> None:
        check = SlaHealthCheck()
        assert check.name == "eaip.sla_engine"


# ── Integration ───────────────────────────────────────────────────────────────


class TestSlaRuntimeModule:
    def test_name(self) -> None:
        module = SlaRuntimeModule()
        assert module.name == "sla_engine"

    def test_service_property(self) -> None:
        module = SlaRuntimeModule()
        assert isinstance(module.service, SlaService)
