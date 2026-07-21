"""Exception hierarchy for the AI cost optimization service."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class AiCostError(EAIPError):
    """Base exception for AI cost-related errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class AiCostBudgetError(AiCostError):
    default_code = ErrorCode.POLICY_VIOLATION

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AiCostRecordError(AiCostError):
    default_code = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AiCostOptimizationError(AiCostError):
    default_code = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AiCostReportError(AiCostError):
    default_code = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AiCostAllocationError(AiCostError):
    default_code = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AiCostAnomalyError(AiCostError):
    default_code = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


__all__ = [
    "AiCostAllocationError",
    "AiCostAnomalyError",
    "AiCostBudgetError",
    "AiCostError",
    "AiCostOptimizationError",
    "AiCostRecordError",
    "AiCostReportError",
]
