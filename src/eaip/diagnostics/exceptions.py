"""Exception hierarchy for diagnostics subsystem."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class DiagnosticsError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class ProbeExecutionError(DiagnosticsError):
    default_code = ErrorCode.INTERNAL_ERROR


__all__ = [
    "DiagnosticsError",
    "ProbeExecutionError",
]
