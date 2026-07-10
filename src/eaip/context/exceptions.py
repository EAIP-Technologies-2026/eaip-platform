"""Context & Prompt Intelligence exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ContextError(EAIPError):
    """Base exception for Context & Prompt Intelligence errors."""

    default_code = ErrorCode.UNKNOWN


class PromptNotFoundError(ContextError):
    """Raised when a requested prompt is not found."""

    default_code = ErrorCode.NOT_FOUND


class TemplateRenderError(ContextError):
    """Raised when a prompt template cannot be rendered."""

    default_code = ErrorCode.VALIDATION_FAILED


class ContextAssemblyError(ContextError):
    """Raised when context assembly fails."""

    default_code = ErrorCode.UNKNOWN


class CompressionError(ContextError):
    """Raised when context compression fails."""

    default_code = ErrorCode.UNKNOWN


class TemplatePolicyError(ContextError):
    """Raised when a template violates a policy check."""

    default_code = ErrorCode.POLICY_VIOLATION


__all__ = [
    "CompressionError",
    "ContextAssemblyError",
    "ContextError",
    "PromptNotFoundError",
    "TemplatePolicyError",
    "TemplateRenderError",
]
