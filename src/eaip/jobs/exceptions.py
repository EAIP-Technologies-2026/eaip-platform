"""Job exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class JobError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class JobNotFoundError(JobError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"job not found: {job_id!r}")


class JobTimeoutError(JobError):
    default_code: ErrorCode = ErrorCode.PROVIDER_TIMEOUT

    def __init__(self, job_id: str, timeout_seconds: float) -> None:
        self.job_id = job_id
        self.timeout_seconds = timeout_seconds
        super().__init__(f"job {job_id!r} timed out after {timeout_seconds}s")


class JobValidationError(JobError):
    default_code: ErrorCode = ErrorCode.VALIDATION_FAILED

    def __init__(self, message: str) -> None:
        super().__init__(f"job validation error: {message}")


__all__ = [
    "JobError",
    "JobNotFoundError",
    "JobTimeoutError",
    "JobValidationError",
]
