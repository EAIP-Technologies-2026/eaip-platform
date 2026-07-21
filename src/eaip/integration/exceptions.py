"""Exception hierarchy for the integration hub."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class IntegrationError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ConnectorNotFoundError(IntegrationError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class RouteNotFoundError(IntegrationError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class MessageDeliveryError(IntegrationError):
    default_code = ErrorCode.GATEWAY_ERROR
    default_severity = ErrorSeverity.ERROR


class TransformationError(IntegrationError):
    default_code = ErrorCode.VALIDATION_FAILED
    default_severity = ErrorSeverity.ERROR


class WebhookDeliveryError(IntegrationError):
    default_code = ErrorCode.GATEWAY_ERROR
    default_severity = ErrorSeverity.ERROR


__all__ = [
    "ConnectorNotFoundError",
    "IntegrationError",
    "MessageDeliveryError",
    "RouteNotFoundError",
    "TransformationError",
    "WebhookDeliveryError",
]
