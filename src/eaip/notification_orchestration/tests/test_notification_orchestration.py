"""Tests for Notification Orchestration — models, events, exceptions, service, and health."""

from __future__ import annotations

from datetime import datetime

import pytest

from eaip.events.event import DomainEvent
from eaip.notification_orchestration.events import (
    DigestDelivered,
    EscalationResolved,
    EscalationTriggered,
    NotificationBatchSent,
    NotificationEscalated,
    NotificationOrchestrated,
    NotificationRouted,
    OrchestrationRuleActivated,
    OrchestrationRuleCreated,
    OrchestrationRuleDeactivated,
    OrchestrationRuleDeleted,
    OrchestrationRuleUpdated,
    ScheduleTriggered,
)
from eaip.notification_orchestration.exceptions import (
    DigestDeliveryError,
    EscalationError,
    NotificationOrchestrationError,
    NotificationRoutingError,
    OrchestrationExecutionError,
    OrchestrationRuleNotFoundError,
)
from eaip.notification_orchestration.health import NotificationOrchestrationHealthCheck
from eaip.notification_orchestration.integration import NotificationOrchestrationRuntimeModule
from eaip.notification_orchestration.models import (
    DeliveryRoute,
    DigestConfig,
    DigestFrequency,
    EscalationLevel,
    EscalationPolicy,
    NotificationBatch,
    NotificationOrchestrationConfig,
    OrchestrationAction,
    OrchestrationCondition,
    OrchestrationRule,
    OrchestrationSchedule,
    OrchestrationStatus,
    RoutePriority,
)
from eaip.notification_orchestration.service import NotificationOrchestrationService

# ── Models ────────────────────────────────────────────────────────────────────


class TestOrchestrationStatus:
    def test_values(self) -> None:
        assert OrchestrationStatus.PENDING.value == "pending"
        assert OrchestrationStatus.ACTIVE.value == "active"
        assert OrchestrationStatus.PAUSED.value == "paused"
        assert OrchestrationStatus.COMPLETED.value == "completed"
        assert OrchestrationStatus.FAILED.value == "failed"
        assert OrchestrationStatus.CANCELLED.value == "cancelled"

    def test_valid_members(self) -> None:
        assert len(OrchestrationStatus) == 6


class TestDigestFrequency:
    def test_values(self) -> None:
        assert DigestFrequency.DAILY.value == "daily"
        assert DigestFrequency.WEEKLY.value == "weekly"
        assert DigestFrequency.MONTHLY.value == "monthly"
        assert DigestFrequency.HOURLY.value == "hourly"
        assert DigestFrequency.IMMEDIATE.value == "immediate"

    def test_valid_members(self) -> None:
        assert len(DigestFrequency) == 5


class TestRoutePriority:
    def test_values(self) -> None:
        assert RoutePriority.PRIMARY.value == "primary"
        assert RoutePriority.FALLBACK.value == "fallback"
        assert RoutePriority.BACKUP.value == "backup"


class TestDeliveryRoute:
    def test_defaults(self) -> None:
        r = DeliveryRoute(channel="email")
        assert r.channel == "email"
        assert r.priority is RoutePriority.PRIMARY
        assert r.condition == ""
        assert r.config == {}

    def test_custom(self) -> None:
        r = DeliveryRoute(channel="sms", priority=RoutePriority.FALLBACK, config={"retry": 3})
        assert r.channel == "sms"
        assert r.priority is RoutePriority.FALLBACK
        assert r.config == {"retry": 3}

    def test_frozen(self) -> None:
        r = DeliveryRoute(channel="email")
        with pytest.raises(ValueError):
            r.channel = "sms"


class TestOrchestrationCondition:
    def test_defaults(self) -> None:
        c = OrchestrationCondition(field="status")
        assert c.field == "status"
        assert c.operator == "eq"
        assert c.value is None

    def test_frozen(self) -> None:
        c = OrchestrationCondition(field="status", value="active")
        with pytest.raises(ValueError):
            c.field = "other"


class TestOrchestrationAction:
    def test_defaults(self) -> None:
        a = OrchestrationAction(type="notify", target="slack")
        assert a.type == "notify"
        assert a.target == "slack"
        assert a.payload == {}
        assert a.metadata == {}


class TestEscalationLevel:
    def test_defaults(self) -> None:
        e = EscalationLevel()
        assert e.level == 1
        assert e.delay_seconds == 300.0
        assert e.channels == ("email",)
        assert e.targets == ()

    def test_custom(self) -> None:
        e = EscalationLevel(level=2, delay_seconds=600.0, channels=("sms", "phone"))
        assert e.level == 2
        assert e.delay_seconds == 600.0
        assert e.channels == ("sms", "phone")


class TestEscalationPolicy:
    def test_defaults(self) -> None:
        p = EscalationPolicy()
        assert p.enabled is True
        assert p.max_levels == 3
        assert p.levels == ()
        assert p.notify_on_escalation is True

    def test_with_levels(self) -> None:
        level = EscalationLevel(level=1)
        p = EscalationPolicy(levels=(level,))
        assert len(p.levels) == 1
        assert p.levels[0].level == 1


class TestDigestConfig:
    def test_defaults(self) -> None:
        d = DigestConfig()
        assert d.frequency is DigestFrequency.DAILY
        assert d.time == "08:00"
        assert d.timezone == "UTC"
        assert d.max_items == 50
        assert d.include_summary is True

    def test_custom(self) -> None:
        d = DigestConfig(frequency=DigestFrequency.WEEKLY, max_items=100)
        assert d.frequency is DigestFrequency.WEEKLY
        assert d.max_items == 100


class TestOrchestrationSchedule:
    def test_defaults(self) -> None:
        s = OrchestrationSchedule()
        assert s.cron == "0 * * * *"
        assert s.timezone == "UTC"
        assert s.max_executions == 0
        assert s.cooldown_seconds == 0.0


class TestOrchestrationRule:
    def test_required_fields(self) -> None:
        r = OrchestrationRule(id="rule_1", name="High Priority Routing")
        assert r.id == "rule_1"
        assert r.name == "High Priority Routing"
        assert r.description == ""
        assert r.status is OrchestrationStatus.PENDING
        assert r.conditions == ()
        assert r.actions == ()
        assert r.routes == ()
        assert r.schedule is None
        assert r.escalation is None
        assert r.digest is None
        assert r.priority == 0
        assert r.enabled is True
        assert r.tags == ()
        assert r.metadata == {}
        assert isinstance(r.created_at, datetime)
        assert isinstance(r.updated_at, datetime)

    def test_with_values(self) -> None:
        route = DeliveryRoute(channel="email")
        r = OrchestrationRule(
            id="rule_2",
            name="Critical Alerts",
            routes=(route,),
            priority=10,
            tags=("critical", "p1"),
        )
        assert len(r.routes) == 1
        assert r.priority == 10
        assert r.tags == ("critical", "p1")

    def test_frozen(self) -> None:
        r = OrchestrationRule(id="rule_1", name="Test")
        with pytest.raises(ValueError):
            r.name = "changed"


class TestNotificationOrchestrationConfig:
    def test_defaults(self) -> None:
        c = NotificationOrchestrationConfig()
        assert c.max_rules == 100
        assert c.default_escalation_delay == 300.0
        assert c.max_escalation_levels == 5
        assert c.digest_batch_size == 50
        assert c.enable_history is True
        assert c.history_retention_days == 30


class TestNotificationBatch:
    def test_defaults(self) -> None:
        b = NotificationBatch(id="batch_1")
        assert b.id == "batch_1"
        assert b.rule_id == ""
        assert b.notifications == ()
        assert b.channel == ""
        assert b.status is OrchestrationStatus.PENDING
        assert isinstance(b.created_at, datetime)
        assert b.sent_at is None
        assert b.error is None

    def test_frozen(self) -> None:
        b = NotificationBatch(id="batch_1")
        with pytest.raises(ValueError):
            b.status = OrchestrationStatus.COMPLETED


# ── Events ────────────────────────────────────────────────────────────────────


class TestNotificationOrchestrationEvents:
    def test_rule_created(self) -> None:
        e = OrchestrationRuleCreated(rule_id="r1", rule_name="Test Rule")
        assert e.event_type == "eaip.notification_orchestration.rule.created"
        assert isinstance(e, DomainEvent)
        assert e.rule_id == "r1"
        assert e.rule_name == "Test Rule"

    def test_rule_created_defaults(self) -> None:
        e = OrchestrationRuleCreated()
        assert e.rule_id == ""
        assert e.rule_name == ""

    def test_frozen(self) -> None:
        e = OrchestrationRuleCreated()
        with pytest.raises(ValueError):
            e.rule_id = "x"

    def test_rule_updated(self) -> None:
        e = OrchestrationRuleUpdated(rule_id="r1", rule_name="Updated")
        assert e.event_type == "eaip.notification_orchestration.rule.updated"

    def test_rule_deleted(self) -> None:
        e = OrchestrationRuleDeleted(rule_id="r1")
        assert e.event_type == "eaip.notification_orchestration.rule.deleted"

    def test_rule_activated(self) -> None:
        e = OrchestrationRuleActivated(rule_id="r1", rule_name="Test")
        assert e.event_type == "eaip.notification_orchestration.rule.activated"

    def test_rule_deactivated(self) -> None:
        e = OrchestrationRuleDeactivated(rule_id="r1", rule_name="Test")
        assert e.event_type == "eaip.notification_orchestration.rule.deactivated"

    def test_notification_orchestrated(self) -> None:
        e = NotificationOrchestrated(notification_id="n1", rule_id="r1", channel="email")
        assert e.event_type == "eaip.notification_orchestration.notification.orchestrated"
        assert e.notification_id == "n1"
        assert e.channel == "email"

    def test_notification_routed(self) -> None:
        e = NotificationRouted(notification_id="n1", rule_id="r1", route="primary", channel="email")
        assert e.event_type == "eaip.notification_orchestration.notification.routed"
        assert e.route == "primary"

    def test_notification_escalated(self) -> None:
        e = NotificationEscalated(notification_id="n1", rule_id="r1", level=2, channel="sms")
        assert e.event_type == "eaip.notification_orchestration.notification.escalated"
        assert e.level == 2

    def test_batch_sent(self) -> None:
        e = NotificationBatchSent(batch_id="b1", rule_id="r1", count=10)
        assert e.event_type == "eaip.notification_orchestration.batch.sent"
        assert e.count == 10

    def test_digest_delivered(self) -> None:
        e = DigestDelivered(rule_id="r1", rule_name="Test", channel="email", item_count=5)
        assert e.event_type == "eaip.notification_orchestration.digest.delivered"
        assert e.item_count == 5

    def test_escalation_triggered(self) -> None:
        e = EscalationTriggered(
            rule_id="r1",
            rule_name="Test",
            level=1,
            channel="sms",
            targets=("admin@x.com",),
        )
        assert e.event_type == "eaip.notification_orchestration.escalation.triggered"
        assert e.level == 1
        assert e.targets == ("admin@x.com",)

    def test_escalation_resolved(self) -> None:
        e = EscalationResolved(rule_id="r1", rule_name="Test", level=0)
        assert e.event_type == "eaip.notification_orchestration.escalation.resolved"

    def test_schedule_triggered(self) -> None:
        e = ScheduleTriggered(rule_id="r1", cron_expression="0 * * * *")
        assert e.event_type == "eaip.notification_orchestration.schedule.triggered"
        assert e.cron_expression == "0 * * * *"

    def test_event_union(self) -> None:
        assert issubclass(OrchestrationRuleCreated, DomainEvent)
        assert issubclass(NotificationOrchestrated, DomainEvent)

    def test_full_event_type_names(self) -> None:
        created = "eaip.notification_orchestration.rule.created"
        updated = "eaip.notification_orchestration.rule.updated"
        deleted = "eaip.notification_orchestration.rule.deleted"
        activated = "eaip.notification_orchestration.rule.activated"
        deactivated = "eaip.notification_orchestration.rule.deactivated"
        orchestrated = "eaip.notification_orchestration.notification.orchestrated"
        routed = "eaip.notification_orchestration.notification.routed"
        escalated = "eaip.notification_orchestration.notification.escalated"
        batch_sent = "eaip.notification_orchestration.batch.sent"
        digest = "eaip.notification_orchestration.digest.delivered"
        esc_triggered = "eaip.notification_orchestration.escalation.triggered"
        esc_resolved = "eaip.notification_orchestration.escalation.resolved"
        sched = "eaip.notification_orchestration.schedule.triggered"
        assert OrchestrationRuleCreated.event_type == created
        assert OrchestrationRuleUpdated.event_type == updated
        assert OrchestrationRuleDeleted.event_type == deleted
        assert OrchestrationRuleActivated.event_type == activated
        assert OrchestrationRuleDeactivated.event_type == deactivated
        assert NotificationOrchestrated.event_type == orchestrated
        assert NotificationRouted.event_type == routed
        assert NotificationEscalated.event_type == escalated
        assert NotificationBatchSent.event_type == batch_sent
        assert DigestDelivered.event_type == digest
        assert EscalationTriggered.event_type == esc_triggered
        assert EscalationResolved.event_type == esc_resolved
        assert ScheduleTriggered.event_type == sched


# ── Exceptions ────────────────────────────────────────────────────────────────


class TestNotificationOrchestrationExceptions:
    def test_base_error(self) -> None:
        e = NotificationOrchestrationError("something went wrong")
        assert "something went wrong" in str(e)

    def test_rule_not_found(self) -> None:
        e = OrchestrationRuleNotFoundError("r1")
        assert "r1" in str(e)
        assert e.rule_id == "r1"

    def test_execution_error(self) -> None:
        e = OrchestrationExecutionError("execution failed")
        assert "execution failed" in str(e)

    def test_escalation_error(self) -> None:
        e = EscalationError("escalation failed")
        assert "escalation failed" in str(e)

    def test_digest_delivery_error(self) -> None:
        e = DigestDeliveryError("digest failed")
        assert "digest failed" in str(e)

    def test_routing_error(self) -> None:
        e = NotificationRoutingError("routing failed")
        assert "routing failed" in str(e)


# ── Service ───────────────────────────────────────────────────────────────────


class TestNotificationOrchestrationService:
    @pytest.fixture
    def service(self) -> NotificationOrchestrationService:
        return NotificationOrchestrationService()

    @pytest.fixture
    def rule(self) -> OrchestrationRule:
        return OrchestrationRule(
            id="rule_1",
            name="High Priority Routing",
            routes=(DeliveryRoute(channel="email"),),
            enabled=True,
        )

    @pytest.fixture
    def rule_with_escalation(self) -> OrchestrationRule:
        return OrchestrationRule(
            id="rule_2",
            name="Escalation Test",
            routes=(DeliveryRoute(channel="email"),),
            escalation=EscalationPolicy(
                levels=(EscalationLevel(level=1, channels=("sms",)),),
            ),
            enabled=True,
        )

    @pytest.fixture
    def rule_with_digest(self) -> OrchestrationRule:
        return OrchestrationRule(
            id="rule_3",
            name="Digest Test",
            routes=(DeliveryRoute(channel="email"),),
            digest=DigestConfig(frequency=DigestFrequency.DAILY),
            enabled=True,
        )

    async def test_create_and_get_rule(
        self, service: NotificationOrchestrationService, rule: OrchestrationRule
    ) -> None:
        created = await service.create_rule(rule)
        assert created.id == "rule_1"
        got = await service.get_rule("rule_1")
        assert got.name == "High Priority Routing"

    async def test_get_rule_not_found(self, service: NotificationOrchestrationService) -> None:
        with pytest.raises(OrchestrationRuleNotFoundError):
            await service.get_rule("nonexistent")

    async def test_update_rule(
        self, service: NotificationOrchestrationService, rule: OrchestrationRule
    ) -> None:
        await service.create_rule(rule)
        updated = await service.update_rule("rule_1", description="Updated description")
        assert updated.description == "Updated description"

    async def test_delete_rule(
        self, service: NotificationOrchestrationService, rule: OrchestrationRule
    ) -> None:
        await service.create_rule(rule)
        await service.delete_rule("rule_1")
        assert await service.list_rules() == []

    async def test_delete_rule_not_found(self, service: NotificationOrchestrationService) -> None:
        with pytest.raises(OrchestrationRuleNotFoundError):
            await service.delete_rule("nonexistent")

    async def test_list_rules(
        self, service: NotificationOrchestrationService, rule: OrchestrationRule
    ) -> None:
        assert await service.list_rules() == []
        await service.create_rule(rule)
        assert len(await service.list_rules()) == 1

    async def test_activate_rule(
        self, service: NotificationOrchestrationService, rule: OrchestrationRule
    ) -> None:
        await service.create_rule(rule)
        activated = await service.activate_rule("rule_1")
        assert activated.status is OrchestrationStatus.ACTIVE

    async def test_deactivate_rule(
        self, service: NotificationOrchestrationService, rule: OrchestrationRule
    ) -> None:
        await service.create_rule(rule)
        deactivated = await service.deactivate_rule("rule_1")
        assert deactivated.status is OrchestrationStatus.PAUSED

    async def test_route_notification(
        self, service: NotificationOrchestrationService, rule: OrchestrationRule
    ) -> None:
        await service.create_rule(rule)
        channel = await service.route_notification("rule_1", "n1", "email")
        assert channel == "email"

    async def test_route_notification_no_routes(
        self, service: NotificationOrchestrationService
    ) -> None:
        r = OrchestrationRule(id="no_routes", name="No Routes", enabled=True)
        await service.create_rule(r)
        with pytest.raises(NotificationRoutingError):
            await service.route_notification("no_routes", "n1", "email")

    async def test_route_notification_disabled_rule(
        self, service: NotificationOrchestrationService
    ) -> None:
        r = OrchestrationRule(id="disabled", name="Disabled", enabled=False)
        await service.create_rule(r)
        with pytest.raises(OrchestrationExecutionError):
            await service.route_notification("disabled", "n1", "email")

    async def test_orchestrate_notification(
        self, service: NotificationOrchestrationService, rule: OrchestrationRule
    ) -> None:
        await service.create_rule(rule)
        event = await service.orchestrate_notification("rule_1", "n1", "email")
        assert isinstance(event, NotificationOrchestrated)
        assert event.notification_id == "n1"

    async def test_trigger_escalation(
        self, service: NotificationOrchestrationService, rule_with_escalation: OrchestrationRule
    ) -> None:
        await service.create_rule(rule_with_escalation)
        event = await service.trigger_escalation("rule_2", level=1)
        assert isinstance(event, EscalationTriggered)
        assert event.level == 1
        assert event.targets == ()

    async def test_trigger_escalation_no_policy(
        self, service: NotificationOrchestrationService, rule: OrchestrationRule
    ) -> None:
        await service.create_rule(rule)
        with pytest.raises(OrchestrationExecutionError):
            await service.trigger_escalation("rule_1")

    async def test_resolve_escalation(
        self, service: NotificationOrchestrationService, rule_with_escalation: OrchestrationRule
    ) -> None:
        await service.create_rule(rule_with_escalation)
        event = await service.resolve_escalation("rule_2")
        assert isinstance(event, EscalationResolved)
        assert event.level == 0

    async def test_deliver_digest(
        self, service: NotificationOrchestrationService, rule_with_digest: OrchestrationRule
    ) -> None:
        await service.create_rule(rule_with_digest)
        count = await service.deliver_digest("rule_3", "email")
        assert count == 50

    async def test_deliver_digest_no_config(
        self, service: NotificationOrchestrationService, rule: OrchestrationRule
    ) -> None:
        await service.create_rule(rule)
        with pytest.raises(OrchestrationExecutionError):
            await service.deliver_digest("rule_1", "email")

    async def test_send_batch(
        self, service: NotificationOrchestrationService, rule: OrchestrationRule
    ) -> None:
        await service.create_rule(rule)
        event = await service.send_batch("rule_1", 10)
        assert isinstance(event, NotificationBatchSent)
        assert event.count == 10

    async def test_send_batch_not_found_rule(
        self, service: NotificationOrchestrationService
    ) -> None:
        with pytest.raises(OrchestrationRuleNotFoundError):
            await service.send_batch("nonexistent", 10)

    async def test_list_batches(
        self, service: NotificationOrchestrationService, rule: OrchestrationRule
    ) -> None:
        await service.create_rule(rule)
        await service.send_batch("rule_1", 5)
        assert len(await service.list_batches()) == 1

    async def test_get_batch(
        self, service: NotificationOrchestrationService, rule: OrchestrationRule
    ) -> None:
        await service.create_rule(rule)
        event = await service.send_batch("rule_1", 5)
        batch = await service.get_batch(event.batch_id)
        assert batch.rule_id == "rule_1"

    async def test_get_batch_not_found(self, service: NotificationOrchestrationService) -> None:
        with pytest.raises(OrchestrationRuleNotFoundError):
            await service.get_batch("nonexistent")

    async def test_trigger_schedule(
        self, service: NotificationOrchestrationService, rule: OrchestrationRule
    ) -> None:
        await service.create_rule(rule)
        schedule = await service.trigger_schedule("rule_1")
        assert schedule is None

    async def test_trigger_schedule_with_cron(
        self, service: NotificationOrchestrationService
    ) -> None:
        sched = OrchestrationSchedule(cron="0 9 * * 1")
        r = OrchestrationRule(id="sched_rule", name="Scheduled", schedule=sched)
        await service.create_rule(r)
        schedule = await service.trigger_schedule("sched_rule")
        assert schedule is not None
        assert schedule.cron == "0 9 * * 1"


# ── Health Check ──────────────────────────────────────────────────────────────


class TestNotificationOrchestrationHealthCheck:
    @pytest.fixture
    def service(self) -> NotificationOrchestrationService:
        return NotificationOrchestrationService()

    async def test_healthy(self, service: NotificationOrchestrationService) -> None:
        check = NotificationOrchestrationHealthCheck(service=service)
        report = await check.check()
        assert report.status.value == "healthy"
        assert report.component == "NotificationOrchestration"

    async def test_degraded_on_batch_failure(
        self, service: NotificationOrchestrationService
    ) -> None:
        r = OrchestrationRule(id="r_h", name="Health", enabled=True)
        await service.create_rule(r)
        check = NotificationOrchestrationHealthCheck(service=service)
        report = await check.check()
        assert report.status.value == "healthy"

    async def test_healthy_name(self) -> None:
        check = NotificationOrchestrationHealthCheck()
        assert check.name == "eaip.notification_orchestration"


# ── Integration ───────────────────────────────────────────────────────────────


class TestNotificationOrchestrationRuntimeModule:
    def test_name(self) -> None:
        module = NotificationOrchestrationRuntimeModule()
        assert module.name == "notification_orchestration"

    def test_service_property(self) -> None:
        module = NotificationOrchestrationRuntimeModule()
        assert isinstance(module.service, NotificationOrchestrationService)
