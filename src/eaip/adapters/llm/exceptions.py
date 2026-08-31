"""LLMAdapter-specific exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class LLMAdapterError(EAIPError):
    """Base for LLMAdapter-related failures."""

    default_code = ErrorCode.PROVIDER_UNAVAILABLE


class ToolExecutionError(LLMAdapterError):
    """Raised when a tool called by the LLM fails during execution."""

    default_code = ErrorCode.INTERNAL_ERROR


class MaxToolRoundsError(LLMAdapterError):
    """Raised when the tool-calling loop exceeds the maximum round count."""

    default_code = ErrorCode.INTERNAL_ERROR


__all__ = [
    "LLMAdapterError",
    "MaxToolRoundsError",
    "ToolExecutionError",
]
