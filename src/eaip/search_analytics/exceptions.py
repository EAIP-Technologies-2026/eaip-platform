"""Search analytics exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class SearchAnalyticsError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class SearchAnalyticsConfigError(SearchAnalyticsError):
    default_code: ErrorCode = ErrorCode.CONFIGURATION_INVALID

    def __init__(self, message: str) -> None:
        super().__init__(message)


class SearchAnalyticsQueryError(SearchAnalyticsError):
    default_code: ErrorCode = ErrorCode.VALIDATION_FAILED

    def __init__(self, message: str) -> None:
        super().__init__(message)


class SearchAnalyticsReportError(SearchAnalyticsError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


class SearchAnalyticsDashboardError(SearchAnalyticsError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, message: str) -> None:
        super().__init__(message)


class SearchAnalyticsAlertError(SearchAnalyticsError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


class SearchMetricsCollectionError(SearchAnalyticsError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


__all__ = [
    "SearchAnalyticsAlertError",
    "SearchAnalyticsConfigError",
    "SearchAnalyticsDashboardError",
    "SearchAnalyticsError",
    "SearchAnalyticsQueryError",
    "SearchAnalyticsReportError",
    "SearchMetricsCollectionError",
]
