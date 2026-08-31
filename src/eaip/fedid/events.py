"""Domain events for federated identity and SSO."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class UserAuthenticated(DomainEvent):
    """Emitted when a user is authenticated via federation."""

    event_type: ClassVar[str] = "eaip.fedid.user.authenticated"

    user_id: str
    idp_id: str
    external_id: str
    method: str = ""


class SSOSessionCreated(DomainEvent):
    """Emitted when an SSO session is created."""

    event_type: ClassVar[str] = "eaip.fedid.sso.session.created"

    session_id: str
    user_id: str
    idp_id: str
    ttl_seconds: int


class IdentityLinked(DomainEvent):
    """Emitted when an external identity is linked to a local user."""

    event_type: ClassVar[str] = "eaip.fedid.identity.linked"

    user_id: str
    idp_id: str
    external_id: str
    details: dict[str, Any]


__all__ = [
    "IdentityLinked",
    "SSOSessionCreated",
    "UserAuthenticated",
]
