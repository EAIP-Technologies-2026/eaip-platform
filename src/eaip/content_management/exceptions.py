"""Exception hierarchy for content management."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class ContentManagementError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ContentNotFoundError(ContentManagementError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING

    def __init__(self, item_id: str) -> None:
        self.item_id = item_id
        super().__init__(f"content item not found: {item_id!r}")


class ContentValidationError(ContentManagementError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.WARNING

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ContentPublishError(ContentManagementError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR

    def __init__(self, item_id: str, message: str) -> None:
        self.item_id = item_id
        super().__init__(f"publish failed for item {item_id!r}: {message}")


class ContentReviewError(ContentManagementError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR

    def __init__(self, item_id: str, message: str) -> None:
        self.item_id = item_id
        super().__init__(f"review failed for item {item_id!r}: {message}")


class ContentVersionError(ContentManagementError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR

    def __init__(self, item_id: str, message: str) -> None:
        self.item_id = item_id
        super().__init__(f"version error for item {item_id!r}: {message}")


class ContentSchedulingError(ContentManagementError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR

    def __init__(self, item_id: str, message: str) -> None:
        self.item_id = item_id
        super().__init__(f"scheduling failed for item {item_id!r}: {message}")


class ContentLocalizationError(ContentManagementError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR

    def __init__(self, item_id: str, message: str) -> None:
        self.item_id = item_id
        super().__init__(f"localization failed for item {item_id!r}: {message}")


class ContentPermissionError(ContentManagementError):
    default_code = ErrorCode.POLICY_VIOLATION
    default_severity = ErrorSeverity.WARNING

    def __init__(self, item_id: str, principal: str) -> None:
        self.item_id = item_id
        self.principal = principal
        super().__init__(f"permission denied for {principal!r} on item {item_id!r}")


__all__ = [
    "ContentLocalizationError",
    "ContentManagementError",
    "ContentNotFoundError",
    "ContentPermissionError",
    "ContentPublishError",
    "ContentReviewError",
    "ContentSchedulingError",
    "ContentValidationError",
    "ContentVersionError",
]
