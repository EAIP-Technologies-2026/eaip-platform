"""Workflow exceptions — structured error types for workflow execution."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class WorkflowError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class WorkflowNotFoundError(WorkflowError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, workflow_id: str) -> None:
        self.workflow_id = workflow_id
        super().__init__(f"workflow not found: {workflow_id!r}")


class StepExecutionError(WorkflowError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, step_id: str, message: str) -> None:
        self.step_id = step_id
        super().__init__(f"step {step_id!r} failed: {message}")


class ApprovalTimeoutError(WorkflowError):
    default_code: ErrorCode = ErrorCode.PROVIDER_TIMEOUT

    def __init__(self, step_id: str, timeout_seconds: float) -> None:
        self.step_id = step_id
        self.timeout_seconds = timeout_seconds
        super().__init__(f"approval step {step_id!r} timed out after {timeout_seconds}s")


class CircularWorkflowError(WorkflowError):
    default_code: ErrorCode = ErrorCode.DEPENDENCY_CYCLE

    def __init__(self, message: str = "") -> None:
        super().__init__(message or "circular workflow dependency detected")


class InvalidWorkflowError(WorkflowError):
    default_code: ErrorCode = ErrorCode.VALIDATION_FAILED

    def __init__(self, message: str) -> None:
        super().__init__(f"invalid workflow: {message}")


class AgentDelegationError(WorkflowError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, agent_id: str, message: str) -> None:
        self.agent_id = agent_id
        super().__init__(f"agent delegation failed for {agent_id!r}: {message}")


class WorkflowTimeoutError(WorkflowError):
    default_code: ErrorCode = ErrorCode.PROVIDER_TIMEOUT

    def __init__(self, workflow_id: str, timeout_seconds: float) -> None:
        self.workflow_id = workflow_id
        self.timeout_seconds = timeout_seconds
        super().__init__(f"workflow {workflow_id!r} timed out after {timeout_seconds}s")


class ParallelExecutionError(WorkflowError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, group_id: str, message: str) -> None:
        self.group_id = group_id
        super().__init__(f"parallel group {group_id!r} failed: {message}")


class ChildWorkflowError(WorkflowError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, child_run_id: str, message: str) -> None:
        self.child_run_id = child_run_id
        super().__init__(f"child workflow {child_run_id!r} failed: {message}")


class DurableExecutionError(WorkflowError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, run_id: str, message: str) -> None:
        self.run_id = run_id
        super().__init__(f"durable execution failed for {run_id!r}: {message}")


__all__ = [
    "AgentDelegationError",
    "ApprovalTimeoutError",
    "ChildWorkflowError",
    "CircularWorkflowError",
    "DurableExecutionError",
    "InvalidWorkflowError",
    "ParallelExecutionError",
    "StepExecutionError",
    "WorkflowError",
    "WorkflowNotFoundError",
    "WorkflowTimeoutError",
]
