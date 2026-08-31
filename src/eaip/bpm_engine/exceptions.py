"""Exception hierarchy for the BPM engine."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class BpmError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ProcessDefinitionError(BpmError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.ERROR

    def __init__(self, message: str, process_key: str = "") -> None:
        self.process_key = process_key
        super().__init__(message)


class ProcessInstanceNotFoundError(BpmError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING

    def __init__(self, instance_id: str) -> None:
        self.instance_id = instance_id
        super().__init__(f"process instance not found: {instance_id!r}")


class ActivityExecutionError(BpmError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR

    def __init__(self, activity_id: str, message: str) -> None:
        self.activity_id = activity_id
        super().__init__(f"activity {activity_id!r} execution failed: {message}")


class GatewayEvaluationError(BpmError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.WARNING

    def __init__(self, gateway_id: str, message: str) -> None:
        self.gateway_id = gateway_id
        super().__init__(f"gateway {gateway_id!r} evaluation failed: {message}")


class SignalDeliveryError(BpmError):
    default_code = ErrorCode.GATEWAY_ERROR
    default_severity = ErrorSeverity.ERROR

    def __init__(self, signal_name: str, message: str) -> None:
        self.signal_name = signal_name
        super().__init__(f"signal {signal_name!r} delivery failed: {message}")


class MessageDeliveryError(BpmError):
    default_code = ErrorCode.GATEWAY_ERROR
    default_severity = ErrorSeverity.ERROR

    def __init__(self, message_name: str, message: str) -> None:
        self.message_name = message_name
        super().__init__(f"message {message_name!r} delivery failed: {message}")


class TimerCancelledError(BpmError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.WARNING

    def __init__(self, timer_id: str) -> None:
        self.timer_id = timer_id
        super().__init__(f"timer cancelled: {timer_id!r}")


__all__ = [
    "ActivityExecutionError",
    "BpmError",
    "GatewayEvaluationError",
    "MessageDeliveryError",
    "ProcessDefinitionError",
    "ProcessInstanceNotFoundError",
    "SignalDeliveryError",
    "TimerCancelledError",
]
