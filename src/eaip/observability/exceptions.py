from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class ObservabilityError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class DashboardNotFoundError(ObservabilityError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class AlertRuleNotFoundError(ObservabilityError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class SloNotFoundError(ObservabilityError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class NotificationFailedError(ObservabilityError):
    default_code = ErrorCode.GATEWAY_ERROR
    default_severity = ErrorSeverity.ERROR


__all__ = [
    "AlertRuleNotFoundError",
    "DashboardNotFoundError",
    "NotificationFailedError",
    "ObservabilityError",
    "SloNotFoundError",
]
