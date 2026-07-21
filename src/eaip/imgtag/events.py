"""Domain events for image tag management."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class TagCreated(DomainEvent):
    """Emitted when a new image tag is created."""

    event_type: ClassVar[str] = "eaip.imgtag.tag.created"

    tag_id: str
    name: str
    repository: str
    digest: str


class TagUpdated(DomainEvent):
    """Emitted when an image tag is updated."""

    event_type: ClassVar[str] = "eaip.imgtag.tag.updated"

    tag_id: str
    name: str
    repository: str
    previous_digest: str
    new_digest: str


class TagDeleted(DomainEvent):
    """Emitted when an image tag is deleted."""

    event_type: ClassVar[str] = "eaip.imgtag.tag.deleted"

    tag_id: str
    name: str
    repository: str


class ManifestPushed(DomainEvent):
    """Emitted when a new image manifest is pushed."""

    event_type: ClassVar[str] = "eaip.imgtag.manifest.pushed"

    manifest_id: str
    repository: str
    digest: str
    size_bytes: int = Field(default=0)
    tags: tuple[str, ...] = Field(default=())
    pushed_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "ManifestPushed",
    "TagCreated",
    "TagDeleted",
    "TagUpdated",
]
