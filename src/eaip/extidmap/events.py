"""Domain events for external identity mapping."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class IdentityMapped(DomainEvent):
    """Emitted when an identity is mapped."""

    event_type: ClassVar[str] = "eaip.extidmap.identity.mapped"

    local_uid: str
    external_uid: str
    external_idp: str


class MappingUpdated(DomainEvent):
    """Emitted when an identity mapping is updated."""

    event_type: ClassVar[str] = "eaip.extidmap.mapping.updated"

    mapping_id: str
    changes: dict[str, Any]


class IdentityUnlinked(DomainEvent):
    """Emitted when an identity mapping is unlinked/revoked."""

    event_type: ClassVar[str] = "eaip.extidmap.identity.unlinked"

    mapping_id: str
    local_uid: str
    external_idp: str


__all__ = [
    "IdentityMapped",
    "IdentityUnlinked",
    "MappingUpdated",
]
