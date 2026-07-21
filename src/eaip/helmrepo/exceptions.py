"""Exception hierarchy for Helm chart repository."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class HelmError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class ChartNotFoundError(HelmError):
    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "ChartNotFoundError",
    "HelmError",
]
