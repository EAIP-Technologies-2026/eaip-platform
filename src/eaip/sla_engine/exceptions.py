"""SLA exceptions — structured error types for SLA lifecycle."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class SlaError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class SlaDefinitionNotFoundError(SlaError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, definition_id: str) -> None:
        self.definition_id = definition_id
        super().__init__(f"SLA definition not found: {definition_id!r}")


class SlaMonitorNotFoundError(SlaError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, monitor_id: str) -> None:
        self.monitor_id = monitor_id
        super().__init__(f"SLA monitor not found: {monitor_id!r}")


class SlaViolationError(SlaError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(f"SLA violation error: {message}")


class SlaPolicyError(SlaError):
    default_code: ErrorCode = ErrorCode.POLICY_VIOLATION

    def __init__(self, message: str) -> None:
        super().__init__(f"SLA policy error: {message}")


class SlaBreachError(SlaError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, definition_id: str, actual_value: float, threshold: float) -> None:
        self.definition_id = definition_id
        self.actual_value = actual_value
        self.threshold = threshold
        msg = (
            f"SLA breached for {definition_id!r}: "
            f"value {actual_value} exceeds threshold {threshold}"
        )
        super().__init__(msg)


class SlaConfigError(SlaError):
    default_code: ErrorCode = ErrorCode.CONFIGURATION_INVALID

    def __init__(self, message: str) -> None:
        super().__init__(f"SLA configuration error: {message}")


__all__ = [
    "SlaBreachError",
    "SlaConfigError",
    "SlaDefinitionNotFoundError",
    "SlaError",
    "SlaMonitorNotFoundError",
    "SlaPolicyError",
    "SlaViolationError",
]
