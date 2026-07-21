"""API Documentation exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ApiDocsError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class DocGenerationError(ApiDocsError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(f"doc generation failed: {message}")


class DocNotFoundError(ApiDocsError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, doc_id: str) -> None:
        self.doc_id = doc_id
        super().__init__(f"documentation not found: {doc_id!r}")


class ChangelogError(ApiDocsError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(f"changelog error: {message}")


__all__ = [
    "ApiDocsError",
    "ChangelogError",
    "DocGenerationError",
    "DocNotFoundError",
]
