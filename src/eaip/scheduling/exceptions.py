from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class SchedulingError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class ScheduleNotFoundError(SchedulingError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, schedule_id: str, tenant_id: str | None = None) -> None:
        self.schedule_id = schedule_id
        self.tenant_id = tenant_id
        msg = f"schedule not found: {schedule_id!r}"
        if tenant_id is not None:
            msg += f" (tenant {tenant_id!r})"
        super().__init__(msg)


class ScheduleConflictError(SchedulingError):
    default_code: ErrorCode = ErrorCode.REGISTRY_DUPLICATE

    def __init__(self, schedule_id: str, message: str = "") -> None:
        self.schedule_id = schedule_id
        super().__init__(message or f"schedule conflict: {schedule_id!r}")


class ScheduleValidationError(SchedulingError):
    default_code: ErrorCode = ErrorCode.VALIDATION_FAILED

    def __init__(self, message: str, field: str | None = None) -> None:
        self.field = field
        super().__init__(message, context={"field": field} if field else {})


__all__ = [
    "ScheduleConflictError",
    "ScheduleNotFoundError",
    "ScheduleValidationError",
    "SchedulingError",
]
