"""Tests for AuthenticationService — authentication, provider management, session validation, identity."""

from __future__ import annotations

import pytest

from eaip.auth.auth_providers import AuthenticationService
from eaip.auth.exceptions import AuthenticationError, ProviderNotFoundError
from eaip.auth.models import (
    AuthenticationRequest,
    IdentityProvider,
    ProviderType,
)


class TestAuthenticationService:
    @pytest.fixture
    def service(self) -> AuthenticationService:
        return AuthenticationService(secret="test-secret-for-auth-providers")

    class TestAuthenticate:
        async def test_successful_authentication(self, service: AuthenticationService) -> None:
            req = AuthenticationRequest(
                id="req1",
                provider="mock",
                credentials={"username": "alice", "password": "s3cret"},
            )
            result = await service.authenticate(req)
            assert result.success is True
            assert result.token != ""
            assert result.refresh_token != ""
            assert result.identity["sub"] == "alice"
            assert result.identity["email"] == "alice@example.com"

        async def test_failed_authentication(self, service: AuthenticationService) -> None:
            req = AuthenticationRequest(
                id="req2",
                provider="mock",
                credentials={"username": "alice", "password": "invalid"},
            )
            result = await service.authenticate(req)
            assert result.success is False
            assert result.error == "Invalid credentials"
            assert result.token == ""

        async def test_missing_credentials(self, service: AuthenticationService) -> None:
            req = AuthenticationRequest(
                id="req3",
                provider="mock",
                credentials={},
            )
            result = await service.authenticate(req)
            assert result.success is False
            assert result.error == "Missing credentials"

        async def test_provider_not_found(self, service: AuthenticationService) -> None:
            req = AuthenticationRequest(
                id="req4",
                provider="nonexistent",
                credentials={"username": "alice", "password": "s3cret"},
            )
            with pytest.raises(ProviderNotFoundError):
                await service.authenticate(req)

        async def test_disabled_provider(self, service: AuthenticationService) -> None:
            disabled = IdentityProvider(
                id="disabled",
                name="Disabled",
                type=ProviderType.LOCAL,
                enabled=False,
            )
            await service.register_provider(disabled)
            req = AuthenticationRequest(
                id="req5",
                provider="disabled",
                credentials={"username": "alice", "password": "s3cret"},
            )
            result = await service.authenticate(req)
            assert result.success is False
            assert "disabled" in result.error

    class TestProviderManagement:
        async def test_register_provider(self, service: AuthenticationService) -> None:
            provider = IdentityProvider(
                id="custom-ldap",
                name="Custom LDAP",
                type=ProviderType.LDAP,
                priority=5,
            )
            await service.register_provider(provider)
            found = await service.get_provider("custom-ldap")
            assert found is not None
            assert found.name == "Custom LDAP"
            assert found.type == ProviderType.LDAP

        async def test_get_provider_nonexistent(self, service: AuthenticationService) -> None:
            found = await service.get_provider("nonexistent")
            assert found is None

        async def test_list_providers(self, service: AuthenticationService) -> None:
            providers = await service.list_providers()
            assert len(providers) == 1
            assert providers[0].id == "mock"

        async def test_remove_provider(self, service: AuthenticationService) -> None:
            provider = IdentityProvider(id="temp", name="Temp", type=ProviderType.LOCAL)
            await service.register_provider(provider)
            await service.remove_provider("temp")
            assert await service.get_provider("temp") is None

        async def test_register_multiple_providers(self, service: AuthenticationService) -> None:
            p1 = IdentityProvider(id="p1", name="P1", type=ProviderType.OAUTH2)
            p2 = IdentityProvider(id="p2", name="P2", type=ProviderType.LDAP)
            await service.register_provider(p1)
            await service.register_provider(p2)
            providers = await service.list_providers()
            assert len(providers) == 3

    class TestSessionValidation:
        async def test_validate_valid_session(self, service: AuthenticationService) -> None:
            req = AuthenticationRequest(
                id="r1", provider="mock", credentials={"username": "alice", "password": "s3cret"}
            )
            result = await service.authenticate(req)
            assert result.success is True
            valid = await service.validate_session(result.token)
            assert valid is True

        async def test_validate_invalid_session(self, service: AuthenticationService) -> None:
            valid = await service.validate_session("invalid.token.string")
            assert valid is False

    class TestGetIdentity:
        async def test_get_identity_success(self, service: AuthenticationService) -> None:
            req = AuthenticationRequest(
                id="r1", provider="mock", credentials={"username": "alice", "password": "s3cret"}
            )
            result = await service.authenticate(req)
            identity = await service.get_identity(result.token)
            assert identity["sub"] == "alice"
            assert identity["email"] == "alice@example.com"

        async def test_get_identity_invalid_token(self, service: AuthenticationService) -> None:
            with pytest.raises(AuthenticationError, match="Cannot get identity"):
                await service.get_identity("bad.token.here")

    class TestMockProviderEdgeCases:
        async def test_empty_username(self, service: AuthenticationService) -> None:
            req = AuthenticationRequest(
                id="r1", provider="mock", credentials={"username": "", "password": "s3cret"}
            )
            result = await service.authenticate(req)
            assert result.success is False

        async def test_empty_password(self, service: AuthenticationService) -> None:
            req = AuthenticationRequest(
                id="r1", provider="mock", credentials={"username": "alice", "password": ""}
            )
            result = await service.authenticate(req)
            assert result.success is False
