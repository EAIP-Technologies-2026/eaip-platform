"""Exception hierarchy for the notification orchestration runtime."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class NotificationOrchestrationError(EAIPError):
    """Base exception for the notification orchestration package."""

    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class OrchestrationRuleNotFoundError(NotificationOrchestrationError):
    """Raised when a requested orchestration rule does not exist."""

    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, rule_id: str) -> None:
        """Initialize the error with the missing rule identifier."""
        self.rule_id = rule_id
        super().__init__(f"Orchestration rule not found: {rule_id!r}")


class OrchestrationExecutionError(NotificationOrchestrationError):
    """Raised when an orchestration execution fails."""

    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        """Initialize the execution error with a descriptive message."""
        super().__init__(f"Orchestration execution error: {message}")


class EscalationError(NotificationOrchestrationError):
    """Raised when an escalation operation fails."""

    default_code: ErrorCode = ErrorCode.GATEWAY_ERROR

    def __init__(self, message: str) -> None:
        """Initialize the escalation error with a descriptive message."""
        super().__init__(f"Escalation error: {message}")


class DigestDeliveryError(NotificationOrchestrationError):
    """Raised when digest delivery fails."""

    default_code: ErrorCode = ErrorCode.GATEWAY_ERROR

    def __init__(self, message: str) -> None:
        """Initialize the digest delivery error with a descriptive message."""
        super().__init__(f"Digest delivery error: {message}")


class NotificationRoutingError(NotificationOrchestrationError):
    """Raised when notification routing fails."""

    default_code: ErrorCode = ErrorCode.GATEWAY_ERROR

    def __init__(self, message: str) -> None:
        """Initialize the routing error with a descriptive message."""
        super().__init__(f"Notification routing error: {message}")


__all__ = [
    "DigestDeliveryError",
    "EscalationError",
    "NotificationOrchestrationError",
    "NotificationRoutingError",
    "OrchestrationExecutionError",
    "OrchestrationRuleNotFoundError",
]
