"""Exception hierarchy for Function as a Service runtime."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class FaaSError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class FunctionNotFoundError(FaaSError):
    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "FaaSError",
    "FunctionNotFoundError",
]
