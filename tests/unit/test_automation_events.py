"""Tests for automation domain events."""

from __future__ import annotations

import pytest

from eaip.automation.events import (
    ActionExecuted,
    ActionFailed,
    ConditionEvaluated,
    RuleExecutionCompleted,
    RuleExecutionFailed,
    RuleExecutionStarted,
    RuleRegistered,
    RuleTriggered,
    RuleUnregistered,
    RuleUpdated,
    ScheduleTriggered,
)
from eaip.automation.models import (
    ActionType,
    AutomationExecution,
    AutomationRule,
    AutomationStatus,
    RuleAction,
    TriggerType,
)
from eaip.events.event import DomainEvent


class TestRuleRegistered:
    def test_event_type(self) -> None:
        rule = AutomationRule(id="r1", name="R1", trigger_type=TriggerType.MANUAL)
        event = RuleRegistered(rule=rule)
        assert event.event_type == "automation.rule.registered"
        assert isinstance(event, DomainEvent)

    def test_rule_content(self) -> None:
        rule = AutomationRule(id="r1", name="Test", trigger_type=TriggerType.MANUAL)
        event = RuleRegistered(rule=rule)
        assert event.rule.id == "r1"
        assert event.rule.name == "Test"


class TestRuleUnregistered:
    def test_event_type(self) -> None:
        event = RuleUnregistered(rule_id="r1", rule_name="R1")
        assert event.event_type == "automation.rule.unregistered"

    def test_fields(self) -> None:
        event = RuleUnregistered(rule_id="r1", rule_name="Test Rule")
        assert event.rule_id == "r1"
        assert event.rule_name == "Test Rule"


class TestRuleUpdated:
    def test_event_type(self) -> None:
        rule = AutomationRule(id="r1", name="R1", trigger_type=TriggerType.MANUAL)
        event = RuleUpdated(rule=rule)
        assert event.event_type == "automation.rule.updated"


class TestRuleTriggered:
    def test_event_type(self) -> None:
        event = RuleTriggered(
            rule_id="r1", rule_name="R1",
            trigger_type="manual", trigger_event={},
        )
        assert event.event_type == "automation.rule.triggered"

    def test_fields(self) -> None:
        event = RuleTriggered(
            rule_id="r1", rule_name="R1",
            trigger_type="event", trigger_event={"order_id": "123"},
        )
        assert event.trigger_event["order_id"] == "123"


class TestRuleExecutionStarted:
    def test_event_type(self) -> None:
        exec1 = AutomationExecution(id="e1", rule_id="r1", trigger_type=TriggerType.MANUAL)
        event = RuleExecutionStarted(execution=exec1)
        assert event.event_type == "automation.rule.execution.started"

    def test_execution_content(self) -> None:
        exec1 = AutomationExecution(
            id="e1", rule_id="r1", rule_name="Test",
            trigger_type=TriggerType.EVENT,
        )
        event = RuleExecutionStarted(execution=exec1)
        assert event.execution.id == "e1"
        assert event.execution.rule_name == "Test"


class TestRuleExecutionCompleted:
    def test_event_type(self) -> None:
        exec1 = AutomationExecution(
            id="e1", rule_id="r1", trigger_type=TriggerType.MANUAL,
            status=AutomationStatus.COMPLETED,
        )
        event = RuleExecutionCompleted(execution=exec1)
        assert event.event_type == "automation.rule.execution.completed"


class TestRuleExecutionFailed:
    def test_event_type(self) -> None:
        exec1 = AutomationExecution(
            id="e1", rule_id="r1", trigger_type=TriggerType.MANUAL,
            status=AutomationStatus.FAILED, error="oops",
        )
        event = RuleExecutionFailed(execution=exec1, error="oops")
        assert event.event_type == "automation.rule.execution.failed"
        assert event.error == "oops"


class TestActionExecuted:
    def test_event_type(self) -> None:
        action = RuleAction(type=ActionType.WEBHOOK, target="https://hook.example.com")
        event = ActionExecuted(
            execution_id="e1", action=action,
            result="ok", duration_ms=100.0,
        )
        assert event.event_type == "automation.action.executed"
        assert event.result == "ok"
        assert event.duration_ms == 100.0

    def test_action_content(self) -> None:
        action = RuleAction(type=ActionType.NOTIFICATION, target="slack")
        event = ActionExecuted(
            execution_id="e1", action=action,
            result="sent", duration_ms=50.0,
        )
        assert event.action.target == "slack"


class TestActionFailed:
    def test_event_type(self) -> None:
        action = RuleAction(type=ActionType.WEBHOOK, target="https://hook.example.com")
        event = ActionFailed(
            execution_id="e1", action=action,
            error="timeout", attempt=1,
        )
        assert event.event_type == "automation.action.failed"
        assert event.error == "timeout"
        assert event.attempt == 1


class TestConditionEvaluated:
    def test_event_type(self) -> None:
        from datetime import datetime, timezone
        event = ConditionEvaluated(
            rule_id="r1", execution_id="e1",
            result=True, evaluated_at=datetime.now(timezone.utc),
        )
        assert event.event_type == "automation.condition.evaluated"
        assert event.result is True


class TestScheduleTriggered:
    def test_event_type(self) -> None:
        event = ScheduleTriggered(rule_id="r1", cron_expression="0 9 * * 1-5")
        assert event.event_type == "automation.schedule.triggered"

    def test_fields(self) -> None:
        event = ScheduleTriggered(rule_id="r1", cron_expression="*/5 * * * *")
        assert event.cron_expression == "*/5 * * * *"


class TestDomainEventBase:
    def test_all_are_domain_events(self) -> None:
        rule = AutomationRule(id="r1", name="R1", trigger_type=TriggerType.MANUAL)
        exec1 = AutomationExecution(id="e1", rule_id="r1", trigger_type=TriggerType.MANUAL)
        action = RuleAction(type=ActionType.WEBHOOK, target="https://hook.example.com")
        from datetime import datetime, timezone

        events = [
            RuleRegistered(rule=rule),
            RuleUnregistered(rule_id="r1", rule_name="R1"),
            RuleUpdated(rule=rule),
            RuleTriggered(rule_id="r1", rule_name="R1", trigger_type="manual", trigger_event={}),
            RuleExecutionStarted(execution=exec1),
            RuleExecutionCompleted(execution=exec1),
            RuleExecutionFailed(execution=exec1, error="err"),
            ActionExecuted(execution_id="e1", action=action, result="ok", duration_ms=1.0),
            ActionFailed(execution_id="e1", action=action, error="err", attempt=1),
            ConditionEvaluated(rule_id="r1", execution_id="e1", result=True, evaluated_at=datetime.now(timezone.utc)),
            ScheduleTriggered(rule_id="r1", cron_expression="* * * * *"),
        ]
        for event in events:
            assert isinstance(event, DomainEvent)
            assert event.occurred_at is not None
