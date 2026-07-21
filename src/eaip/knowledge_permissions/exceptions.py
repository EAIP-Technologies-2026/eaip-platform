"""Knowledge permission exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class KnowledgePermissionError(EAIPError):
    """Base for knowledge permission failures."""

    default_code = ErrorCode.POLICY_VIOLATION


class PermissionNotFoundError(KnowledgePermissionError):
    """Raised when a permission is not found."""

    default_code = ErrorCode.NOT_FOUND


class PermissionDeniedError(KnowledgePermissionError):
    """Raised when access is denied by a permission check."""

    default_code = ErrorCode.POLICY_VIOLATION


class PermissionConfigError(KnowledgePermissionError):
    """Raised when permission configuration is invalid."""

    default_code = ErrorCode.CONFIGURATION_INVALID


class PermissionEvaluationError(KnowledgePermissionError):
    """Raised when permission evaluation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class PermissionRoleError(KnowledgePermissionError):
    """Raised when a role operation fails."""

    default_code = ErrorCode.NOT_FOUND


class PermissionAssignmentError(KnowledgePermissionError):
    """Raised when a role assignment operation fails."""

    default_code = ErrorCode.VALIDATION_FAILED


class PermissionAuditError(KnowledgePermissionError):
    """Raised when an audit operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


__all__ = [
    "KnowledgePermissionError",
    "PermissionAssignmentError",
    "PermissionAuditError",
    "PermissionConfigError",
    "PermissionDeniedError",
    "PermissionEvaluationError",
    "PermissionNotFoundError",
    "PermissionRoleError",
]
