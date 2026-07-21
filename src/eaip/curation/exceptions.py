"""Exception hierarchy for the knowledge curation service."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class CurationError(EAIPError):
    """Base exception for curation-related failures."""

    default_code = ErrorCode.INTERNAL_ERROR


class SubmissionNotFoundError(CurationError):
    """Raised when a content submission is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "CurationError",
    "SubmissionNotFoundError",
]
