"""Tests for auth models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.auth.models import (
    AuthenticationRequest,
    AuthenticationResult,
    AuthToken,
    IdentityProvider,
    ProviderType,
    TokenConfig,
    TokenStatus,
    TokenType,
)


class TestAuthToken:
    def test_minimal(self) -> None:
        ts = datetime.now(UTC)
        t = AuthToken(
            id="tok1",
            type=TokenType.ACCESS,
            issuer="eaip",
            subject="user1",
            expires_at=ts,
            token_hash="abc123",
        )
        assert t.id == "tok1"
        assert t.type == TokenType.ACCESS
        assert t.audience == ()
        assert t.claims == {}
        assert t.status == TokenStatus.ACTIVE
        assert t.metadata == {}
        assert t.not_before is None

    def test_frozen(self) -> None:
        ts = datetime.now(UTC)
        t = AuthToken(
            id="tok1",
            type=TokenType.ACCESS,
            issuer="eaip",
            subject="u1",
            expires_at=ts,
            token_hash="h",
        )
        with pytest.raises(ValidationError):
            t.status = TokenStatus.EXPIRED

    def test_extra_forbidden(self) -> None:
        ts = datetime.now(UTC)
        with pytest.raises(ValidationError):
            AuthToken(
                id="tok1",
                type=TokenType.ACCESS,
                issuer="eaip",
                subject="u1",
                expires_at=ts,
                token_hash="h",
                unknown=True,
            )

    def test_all_types_and_statuses(self) -> None:
        ts = datetime.now(UTC)
        for typ in TokenType:
            t = AuthToken(
                id="tok1", type=typ, issuer="eaip", subject="u1", expires_at=ts, token_hash="h"
            )
            assert t.type == typ
        for st in TokenStatus:
            t = AuthToken(
                id="tok1",
                type=TokenType.ACCESS,
                issuer="eaip",
                subject="u1",
                expires_at=ts,
                token_hash="h",
                status=st,
            )
            assert t.status == st

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        nbf = datetime.now(UTC)
        t = AuthToken(
            id="tok1",
            type=TokenType.API,
            issuer="system",
            subject="service-account",
            audience=("eaip", "ext-api"),
            claims={"role": "admin"},
            issued_at=ts,
            expires_at=ts,
            not_before=nbf,
            token_hash="hash123",
            metadata={"env": "prod"},
            status=TokenStatus.ACTIVE,
        )
        assert t.audience == ("eaip", "ext-api")
        assert t.claims == {"role": "admin"}
        assert t.not_before == nbf
        assert t.metadata == {"env": "prod"}


class TestTokenConfig:
    def test_defaults(self) -> None:
        c = TokenConfig()
        assert c.access_token_ttl_seconds == 900
        assert c.refresh_token_ttl_seconds == 86_400
        assert c.issuer == "eaip"
        assert c.audience == ("eaip",)
        assert c.signing_algorithm == "HS256"
        assert c.secret_key_ref == "eaip-auth-secret"
        assert c.enable_refresh_rotation is True
        assert c.enable_revocation is True

    def test_custom(self) -> None:
        c = TokenConfig(
            access_token_ttl_seconds=1800,
            refresh_token_ttl_seconds=172_800,
            issuer="myapp",
            audience=("myapp", "admin"),
            signing_algorithm="HS512",
            secret_key_ref="custom-secret",
            enable_refresh_rotation=False,
            enable_revocation=False,
        )
        assert c.access_token_ttl_seconds == 1800
        assert c.refresh_token_ttl_seconds == 172_800
        assert c.issuer == "myapp"
        assert c.audience == ("myapp", "admin")
        assert c.signing_algorithm == "HS512"
        assert c.enable_refresh_rotation is False
        assert c.enable_revocation is False

    def test_frozen(self) -> None:
        c = TokenConfig()
        with pytest.raises(ValidationError):
            c.issuer = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            TokenConfig(unknown=True)


class TestAuthenticationRequest:
    def test_minimal(self) -> None:
        r = AuthenticationRequest(id="req1", provider="mock")
        assert r.credentials == {}
        assert r.client_id == ""
        assert r.redirect_uri == ""
        assert r.scope == ()
        assert r.metadata == {}

    def test_frozen(self) -> None:
        r = AuthenticationRequest(id="req1", provider="mock")
        with pytest.raises(ValidationError):
            r.provider = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            AuthenticationRequest(id="req1", provider="mock", bad=True)

    def test_full(self) -> None:
        r = AuthenticationRequest(
            id="req1",
            provider="oidc",
            credentials={"username": "alice", "password": "s3cret"},
            client_id="web-app",
            redirect_uri="https://app.example.com/callback",
            scope=("openid", "profile", "email"),
            metadata={"ip": "10.0.0.1"},
        )
        assert r.credentials == {"username": "alice", "password": "s3cret"}
        assert r.client_id == "web-app"
        assert r.redirect_uri == "https://app.example.com/callback"
        assert r.scope == ("openid", "profile", "email")
        assert r.metadata == {"ip": "10.0.0.1"}


class TestAuthenticationResult:
    def test_minimal(self) -> None:
        r = AuthenticationResult(id="res1", success=True)
        assert r.token == ""
        assert r.refresh_token == ""
        assert r.identity == {}
        assert r.claims == {}
        assert r.error == ""
        assert r.provider == ""
        assert r.metadata == {}

    def test_frozen(self) -> None:
        r = AuthenticationResult(id="res1", success=True)
        with pytest.raises(ValidationError):
            r.success = False

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            AuthenticationResult(id="res1", success=True, bad=True)

    def test_failure(self) -> None:
        r = AuthenticationResult(
            id="res1", success=False, error="Invalid credentials", provider="mock"
        )
        assert r.success is False
        assert r.error == "Invalid credentials"
        assert r.provider == "mock"

    def test_full_success(self) -> None:
        r = AuthenticationResult(
            id="res1",
            success=True,
            token="jwt.eyJzdWIiOiJhbGljZSJ9.signature",
            refresh_token="refresh.jwt.signature",
            identity={"sub": "alice", "name": "Alice"},
            claims={"sub": "alice", "role": "user"},
            provider="mock",
            metadata={"login_method": "password"},
        )
        assert r.token.startswith("jwt")
        assert r.identity == {"sub": "alice", "name": "Alice"}
        assert r.metadata == {"login_method": "password"}


class TestIdentityProvider:
    def test_minimal(self) -> None:
        p = IdentityProvider(id="p1", name="LDAP", type=ProviderType.LDAP)
        assert p.config == {}
        assert p.enabled is True
        assert p.priority == 0
        assert p.metadata == {}

    def test_frozen(self) -> None:
        p = IdentityProvider(id="p1", name="P1", type=ProviderType.LOCAL)
        with pytest.raises(ValidationError):
            p.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            IdentityProvider(id="p1", name="P1", type=ProviderType.LOCAL, bad=True)

    def test_all_types(self) -> None:
        for pt in ProviderType:
            p = IdentityProvider(id="p1", name=pt.value, type=pt)
            assert p.type == pt

    def test_disabled_with_priority(self) -> None:
        p = IdentityProvider(
            id="p1",
            name="Backup",
            type=ProviderType.OAUTH2,
            enabled=False,
            priority=10,
            metadata={"backup": True},
        )
        assert p.enabled is False
        assert p.priority == 10
        assert p.metadata == {"backup": True}
