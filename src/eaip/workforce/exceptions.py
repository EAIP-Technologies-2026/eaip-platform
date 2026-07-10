"""Workforce exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class WorkforceError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class WorkerNotFoundError(WorkforceError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, worker_id: str) -> None:
        self.worker_id = worker_id
        super().__init__(f"worker not found: {worker_id!r}")


class WorkerBusyError(WorkforceError):
    default_code: ErrorCode = ErrorCode.RATE_LIMITED

    def __init__(self, worker_id: str, max_concurrent: int) -> None:
        self.worker_id = worker_id
        self.max_concurrent = max_concurrent
        super().__init__(f"worker {worker_id!r} busy (max {max_concurrent} concurrent runs)")


class AssignmentError(WorkforceError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, assignment_id: str, message: str) -> None:
        self.assignment_id = assignment_id
        super().__init__(f"assignment {assignment_id!r} failed: {message}")


__all__ = [
    "AssignmentError",
    "WorkerBusyError",
    "WorkerNotFoundError",
    "WorkforceError",
]
