"""Tenant-specific exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class TenantError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class TenantNotFoundError(TenantError):
    default_code = ErrorCode.NOT_FOUND


class TenantSuspendedError(TenantError):
    default_code = ErrorCode.POLICY_VIOLATION


class TenantQuotaExceededError(TenantError):
    default_code = ErrorCode.POLICY_VIOLATION


class UserNotFoundError(TenantError):
    default_code = ErrorCode.NOT_FOUND


class BillingError(TenantError):
    default_code = ErrorCode.INTERNAL_ERROR


class FeatureNotAvailableError(TenantError):
    default_code = ErrorCode.POLICY_VIOLATION
