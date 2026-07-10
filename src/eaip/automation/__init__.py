"""Enterprise Automation Runtime - rule execution, triggers, scheduling, and observability."""

from __future__ import annotations

from eaip.automation.engine import AutomationEngine
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
from eaip.automation.exceptions import (
    ActionExecutionError,
    AutomationError,
    ConditionEvaluationError,
    RuleExecutionError,
    RuleNotFoundError,
    TriggerProcessingError,
)
from eaip.automation.executor import ActionExecutor
from eaip.automation.health import AutomationHealthCheck
from eaip.automation.history import ExecutionHistory
from eaip.automation.integration import AutomationRuntimeModule
from eaip.automation.models import (
    AutomationConfig,
    AutomationExecution,
    AutomationRule,
    ExecutionHistoryEntry,
    RuleAction,
    RuleCondition,
    TriggerEvent,
)
from eaip.automation.scheduler import AutomationScheduler
from eaip.automation.triggers import TriggerService

__all__ = [
    "ActionExecuted",
    "ActionExecutionError",
    "ActionExecutor",
    "ActionFailed",
    "AutomationConfig",
    "AutomationEngine",
    "AutomationError",
    "AutomationExecution",
    "AutomationHealthCheck",
    "AutomationRule",
    "AutomationRuntimeModule",
    "AutomationScheduler",
    "ConditionEvaluated",
    "ConditionEvaluationError",
    "ExecutionHistory",
    "ExecutionHistoryEntry",
    "RuleAction",
    "RuleCondition",
    "RuleExecutionCompleted",
    "RuleExecutionError",
    "RuleExecutionFailed",
    "RuleExecutionStarted",
    "RuleNotFoundError",
    "RuleRegistered",
    "RuleTriggered",
    "RuleUnregistered",
    "RuleUpdated",
    "ScheduleTriggered",
    "TriggerEvent",
    "TriggerProcessingError",
    "TriggerService",
]
