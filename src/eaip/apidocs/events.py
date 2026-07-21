"""API Documentation domain events."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class DocGenerated(DomainEvent):
    event_type: ClassVar[str] = "eaip.apidocs.doc.generated"
    doc_id: str = ""
    source_version: str = ""
    format: str = ""


class DocPublished(DomainEvent):
    event_type: ClassVar[str] = "eaip.apidocs.doc.published"
    doc_id: str = ""
    source_version: str = ""
    format: str = ""


class ChangelogCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.apidocs.changelog.created"
    changelog_id: str = ""
    version: str = ""
    change_count: int = 0


class EndpointDocRegistered(DomainEvent):
    event_type: ClassVar[str] = "eaip.apidocs.endpoint.registered"
    endpoint_id: str = ""
    endpoint_path: str = ""
    method: str = ""


ApiDocsEvent = DocGenerated | DocPublished | ChangelogCreated | EndpointDocRegistered

__all__ = [
    "ApiDocsEvent",
    "ChangelogCreated",
    "DocGenerated",
    "DocPublished",
    "EndpointDocRegistered",
]
