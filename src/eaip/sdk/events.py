"""Domain events raised by the SDK package."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from eaip.events.event import DomainEvent


class SdkCreated(DomainEvent):
    """Published after a new SDK definition is created."""

    event_type: ClassVar[str] = "eaip.sdk.created"

    sdk_id: str
    name: str
    language: str
    version: str


class SdkPublished(DomainEvent):
    """Published after an SDK is published."""

    event_type: ClassVar[str] = "eaip.sdk.published"

    sdk_id: str
    version: str
    timestamp: datetime | None = None


class SdkDeprecated(DomainEvent):
    """Published after an SDK is deprecated."""

    event_type: ClassVar[str] = "eaip.sdk.deprecated"

    sdk_id: str
    version: str
    timestamp: datetime | None = None


class SdkBuildStarted(DomainEvent):
    """Published when an SDK build starts."""

    event_type: ClassVar[str] = "eaip.sdk.build_started"

    build_id: str
    sdk_id: str
    version: str


class SdkBuildCompleted(DomainEvent):
    """Published when an SDK build completes successfully."""

    event_type: ClassVar[str] = "eaip.sdk.build_completed"

    build_id: str
    sdk_id: str
    version: str
    duration_ms: int = 0
    artifact_url: str = ""


class SdkBuildFailed(DomainEvent):
    """Published when an SDK build fails."""

    event_type: ClassVar[str] = "eaip.sdk.build_failed"

    build_id: str
    sdk_id: str
    version: str
    error: str = ""


class ClientCreated(DomainEvent):
    """Published after a new API client is created."""

    event_type: ClassVar[str] = "eaip.sdk.client_created"

    client_id: str
    sdk_id: str
    name: str


class ClientRevoked(DomainEvent):
    """Published after an API client is revoked."""

    event_type: ClassVar[str] = "eaip.sdk.client_revoked"

    client_id: str
    sdk_id: str


class ClientExpired(DomainEvent):
    """Published after an API client expires."""

    event_type: ClassVar[str] = "eaip.sdk.client_expired"

    client_id: str
    sdk_id: str
