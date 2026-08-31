"""Exception hierarchy for the cost intelligence engine."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class CostError(EAIPError):
    """Base exception for cost-related errors."""

    default_code = ErrorCode.INTERNAL_ERROR  # EAIP-0017


class BudgetNotFoundError(CostError):
    default_code = ErrorCode.NOT_FOUND  # EAIP-0003


class BudgetExceededError(CostError):
    default_code = ErrorCode.POLICY_VIOLATION  # EAIP-0012


class AlertNotFoundError(CostError):
    default_code = ErrorCode.NOT_FOUND  # EAIP-0003


class RecommendationNotFoundError(CostError):
    default_code = ErrorCode.NOT_FOUND  # EAIP-0003


class ChargebackError(CostError):
    default_code = ErrorCode.INTERNAL_ERROR  # EAIP-0017
