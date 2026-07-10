"""Exception hierarchy for the automation runtime."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class AutomationError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class RuleNotFoundError(AutomationError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class RuleExecutionError(AutomationError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ActionExecutionError(AutomationError):
    default_code = ErrorCode.GATEWAY_ERROR
    default_severity = ErrorSeverity.ERROR


class ConditionEvaluationError(AutomationError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.WARNING


class TriggerProcessingError(AutomationError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


__all__ = [
    "ActionExecutionError",
    "AutomationError",
    "ConditionEvaluationError",
    "RuleExecutionError",
    "RuleNotFoundError",
    "TriggerProcessingError",
]
