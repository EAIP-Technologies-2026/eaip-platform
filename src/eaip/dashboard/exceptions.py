"""Exception hierarchy for the custom dashboard builder."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class DashboardError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class DashboardNotFoundError(DashboardError):
    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "DashboardError",
    "DashboardNotFoundError",
]
