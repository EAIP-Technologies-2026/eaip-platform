from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="forbid",
        env_prefix="EAIP_DB_",
    )

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    name: str = Field(default="eaip")
    user: str = Field(default="eaip")
    password: str = Field(default="")
    min_pool_size: int = Field(default=2)
    max_pool_size: int = Field(default=20)
    statement_cache_size: int = Field(default=100)
    max_inactive_connection_lifetime: float = Field(default=300.0)
    enable_migrations: bool = Field(default=True)
    migration_table: str = Field(default="_eaip_migrations")
    echo: bool = Field(default=False)

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def dsn_no_credentials(self) -> str:
        return f"postgresql://{self.host}:{self.port}/{self.name}"


class NeonDatabaseSettings(BaseSettings):
    """Neon-specific database settings.

    Read from ``EAIP_NEON_*`` environment variables.
    """

    model_config = SettingsConfigDict(
        extra="forbid",
        env_prefix="EAIP_NEON_",
    )

    host: str = Field(default="ep-example-abc.us-east-2.aws.neon.tech")
    port: int = Field(default=5432)
    name: str = Field(default="eaip")
    user: str = Field(default="eaip")
    password: str = Field(default="")
    min_pool_size: int = Field(default=2)
    max_pool_size: int = Field(default=20)
    statement_cache_size: int = Field(default=100)
    max_inactive_connection_lifetime: float = Field(default=300.0)
    enable_migrations: bool = Field(default=True)
    migration_table: str = Field(default="_eaip_migrations")
    echo: bool = Field(default=False)
    project_id: str | None = Field(default=None)
    branch: str | None = Field(default=None)

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def dsn_no_credentials(self) -> str:
        return f"postgresql://{self.host}:{self.port}/{self.name}"


class DatabaseProviderSettings(BaseSettings):
    """Database provider selection and configuration.

    ``provider`` selects the backend: ``"local"`` uses Docker PostgreSQL
    (default), ``"neon"`` uses Neon serverless Postgres.

    Read from ``EAIP_DB_PROVIDER`` environment variable.
    """

    model_config = SettingsConfigDict(
        extra="forbid",
        env_prefix="EAIP_DB_",
    )

    provider: str = Field(default="local")
    neon: NeonDatabaseSettings = Field(default_factory=NeonDatabaseSettings)

    def resolve(self) -> DatabaseSettings:
        """Return the active :class:`DatabaseSettings` for the selected provider."""
        if self.provider == "neon":
            return DatabaseSettings(
                host=self.neon.host,
                port=self.neon.port,
                name=self.neon.name,
                user=self.neon.user,
                password=self.neon.password,
                min_pool_size=self.neon.min_pool_size,
                max_pool_size=self.neon.max_pool_size,
                statement_cache_size=self.neon.statement_cache_size,
                max_inactive_connection_lifetime=self.neon.max_inactive_connection_lifetime,
                enable_migrations=self.neon.enable_migrations,
                migration_table=self.neon.migration_table,
                echo=self.neon.echo,
            )
        return DatabaseSettings()


__all__ = ["DatabaseProviderSettings", "DatabaseSettings", "NeonDatabaseSettings"]
