"""Exception hierarchy for the platform audit viewer."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class AuditViewerError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class EntryNotFoundError(AuditViewerError):
    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "AuditViewerError",
    "EntryNotFoundError",
]
