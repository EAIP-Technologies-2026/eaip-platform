"""Department-management-specific exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class DepartmentError(EAIPError):
    """Base exception for all department-management errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class DepartmentNotFoundError(DepartmentError):
    """Raised when a requested department does not exist."""

    default_code = ErrorCode.NOT_FOUND


class DepartmentConfigError(DepartmentError):
    """Raised when a department configuration is invalid."""

    default_code = ErrorCode.CONFIGURATION_INVALID


class DepartmentMemberError(DepartmentError):
    """Raised when a member operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class DepartmentHierarchyError(DepartmentError):
    """Raised when a hierarchy operation is invalid."""

    default_code = ErrorCode.VALIDATION_FAILED


class DepartmentBudgetError(DepartmentError):
    """Raised when a budget operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class DepartmentResourceError(DepartmentError):
    """Raised when a resource operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR
