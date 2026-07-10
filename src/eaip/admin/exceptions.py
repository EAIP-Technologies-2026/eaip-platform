"""Admin-specific exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class AdminError(EAIPError):
    """Base exception for all admin-package errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class AdminActionError(AdminError):
    """Raised when an administrative action fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class ConfigNotFoundError(AdminError):
    """Raised when a requested configuration key does not exist."""

    default_code = ErrorCode.NOT_FOUND


class AuditQueryError(AdminError):
    """Raised when an audit log query fails."""

    default_code = ErrorCode.INTERNAL_ERROR
