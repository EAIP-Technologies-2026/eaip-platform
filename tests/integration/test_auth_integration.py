"""Integration tests for the full authentication flow.

Covers login, logout, refresh, expired sessions, revoked tokens,
concurrent sessions, and current user identity.
"""

from __future__ import annotations

import pytest

from eaip.auth.auth_providers import AuthenticationService
from eaip.auth.events import (
    AllSessionsRevoked,
    AuthenticationFailed,
    AuthenticationSucceeded,
    UserLoggedIn,
    UserLoggedOut,
    UserSessionCreated,
)
from eaip.auth.models import AuthenticationRequest, TokenStatus
from eaip.events.bus import EventBus


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def auth_service(event_bus: EventBus) -> AuthenticationService:
    return AuthenticationService(secret="integration-test-secret", event_bus=event_bus)


class TestAuthIntegration:
    """End-to-end authentication flow."""

    async def test_login_and_get_current_user(self, auth_service: AuthenticationService) -> None:
        """Login should return tokens and allow getting current user."""
        req = AuthenticationRequest(
            id="req1",
            provider="mock",
            credentials={"username": "alice", "password": "pass"},
        )
        result = await auth_service.authenticate(req)
        assert result.success
        assert result.token
        assert result.refresh_token
        assert result.identity["sub"] == "alice"

        user = await auth_service.get_current_user(result.token)
        assert user is not None
        assert user["sub"] == "alice"

    async def test_login_invalid_credentials(self, auth_service: AuthenticationService) -> None:
        """Invalid credentials should fail."""
        req = AuthenticationRequest(
            id="req2",
            provider="mock",
            credentials={"username": "alice", "password": "invalid"},
        )
        result = await auth_service.authenticate(req)
        assert not result.success
        assert "Invalid credentials" in result.error

    async def test_logout_revokes_token(self, auth_service: AuthenticationService) -> None:
        """Logout should revoke the access token."""
        req = AuthenticationRequest(
            id="req3",
            provider="mock",
            credentials={"username": "bob", "password": "pass"},
        )
        login = await auth_service.authenticate(req)
        assert login.success

        await auth_service.logout(login.token, user_id="bob")

        user = await auth_service.get_current_user(login.token)
        assert user is None

    async def test_refresh_token_flow(self, auth_service: AuthenticationService) -> None:
        """Refresh token should return new access and refresh tokens."""
        req = AuthenticationRequest(
            id="req4",
            provider="mock",
            credentials={"username": "carol", "password": "pass"},
        )
        login = await auth_service.authenticate(req)
        assert login.success
        assert login.refresh_token

        new_access, new_refresh = await auth_service.token_service.refresh_token(
            login.refresh_token
        )
        assert new_access.status == TokenStatus.ACTIVE
        assert new_refresh.status == TokenStatus.ACTIVE

    async def test_revoked_token_rejected(self, auth_service: AuthenticationService) -> None:
        """A revoked token should be rejected."""
        req = AuthenticationRequest(
            id="req5",
            provider="mock",
            credentials={"username": "dave", "password": "pass"},
        )
        login = await auth_service.authenticate(req)
        assert login.success

        token_string = login.token
        valid_before, _, _ = await auth_service.token_service.validate_token(token_string)
        assert valid_before

        from eaip.auth.tokens import _parse_jwt

        payload = _parse_jwt(token_string, auth_service.token_service._secret)
        token_id = payload.get("jti", "")
        assert token_id

        await auth_service.token_service.revoke_token(token_id)

        valid_after, _, _ = await auth_service.token_service.validate_token(token_string)
        assert not valid_after

    async def test_refresh_with_rotation(self, auth_service: AuthenticationService) -> None:
        """Refresh rotation should invalidate the old refresh token."""
        req = AuthenticationRequest(
            id="req6",
            provider="mock",
            credentials={"username": "eve", "password": "pass"},
        )
        login = await auth_service.authenticate(req)
        assert login.refresh_token

        new_access, new_refresh = await auth_service.token_service.refresh_token(
            login.refresh_token
        )
        assert new_access is not None
        assert new_refresh is not None

        valid, _, _ = await auth_service.token_service.validate_token(login.refresh_token)
        assert not valid

    async def test_logout_all_sessions(self, auth_service: AuthenticationService) -> None:
        """Logout all sessions should revoke every token for a user."""
        req1 = AuthenticationRequest(
            id="req7a",
            provider="mock",
            credentials={"username": "frank", "password": "pass"},
        )
        req2 = AuthenticationRequest(
            id="req7b",
            provider="mock",
            credentials={"username": "frank", "password": "pass"},
        )
        login1 = await auth_service.authenticate(req1)
        login2 = await auth_service.authenticate(req2)
        assert login1.success
        assert login2.success

        count = await auth_service.logout_all_sessions("frank")

        user1 = await auth_service.get_current_user(login1.token)
        user2 = await auth_service.get_current_user(login2.token)
        assert user1 is None
        assert user2 is None


class TestAuthEvents:
    """Verify identity events are published during auth operations."""

    async def test_login_publishes_events(self) -> None:
        events: list[str] = []
        bus = EventBus()

        async def collect(event: object) -> None:
            events.append(type(event).__name__)

        bus.subscribe(AuthenticationSucceeded, collect)
        bus.subscribe(UserLoggedIn, collect)
        bus.subscribe(UserSessionCreated, collect)

        svc = AuthenticationService(secret="event-test-secret", event_bus=bus)
        req = AuthenticationRequest(
            id="evt1",
            provider="mock",
            credentials={"username": "grace", "password": "pass"},
        )
        await svc.authenticate(req)
        assert "AuthenticationSucceeded" in events
        assert "UserLoggedIn" in events
        assert "UserSessionCreated" in events

    async def test_logout_publishes_event(self) -> None:
        events: list[str] = []
        bus = EventBus()

        async def collect(event: object) -> None:
            events.append(type(event).__name__)

        bus.subscribe(UserLoggedOut, collect)

        svc = AuthenticationService(secret="event-test-secret-2", event_bus=bus)
        req = AuthenticationRequest(
            id="evt2",
            provider="mock",
            credentials={"username": "heidi", "password": "pass"},
        )
        login = await svc.authenticate(req)
        await svc.logout(login.token, user_id="heidi")
        assert "UserLoggedOut" in events

    async def test_login_failed_publishes_event(self) -> None:
        events: list[str] = []
        bus = EventBus()

        async def collect(event: object) -> None:
            events.append(type(event).__name__)

        bus.subscribe(AuthenticationFailed, collect)

        svc = AuthenticationService(secret="event-test-secret-3", event_bus=bus)
        req = AuthenticationRequest(
            id="evt3",
            provider="mock",
            credentials={"username": "ivan", "password": "invalid"},
        )
        await svc.authenticate(req)
        assert "AuthenticationFailed" in events

    async def test_logout_all_sessions_publishes_event(self) -> None:
        events: list[str] = []
        bus = EventBus()

        async def collect(event: object) -> None:
            events.append(type(event).__name__)

        bus.subscribe(AllSessionsRevoked, collect)

        svc = AuthenticationService(secret="event-test-secret-4", event_bus=bus)
        req = AuthenticationRequest(
            id="evt4",
            provider="mock",
            credentials={"username": "judy", "password": "pass"},
        )
        await svc.authenticate(req)
        await svc.logout_all_sessions("judy")
        assert "AllSessionsRevoked" in events

    async def test_get_current_user_missing_token(
        self, auth_service: AuthenticationService
    ) -> None:
        """get_current_user should return None for invalid token."""
        user = await auth_service.get_current_user("invalid-token-string")
        assert user is None
