"""Exception hierarchy for the retry orchestration."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class RetryOrchestrationError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class RetryError(RetryOrchestrationError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class RetryPolicyNotFoundError(RetryError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING

    def __init__(self, policy_id: str) -> None:
        self.policy_id = policy_id
        super().__init__(f"retry policy not found: {policy_id!r}")


class RetryExecutionError(RetryError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR

    def __init__(self, execution_id: str, message: str) -> None:
        self.execution_id = execution_id
        super().__init__(f"retry execution {execution_id!r} failed: {message}")


class RetryExhaustedError(RetryError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR

    def __init__(self, policy_id: str, total_attempts: int, last_error: str) -> None:
        self.policy_id = policy_id
        self.total_attempts = total_attempts
        self.last_error = last_error
        super().__init__(
            f"retry exhausted for policy {policy_id!r} after "
            f"{total_attempts} attempt(s): {last_error}"
        )


class RetryConfigError(RetryError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.WARNING

    def __init__(self, message: str) -> None:
        super().__init__(f"retry config error: {message}")


class CircuitBreakerOpenError(RetryError):
    default_code = ErrorCode.GATEWAY_ERROR
    default_severity = ErrorSeverity.ERROR

    def __init__(self, policy_id: str) -> None:
        self.policy_id = policy_id
        super().__init__(f"circuit breaker open for policy {policy_id!r}")


class CircuitBreakerConfigError(RetryError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.WARNING

    def __init__(self, message: str) -> None:
        super().__init__(f"circuit breaker config error: {message}")


__all__ = [
    "CircuitBreakerConfigError",
    "CircuitBreakerOpenError",
    "RetryConfigError",
    "RetryError",
    "RetryExecutionError",
    "RetryExhaustedError",
    "RetryOrchestrationError",
    "RetryPolicyNotFoundError",
]
