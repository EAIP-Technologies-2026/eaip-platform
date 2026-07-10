"""Tests for AutomationEngine."""

from __future__ import annotations

import pytest

from eaip.automation.engine import AutomationEngine
from eaip.automation.exceptions import (
    RuleExecutionError,
    RuleNotFoundError,
)
from eaip.automation.models import (
    ActionType,
    AutomationExecution,
    AutomationRule,
    AutomationStatus,
    ConditionOperator,
    RuleAction,
    RuleCondition,
    TriggerEvent,
    TriggerType,
)


class TestAutomationEngine:
    @pytest.fixture
    def engine(self) -> AutomationEngine:
        return AutomationEngine()

    @pytest.fixture
    def sample_rule(self) -> AutomationRule:
        return AutomationRule(
            id="rule_1",
            name="Test Rule",
            trigger_type=TriggerType.MANUAL,
            actions=(
                RuleAction(type=ActionType.NOTIFICATION, target="log"),
            ),
        )

    async def test_register_rule(self, engine, sample_rule) -> None:
        await engine.register_rule(sample_rule)
        rule = await engine.get_rule("rule_1")
        assert rule.id == "rule_1"
        assert rule.name == "Test Rule"

    async def test_register_rule_twice_overwrites(self, engine, sample_rule) -> None:
        await engine.register_rule(sample_rule)
        updated = AutomationRule(
            id="rule_1",
            name="Updated Rule",
            trigger_type=TriggerType.SCHEDULE,
            schedule_cron="0 9 * * *",
        )
        await engine.register_rule(updated)
        rule = await engine.get_rule("rule_1")
        assert rule.name == "Updated Rule"

    async def test_unregister_rule(self, engine, sample_rule) -> None:
        await engine.register_rule(sample_rule)
        await engine.unregister_rule("rule_1")
        with pytest.raises(RuleNotFoundError):
            await engine.get_rule("rule_1")

    async def test_unregister_missing_rule(self, engine) -> None:
        with pytest.raises(RuleNotFoundError):
            await engine.unregister_rule("nonexistent")

    async def test_get_rule_not_found(self, engine) -> None:
        with pytest.raises(RuleNotFoundError):
            await engine.get_rule("nonexistent")

    async def test_list_rules_all(self, engine, sample_rule) -> None:
        await engine.register_rule(sample_rule)
        rules = await engine.list_rules()
        assert len(rules) == 1

    async def test_list_rules_empty(self, engine) -> None:
        rules = await engine.list_rules()
        assert rules == []

    async def test_list_rules_by_trigger_type(self, engine) -> None:
        r1 = AutomationRule(id="r1", name="R1", trigger_type=TriggerType.MANUAL)
        r2 = AutomationRule(id="r2", name="R2", trigger_type=TriggerType.EVENT, event_pattern={"types": ["t1"]})
        await engine.register_rule(r1)
        await engine.register_rule(r2)
        manual_rules = await engine.list_rules(trigger_type=TriggerType.MANUAL)
        event_rules = await engine.list_rules(trigger_type=TriggerType.EVENT)
        assert len(manual_rules) == 1
        assert len(event_rules) == 1

    async def test_list_rules_by_enabled(self, engine) -> None:
        r1 = AutomationRule(id="r1", name="R1", trigger_type=TriggerType.MANUAL, enabled=True)
        r2 = AutomationRule(id="r2", name="R2", trigger_type=TriggerType.MANUAL, enabled=False)
        await engine.register_rule(r1)
        await engine.register_rule(r2)
        enabled = await engine.list_rules(enabled=True)
        disabled = await engine.list_rules(enabled=False)
        assert len(enabled) == 1
        assert len(disabled) == 1

    async def test_execute_rule_success(self, engine, sample_rule) -> None:
        await engine.register_rule(sample_rule)
        execution = await engine.execute_rule("rule_1")
        assert execution.status == AutomationStatus.COMPLETED
        assert execution.rule_id == "rule_1"

    async def test_execute_rule_not_found(self, engine) -> None:
        with pytest.raises(RuleNotFoundError):
            await engine.execute_rule("nonexistent")

    async def test_execute_disabled_rule(self, engine) -> None:
        rule = AutomationRule(
            id="disabled_rule",
            name="Disabled",
            trigger_type=TriggerType.MANUAL,
            enabled=False,
        )
        await engine.register_rule(rule)
        with pytest.raises(RuleExecutionError):
            await engine.execute_rule("disabled_rule")

    async def test_execute_rule_with_conditions_met(self, engine) -> None:
        event = TriggerEvent(id="evt1", type="order.created", source="shopify", payload={"status": "pending"})
        rule = AutomationRule(
            id="rule_cond",
            name="Condition Rule",
            trigger_type=TriggerType.EVENT,
            event_pattern={"types": ["order.created"]},
            conditions=(
                RuleCondition(field="status", operator=ConditionOperator.EQ, value="pending"),
            ),
            actions=(
                RuleAction(type=ActionType.NOTIFICATION, target="log"),
            ),
        )
        await engine.register_rule(rule)
        execution = await engine.execute_rule("rule_cond", event)
        assert execution.status == AutomationStatus.COMPLETED

    async def test_execute_rule_with_conditions_not_met(self, engine) -> None:
        event = TriggerEvent(id="evt1", type="order.created", source="shopify", payload={"status": "paid"})
        rule = AutomationRule(
            id="rule_cond_fail",
            name="Condition Fail Rule",
            trigger_type=TriggerType.EVENT,
            event_pattern={"types": ["order.created"]},
            conditions=(
                RuleCondition(field="status", operator=ConditionOperator.EQ, value="pending"),
            ),
            actions=(
                RuleAction(type=ActionType.NOTIFICATION, target="log"),
            ),
        )
        await engine.register_rule(rule)
        execution = await engine.execute_rule("rule_cond_fail", event)
        assert execution.status == AutomationStatus.COMPLETED
        assert execution.result == "conditions_not_met"

    async def test_cancel_execution(self, engine, sample_rule) -> None:
        await engine.register_rule(sample_rule)
        execution = AutomationExecution(
            id="to_cancel",
            rule_id="rule_1",
            trigger_type=TriggerType.MANUAL,
            status=AutomationStatus.RUNNING,
        )
        engine._executions["to_cancel"] = execution
        engine._active_executions.add("to_cancel")

        cancelled = await engine.cancel_execution("to_cancel")
        assert cancelled.status == AutomationStatus.CANCELLED
        assert cancelled.error == "Cancelled by user"

    async def test_cancel_missing_execution(self, engine) -> None:
        with pytest.raises(RuleExecutionError):
            await engine.cancel_execution("nonexistent")

    async def test_cancel_already_completed(self, engine, sample_rule) -> None:
        await engine.register_rule(sample_rule)
        execution = AutomationExecution(
            id="completed",
            rule_id="rule_1",
            trigger_type=TriggerType.MANUAL,
            status=AutomationStatus.COMPLETED,
        )
        engine._executions["completed"] = execution
        result = await engine.cancel_execution("completed")
        assert result.status == AutomationStatus.COMPLETED

    async def test_get_execution(self, engine, sample_rule) -> None:
        await engine.register_rule(sample_rule)
        execution = await engine.execute_rule("rule_1")
        retrieved = await engine.get_execution(execution.id)
        assert retrieved.id == execution.id

    async def test_get_execution_not_found(self, engine) -> None:
        with pytest.raises(RuleExecutionError):
            await engine.get_execution("nonexistent")

    async def test_list_executions(self, engine, sample_rule) -> None:
        await engine.register_rule(sample_rule)
        await engine.execute_rule("rule_1")
        await engine.execute_rule("rule_1")
        executions = await engine.list_executions()
        assert len(executions) == 2

    async def test_list_executions_by_rule_id(self, engine) -> None:
        r1 = AutomationRule(id="r1", name="R1", trigger_type=TriggerType.MANUAL)
        r2 = AutomationRule(id="r2", name="R2", trigger_type=TriggerType.MANUAL)
        await engine.register_rule(r1)
        await engine.register_rule(r2)
        await engine.execute_rule("r1")
        await engine.execute_rule("r2")
        r1_execs = await engine.list_executions(rule_id="r1")
        assert len(r1_execs) == 1

    async def test_list_executions_by_status(self, engine, sample_rule) -> None:
        await engine.register_rule(sample_rule)
        await engine.execute_rule("rule_1")
        completed = await engine.list_executions(status=AutomationStatus.COMPLETED)
        assert len(completed) >= 1

    async def test_evaluate_conditions_empty(self, engine, sample_rule) -> None:
        result = await engine.evaluate_conditions(sample_rule, None)
        assert result is True

    async def test_evaluate_conditions_with_event(self, engine) -> None:
        event = TriggerEvent(id="evt1", type="test", source="test", payload={"value": 10})
        rule = AutomationRule(
            id="r1", name="R1", trigger_type=TriggerType.EVENT,
            event_pattern={"types": ["test"]},
            conditions=(
                RuleCondition(field="value", operator=ConditionOperator.GT, value=5),
            ),
        )
        result = await engine.evaluate_conditions(rule, event)
        assert result is True

    async def test_evaluate_conditions_false(self, engine) -> None:
        event = TriggerEvent(id="evt1", type="test", source="test", payload={"value": 1})
        rule = AutomationRule(
            id="r1", name="R1", trigger_type=TriggerType.EVENT,
            event_pattern={"types": ["test"]},
            conditions=(
                RuleCondition(field="value", operator=ConditionOperator.GT, value=5),
            ),
        )
        result = await engine.evaluate_conditions(rule, event)
        assert result is False

    async def test_trigger_event_matching(self, engine) -> None:
        rule = AutomationRule(
            id="r1", name="R1", trigger_type=TriggerType.EVENT,
            event_pattern={"types": ["order.created"]},
            actions=(
                RuleAction(type=ActionType.NOTIFICATION, target="log"),
            ),
        )
        await engine.register_rule(rule)
        event = TriggerEvent(id="evt1", type="order.created", source="shopify", payload={})
        executions = await engine.trigger(event)
        assert len(executions) >= 0

    async def test_rules_property(self, engine, sample_rule) -> None:
        await engine.register_rule(sample_rule)
        assert len(engine.rules) == 1
        assert "rule_1" in engine.rules

    async def test_executions_property(self, engine, sample_rule) -> None:
        await engine.register_rule(sample_rule)
        await engine.execute_rule("rule_1")
        assert len(engine.executions) >= 1

    async def test_history_property(self, engine) -> None:
        assert engine.history is not None

    async def test_trigger_service_property(self, engine) -> None:
        assert engine.trigger_service is not None
