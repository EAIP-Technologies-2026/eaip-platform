"""Exception hierarchy for the AI Guardrails engine."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class GuardrailError(EAIPError):
    """Base exception for guardrail errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class GuardrailViolationError(GuardrailError):
    """Raised when a guardrail rule is violated."""

    default_code = ErrorCode.POLICY_VIOLATION


class GuardrailConfigError(GuardrailError):
    """Raised when guardrail configuration is invalid."""

    default_code = ErrorCode.CONFIGURATION_INVALID


__all__ = [
    "GuardrailConfigError",
    "GuardrailError",
    "GuardrailViolationError",
]
