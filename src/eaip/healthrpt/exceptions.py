"""Exception hierarchy for the enterprise health reporter."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ReporterError(EAIPError):
    """Base exception for health reporter errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class ComponentNotFoundError(ReporterError):
    """Raised when a component is not found in the health reporter."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "ComponentNotFoundError",
    "ReporterError",
]
