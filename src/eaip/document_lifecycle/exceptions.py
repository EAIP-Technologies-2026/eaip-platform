"""Exception hierarchy for the document lifecycle."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class DocumentLifecycleError(EAIPError):
    """Base exception for document lifecycle errors."""

    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class DocumentNotFoundError(DocumentLifecycleError):
    """Raised when a document is not found."""

    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING

    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        super().__init__(f"document not found: {document_id!r}")


class DocumentVersionError(DocumentLifecycleError):
    """Raised when a document version operation fails."""

    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.ERROR

    def __init__(self, document_id: str, message: str) -> None:
        self.document_id = document_id
        super().__init__(f"version error for document {document_id!r}: {message}")


class DocumentStatusError(DocumentLifecycleError):
    """Raised when an invalid status transition is attempted."""

    default_code = ErrorCode.LIFECYCLE_FORBIDDEN
    default_severity = ErrorSeverity.ERROR

    def __init__(self, document_id: str, current: str, target: str) -> None:
        self.document_id = document_id
        self.current = current
        self.target = target
        msg = f"cannot transition document {document_id!r} from {current!r} to {target!r}"
        super().__init__(msg)


class DocumentApprovalError(DocumentLifecycleError):
    """Raised when a document approval operation fails."""

    default_code = ErrorCode.LIFECYCLE_FORBIDDEN
    default_severity = ErrorSeverity.ERROR

    def __init__(self, document_id: str, message: str) -> None:
        self.document_id = document_id
        super().__init__(f"approval error for document {document_id!r}: {message}")


class DocumentReviewError(DocumentLifecycleError):
    """Raised when a document review operation fails."""

    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.ERROR

    def __init__(self, document_id: str, message: str) -> None:
        self.document_id = document_id
        super().__init__(f"review error for document {document_id!r}: {message}")


class DocumentExpiryError(DocumentLifecycleError):
    """Raised when a document expiry operation fails."""

    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.ERROR

    def __init__(self, document_id: str, message: str) -> None:
        self.document_id = document_id
        super().__init__(f"expiry error for document {document_id!r}: {message}")


class DocumentRetentionError(DocumentLifecycleError):
    """Raised when a document retention operation fails."""

    default_code = ErrorCode.POLICY_VIOLATION
    default_severity = ErrorSeverity.ERROR

    def __init__(self, document_id: str, message: str) -> None:
        self.document_id = document_id
        super().__init__(f"retention error for document {document_id!r}: {message}")


class DocumentArchiveError(DocumentLifecycleError):
    """Raised when a document archive operation fails."""

    default_code = ErrorCode.LIFECYCLE_FORBIDDEN
    default_severity = ErrorSeverity.ERROR

    def __init__(self, document_id: str, message: str) -> None:
        self.document_id = document_id
        super().__init__(f"archive error for document {document_id!r}: {message}")


__all__ = [
    "DocumentApprovalError",
    "DocumentArchiveError",
    "DocumentExpiryError",
    "DocumentLifecycleError",
    "DocumentNotFoundError",
    "DocumentRetentionError",
    "DocumentReviewError",
    "DocumentStatusError",
    "DocumentVersionError",
]
