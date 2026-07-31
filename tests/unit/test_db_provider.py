"""Tests for :mod:`eaip.db.provider` — database provider selection."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from eaip.db.provider import (
    DatabaseProvider,
    LocalPostgresProvider,
    NeonPostgresProvider,
    resolve_provider,
)
from eaip.settings.db_settings import (
    DatabaseProviderSettings,
    DatabaseSettings,
    NeonDatabaseSettings,
)


@pytest.fixture
def local_settings() -> DatabaseSettings:
    return DatabaseSettings(
        host="db.local",
        port=5433,
        name="eaip_test",
        user="test_user",
        password="test_pass",
        min_pool_size=1,
        max_pool_size=5,
    )


@pytest.fixture
def neon_settings() -> NeonDatabaseSettings:
    return NeonDatabaseSettings(
        host="ep-example.us-east-2.aws.neon.tech",
        name="eaip_neon",
        user="neon_user",
        password="neon_pass",
        project_id="proj-1",
        branch="main",
    )


class TestDatabaseProvider:
    def test_is_abstract(self) -> None:
        with pytest.raises(TypeError):
            DatabaseProvider()  # type: ignore[abstract]


class TestLocalPostgresProvider:
    def test_name(self, local_settings: DatabaseSettings) -> None:
        assert LocalPostgresProvider(local_settings).name() == "local"

    def test_settings_returns_stored(self, local_settings: DatabaseSettings) -> None:
        provider = LocalPostgresProvider(local_settings)
        assert provider.settings() is local_settings

    def test_connection_kwargs(self, local_settings: DatabaseSettings) -> None:
        provider = LocalPostgresProvider(local_settings)
        kwargs = provider.connection_kwargs()
        assert kwargs["dsn"] == local_settings.dsn
        assert kwargs["min_size"] == 1
        assert kwargs["max_size"] == 5
        assert kwargs["statement_cache_size"] == local_settings.statement_cache_size
        assert (
            kwargs["max_inactive_connection_lifetime"]
            == local_settings.max_inactive_connection_lifetime
        )
        assert "ssl" not in kwargs

    async def test_health_delegates_to_database_connection(
        self,
        local_settings: DatabaseSettings,
    ) -> None:
        provider = LocalPostgresProvider(local_settings)
        with patch(
            "eaip.infrastructure.db.connection.DatabaseConnection.health",
            new=AsyncMock(return_value={"status": "healthy", "provider": "local"}),
        ) as health:
            result = await provider.health()
        health.assert_awaited_once()
        assert result["status"] == "healthy"


class TestNeonPostgresProvider:
    def test_name(self, neon_settings: NeonDatabaseSettings) -> None:
        assert NeonPostgresProvider(neon_settings).name() == "neon"

    def test_settings_returns_database_settings(self, neon_settings: NeonDatabaseSettings) -> None:
        provider = NeonPostgresProvider(neon_settings)
        resolved = provider.settings()
        assert isinstance(resolved, DatabaseSettings)
        assert resolved.host == neon_settings.host
        assert resolved.user == neon_settings.user
        assert resolved.password == neon_settings.password

    def test_connection_kwargs_include_ssl(self, neon_settings: NeonDatabaseSettings) -> None:
        provider = NeonPostgresProvider(neon_settings)
        kwargs = provider.connection_kwargs()
        assert kwargs["dsn"] == neon_settings.dsn
        assert kwargs["ssl"] == "require"

    async def test_health_delegates_to_database_connection(
        self,
        neon_settings: NeonDatabaseSettings,
    ) -> None:
        provider = NeonPostgresProvider(neon_settings)
        with patch(
            "eaip.infrastructure.db.connection.DatabaseConnection.health",
            new=AsyncMock(return_value={"status": "healthy"}),
        ) as health:
            result = await provider.health()
        health.assert_awaited_once()
        assert result["status"] == "healthy"


class TestResolveProvider:
    def test_local_default(self, local_settings: DatabaseSettings) -> None:
        provider = resolve_provider("local", local_settings)
        assert isinstance(provider, LocalPostgresProvider)

    def test_neon_selection(self, local_settings: DatabaseSettings) -> None:
        provider = resolve_provider("neon", local_settings)
        assert isinstance(provider, NeonPostgresProvider)

    def test_unknown_provider_falls_back_to_local(self, local_settings: DatabaseSettings) -> None:
        provider = resolve_provider("unknown", local_settings)
        assert isinstance(provider, LocalPostgresProvider)

    def test_resolve_provider_via_settings_resolve(self) -> None:
        settings = DatabaseProviderSettings(provider="local")
        provider = resolve_provider(settings.provider, settings.resolve())
        assert isinstance(provider, LocalPostgresProvider)


__all__: list[str] = []
