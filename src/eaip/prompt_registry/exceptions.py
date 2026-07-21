"""Prompt Registry exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class PromptRegistryError(EAIPError):
    """Base exception for Prompt Registry errors."""

    default_code = ErrorCode.UNKNOWN


class PromptNotFoundError(PromptRegistryError):
    """Raised when a requested prompt definition is not found."""

    default_code = ErrorCode.NOT_FOUND


class PromptVersionNotFoundError(PromptRegistryError):
    """Raised when a requested prompt version is not found."""

    default_code = ErrorCode.NOT_FOUND


class PromptValidationError(PromptRegistryError):
    """Raised when a prompt or version fails validation."""

    default_code = ErrorCode.VALIDATION_FAILED


class PromptPublishError(PromptRegistryError):
    """Raised when a prompt cannot be published."""

    default_code = ErrorCode.UNKNOWN


class PromptVersionConflictError(PromptRegistryError):
    """Raised when a version conflict occurs (e.g. duplicate version string)."""

    default_code = ErrorCode.REGISTRY_DUPLICATE


class PromptTemplateError(PromptRegistryError):
    """Raised when a prompt template contains errors."""

    default_code = ErrorCode.VALIDATION_FAILED


class PromptApprovalError(PromptRegistryError):
    """Raised when a prompt approval operation fails."""

    default_code = ErrorCode.POLICY_VIOLATION


class PromptArchivalError(PromptRegistryError):
    """Raised when a prompt archival operation fails."""

    default_code = ErrorCode.UNKNOWN


__all__ = [
    "PromptApprovalError",
    "PromptArchivalError",
    "PromptNotFoundError",
    "PromptPublishError",
    "PromptRegistryError",
    "PromptTemplateError",
    "PromptValidationError",
    "PromptVersionConflictError",
    "PromptVersionNotFoundError",
]
