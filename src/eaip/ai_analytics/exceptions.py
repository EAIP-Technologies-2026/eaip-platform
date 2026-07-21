"""AI Analytics exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class AiAnalyticsError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class AiAnalyticsConfigError(AiAnalyticsError):
    default_code: ErrorCode = ErrorCode.CONFIGURATION_INVALID

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AiAnalyticsMetricError(AiAnalyticsError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AiAnalyticsReportError(AiAnalyticsError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AiAnalyticsDashboardError(AiAnalyticsError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AiAnalyticsExportError(AiAnalyticsError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AiAnalyticsQueryError(AiAnalyticsError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AiAnomalyDetectionError(AiAnalyticsError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


__all__ = [
    "AiAnalyticsConfigError",
    "AiAnalyticsDashboardError",
    "AiAnalyticsError",
    "AiAnalyticsExportError",
    "AiAnalyticsMetricError",
    "AiAnalyticsQueryError",
    "AiAnalyticsReportError",
    "AiAnomalyDetectionError",
]
