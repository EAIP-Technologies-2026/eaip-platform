"""Tests for auth domain events."""

from __future__ import annotations

from datetime import UTC, datetime

from eaip.auth.events import (
    AuthenticationFailed,
    AuthenticationSucceeded,
    ProviderRegistered,
    ProviderUnregistered,
    TokenCreated,
    TokenExpired,
    TokenRefreshed,
    TokenRevoked,
    TokenValidated,
)
from eaip.auth.models import AuthToken, IdentityProvider, ProviderType, TokenType
from eaip.events.event import DomainEvent


class TestTokenCreated:
    def test_event_type(self) -> None:
        ts = datetime.now(UTC)
        token = AuthToken(
            id="t1",
            type=TokenType.ACCESS,
            issuer="eaip",
            subject="u1",
            expires_at=ts,
            token_hash="h",
        )
        event = TokenCreated(token=token)
        assert event.event_type == "auth.token.created"
        assert isinstance(event, DomainEvent)

    def test_token_content(self) -> None:
        ts = datetime.now(UTC)
        token = AuthToken(
            id="t1",
            type=TokenType.ACCESS,
            issuer="eaip",
            subject="u1",
            expires_at=ts,
            token_hash="h",
        )
        event = TokenCreated(token=token)
        assert event.token.id == "t1"
        assert event.token.subject == "u1"


class TestTokenValidated:
    def test_event_type(self) -> None:
        event = TokenValidated(token_id="t1", valid=True)
        assert event.event_type == "auth.token.validated"

    def test_valid_true(self) -> None:
        event = TokenValidated(token_id="t1", valid=True)
        assert event.valid is True
        assert event.error == ""

    def test_valid_false_with_error(self) -> None:
        event = TokenValidated(token_id="t1", valid=False, error="Token expired")
        assert event.valid is False
        assert event.error == "Token expired"


class TestTokenExpired:
    def test_event_type(self) -> None:
        event = TokenExpired(token_id="t1", subject="u1", token_type="access")
        assert event.event_type == "auth.token.expired"

    def test_fields(self) -> None:
        event = TokenExpired(token_id="t1", subject="alice", token_type="refresh")
        assert event.token_id == "t1"
        assert event.subject == "alice"
        assert event.token_type == "refresh"


class TestTokenRevoked:
    def test_event_type(self) -> None:
        event = TokenRevoked(token_id="t1", subject="u1")
        assert event.event_type == "auth.token.revoked"

    def test_fields(self) -> None:
        event = TokenRevoked(token_id="t1", subject="alice", reason="compromised")
        assert event.token_id == "t1"
        assert event.subject == "alice"
        assert event.reason == "compromised"

    def test_default_reason(self) -> None:
        event = TokenRevoked(token_id="t1", subject="u1")
        assert event.reason == ""


class TestTokenRefreshed:
    def test_event_type(self) -> None:
        event = TokenRefreshed(old_token_id="t1", new_token_id="t2", subject="u1")
        assert event.event_type == "auth.token.refreshed"

    def test_fields(self) -> None:
        event = TokenRefreshed(old_token_id="old1", new_token_id="new1", subject="alice")
        assert event.old_token_id == "old1"
        assert event.new_token_id == "new1"
        assert event.subject == "alice"


class TestAuthenticationSucceeded:
    def test_event_type(self) -> None:
        event = AuthenticationSucceeded(
            request_id="r1", provider="mock", subject="u1", identity={"sub": "u1"}
        )
        assert event.event_type == "auth.authentication.succeeded"

    def test_fields(self) -> None:
        event = AuthenticationSucceeded(
            request_id="req1",
            provider="mock",
            subject="alice",
            identity={"sub": "alice", "email": "alice@example.com"},
        )
        assert event.request_id == "req1"
        assert event.provider == "mock"
        assert event.subject == "alice"
        assert event.identity == {"sub": "alice", "email": "alice@example.com"}


class TestAuthenticationFailed:
    def test_event_type(self) -> None:
        event = AuthenticationFailed(request_id="r1", provider="mock", error="bad password")
        assert event.event_type == "auth.authentication.failed"

    def test_fields(self) -> None:
        event = AuthenticationFailed(
            request_id="req1",
            provider="mock",
            error="Invalid credentials",
            credentials_type="password",
        )
        assert event.request_id == "req1"
        assert event.provider == "mock"
        assert event.error == "Invalid credentials"
        assert event.credentials_type == "password"

    def test_default_credentials_type(self) -> None:
        event = AuthenticationFailed(request_id="r1", provider="mock", error="err")
        assert event.credentials_type == ""


class TestProviderRegistered:
    def test_event_type(self) -> None:
        p = IdentityProvider(id="p1", name="P1", type=ProviderType.LOCAL)
        event = ProviderRegistered(provider=p)
        assert event.event_type == "auth.provider.registered"

    def test_provider_content(self) -> None:
        p = IdentityProvider(id="ldap1", name="Corporate LDAP", type=ProviderType.LDAP)
        event = ProviderRegistered(provider=p)
        assert event.provider.id == "ldap1"
        assert event.provider.name == "Corporate LDAP"


class TestProviderUnregistered:
    def test_event_type(self) -> None:
        event = ProviderUnregistered(provider_id="p1", provider_name="P1")
        assert event.event_type == "auth.provider.unregistered"

    def test_fields(self) -> None:
        event = ProviderUnregistered(provider_id="ldap1", provider_name="Corporate LDAP")
        assert event.provider_id == "ldap1"
        assert event.provider_name == "Corporate LDAP"


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(TokenCreated, DomainEvent)
        assert issubclass(TokenValidated, DomainEvent)
        assert issubclass(TokenExpired, DomainEvent)
        assert issubclass(TokenRevoked, DomainEvent)
        assert issubclass(TokenRefreshed, DomainEvent)
        assert issubclass(AuthenticationSucceeded, DomainEvent)
        assert issubclass(AuthenticationFailed, DomainEvent)
        assert issubclass(ProviderRegistered, DomainEvent)
        assert issubclass(ProviderUnregistered, DomainEvent)
