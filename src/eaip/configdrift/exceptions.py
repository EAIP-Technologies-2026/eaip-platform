"""Exception hierarchy for the configuration drift detection service."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class DriftDetectionError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class SnapshotNotFoundError(DriftDetectionError):
    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "DriftDetectionError",
    "SnapshotNotFoundError",
]
