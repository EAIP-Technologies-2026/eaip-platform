"""Exception hierarchy for the metering and usage service."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class MeteringError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class MetricNotFoundError(MeteringError):
    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "MeteringError",
    "MetricNotFoundError",
]
