"""Domain events raised by the Developer API & SDK Platform."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from eaip.events.event import DomainEvent


class ApiVersionRegistered(DomainEvent):
    """Published when a new API version is registered."""

    event_type: ClassVar[str] = "eaip.devplatform.api_version_registered"

    version_id: str
    version_string: str


class ApiVersionDeprecated(DomainEvent):
    """Published when an API version is deprecated."""

    event_type: ClassVar[str] = "eaip.devplatform.api_version_deprecated"

    version_id: str
    version_string: str
    sunset_at: datetime | None = None


class ApiVersionSunset(DomainEvent):
    """Published when an API version is sunset / retired."""

    event_type: ClassVar[str] = "eaip.devplatform.api_version_sunset"

    version_id: str
    version_string: str


class DeveloperKeyCreated(DomainEvent):
    """Published when a new developer key is created."""

    event_type: ClassVar[str] = "eaip.devplatform.developer_key_created"

    key_id: str
    developer_id: str
    name: str


class DeveloperKeyRevoked(DomainEvent):
    """Published when a developer key is revoked."""

    event_type: ClassVar[str] = "eaip.devplatform.developer_key_revoked"

    key_id: str
    developer_id: str


class DeveloperKeyExpired(DomainEvent):
    """Published when a developer key expires."""

    event_type: ClassVar[str] = "eaip.devplatform.developer_key_expired"

    key_id: str
    developer_id: str


class UsageRecorded(DomainEvent):
    """Published when an API usage record is captured."""

    event_type: ClassVar[str] = "eaip.devplatform.usage_recorded"

    record_id: str
    developer_id: str
    api_version: str
    endpoint: str
    status_code: int
    response_time_ms: float


class PlaygroundSessionCreated(DomainEvent):
    """Published when a playground session is created."""

    event_type: ClassVar[str] = "eaip.devplatform.playground_session_created"

    session_id: str
    developer_id: str
    endpoint_id: str


__all__ = [
    "ApiVersionDeprecated",
    "ApiVersionRegistered",
    "ApiVersionSunset",
    "DeveloperKeyCreated",
    "DeveloperKeyExpired",
    "DeveloperKeyRevoked",
    "PlaygroundSessionCreated",
    "UsageRecorded",
]
