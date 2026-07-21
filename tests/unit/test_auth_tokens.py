"""Tests for TokenService — creation, validation, refresh, revocation, and lifecycle."""

from __future__ import annotations

import pytest

from eaip.auth.exceptions import TokenInvalidError
from eaip.auth.models import TokenConfig, TokenStatus, TokenType
from eaip.auth.tokens import TokenService


class TestTokenService:
    @pytest.fixture
    def service(self) -> TokenService:
        return TokenService(secret="test-secret-key")

    @pytest.fixture
    def config(self) -> TokenConfig:
        return TokenConfig(
            access_token_ttl_seconds=300,
            refresh_token_ttl_seconds=600,
            issuer="test-issuer",
        )

    @pytest.fixture
    def configured_service(self, config: TokenConfig) -> TokenService:
        return TokenService(config=config, secret="test-secret")

    class TestCreateToken:
        async def test_create_access_token(self, service: TokenService) -> None:
            token = await service.create_token(
                subject="alice", type=TokenType.ACCESS, claims={"role": "user"}
            )
            assert token.subject == "alice"
            assert token.type == TokenType.ACCESS
            assert token.claims == {"role": "user"}
            assert token.status == TokenStatus.ACTIVE
            assert token.issuer == "eaip"
            assert token.id is not None

        async def test_create_refresh_token(self, service: TokenService) -> None:
            token = await service.create_token(subject="bob", type=TokenType.REFRESH)
            assert token.type == TokenType.REFRESH
            assert token.subject == "bob"

        async def test_custom_ttl(self, service: TokenService) -> None:
            token = await service.create_token(subject="alice", type=TokenType.ACCESS, ttl=60)
            diff = (token.expires_at - token.issued_at).total_seconds()
            assert abs(diff - 60) < 1

        async def test_default_ttl(self, configured_service: TokenService) -> None:
            token = await configured_service.create_token(subject="alice", type=TokenType.ACCESS)
            diff = (token.expires_at - token.issued_at).total_seconds()
            assert abs(diff - 300) < 1

        async def test_token_has_hash(self, service: TokenService) -> None:
            token = await service.create_token(subject="alice", type=TokenType.ACCESS)
            assert len(token.token_hash) == 64
            assert isinstance(token.token_hash, str)

        async def test_issued_at_is_utc(self, service: TokenService) -> None:
            token = await service.create_token(subject="alice", type=TokenType.ACCESS)
            assert token.issued_at.tzinfo is not None

    class TestValidateToken:
        async def test_valid_token(self, service: TokenService) -> None:
            token = await service.create_token(
                subject="alice", type=TokenType.ACCESS, claims={"role": "admin"}
            )
            token_str = await service.get_token_string(token.id)
            assert token_str is not None
            valid, claims, error = await service.validate_token(token_str)
            assert valid is True
            assert claims == {"role": "admin"}
            assert error == ""

        async def test_invalid_signature(self, service: TokenService) -> None:
            token = await service.create_token(subject="alice", type=TokenType.ACCESS)
            token_str = await service.get_token_string(token.id)
            assert token_str is not None
            parts = token_str.split(".")
            tampered = parts[0] + "." + parts[1] + ".invalidsig"
            valid, _claims, error = await service.validate_token(tampered)
            assert valid is False
            assert "signature" in error.lower()

        async def test_malformed_token(self, service: TokenService) -> None:
            valid, _claims, _error = await service.validate_token("not.a.jwt")
            assert valid is False

        async def test_expired_token(self, service: TokenService) -> None:
            token = await service.create_token(subject="alice", type=TokenType.ACCESS, ttl=-1)
            token_str = await service.get_token_string(token.id)
            assert token_str is not None
            valid, _claims, error = await service.validate_token(token_str)
            assert valid is False
            assert "expired" in error.lower()

        async def test_revoked_token(self, service: TokenService) -> None:
            token = await service.create_token(subject="alice", type=TokenType.ACCESS)
            await service.revoke_token(token.id)
            token_str = await service.get_token_string(token.id)
            assert token_str is not None
            valid, _claims, error = await service.validate_token(token_str)
            assert valid is False
            assert "revoked" in error.lower()

    class TestRefreshToken:
        async def test_refresh_success(self, configured_service: TokenService) -> None:
            refresh = await configured_service.create_token(subject="alice", type=TokenType.REFRESH)
            refresh_str = await configured_service.get_token_string(refresh.id)
            assert refresh_str is not None
            new_access, new_refresh = await configured_service.refresh_token(refresh_str)
            assert new_access.type == TokenType.ACCESS
            assert new_access.subject == "alice"
            assert new_refresh.type == TokenType.REFRESH

        async def test_refresh_with_rotation(self, configured_service: TokenService) -> None:
            config = TokenConfig(enable_refresh_rotation=True)
            svc = TokenService(config=config, secret="test")
            refresh = await svc.create_token(subject="alice", type=TokenType.REFRESH)
            refresh_str = await svc.get_token_string(refresh.id)
            assert refresh_str is not None
            await svc.refresh_token(refresh_str)
            stored = await svc.get_token(refresh.id)
            assert stored is not None
            assert stored.status == TokenStatus.REVOKED

        async def test_refresh_access_token_fails(self, service: TokenService) -> None:
            access = await service.create_token(subject="alice", type=TokenType.ACCESS)
            access_str = await service.get_token_string(access.id)
            assert access_str is not None
            with pytest.raises(TokenInvalidError, match="not a refresh token"):
                await service.refresh_token(access_str)

        async def test_refresh_invalid_token(self, service: TokenService) -> None:
            with pytest.raises(TokenInvalidError, match="Cannot refresh"):
                await service.refresh_token("invalid.refresh.token")

    class TestRevokeToken:
        async def test_revoke_token(self, service: TokenService) -> None:
            token = await service.create_token(subject="alice", type=TokenType.ACCESS)
            await service.revoke_token(token.id)
            stored = await service.get_token(token.id)
            assert stored is not None
            assert stored.status == TokenStatus.REVOKED

        async def test_revoke_nonexistent_token(self, service: TokenService) -> None:
            await service.revoke_token("nonexistent")

        async def test_revoke_all_user_tokens(self, service: TokenService) -> None:
            t1 = await service.create_token(subject="alice", type=TokenType.ACCESS)
            t2 = await service.create_token(subject="alice", type=TokenType.REFRESH)
            t3 = await service.create_token(subject="bob", type=TokenType.ACCESS)
            await service.revoke_all_user_tokens("alice")
            assert (await service.get_token(t1.id)).status == TokenStatus.REVOKED
            assert (await service.get_token(t2.id)).status == TokenStatus.REVOKED
            assert (await service.get_token(t3.id)).status == TokenStatus.ACTIVE

    class TestGetToken:
        async def test_get_existing(self, service: TokenService) -> None:
            token = await service.create_token(subject="alice", type=TokenType.ACCESS)
            found = await service.get_token(token.id)
            assert found is not None
            assert found.id == token.id

        async def test_get_nonexistent(self, service: TokenService) -> None:
            found = await service.get_token("nonexistent")
            assert found is None

    class TestListTokens:
        async def test_list_all(self, service: TokenService) -> None:
            await service.create_token(subject="alice", type=TokenType.ACCESS)
            await service.create_token(subject="bob", type=TokenType.ACCESS)
            tokens = await service.list_tokens()
            assert len(tokens) == 2

        async def test_list_by_subject(self, service: TokenService) -> None:
            await service.create_token(subject="alice", type=TokenType.ACCESS)
            await service.create_token(subject="bob", type=TokenType.ACCESS)
            tokens = await service.list_tokens(subject="alice")
            assert len(tokens) == 1
            assert tokens[0].subject == "alice"

        async def test_list_by_status(self, service: TokenService) -> None:
            t = await service.create_token(subject="alice", type=TokenType.ACCESS)
            await service.revoke_token(t.id)
            tokens = await service.list_tokens(status=TokenStatus.REVOKED)
            assert len(tokens) == 1
            assert tokens[0].status == TokenStatus.REVOKED

        async def test_list_limit(self, service: TokenService) -> None:
            for i in range(5):
                await service.create_token(subject=f"user{i}", type=TokenType.ACCESS)
            tokens = await service.list_tokens(limit=3)
            assert len(tokens) == 3

        async def test_list_empty(self, service: TokenService) -> None:
            tokens = await service.list_tokens(subject="nonexistent")
            assert len(tokens) == 0

    class TestTokenStringRoundtrip:
        async def test_token_string_stored(self, service: TokenService) -> None:
            token = await service.create_token(subject="alice", type=TokenType.ACCESS)
            token_str = await service.get_token_string(token.id)
            assert token_str is not None
            assert token_str.count(".") == 2

        async def test_multiple_tokens_unique_strings(self, service: TokenService) -> None:
            t1 = await service.create_token(subject="a", type=TokenType.ACCESS)
            t2 = await service.create_token(subject="b", type=TokenType.ACCESS)
            s1 = await service.get_token_string(t1.id)
            s2 = await service.get_token_string(t2.id)
            assert s1 != s2
