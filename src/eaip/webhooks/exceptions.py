"""Exception hierarchy for the webhook dispatcher."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class WebhookError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class EndpointNotFoundError(WebhookError):
    default_code = ErrorCode.ENDPOINT_NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class DeliveryError(WebhookError):
    default_code = ErrorCode.GATEWAY_ERROR
    default_severity = ErrorSeverity.ERROR


class SignatureError(WebhookError):
    default_code = ErrorCode.AUTH_FAILED
    default_severity = ErrorSeverity.WARNING


class RateLimitExceededError(WebhookError):
    default_code = ErrorCode.RATE_LIMITED
    default_severity = ErrorSeverity.WARNING


class MaxRetriesExceededError(WebhookError):
    default_code = ErrorCode.GATEWAY_ERROR
    default_severity = ErrorSeverity.ERROR


__all__ = [
    "DeliveryError",
    "EndpointNotFoundError",
    "MaxRetriesExceededError",
    "RateLimitExceededError",
    "SignatureError",
    "WebhookError",
]
