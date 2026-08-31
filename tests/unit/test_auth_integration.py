"""Tests for AuthRuntimeModule and AuthHealthCheck integration."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.auth.auth_providers import AuthenticationService
from eaip.auth.health import AuthHealthCheck
from eaip.auth.integration import AuthRuntimeModule
from eaip.auth.models import TokenConfig, TokenType
from eaip.auth.tokens import TokenService
from eaip.health.checks import HealthStatus


class TestAuthRuntimeModule:
    def test_module_name(self) -> None:
        module = AuthRuntimeModule()
        assert module.name == "auth"

    def test_default_config(self) -> None:
        module = AuthRuntimeModule()
        assert module._config.access_token_ttl_seconds == 900

    def test_custom_config(self) -> None:
        config = TokenConfig(access_token_ttl_seconds=1800)
        module = AuthRuntimeModule(config=config)
        assert module._config.access_token_ttl_seconds == 1800

    def test_token_service_property(self) -> None:
        module = AuthRuntimeModule()
        assert module.token_service is not None

    def test_auth_service_property(self) -> None:
        module = AuthRuntimeModule()
        assert module.auth_service is not None

    def test_custom_services(self) -> None:
        config = TokenConfig()
        ts = TokenService(config=config)
        auth_svc = AuthenticationService(token_service=ts)
        module = AuthRuntimeModule(config=config, token_service=ts, auth_service=auth_svc)
        assert module.token_service is ts
        assert module.auth_service is auth_svc

    async def test_start(self) -> None:
        module = AuthRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()
        await module.start(kernel)
        kernel.platform.capabilities.register.assert_called_once()
        kernel.platform.health.register.assert_called_once()

    async def test_start_health_check_type(self) -> None:
        module = AuthRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()
        await module.start(kernel)
        registered_check = kernel.platform.health.register.call_args[0][0]
        assert isinstance(registered_check, AuthHealthCheck)

    async def test_stop(self) -> None:
        module = AuthRuntimeModule()
        kernel = MagicMock()
        await module.stop(kernel)


class TestAuthHealthCheck:
    @pytest.fixture
    def token_service(self) -> TokenService:
        return TokenService()

    async def test_healthy(self, token_service: TokenService) -> None:
        await token_service.create_token(subject="alice", type=TokenType.ACCESS)
        check = AuthHealthCheck(token_service=token_service)
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.component == "auth"
        assert report.details["tokens_total"] == 1
        assert report.details["tokens_active"] == 1

    async def test_healthy_with_multiple_tokens(self, token_service: TokenService) -> None:
        await token_service.create_token(subject="alice", type=TokenType.ACCESS)
        await token_service.create_token(subject="bob", type=TokenType.REFRESH)
        check = AuthHealthCheck(token_service=token_service)
        report = await check.check()
        assert report.status == HealthStatus.HEALTHY
        assert report.details["tokens_total"] == 2

    async def test_degraded_when_no_tokens(self) -> None:
        svc = TokenService()
        check = AuthHealthCheck(token_service=svc)
        report = await check.check()
        assert report.status == HealthStatus.DEGRADED
        assert "No tokens" in report.message

    async def test_degraded_with_revoked_tokens(self, token_service: TokenService) -> None:
        t = await token_service.create_token(subject="alice", type=TokenType.ACCESS)
        await token_service.revoke_token(t.id)
        check = AuthHealthCheck(token_service=token_service)
        report = await check.check()
        assert report.details["tokens_total"] == 1
        assert report.details["tokens_active"] == 0

    async def test_config_details_in_report(self) -> None:
        config = TokenConfig(issuer="custom-issuer", signing_algorithm="HS512")
        svc = TokenService(config=config)
        check = AuthHealthCheck(token_service=svc)
        report = await check.check()
        assert report.details["token_config_issuer"] == "custom-issuer"
        assert report.details["signing_algorithm"] == "HS512"
