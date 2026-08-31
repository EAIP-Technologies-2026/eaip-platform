"""Organization-specific exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class OrganizationError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class OrganizationNotFoundError(OrganizationError):
    default_code = ErrorCode.NOT_FOUND


class OrganizationConfigError(OrganizationError):
    default_code = ErrorCode.CONFIGURATION_INVALID


class OrganizationMemberError(OrganizationError):
    default_code = ErrorCode.POLICY_VIOLATION


class OrganizationUnitError(OrganizationError):
    default_code = ErrorCode.POLICY_VIOLATION


class OrganizationPolicyError(OrganizationError):
    default_code = ErrorCode.POLICY_NOT_FOUND


class OrganizationDomainError(OrganizationError):
    default_code = ErrorCode.VALIDATION_FAILED


class OrganizationSubscriptionError(OrganizationError):
    default_code = ErrorCode.INTERNAL_ERROR
