from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="forbid",
    )

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    name: str = Field(default="eaip")
    user: str = Field(default="eaip")
    password: str = Field(default="eaip_dev_password")
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


__all__ = ["DatabaseSettings"]
