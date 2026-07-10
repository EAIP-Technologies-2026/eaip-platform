"""Goal exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class GoalError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class GoalNotFoundError(GoalError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, goal_id: str) -> None:
        self.goal_id = goal_id
        super().__init__(f"goal not found: {goal_id!r}")


class GoalValidationError(GoalError):
    default_code: ErrorCode = ErrorCode.VALIDATION_FAILED

    def __init__(self, message: str) -> None:
        super().__init__(message)


class KpiNotFoundError(GoalError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, kpi_id: str) -> None:
        self.kpi_id = kpi_id
        super().__init__(f"KPI not found: {kpi_id!r}")


class GoalEngineError(GoalError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


__all__ = [
    "GoalEngineError",
    "GoalError",
    "GoalNotFoundError",
    "GoalValidationError",
    "KpiNotFoundError",
]
