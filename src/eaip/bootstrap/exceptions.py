"""Bootstrap exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class BootstrapError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class TemplateNotFoundError(BootstrapError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, template_id: str) -> None:
        self.template_id = template_id
        super().__init__(f"project template not found: {template_id!r}")


class ScaffoldError(BootstrapError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, template_id: str, message: str) -> None:
        self.template_id = template_id
        super().__init__(f"scaffold failed for template {template_id!r}: {message}")


class FileGenerationError(BootstrapError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, file_path: str, message: str) -> None:
        self.file_path = file_path
        super().__init__(f"file generation failed for {file_path!r}: {message}")


__all__ = [
    "BootstrapError",
    "FileGenerationError",
    "ScaffoldError",
    "TemplateNotFoundError",
]
