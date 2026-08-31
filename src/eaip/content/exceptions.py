"""Exception hierarchy for the content registry."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class ContentError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ContentNotFoundError(ContentError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING

    def __init__(self, item_id: str) -> None:
        self.item_id = item_id
        super().__init__(f"content item not found: {item_id!r}")


class VersionNotFoundError(ContentError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING

    def __init__(self, item_id: str, version: str) -> None:
        self.item_id = item_id
        self.version = version
        super().__init__(f"version {version!r} not found for item {item_id!r}")


class WorkflowNotFoundError(ContentError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING

    def __init__(self, workflow_id: str) -> None:
        self.workflow_id = workflow_id
        super().__init__(f"publishing workflow not found: {workflow_id!r}")


class PublishingError(ContentError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR

    def __init__(self, item_id: str, message: str) -> None:
        self.item_id = item_id
        super().__init__(f"publishing failed for item {item_id!r}: {message}")


__all__ = [
    "ContentError",
    "ContentNotFoundError",
    "PublishingError",
    "VersionNotFoundError",
    "WorkflowNotFoundError",
]
