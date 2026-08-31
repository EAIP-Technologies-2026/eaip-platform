"""Analytics exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class AnalyticsError(EAIPError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR


class MetricNotFoundError(AnalyticsError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, metric_id: str) -> None:
        self.metric_id = metric_id
        super().__init__(f"metric not found: {metric_id!r}")


class ReportError(AnalyticsError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


class DashboardNotFoundError(AnalyticsError):
    default_code: ErrorCode = ErrorCode.NOT_FOUND

    def __init__(self, dashboard_id: str) -> None:
        self.dashboard_id = dashboard_id
        super().__init__(f"dashboard not found: {dashboard_id!r}")


class AnalyticsQueryError(AnalyticsError):
    default_code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)


__all__ = [
    "AnalyticsError",
    "AnalyticsQueryError",
    "DashboardNotFoundError",
    "MetricNotFoundError",
    "ReportError",
]
