"""Exception hierarchy for the enterprise template engine."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class TemplateEngineError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class TemplateNotFoundError(TemplateEngineError):
    default_code = ErrorCode.NOT_FOUND


class TemplateRenderError(TemplateEngineError):
    default_code = ErrorCode.INTERNAL_ERROR


__all__ = [
    "TemplateEngineError",
    "TemplateNotFoundError",
    "TemplateRenderError",
]
