"""Exception hierarchy for long-running workflows."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class LongRunningError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class WorkflowNotFoundError(LongRunningError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, workflow_id: str) -> None:
        self.workflow_id = workflow_id
        super().__init__(f"long-running workflow not found: {workflow_id!r}")


class WorkflowStatePersistenceError(LongRunningError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, workflow_id: str, message: str) -> None:
        self.workflow_id = workflow_id
        super().__init__(f"state persistence failed for {workflow_id!r}: {message}")


class WorkflowRecoveryError(LongRunningError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, workflow_id: str, message: str) -> None:
        self.workflow_id = workflow_id
        super().__init__(f"workflow recovery failed for {workflow_id!r}: {message}")


class WorkflowCheckpointError(LongRunningError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, workflow_id: str, message: str) -> None:
        self.workflow_id = workflow_id
        super().__init__(f"checkpoint failed for {workflow_id!r}: {message}")


class WorkflowContinuationError(LongRunningError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, workflow_id: str, message: str) -> None:
        self.workflow_id = workflow_id
        super().__init__(f"continuation failed for {workflow_id!r}: {message}")


class WorkflowHeartbeatTimeoutError(LongRunningError):
    default_code: ErrorCode = ErrorCode.PROVIDER_TIMEOUT

    def __init__(self, workflow_id: str, timeout_seconds: float) -> None:
        self.workflow_id = workflow_id
        self.timeout_seconds = timeout_seconds
        super().__init__(f"heartbeat timeout for {workflow_id!r} after {timeout_seconds}s")


class WorkflowExecutionTimeoutError(LongRunningError):
    default_code: ErrorCode = ErrorCode.PROVIDER_TIMEOUT

    def __init__(self, workflow_id: str, timeout_seconds: float) -> None:
        self.workflow_id = workflow_id
        self.timeout_seconds = timeout_seconds
        super().__init__(f"execution timeout for {workflow_id!r} after {timeout_seconds}s")


__all__ = [
    "LongRunningError",
    "WorkflowCheckpointError",
    "WorkflowContinuationError",
    "WorkflowExecutionTimeoutError",
    "WorkflowHeartbeatTimeoutError",
    "WorkflowNotFoundError",
    "WorkflowRecoveryError",
    "WorkflowStatePersistenceError",
]
