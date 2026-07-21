"""Tests for FederatedIdentityProvider service."""

from __future__ import annotations

import pytest

from eaip.fedid.exceptions import AuthenticationFailedError, FederationError, ProviderNotFoundError
from eaip.fedid.models import (
    FederatedUser,
    FederationConfig,
    IdentityProvider,
    IdpType,
    SSOSession,
    SSOStatus,
)
from eaip.fedid.provider import FederatedIdentityProvider


class TestFederatedIdentityProvider:
    @pytest.fixture
    def provider(self) -> FederatedIdentityProvider:
        return FederatedIdentityProvider()

    @pytest.fixture
    def sample_idp(self) -> IdentityProvider:
        return IdentityProvider(
            id="azure1",
            name="Azure AD",
            idp_type=IdpType.AZURE_AD,
            issuer_url="https://login.microsoftonline.com",
            client_id="abc123",
        )

    class TestRegisterProvider:
        async def test_register_provider(
            self, provider: FederatedIdentityProvider, sample_idp: IdentityProvider
        ) -> None:
            result = await provider.register_provider(sample_idp)
            assert result.id == "azure1"
            assert result.name == "Azure AD"

        async def test_list_providers(
            self, provider: FederatedIdentityProvider, sample_idp: IdentityProvider
        ) -> None:
            await provider.register_provider(sample_idp)
            idps = await provider.list_providers()
            assert len(idps) == 1

    class TestGetProvider:
        async def test_get_provider(
            self, provider: FederatedIdentityProvider, sample_idp: IdentityProvider
        ) -> None:
            await provider.register_provider(sample_idp)
            idp = await provider.get_provider("azure1")
            assert idp.idp_type == IdpType.AZURE_AD

        async def test_get_provider_not_found(self, provider: FederatedIdentityProvider) -> None:
            with pytest.raises(ProviderNotFoundError):
                await provider.get_provider("nonexistent")

    class TestAuthenticate:
        async def test_authenticate(
            self, provider: FederatedIdentityProvider, sample_idp: IdentityProvider
        ) -> None:
            await provider.register_provider(sample_idp)
            user = await provider.authenticate("azure1", "ext-user-1")
            assert user.idp_id == "azure1"
            assert user.external_id == "ext-user-1"

        async def test_authenticate_provider_not_found(
            self, provider: FederatedIdentityProvider
        ) -> None:
            with pytest.raises(ProviderNotFoundError):
                await provider.authenticate("nonexistent", "ext-user-1")

        async def test_authenticate_disabled_provider(
            self, provider: FederatedIdentityProvider
        ) -> None:
            disabled = IdentityProvider(
                id="disabled1", name="Disabled", idp_type=IdpType.LDAP, enabled=False
            )
            await provider.register_provider(disabled)
            with pytest.raises(AuthenticationFailedError):
                await provider.authenticate("disabled1", "ext-user-1")

        async def test_authenticate_same_user_returns_same(
            self, provider: FederatedIdentityProvider, sample_idp: IdentityProvider
        ) -> None:
            await provider.register_provider(sample_idp)
            user1 = await provider.authenticate("azure1", "ext-user-1")
            user2 = await provider.authenticate("azure1", "ext-user-1")
            assert user1.id == user2.id

    class TestCreateSession:
        async def test_create_session(
            self, provider: FederatedIdentityProvider, sample_idp: IdentityProvider
        ) -> None:
            await provider.register_provider(sample_idp)
            user = await provider.authenticate("azure1", "ext-user-1")
            session = await provider.create_session(user.id, "azure1")
            assert session.user_id == user.id
            assert session.idp_id == "azure1"
            assert session.status == SSOStatus.ACTIVE

        async def test_create_session_user_not_found(
            self, provider: FederatedIdentityProvider, sample_idp: IdentityProvider
        ) -> None:
            await provider.register_provider(sample_idp)
            with pytest.raises(FederationError):
                await provider.create_session("nonexistent", "azure1")

        async def test_create_session_provider_not_found(
            self, provider: FederatedIdentityProvider, sample_idp: IdentityProvider
        ) -> None:
            await provider.register_provider(sample_idp)
            user = await provider.authenticate("azure1", "ext-user")
            with pytest.raises(ProviderNotFoundError):
                await provider.create_session(user.id, "nonexistent")

    class TestValidateSession:
        async def test_validate_session(
            self, provider: FederatedIdentityProvider, sample_idp: IdentityProvider
        ) -> None:
            await provider.register_provider(sample_idp)
            user = await provider.authenticate("azure1", "ext-user-1")
            session = await provider.create_session(user.id, "azure1")
            validated = await provider.validate_session(session.id)
            assert validated.id == session.id

        async def test_validate_session_not_found(
            self, provider: FederatedIdentityProvider
        ) -> None:
            with pytest.raises(FederationError):
                await provider.validate_session("nonexistent")

    class TestExchangeToken:
        async def test_exchange_token(
            self, provider: FederatedIdentityProvider, sample_idp: IdentityProvider
        ) -> None:
            await provider.register_provider(sample_idp)
            user = await provider.authenticate("azure1", "ext-user-1")
            session = await provider.create_session(user.id, "azure1")
            new_session = await provider.exchange_token(session.id)
            assert new_session.user_id == user.id
            assert new_session.id != session.id

        async def test_exchange_token_not_found(self, provider: FederatedIdentityProvider) -> None:
            with pytest.raises(FederationError):
                await provider.exchange_token("nonexistent")

    class TestRevokeSession:
        async def test_revoke_session(
            self, provider: FederatedIdentityProvider, sample_idp: IdentityProvider
        ) -> None:
            await provider.register_provider(sample_idp)
            user = await provider.authenticate("azure1", "ext-user-1")
            session = await provider.create_session(user.id, "azure1")
            await provider.revoke_session(session.id)
            with pytest.raises(FederationError):
                await provider.validate_session(session.id)

        async def test_revoke_session_not_found(self, provider: FederatedIdentityProvider) -> None:
            with pytest.raises(FederationError):
                await provider.revoke_session("nonexistent")

    class TestLinkIdentity:
        async def test_link_identity(
            self, provider: FederatedIdentityProvider, sample_idp: IdentityProvider
        ) -> None:
            await provider.register_provider(sample_idp)
            user = await provider.link_identity("usr-1", "azure1", "ext-user-1")
            assert user.id == "usr-1"
            assert user.external_id == "ext-user-1"
            assert user.idp_id == "azure1"

        async def test_link_identity_provider_not_found(
            self, provider: FederatedIdentityProvider
        ) -> None:
            with pytest.raises(ProviderNotFoundError):
                await provider.link_identity("usr-1", "nonexistent", "ext-user-1")

    class TestListSessions:
        async def test_list_sessions(
            self, provider: FederatedIdentityProvider, sample_idp: IdentityProvider
        ) -> None:
            await provider.register_provider(sample_idp)
            user = await provider.authenticate("azure1", "ext-user-1")
            await provider.create_session(user.id, "azure1")
            sessions = await provider.list_sessions(user_id=user.id)
            assert len(sessions) == 1

        async def test_list_all_sessions(
            self, provider: FederatedIdentityProvider, sample_idp: IdentityProvider
        ) -> None:
            await provider.register_provider(sample_idp)
            user1 = await provider.authenticate("azure1", "ext-1")
            user2 = await provider.authenticate("azure1", "ext-2")
            await provider.create_session(user1.id, "azure1")
            await provider.create_session(user2.id, "azure1")
            sessions = await provider.list_sessions()
            assert len(sessions) == 2

    class TestGetUser:
        async def test_get_user(
            self, provider: FederatedIdentityProvider, sample_idp: IdentityProvider
        ) -> None:
            await provider.register_provider(sample_idp)
            user = await provider.authenticate("azure1", "ext-user-1")
            found = await provider.get_user(user.id)
            assert found.id == user.id

        async def test_get_user_not_found(self, provider: FederatedIdentityProvider) -> None:
            with pytest.raises(FederationError):
                await provider.get_user("nonexistent")

    class TestConfig:
        def test_default_config(self) -> None:
            p = FederatedIdentityProvider()
            assert p.config.session_ttl_seconds == 3600
            assert p.config.enable_refresh is True

        def test_custom_config(self) -> None:
            config = FederationConfig(session_ttl_seconds=7200, max_sessions_per_user=5)
            p = FederatedIdentityProvider(config=config)
            assert p.config.session_ttl_seconds == 7200
            assert p.config.max_sessions_per_user == 5


class TestIdentityProviderModel:
    def test_all_idp_types(self) -> None:
        for idp_type in IdpType:
            idp = IdentityProvider(id=idp_type.value, name=idp_type.value, idp_type=idp_type)
            assert idp.idp_type == idp_type

    def test_defaults(self) -> None:
        idp = IdentityProvider(id="idp1", name="Test", idp_type=IdpType.OIDC)
        assert idp.enabled is True
        assert idp.issuer_url == ""
        assert idp.client_id == ""


class TestSSOSessionModel:
    def test_default_status(self) -> None:
        from datetime import datetime, timedelta, UTC

        session = SSOSession(
            id="s1", user_id="u1", idp_id="idp1", expires_at=datetime.now(UTC) + timedelta(hours=1)
        )
        assert session.status == SSOStatus.ACTIVE
