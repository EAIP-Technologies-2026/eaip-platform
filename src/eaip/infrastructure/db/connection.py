from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.db.connection")


class DatabaseConnection:
    _pool: Any = None
    _provider_name: str = "local"

    @classmethod
    async def initialize(cls, provider_name: str, **kwargs: Any) -> None:
        import asyncpg

        cls._provider_name = provider_name
        if cls._pool is not None:
            return
        cls._pool = await asyncpg.create_pool(**kwargs)
        log.info(
            "db.pool.initialized",
            provider=provider_name,
            min_size=kwargs.get("min_size"),
            max_size=kwargs.get("max_size"),
        )

    @classmethod
    async def close(cls) -> None:
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None
            log.info("db.pool.closed")

    @classmethod
    @asynccontextmanager
    async def connection(cls) -> AsyncIterator[Any]:
        if cls._pool is None:
            raise RuntimeError("DatabaseConnection pool not initialized. Call initialize() first.")
        async with cls._pool.acquire() as conn:
            yield conn

    @classmethod
    @asynccontextmanager
    async def transaction(cls) -> AsyncIterator[Any]:
        if cls._pool is None:
            raise RuntimeError("DatabaseConnection pool not initialized.")
        async with cls._pool.acquire() as conn, conn.transaction():
            yield conn

    @classmethod
    async def execute(cls, query: str, *args: Any) -> str:
        async with cls.connection() as conn:
            return await conn.execute(query, *args)

    @classmethod
    async def fetchrow(cls, query: str, *args: Any) -> Any:
        async with cls.connection() as conn:
            return await conn.fetchrow(query, *args)

    @classmethod
    async def fetch(cls, query: str, *args: Any) -> list[Any]:
        async with cls.connection() as conn:
            return await conn.fetch(query, *args)

    @classmethod
    async def fetchval(cls, query: str, *args: Any) -> Any:
        async with cls.connection() as conn:
            return await conn.fetchval(query, *args)

    @classmethod
    def get_pool(cls) -> Any:
        return cls._pool

    @classmethod
    async def health(cls) -> dict[str, Any]:
        if cls._pool is None:
            return {"status": "not_initialized", "provider": cls._provider_name}
        try:
            async with cls.connection() as conn:
                val = await conn.fetchval("SELECT 1")
                return {"status": "healthy", "provider": cls._provider_name, "ping": val == 1}
        except Exception as e:
            return {"status": "unhealthy", "provider": cls._provider_name, "error": str(e)}


async def get_db() -> DatabaseConnection:
    return DatabaseConnection


__all__ = ["DatabaseConnection", "get_db"]
