"""Domain events raised by the admin_api package."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from eaip.events.event import DomainEvent


class ApiDefinitionCreated(DomainEvent):
    """Published when a new API definition is created."""

    event_type: ClassVar[str] = "eaip.admin_api.api_definition.created"

    api_definition_id: str
    name: str


class ApiDefinitionUpdated(DomainEvent):
    """Published when an API definition is updated."""

    event_type: ClassVar[str] = "eaip.admin_api.api_definition.updated"

    api_definition_id: str
    name: str


class ApiDefinitionDeleted(DomainEvent):
    """Published when an API definition is deleted."""

    event_type: ClassVar[str] = "eaip.admin_api.api_definition.deleted"

    api_definition_id: str
    name: str


class ApiVersionReleased(DomainEvent):
    """Published when an API version is released."""

    event_type: ClassVar[str] = "eaip.admin_api.api_version.released"

    version_id: str
    api_definition_id: str
    version_string: str


class ApiVersionDeprecated(DomainEvent):
    """Published when an API version is deprecated."""

    event_type: ClassVar[str] = "eaip.admin_api.api_version.deprecated"

    version_id: str
    api_definition_id: str
    version_string: str
    sunset_at: datetime | None = None


class ApiVersionRetired(DomainEvent):
    """Published when an API version is retired."""

    event_type: ClassVar[str] = "eaip.admin_api.api_version.retired"

    version_id: str
    api_definition_id: str
    version_string: str


class ApiEndpointAdded(DomainEvent):
    """Published when an endpoint is added to an API version."""

    event_type: ClassVar[str] = "eaip.admin_api.api_endpoint.added"

    endpoint_id: str
    api_definition_id: str
    api_version_id: str
    path: str
    method: str


class ApiEndpointRemoved(DomainEvent):
    """Published when an endpoint is removed from an API version."""

    event_type: ClassVar[str] = "eaip.admin_api.api_endpoint.removed"

    endpoint_id: str
    api_definition_id: str
    api_version_id: str


class ApiEndpointUpdated(DomainEvent):
    """Published when an endpoint is updated."""

    event_type: ClassVar[str] = "eaip.admin_api.api_endpoint.updated"

    endpoint_id: str
    api_definition_id: str
    api_version_id: str
    path: str
    method: str


class ApiRequestReceived(DomainEvent):
    """Published when an API request is received."""

    event_type: ClassVar[str] = "eaip.admin_api.api_request.received"

    request_id: str
    endpoint_id: str
    method: str
    path: str
    api_client_id: str | None = None


class ApiResponseSent(DomainEvent):
    """Published when an API response is sent."""

    event_type: ClassVar[str] = "eaip.admin_api.api_response.sent"

    response_id: str
    request_id: str
    status_code: int
    duration_ms: float


class ApiClientCreated(DomainEvent):
    """Published when a new API client is created."""

    event_type: ClassVar[str] = "eaip.admin_api.api_client.created"

    client_id: str
    name: str
    client_id_str: str


class ApiClientUpdated(DomainEvent):
    """Published when an API client is updated."""

    event_type: ClassVar[str] = "eaip.admin_api.api_client.updated"

    client_id: str
    name: str


class ApiClientDeleted(DomainEvent):
    """Published when an API client is deleted."""

    event_type: ClassVar[str] = "eaip.admin_api.api_client.deleted"

    client_id: str
    name: str


class ApiClientActivated(DomainEvent):
    """Published when an API client is activated."""

    event_type: ClassVar[str] = "eaip.admin_api.api_client.activated"

    client_id: str


class ApiClientDeactivated(DomainEvent):
    """Published when an API client is deactivated."""

    event_type: ClassVar[str] = "eaip.admin_api.api_client.deactivated"

    client_id: str


class ApiClientTokenRotated(DomainEvent):
    """Published when an API client token is rotated."""

    event_type: ClassVar[str] = "eaip.admin_api.api_client.token_rotated"

    client_id: str
    token_id: str


class ApiUsageMetricCollected(DomainEvent):
    """Published when usage metrics are collected."""

    event_type: ClassVar[str] = "eaip.admin_api.usage_metric.collected"

    metric_id: str
    endpoint_id: str
    request_count: int
    response_count: int


class ApiAuditLogged(DomainEvent):
    """Published when an audit entry is logged."""

    event_type: ClassVar[str] = "eaip.admin_api.audit.logged"

    entry_id: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    outcome: str


class ApiDocumentationGenerated(DomainEvent):
    """Published when API documentation is generated."""

    event_type: ClassVar[str] = "eaip.admin_api.documentation.generated"

    documentation_id: str
    api_definition_id: str
    api_version_id: str
    format: str


__all__ = [
    "ApiAuditLogged",
    "ApiClientActivated",
    "ApiClientCreated",
    "ApiClientDeactivated",
    "ApiClientDeleted",
    "ApiClientTokenRotated",
    "ApiClientUpdated",
    "ApiDefinitionCreated",
    "ApiDefinitionDeleted",
    "ApiDefinitionUpdated",
    "ApiDocumentationGenerated",
    "ApiEndpointAdded",
    "ApiEndpointRemoved",
    "ApiEndpointUpdated",
    "ApiRequestReceived",
    "ApiResponseSent",
    "ApiUsageMetricCollected",
    "ApiVersionDeprecated",
    "ApiVersionReleased",
    "ApiVersionRetired",
]
