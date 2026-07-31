"""Tests for :mod:`eaip.settings.db_settings` — database configuration models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.settings.core_settings import load_platform_settings
from eaip.settings.db_settings import (
    DatabaseProviderSettings,
    DatabaseSettings,
    NeonDatabaseSettings,
)


class TestDatabaseSettings:
    def test_defaults(self) -> None:
        s = DatabaseSettings()
        assert s.host == "localhost"
        assert s.port == 5432
        assert s.name == "eaip"
        assert s.user == "eaip"
        assert s.password == ""
        assert s.enable_migrations is True
        assert s.migration_table == "_eaip_migrations"
        assert s.echo is False

    def test_dsn_builds_url(self) -> None:
        s = DatabaseSettings(host="h", port=5433, name="n", user="u", password="p")
        assert s.dsn == "postgresql://u:p@h:5433/n"

    def test_dsn_no_credentials_omits_user_password(self) -> None:
        s = DatabaseSettings(host="h", port=5433, name="n", user="u", password="p")
        assert s.dsn_no_credentials == "postgresql://h:5433/n"

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DatabaseSettings(unknown="x")


class TestNeonDatabaseSettings:
    def test_defaults(self) -> None:
        s = NeonDatabaseSettings()
        assert s.project_id is None
        assert s.branch is None
        assert s.host.startswith("ep-")

    def test_dsn_builds_url(self) -> None:
        s = NeonDatabaseSettings(host="ep-x.aws.neon.tech", user="u", password="p", name="n")
        assert s.dsn == "postgresql://u:p@ep-x.aws.neon.tech:5432/n"

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NeonDatabaseSettings(unknown="x")


class TestDatabaseProviderSettings:
    def test_default_provider_is_local(self) -> None:
        s = DatabaseProviderSettings()
        assert s.provider == "local"

    def test_resolve_local_returns_database_settings(self) -> None:
        s = DatabaseProviderSettings(provider="local")
        resolved = s.resolve()
        assert isinstance(resolved, DatabaseSettings)

    def test_resolve_neon_returns_database_settings_from_neon(self) -> None:
        s = DatabaseProviderSettings(
            provider="neon",
            neon=NeonDatabaseSettings(
                host="ep-neon.aws.neon.tech",
                name="n",
                user="u",
                password="p",
                port=5433,
                max_pool_size=8,
            ),
        )
        resolved = s.resolve()
        assert resolved.host == "ep-neon.aws.neon.tech"
        assert resolved.name == "n"
        assert resolved.user == "u"
        assert resolved.password == "p"
        assert resolved.port == 5433
        assert resolved.max_pool_size == 8

    def test_resolve_neon_ignores_project_metadata(self) -> None:
        s = DatabaseProviderSettings(
            provider="neon",
            neon=NeonDatabaseSettings(project_id="proj", branch="main"),
        )
        resolved = s.resolve()
        assert not hasattr(resolved, "project_id")

    def test_env_provider_parsing(self, monkeypatch: object) -> None:
        monkeypatch.setenv("EAIP_DB_PROVIDER", "neon")  # type: ignore[attr-defined]
        s = DatabaseProviderSettings()
        assert s.provider == "neon"

    def test_env_neon_host_parsing(self, monkeypatch: object) -> None:
        monkeypatch.setenv("EAIP_NEON_HOST", "ep-env.aws.neon.tech")  # type: ignore[attr-defined]
        s = DatabaseProviderSettings()
        assert s.neon.host == "ep-env.aws.neon.tech"

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DatabaseProviderSettings(unknown="x")


class TestDatabaseSettingsEnvParsing:
    def test_platform_db_host_parsing(self, monkeypatch: object) -> None:
        monkeypatch.setenv("EAIP_DB__HOST", "db.platform.local")  # type: ignore[attr-defined]
        s = load_platform_settings()
        assert s.db.host == "db.platform.local"

    def test_platform_db_provider_env(self, monkeypatch: object) -> None:
        monkeypatch.setenv("EAIP_DB_PROVIDER", "neon")  # type: ignore[attr-defined]
        monkeypatch.setenv("EAIP_NEON_HOST", "ep-platform.aws.neon.tech")  # type: ignore[attr-defined]
        s = load_platform_settings()
        assert s.database_provider.provider == "neon"
        assert s.database_provider.neon.host == "ep-platform.aws.neon.tech"

    def test_local_env_does_not_leak_into_resolve(self, monkeypatch: object) -> None:
        monkeypatch.setenv("EAIP_DB__HOST", "db.platform.local")  # type: ignore[attr-defined]
        s = load_platform_settings()
        assert s.database_provider.resolve().host == "localhost"


__all__: list[str] = []
