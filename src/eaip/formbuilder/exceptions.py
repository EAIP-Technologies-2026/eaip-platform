"""Exception hierarchy for form builder service."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class FormBuilderError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class FormNotFoundError(FormBuilderError):
    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "FormBuilderError",
    "FormNotFoundError",
]
