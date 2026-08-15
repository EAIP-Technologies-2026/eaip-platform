"""Authentication service — provider abstraction, in-memory identity store, and mock provider."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from eaip.auth.events import (
    AllSessionsRevoked,
    AuthenticationFailed,
    AuthenticationSucceeded,
    ProviderRegistered,
    ProviderUnregistered,
    UserLoggedIn,
    UserLoggedOut,
    UserSessionCreated,
)
from eaip.auth.exceptions import AuthenticationError, ProviderNotFoundError
from eaip.auth.models import (
    AuthenticationRequest,
    AuthenticationResult,
    IdentityProvider,
    ProviderType,
    TokenType,
)
from eaip.auth.tokens import TokenService, _parse_jwt
from eaip.events.bus import EventBus
from eaip.ports.secret_provider import SecretProviderPort


class _InMemoryIdentityStore:
    def __init__(self) -> None:
        self._identities: dict[str, dict[str, Any]] = {}

    def add(self, subject: str, identity: dict[str, Any]) -> None:
        self._identities[subject] = identity

    def get(self, subject: str) -> dict[str, Any] | None:
        return self._identities.get(subject)

    def remove(self, subject: str) -> None:
        self._identities.pop(subject, None)

    def list(self) -> Sequence[dict[str, Any]]:
        return list(self._identities.values())


class MockIdentityProvider:
    def __init__(self, provider: IdentityProvider) -> None:
        self._provider = provider

    @property
    def id(self) -> str:
        return self._provider.id

    @property
    def provider(self) -> IdentityProvider:
        return self._provider

    async def authenticate(self, request: AuthenticationRequest) -> AuthenticationResult:
        username = request.credentials.get("username", "")
        password = request.credentials.get("password", "")

        if not username or not password:
            return AuthenticationResult(
                id=request.id,
                success=False,
                error="Missing credentials",
                provider=request.provider,
            )

        if password == "invalid":
            return AuthenticationResult(
                id=request.id,
                success=False,
                error="Invalid credentials",
                provider=request.provider,
            )

        identity = {
            "sub": username,
            "name": username,
            "email": f"{username}@example.com",
            "provider": request.provider,
            "roles": ["admin", "user"],
        }

        return AuthenticationResult(
            id=request.id,
            success=True,
            token="",
            identity=identity,
            claims=identity,
            provider=request.provider,
        )


class AuthenticationService:
    def __init__(
        self,
        token_service: TokenService | None = None,
        secret: str | None = None,
        secret_provider: SecretProviderPort | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._event_bus = event_bus
        if token_service is not None:
            self._token_service = token_service
        else:
            self._token_service = TokenService(
                secret=secret, secret_provider=secret_provider, event_bus=event_bus
            )
        self._providers: dict[str, IdentityProvider] = {}
        self._mock_instances: dict[str, MockIdentityProvider] = {}
        self._identity_store = _InMemoryIdentityStore()

        mock_provider = IdentityProvider(
            id="mock",
            name="Mock Provider",
            type=ProviderType.LOCAL,
            enabled=True,
            priority=0,
        )
        self._providers["mock"] = mock_provider
        self._mock_instances["mock"] = MockIdentityProvider(mock_provider)

    @property
    def token_service(self) -> TokenService:
        return self._token_service

    async def authenticate(self, request: AuthenticationRequest) -> AuthenticationResult:
        provider = self._providers.get(request.provider)
        if provider is None:
            raise ProviderNotFoundError(f"Provider '{request.provider}' not found")

        if not provider.enabled:
            return AuthenticationResult(
                id=request.id,
                success=False,
                error=f"Provider '{request.provider}' is disabled",
                provider=request.provider,
            )

        mock = self._mock_instances.get(request.provider)
        if mock is None:
            await self._emit(
                AuthenticationFailed(
                    request_id=request.id,
                    provider=request.provider,
                    error="No handler for provider",
                )
            )
            return AuthenticationResult(
                id=request.id,
                success=False,
                error="No authentication handler for provider",
                provider=request.provider,
            )

        result = await mock.authenticate(request)

        if result.success:
            subject = result.identity.get("sub", "")
            self._identity_store.add(subject, result.identity)

            token = await self._token_service.create_token(
                subject=subject,
                type=TokenType.ACCESS,
                claims=result.claims,
            )
            refresh = await self._token_service.create_token(
                subject=subject,
                type=TokenType.REFRESH,
            )

            token_str = await self._token_service.get_token_string(token.id) or ""
            refresh_str = await self._token_service.get_token_string(refresh.id) or ""

            result = AuthenticationResult(
                id=request.id,
                success=True,
                token=token_str,
                refresh_token=refresh_str,
                identity=result.identity,
                claims=result.claims,
                provider=request.provider,
            )

            await self._emit(
                AuthenticationSucceeded(
                    request_id=request.id,
                    provider=request.provider,
                    subject=subject,
                    identity=result.identity,
                )
            )
            await self._emit(
                UserLoggedIn(
                    user_id=subject,
                    provider=request.provider,
                    token_id=token.id,
                    refresh_token_id=refresh.id,
                    client_id=request.client_id,
                )
            )
            await self._emit(
                UserSessionCreated(
                    user_id=subject,
                    token_id=token.id,
                    client_id=request.client_id,
                )
            )
        else:
            await self._emit(
                AuthenticationFailed(
                    request_id=request.id,
                    provider=request.provider,
                    error=result.error,
                )
            )

        return result

    async def logout(self, token_string: str, user_id: str | None = None) -> None:
        """Log out a user by revoking their token.

        Args:
            token_string: The access token to revoke.
            user_id: Optional user identifier for event publishing.
        """
        valid, _, _ = await self._token_service.validate_token(token_string)
        if not valid:
            return
        try:
            payload = _parse_jwt(token_string, self._token_service._secret)
        except Exception:
            return
        token_id = payload.get("jti", "")
        if not token_id:
            return
        await self._token_service.revoke_token(token_id)
        subject = user_id or payload.get("sub", "unknown")
        await self._emit(
            UserLoggedOut(
                user_id=subject,
                token_id=token_id,
                reason="manual",
            )
        )

    async def get_current_user(self, token_string: str) -> dict[str, Any] | None:
        """Return the current user's identity from a token string.

        Args:
            token_string: The access token string.

        Returns:
            The user identity dict, or ``None`` if invalid.
        """
        valid, claims, error = await self._token_service.validate_token(token_string)
        if not valid:
            return None
        sub = claims.get("sub", "")
        identity = self._identity_store.get(sub) or {}
        return {**identity, **claims}

    async def logout_all_sessions(self, user_id: str) -> int:
        """Revoke all active sessions for a user.

        Args:
            user_id: The user identifier.

        Returns:
            The number of revoked sessions.
        """
        before = self._token_service._tokens.size
        await self._token_service.revoke_all_user_tokens(user_id)
        after = self._token_service._tokens.size
        count = before - after
        await self._emit(AllSessionsRevoked(user_id=user_id, count=count))
        return count

    async def get_session_token_ids(self, user_id: str) -> list[str]:
        """Return all active token IDs for a user."""
        ids: list[str] = []
        async for token in self._token_service._tokens.iter_all():
            if token.subject == user_id and token.status.value == "active":
                ids.append(token.id)
        return ids

    async def register_provider(self, provider: IdentityProvider) -> None:
        self._providers[provider.id] = provider
        self._mock_instances[provider.id] = MockIdentityProvider(provider)
        await self._emit(ProviderRegistered(provider=provider))

    async def get_provider(self, provider_id: str) -> IdentityProvider | None:
        return self._providers.get(provider_id)

    async def list_providers(self) -> Sequence[IdentityProvider]:
        return list(self._providers.values())

    async def remove_provider(self, provider_id: str) -> None:
        provider = self._providers.pop(provider_id, None)
        self._mock_instances.pop(provider_id, None)
        if provider is not None:
            await self._emit(
                ProviderUnregistered(
                    provider_id=provider.id,
                    provider_name=provider.name,
                )
            )

    async def validate_session(self, token_string: str) -> bool:
        valid, _claims, _error = await self._token_service.validate_token(token_string)
        return valid

    async def get_identity(self, token_string: str) -> dict[str, Any]:
        valid, claims, error = await self._token_service.validate_token(token_string)
        if not valid:
            raise AuthenticationError(f"Cannot get identity: {error}")
        sub = claims.get("sub", "")
        identity = self._identity_store.get(sub) or {}
        return {**identity, **claims}

    async def _emit(self, event: Any) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)


__all__ = [
    "AuthenticationService",
    "MockIdentityProvider",
    "_InMemoryIdentityStore",
]
