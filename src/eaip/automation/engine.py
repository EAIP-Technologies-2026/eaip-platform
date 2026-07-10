"""Automation engine - rule registration, execution, concurrency control, and lifecycle."""

from __future__ import annotations

import asyncio
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from eaip.automation.events import (
    ConditionEvaluated,
    RuleExecutionCompleted,
    RuleExecutionFailed,
    RuleExecutionStarted,
    RuleRegistered,
    RuleTriggered,
    RuleUnregistered,
    RuleUpdated,
)
from eaip.automation.exceptions import (
    ActionExecutionError,
    ConditionEvaluationError,
    RuleExecutionError,
    RuleNotFoundError,
)
from eaip.automation.executor import ActionExecutor
from eaip.automation.history import ExecutionHistory
from eaip.automation.models import (
    AutomationConfig,
    AutomationExecution,
    AutomationRule,
    AutomationStatus,
    ConditionOperator,
    LogicOperator,
    RuleCondition,
    TriggerEvent,
    TriggerType,
)
from eaip.automation.triggers import TriggerService
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger


class AutomationEngine:
    def __init__(
        self,
        config: AutomationConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._config = config or AutomationConfig()
        self._event_bus = event_bus or EventBus()
        self._log = get_logger("eaip.automation.engine")
        self._rules: dict[str, AutomationRule] = {}
        self._executions: dict[str, AutomationExecution] = {}
        self._active_executions: set[str] = set()
        self._semaphore = asyncio.Semaphore(self._config.max_concurrent_executions)
        self._trigger_service = TriggerService(self._event_bus)
        self._action_executor = ActionExecutor()
        self._history = ExecutionHistory()

    @property
    def rules(self) -> dict[str, AutomationRule]:
        return dict(self._rules)

    @property
    def executions(self) -> dict[str, AutomationExecution]:
        return dict(self._executions)

    @property
    def history(self) -> ExecutionHistory:
        return self._history

    @property
    def trigger_service(self) -> TriggerService:
        return self._trigger_service

    async def register_rule(self, rule: AutomationRule) -> None:
        self._rules[rule.id] = rule
        await self._event_bus.publish(RuleRegistered(rule=rule))
        self._log.info("rule.registered", rule_id=rule.id, rule_name=rule.name)

    async def unregister_rule(self, rule_id: str) -> None:
        rule = self._rules.pop(rule_id, None)
        if rule is None:
            raise RuleNotFoundError(f"Rule {rule_id!r} not found", context={"rule_id": rule_id})
        await self._event_bus.publish(RuleUnregistered(rule_id=rule_id, rule_name=rule.name))
        self._log.info("rule.unregistered", rule_id=rule_id)

    async def get_rule(self, rule_id: str) -> AutomationRule:
        rule = self._rules.get(rule_id)
        if rule is None:
            raise RuleNotFoundError(f"Rule {rule_id!r} not found", context={"rule_id": rule_id})
        return rule

    async def list_rules(
        self, trigger_type: TriggerType | None = None, enabled: bool | None = None,
    ) -> list[AutomationRule]:
        result = list(self._rules.values())
        if trigger_type is not None:
            result = [r for r in result if r.trigger_type == trigger_type]
        if enabled is not None:
            result = [r for r in result if r.enabled == enabled]
        return result

    async def trigger(self, event: TriggerEvent) -> list[AutomationExecution]:
        triggered: list[AutomationExecution] = []
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            if rule.trigger_type == TriggerType.EVENT:
                if event.type in rule.event_pattern.get("types", [event.type]) if rule.event_pattern else False:
                    continue
                if rule.event_pattern and event.type not in rule.event_pattern.get("types", [event.type]):
                    continue
            elif rule.trigger_type != TriggerType.MANUAL and rule.trigger_type != TriggerType.WEBHOOK:
                continue
            execution = await self.execute_rule(rule.id, event)
            triggered.append(execution)
        return triggered

    async def execute_rule(
        self, rule_id: str, trigger_event: TriggerEvent | None = None,
    ) -> AutomationExecution:
        rule = await self.get_rule(rule_id)
        if not rule.enabled:
            raise RuleExecutionError(
                f"Rule {rule_id!r} is disabled",
                context={"rule_id": rule_id},
            )

        execution_id = str(uuid.uuid4())
        execution = AutomationExecution(
            id=execution_id,
            rule_id=rule.id,
            rule_name=rule.name,
            trigger_type=rule.trigger_type,
            trigger_event=trigger_event.model_dump() if trigger_event else {},
            status=AutomationStatus.RUNNING,
            started_at=datetime.now(UTC),
        )
        self._executions[execution_id] = execution
        self._active_executions.add(execution_id)

        await self._event_bus.publish(
            RuleExecutionStarted(execution=execution),
        )

        async with self._semaphore:
            try:
                result = await self.evaluate_and_execute(rule, trigger_event)
                duration_ms = (datetime.now(UTC) - execution.started_at).total_seconds() * 1000
                execution = AutomationExecution(
                    id=execution_id,
                    rule_id=rule.id,
                    rule_name=rule.name,
                    trigger_type=rule.trigger_type,
                    trigger_event=execution.trigger_event,
                    status=AutomationStatus.COMPLETED,
                    started_at=execution.started_at,
                    completed_at=datetime.now(UTC),
                    duration_ms=duration_ms,
                    result=result.get("result", ""),
                    actions_executed=result.get("actions_executed", 0),
                    actions_failed=result.get("actions_failed", 0),
                )
                self._executions[execution_id] = execution
                await self._history.record_execution(execution)
                await self._event_bus.publish(
                    RuleExecutionCompleted(execution=execution),
                )
            except Exception as exc:
                duration_ms = (datetime.now(UTC) - execution.started_at).total_seconds() * 1000
                execution = AutomationExecution(
                    id=execution_id,
                    rule_id=rule.id,
                    rule_name=rule.name,
                    trigger_type=rule.trigger_type,
                    trigger_event=execution.trigger_event,
                    status=AutomationStatus.FAILED,
                    started_at=execution.started_at,
                    completed_at=datetime.now(UTC),
                    duration_ms=duration_ms,
                    error=str(exc),
                    actions_executed=0,
                    actions_failed=0,
                )
                self._executions[execution_id] = execution
                await self._history.record_execution(execution)
                await self._event_bus.publish(
                    RuleExecutionFailed(execution=execution, error=str(exc)),
                )
            finally:
                self._active_executions.discard(execution_id)

        return execution

    async def cancel_execution(self, execution_id: str) -> AutomationExecution:
        execution = self._executions.get(execution_id)
        if execution is None:
            raise RuleExecutionError(
                f"Execution {execution_id!r} not found",
                context={"execution_id": execution_id},
            )
        if execution.status not in (AutomationStatus.PENDING, AutomationStatus.RUNNING):
            return execution

        execution = AutomationExecution(
            id=execution.id,
            rule_id=execution.rule_id,
            rule_name=execution.rule_name,
            trigger_type=execution.trigger_type,
            trigger_event=execution.trigger_event,
            status=AutomationStatus.CANCELLED,
            started_at=execution.started_at,
            completed_at=datetime.now(UTC),
            duration_ms=(datetime.now(UTC) - execution.started_at).total_seconds() * 1000,
            error="Cancelled by user",
        )
        self._executions[execution_id] = execution
        self._active_executions.discard(execution_id)
        await self._history.record_execution(execution)
        return execution

    async def get_execution(self, execution_id: str) -> AutomationExecution:
        execution = self._executions.get(execution_id)
        if execution is None:
            raise RuleExecutionError(
                f"Execution {execution_id!r} not found",
                context={"execution_id": execution_id},
            )
        return execution

    async def list_executions(
        self,
        rule_id: str | None = None,
        status: AutomationStatus | None = None,
        limit: int = 100,
    ) -> list[AutomationExecution]:
        result = list(self._executions.values())
        if rule_id is not None:
            result = [e for e in result if e.rule_id == rule_id]
        if status is not None:
            result = [e for e in result if e.status == status]
        result.sort(key=lambda e: e.started_at, reverse=True)
        return result[:limit]

    async def evaluate_conditions(
        self, rule: AutomationRule, event: TriggerEvent | None,
    ) -> bool:
        if not rule.conditions:
            return True

        for condition in rule.conditions:
            evaluated = self._evaluate_single_condition(condition, event)
            await self._event_bus.publish(
                ConditionEvaluated(
                    rule_id=rule.id,
                    execution_id="",
                    result=evaluated,
                    evaluated_at=datetime.now(UTC),
                ),
            )

        combined = self._combine_conditions(rule.conditions, event)
        return combined

    def _evaluate_single_condition(
        self, condition: RuleCondition, event: TriggerEvent | None,
    ) -> bool:
        if event is None:
            return False

        payload = event.payload
        field_value = self._resolve_field(payload, condition.field)

        if condition.operator == ConditionOperator.EXISTS:
            return condition.value is True if field_value is not None else condition.value is False

        if field_value is None:
            return False

        try:
            if condition.operator == ConditionOperator.EQ:
                return bool(field_value == condition.value)
            elif condition.operator == ConditionOperator.NEQ:
                return bool(field_value != condition.value)
            elif condition.operator == ConditionOperator.GT:
                return bool(field_value > condition.value)
            elif condition.operator == ConditionOperator.GTE:
                return bool(field_value >= condition.value)
            elif condition.operator == ConditionOperator.LT:
                return bool(field_value < condition.value)
            elif condition.operator == ConditionOperator.LTE:
                return bool(field_value <= condition.value)
            elif condition.operator == ConditionOperator.IN:
                return field_value in (condition.value or [])
            elif condition.operator == ConditionOperator.CONTAINS:
                return condition.value in field_value if isinstance(field_value, (str, list, tuple)) else False
            elif condition.operator == ConditionOperator.MATCHES:
                import re
                return bool(re.match(str(condition.value), str(field_value)))
        except (TypeError, ValueError) as exc:
            raise ConditionEvaluationError(
                f"Failed to evaluate condition: {exc}",
                context={"field": condition.field, "operator": condition.operator},
            )

    def _resolve_field(self, payload: dict[str, Any], field: str) -> Any:
        parts = field.split(".")
        current: Any = payload
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def _combine_conditions(
        self, conditions: tuple[RuleCondition, ...], event: TriggerEvent | None,
    ) -> bool:
        if not conditions:
            return True

        result = self._evaluate_single_condition(conditions[0], event)
        for condition in conditions[1:]:
            evaluated = self._evaluate_single_condition(condition, event)
            if condition.logic == LogicOperator.AND:
                result = result and evaluated
            else:
                result = result or evaluated
        return result

    async def execute_actions(
        self, rule: AutomationRule, event: TriggerEvent | None,
    ) -> dict[str, Any]:
        if not rule.actions:
            return {"result": "", "actions_executed": 0, "actions_failed": 0}

        context = event.model_dump() if event else {}
        actions_executed = 0
        actions_failed = 0
        last_result = ""

        for action in rule.actions:
            try:
                result = await self._action_executor.execute_action(action, context)
                actions_executed += 1
                last_result = result
            except ActionExecutionError:
                actions_failed += 1
                if not action.retry_on_failure:
                    raise

        return {
            "result": last_result,
            "actions_executed": actions_executed,
            "actions_failed": actions_failed,
        }

    async def evaluate_and_execute(
        self, rule: AutomationRule, event: TriggerEvent | None,
    ) -> dict[str, Any]:
        conditions_met = await self.evaluate_conditions(rule, event)
        if not conditions_met:
            return {"result": "conditions_not_met", "actions_executed": 0, "actions_failed": 0}

        await self._event_bus.publish(
            RuleTriggered(
                rule_id=rule.id,
                rule_name=rule.name,
                trigger_type=rule.trigger_type,
                trigger_event=event.model_dump() if event else {},
            ),
        )

        return await self.execute_actions(rule, event)


__all__ = ["AutomationEngine"]
