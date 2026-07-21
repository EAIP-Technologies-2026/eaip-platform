"""Exception hierarchy for the notification engine."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class NotificationError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ChannelNotAvailableError(NotificationError):
    default_code = ErrorCode.PROVIDER_UNAVAILABLE
    default_severity = ErrorSeverity.WARNING


class TemplateNotFoundError(NotificationError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class DeliveryFailedError(NotificationError):
    default_code = ErrorCode.GATEWAY_ERROR
    default_severity = ErrorSeverity.ERROR


class PreferenceNotFoundError(NotificationError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


__all__ = [
    "ChannelNotAvailableError",
    "DeliveryFailedError",
    "NotificationError",
    "PreferenceNotFoundError",
    "TemplateNotFoundError",
]
