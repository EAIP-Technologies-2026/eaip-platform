"""Tests for automation models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from eaip.automation.models import (
    ActionType,
    AutomationConfig,
    AutomationExecution,
    AutomationRule,
    AutomationStatus,
    ConditionOperator,
    ExecutionHistoryEntry,
    LogicOperator,
    RuleAction,
    RuleCondition,
    TriggerEvent,
    TriggerType,
)


class TestRuleCondition:
    def test_defaults(self) -> None:
        c = RuleCondition(field="status", operator=ConditionOperator.EQ, value="active")
        assert c.field == "status"
        assert c.operator == ConditionOperator.EQ
        assert c.value == "active"
        assert c.logic == LogicOperator.AND

    def test_frozen(self) -> None:
        c = RuleCondition(field="status", operator=ConditionOperator.EQ, value="active")
        with pytest.raises(ValidationError):
            c.field = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            RuleCondition(field="x", operator=ConditionOperator.EQ, value=1, extra_field="nope")

    def test_all_operators(self) -> None:
        for op in ConditionOperator:
            c = RuleCondition(field="f", operator=op, value=1)
            assert c.operator == op

    def test_in_operator(self) -> None:
        c = RuleCondition(field="color", operator=ConditionOperator.IN, value=["red", "blue"])
        assert c.value == ["red", "blue"]


class TestRuleAction:
    def test_defaults(self) -> None:
        a = RuleAction(type=ActionType.WEBHOOK, target="https://example.com/hook")
        assert a.type == ActionType.WEBHOOK
        assert a.payload == {}
        assert a.timeout_seconds == 30.0
        assert a.retry_on_failure is True

    def test_frozen(self) -> None:
        a = RuleAction(type=ActionType.WEBHOOK, target="https://example.com/hook")
        with pytest.raises(ValidationError):
            a.target = "changed"

    def test_workflow_action(self) -> None:
        a = RuleAction(
            type=ActionType.WORKFLOW,
            target="wf_order_processing",
            payload={"order_id": "123"},
        )
        assert a.type == ActionType.WORKFLOW
        assert a.payload == {"order_id": "123"}

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            RuleAction(type=ActionType.WEBHOOK, target="x", unknown=True)


class TestAutomationRule:
    def test_minimal(self) -> None:
        r = AutomationRule(
            id="rule_1",
            name="Test Rule",
            trigger_type=TriggerType.MANUAL,
        )
        assert r.id == "rule_1"
        assert r.enabled is True
        assert r.priority == 0
        assert r.max_retries == 3

    def test_full(self) -> None:
        r = AutomationRule(
            id="rule_2",
            name="Full Rule",
            description="A rule with everything",
            trigger_type=TriggerType.EVENT,
            event_pattern={"types": ["order.created"]},
            conditions=(
                RuleCondition(field="status", operator=ConditionOperator.EQ, value="pending"),
            ),
            actions=(
                RuleAction(type=ActionType.WEBHOOK, target="https://hook.example.com"),
            ),
            enabled=True,
            priority=10,
            max_retries=5,
            timeout_seconds=120.0,
            tags=("production", "critical"),
            metadata={"owner": "team-a"},
        )
        assert r.trigger_type == TriggerType.EVENT
        assert r.event_pattern == {"types": ["order.created"]}
        assert len(r.conditions) == 1
        assert len(r.actions) == 1
        assert r.priority == 10

    def test_schedule_trigger(self) -> None:
        r = AutomationRule(
            id="rule_3",
            name="Scheduled Rule",
            trigger_type=TriggerType.SCHEDULE,
            schedule_cron="0 9 * * 1-5",
        )
        assert r.schedule_cron == "0 9 * * 1-5"

    def test_frozen(self) -> None:
        r = AutomationRule(id="r1", name="R1", trigger_type=TriggerType.MANUAL)
        with pytest.raises(ValidationError):
            r.name = "Changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            AutomationRule(id="r1", name="R1", trigger_type=TriggerType.MANUAL, bad="value")


class TestAutomationExecution:
    def test_defaults(self) -> None:
        e = AutomationExecution(
            id="exec_1",
            rule_id="rule_1",
            trigger_type=TriggerType.MANUAL,
        )
        assert e.status == AutomationStatus.PENDING
        assert e.actions_executed == 0
        assert e.retry_attempt == 0

    def test_completed(self) -> None:
        started = datetime.now(timezone.utc)
        e = AutomationExecution(
            id="exec_2",
            rule_id="rule_1",
            rule_name="Test Rule",
            trigger_type=TriggerType.EVENT,
            status=AutomationStatus.COMPLETED,
            started_at=started,
            completed_at=started,
            duration_ms=1500.0,
            result="success",
            actions_executed=2,
            actions_failed=0,
        )
        assert e.status == AutomationStatus.COMPLETED
        assert e.result == "success"
        assert e.actions_executed == 2

    def test_failed(self) -> None:
        e = AutomationExecution(
            id="exec_3",
            rule_id="rule_1",
            trigger_type=TriggerType.SCHEDULE,
            status=AutomationStatus.FAILED,
            error="Connection timeout",
            actions_failed=1,
        )
        assert e.error == "Connection timeout"
        assert e.actions_failed == 1

    def test_all_statuses(self) -> None:
        for s in AutomationStatus:
            e = AutomationExecution(
                id=f"exec_{s}", rule_id="r1", trigger_type=TriggerType.MANUAL, status=s,
            )
            assert e.status == s


class TestTriggerEvent:
    def test_defaults(self) -> None:
        e = TriggerEvent(id="evt_1", type="order.created", source="shopify")
        assert e.payload == {}
        assert e.correlation_id == ""
        assert e.metadata == {}

    def test_with_payload(self) -> None:
        e = TriggerEvent(
            id="evt_2", type="order.updated", source="shopify",
            payload={"order_id": "ord-123", "status": "paid"},
            correlation_id="corr-abc",
            metadata={"env": "prod"},
        )
        assert e.payload["order_id"] == "ord-123"
        assert e.correlation_id == "corr-abc"

    def test_frozen(self) -> None:
        e = TriggerEvent(id="evt_1", type="t", source="s")
        with pytest.raises(ValidationError):
            e.type = "changed"


class TestAutomationConfig:
    def test_defaults(self) -> None:
        c = AutomationConfig()
        assert c.max_concurrent_executions == 10
        assert c.default_timeout_seconds == 60.0
        assert c.enable_execution_history is True
        assert c.history_retention_days == 30

    def test_custom(self) -> None:
        c = AutomationConfig(
            max_concurrent_executions=5,
            default_timeout_seconds=120.0,
            enable_execution_history=False,
            history_retention_days=7,
            enable_audit_logging=False,
            max_retries_default=5,
            cooldown_seconds=2.0,
        )
        assert c.max_concurrent_executions == 5
        assert c.cooldown_seconds == 2.0

    def test_frozen(self) -> None:
        c = AutomationConfig()
        with pytest.raises(ValidationError):
            c.max_concurrent_executions = 20


class TestExecutionHistoryEntry:
    def test_minimal(self) -> None:
        started = datetime.now(timezone.utc)
        e = ExecutionHistoryEntry(
            execution_id="exec_1",
            rule_id="rule_1",
            status=AutomationStatus.COMPLETED,
            started_at=started,
            trigger_type=TriggerType.MANUAL,
        )
        assert e.execution_id == "exec_1"
        assert e.duration_ms == 0.0

    def test_with_error(self) -> None:
        started = datetime.now(timezone.utc)
        e = ExecutionHistoryEntry(
            execution_id="exec_2",
            rule_id="rule_1",
            status=AutomationStatus.FAILED,
            started_at=started,
            completed_at=started,
            duration_ms=500.0,
            trigger_type=TriggerType.EVENT,
            result_summary="",
            error_summary="Timeout",
        )
        assert e.error_summary == "Timeout"

    def test_frozen(self) -> None:
        started = datetime.now(timezone.utc)
        e = ExecutionHistoryEntry(
            execution_id="e1", rule_id="r1", status=AutomationStatus.PENDING,
            started_at=started, trigger_type=TriggerType.MANUAL,
        )
        with pytest.raises(ValidationError):
            e.execution_id = "changed"
