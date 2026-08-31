"""FederatedIdentityProvider — manages identity providers, SSO sessions, and token exchange."""

from __future__ import annotations

from datetime import timedelta

from eaip.fedid.events import IdentityLinked, SSOSessionCreated, UserAuthenticated
from eaip.fedid.exceptions import AuthenticationFailedError, FederationError, ProviderNotFoundError
from eaip.fedid.models import (
    FederatedUser,
    FederationConfig,
    IdentityProvider,
    SSOSession,
    SSOStatus,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class FederatedIdentityProvider:
    """Central service for federated identity and SSO management."""

    def __init__(self, config: FederationConfig | None = None) -> None:
        self._config = config or FederationConfig()
        self._providers: dict[str, IdentityProvider] = {}
        self._users: dict[str, FederatedUser] = {}
        self._sessions: dict[str, SSOSession] = {}
        self._external_map: dict[str, str] = {}
        self._log = get_logger("eaip.fedid.provider")

    @property
    def config(self) -> FederationConfig:
        return self._config

    async def register_provider(self, provider: IdentityProvider) -> IdentityProvider:
        """Register a new identity provider."""
        self._providers[provider.id] = provider
        self._log.info("fedid.provider.registered", provider_id=provider.id, name=provider.name)
        return provider

    async def authenticate(self, idp_id: str, external_id: str, method: str = "") -> FederatedUser:
        """Authenticate a user via a federated identity provider."""
        provider = self._providers.get(idp_id)
        if provider is None:
            raise ProviderNotFoundError(f"Identity provider '{idp_id}' not found")
        if not provider.enabled:
            raise AuthenticationFailedError(f"Provider '{idp_id}' is disabled")

        user = await self._find_or_create_user(idp_id, external_id)
        event = UserAuthenticated(
            user_id=user.id,
            idp_id=idp_id,
            external_id=external_id,
            method=method,
        )
        self._log.info("fedid.user.authenticated", user_id=user.id, idp_id=idp_id)
        return user

    async def create_session(self, user_id: str, idp_id: str) -> SSOSession:
        """Create an SSO session for an authenticated user."""
        user = self._users.get(user_id)
        if user is None:
            raise FederationError(f"User '{user_id}' not found")
        if idp_id not in self._providers:
            raise ProviderNotFoundError(f"Identity provider '{idp_id}' not found")

        import uuid

        session = SSOSession(
            id=f"sess_{uuid.uuid4().hex[:12]}_{user_id}",
            user_id=user_id,
            idp_id=idp_id,
            expires_at=utc_now() + timedelta(seconds=self._config.session_ttl_seconds),
        )
        self._sessions[session.id] = session
        self._trim_sessions(user_id)

        event = SSOSessionCreated(
            session_id=session.id,
            user_id=user_id,
            idp_id=idp_id,
            ttl_seconds=self._config.session_ttl_seconds,
        )
        self._log.info("fedid.session.created", session_id=session.id, user_id=user_id)
        return session

    async def link_identity(self, user_id: str, idp_id: str, external_id: str) -> FederatedUser:
        """Link an external identity to a local user."""
        if idp_id not in self._providers:
            raise ProviderNotFoundError(f"Identity provider '{idp_id}' not found")

        user = FederatedUser(
            id=user_id,
            external_id=external_id,
            idp_id=idp_id,
        )
        self._users[user_id] = user
        self._external_map[f"{idp_id}:{external_id}"] = user_id

        event = IdentityLinked(
            user_id=user_id,
            idp_id=idp_id,
            external_id=external_id,
            details={"provider_name": self._providers[idp_id].name},
        )
        self._log.info("fedid.identity.linked", user_id=user_id, idp_id=idp_id)
        return user

    async def exchange_token(self, session_id: str) -> SSOSession:
        """Exchange an SSO session token for a new session."""
        session = self._sessions.get(session_id)
        if session is None:
            raise FederationError(f"Session '{session_id}' not found")
        if session.status != SSOStatus.ACTIVE:
            raise FederationError(f"Session '{session_id}' is {session.status.value}")
        if utc_now() > session.expires_at:
            expired = session.model_copy(update={"status": SSOStatus.EXPIRED}, deep=True)
            self._sessions[session_id] = expired
            raise FederationError(f"Session '{session_id}' has expired")

        import uuid

        new_session = SSOSession(
            id=f"sess_{uuid.uuid4().hex[:12]}_{session.user_id}",
            user_id=session.user_id,
            idp_id=session.idp_id,
            expires_at=utc_now() + timedelta(seconds=self._config.session_ttl_seconds),
        )
        self._sessions[new_session.id] = new_session
        self._log.info("fedid.token.exchanged", old_session=session_id, new_session=new_session.id)
        return new_session

    async def validate_session(self, session_id: str) -> SSOSession:
        """Validate an SSO session."""
        session = self._sessions.get(session_id)
        if session is None:
            raise FederationError(f"Session '{session_id}' not found")
        if session.status != SSOStatus.ACTIVE:
            raise FederationError(f"Session '{session_id}' is {session.status.value}")
        if utc_now() > session.expires_at:
            expired = session.model_copy(update={"status": SSOStatus.EXPIRED}, deep=True)
            self._sessions[session_id] = expired
            raise FederationError(f"Session '{session_id}' has expired")
        return session

    async def revoke_session(self, session_id: str) -> None:
        """Revoke an SSO session."""
        session = self._sessions.get(session_id)
        if session is None:
            raise FederationError(f"Session '{session_id}' not found")
        revoked = session.model_copy(update={"status": SSOStatus.REVOKED}, deep=True)
        self._sessions[session_id] = revoked
        self._log.info("fedid.session.revoked", session_id=session_id)

    async def get_provider(self, idp_id: str) -> IdentityProvider:
        """Retrieve an identity provider by ID."""
        provider = self._providers.get(idp_id)
        if provider is None:
            raise ProviderNotFoundError(f"Identity provider '{idp_id}' not found")
        return provider

    async def list_providers(self) -> list[IdentityProvider]:
        """List all registered identity providers."""
        return list(self._providers.values())

    async def get_user(self, user_id: str) -> FederatedUser:
        """Retrieve a federated user by ID."""
        user = self._users.get(user_id)
        if user is None:
            raise FederationError(f"User '{user_id}' not found")
        return user

    async def list_sessions(self, user_id: str | None = None) -> list[SSOSession]:
        """List all SSO sessions, optionally filtered by user."""
        if user_id is None:
            return list(self._sessions.values())
        return [s for s in self._sessions.values() if s.user_id == user_id]

    async def _find_or_create_user(self, idp_id: str, external_id: str) -> FederatedUser:
        """Find an existing user or create a new one."""
        key = f"{idp_id}:{external_id}"
        existing_uid = self._external_map.get(key)
        if existing_uid is not None and existing_uid in self._users:
            return self._users[existing_uid]

        import uuid

        user_id = f"usr_{uuid.uuid4().hex[:8]}"
        user = FederatedUser(
            id=user_id,
            external_id=external_id,
            idp_id=idp_id,
        )
        self._users[user_id] = user
        self._external_map[key] = user_id
        return user

    def _trim_sessions(self, user_id: str) -> None:
        """Remove excess sessions for a user."""
        user_sessions = [s for s in self._sessions.values() if s.user_id == user_id]
        if len(user_sessions) > self._config.max_sessions_per_user:
            sorted_sessions = sorted(user_sessions, key=lambda s: s.created_at)
            for old in sorted_sessions[: -self._config.max_sessions_per_user]:
                del self._sessions[old.id]


__all__ = ["FederatedIdentityProvider"]
