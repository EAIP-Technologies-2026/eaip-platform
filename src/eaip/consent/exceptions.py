"""Exception hierarchy for consent and privacy management."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ConsentError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class ConsentNotFoundError(ConsentError):
    default_code = ErrorCode.NOT_FOUND


class ConsentRevokedError(ConsentError):
    default_code = ErrorCode.POLICY_VIOLATION


class DataSubjectRequestError(ConsentError):
    default_code = ErrorCode.INTERNAL_ERROR


__all__ = [
    "ConsentError",
    "ConsentNotFoundError",
    "ConsentRevokedError",
    "DataSubjectRequestError",
]
