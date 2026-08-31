"""Exception hierarchy for the credential rotator."""

from __future__ import annotations

from eaip.exceptions import EAIPError, ErrorCode


class CredRotError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class CredentialNotFoundError(CredRotError):
    default_code = ErrorCode.NOT_FOUND
