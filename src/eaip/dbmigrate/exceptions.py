"""Exception hierarchy for database migration."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class DBMigrationError(EAIPError):
    """Base exception for database migration errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class ScriptNotFoundError(DBMigrationError):
    """Raised when a migration script is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "DBMigrationError",
    "ScriptNotFoundError",
]
