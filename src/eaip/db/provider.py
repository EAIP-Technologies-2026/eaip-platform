from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from eaip.settings.db_settings import DatabaseSettings, NeonDatabaseSettings


class DatabaseProvider(ABC):
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def settings(self) -> DatabaseSettings: ...

    @abstractmethod
    def connection_kwargs(self) -> dict[str, Any]: ...

    @abstractmethod
    async def health(self) -> dict[str, Any]: ...


class LocalPostgresProvider(DatabaseProvider):
    def __init__(self, settings: DatabaseSettings) -> None:
        self._settings = settings

    def name(self) -> str:
        return "local"

    def settings(self) -> DatabaseSettings:
        return self._settings

    def connection_kwargs(self) -> dict[str, Any]:
        return {
            "dsn": self._settings.dsn,
            "min_size": self._settings.min_pool_size,
            "max_size": self._settings.max_pool_size,
            "statement_cache_size": self._settings.statement_cache_size,
            "max_inactive_connection_lifetime": self._settings.max_inactive_connection_lifetime,
        }

    async def health(self) -> dict[str, Any]:
        from eaip.infrastructure.db.connection import DatabaseConnection

        return await DatabaseConnection.health()


class NeonPostgresProvider(DatabaseProvider):
    def __init__(self, settings: NeonDatabaseSettings) -> None:
        self._settings = settings

    def name(self) -> str:
        return "neon"

    def settings(self) -> DatabaseSettings:
        return DatabaseSettings(
            host=self._settings.host,
            port=self._settings.port,
            name=self._settings.name,
            user=self._settings.user,
            password=self._settings.password,
            min_pool_size=self._settings.min_pool_size,
            max_pool_size=self._settings.max_pool_size,
            statement_cache_size=self._settings.statement_cache_size,
            max_inactive_connection_lifetime=self._settings.max_inactive_connection_lifetime,
            enable_migrations=self._settings.enable_migrations,
            migration_table=self._settings.migration_table,
            echo=self._settings.echo,
        )

    def connection_kwargs(self) -> dict[str, Any]:
        return {
            "dsn": self._settings.dsn,
            "min_size": self._settings.min_pool_size,
            "max_size": self._settings.max_pool_size,
            "statement_cache_size": self._settings.statement_cache_size,
            "max_inactive_connection_lifetime": self._settings.max_inactive_connection_lifetime,
            "ssl": "require",
        }

    async def health(self) -> dict[str, Any]:
        from eaip.infrastructure.db.connection import DatabaseConnection

        return await DatabaseConnection.health()


def resolve_provider(provider_name: str, settings: DatabaseSettings) -> DatabaseProvider:
    if provider_name == "neon":
        return NeonPostgresProvider(settings)
    return LocalPostgresProvider(settings)


__all__ = ["DatabaseProvider", "LocalPostgresProvider", "NeonPostgresProvider", "resolve_provider"]
