"""Workflow Template Library exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class TemplateError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class TemplateNotFoundError(TemplateError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, template_id: str) -> None:
        self.template_id = template_id
        super().__init__(f"workflow template not found: {template_id!r}")


class CategoryNotFoundError(TemplateError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, category_id: str) -> None:
        self.category_id = category_id
        super().__init__(f"template category not found: {category_id!r}")


class TemplateImportError(TemplateError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, template_id: str, message: str) -> None:
        self.template_id = template_id
        super().__init__(f"template import failed for {template_id!r}: {message}")


__all__ = [
    "CategoryNotFoundError",
    "TemplateError",
    "TemplateImportError",
    "TemplateNotFoundError",
]
