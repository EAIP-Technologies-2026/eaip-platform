"""Domain events for the token & authentication service."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.auth.models import AuthToken, IdentityProvider
from eaip.events.event import DomainEvent


class TokenCreated(DomainEvent):
    event_type: ClassVar[str] = "auth.token.created"
    token: AuthToken


class TokenValidated(DomainEvent):
    event_type: ClassVar[str] = "auth.token.validated"
    token_id: str
    valid: bool
    error: str = ""


class TokenExpired(DomainEvent):
    event_type: ClassVar[str] = "auth.token.expired"
    token_id: str
    subject: str
    token_type: str


class TokenRevoked(DomainEvent):
    event_type: ClassVar[str] = "auth.token.revoked"
    token_id: str
    subject: str
    reason: str = ""


class TokenRefreshed(DomainEvent):
    event_type: ClassVar[str] = "auth.token.refreshed"
    old_token_id: str
    new_token_id: str
    subject: str


class AuthenticationSucceeded(DomainEvent):
    event_type: ClassVar[str] = "auth.authentication.succeeded"
    request_id: str
    provider: str
    subject: str
    identity: dict[str, Any]


class AuthenticationFailed(DomainEvent):
    event_type: ClassVar[str] = "auth.authentication.failed"
    request_id: str
    provider: str
    error: str
    credentials_type: str = ""


class ProviderRegistered(DomainEvent):
    event_type: ClassVar[str] = "auth.provider.registered"
    provider: IdentityProvider


class ProviderUnregistered(DomainEvent):
    event_type: ClassVar[str] = "auth.provider.unregistered"
    provider_id: str
    provider_name: str


# ── Identity lifecycle events ───────────────────────────────────────


class UserLoggedIn(DomainEvent):
    event_type: ClassVar[str] = "auth.user.logged_in"
    user_id: str
    provider: str
    token_id: str
    refresh_token_id: str
    client_id: str = ""


class UserLoggedOut(DomainEvent):
    event_type: ClassVar[str] = "auth.user.logged_out"
    user_id: str
    token_id: str
    reason: str = "manual"


class UserSessionCreated(DomainEvent):
    event_type: ClassVar[str] = "auth.session.created"
    user_id: str
    token_id: str
    client_id: str = ""


class UserSessionExpired(DomainEvent):
    event_type: ClassVar[str] = "auth.session.expired"
    user_id: str
    token_id: str


class AllSessionsRevoked(DomainEvent):
    event_type: ClassVar[str] = "auth.all_sessions.revoked"
    user_id: str
    count: int = 0


class PermissionChanged(DomainEvent):
    event_type: ClassVar[str] = "auth.permission.changed"
    user_id: str
    permissions: tuple[str, ...] = ()


class WorkspaceChanged(DomainEvent):
    event_type: ClassVar[str] = "auth.workspace.changed"
    user_id: str
    workspace_id: str


__all__ = [
    "AllSessionsRevoked",
    "AuthenticationFailed",
    "AuthenticationSucceeded",
    "PermissionChanged",
    "ProviderRegistered",
    "ProviderUnregistered",
    "TokenCreated",
    "TokenExpired",
    "TokenRefreshed",
    "TokenRevoked",
    "TokenValidated",
    "UserLoggedIn",
    "UserLoggedOut",
    "UserSessionCreated",
    "UserSessionExpired",
    "WorkspaceChanged",
]
