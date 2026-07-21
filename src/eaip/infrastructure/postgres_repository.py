"""PostgreSQL-backed implementation of :class:`AbstractRepository`.

Provides durable storage for entities behind the existing repository
abstraction.  Connection pooling is handled via ``asyncpg``.

Usage::

    from eaip.infrastructure.postgres_repository import PostgresRepository

    repo = PostgresRepository[CorrelationId, AuthToken](
        table_name="auth_tokens",
        dsn="postgresql://user:pass@host:5432/db",
    )
    await repo.add(token)
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any, TypeVar

from eaip.interfaces.repository import AbstractRepository

ID = TypeVar("ID")
T = TypeVar("T")


class PostgresRepository(AbstractRepository[ID, T]):
    """Production PostgreSQL repository implementing :class:`AbstractRepository`.

    Uses asyncpg for connection pooling and parameterized queries.
    Serializes entities as JSONB for maximum schema flexibility.
    """

    def __init__(
        self,
        table_name: str,
        dsn: str | None = None,
        pool_min_size: int = 2,
        pool_max_size: int = 10,
        *,
        tenant_column: str | None = None,
    ) -> None:
        self._table_name = table_name
        self._dsn = dsn
        self._pool_min_size = pool_min_size
        self._pool_max_size = pool_max_size
        self._tenant_column = tenant_column
        self._pool: Any = None
        self._hit_count: int = 0
        self._miss_count: int = 0

    async def _ensure_pool(self) -> Any:
        if self._pool is None:
            import asyncpg  # type: ignore[import-not-found]

            self._pool = await asyncpg.create_pool(
                dsn=self._dsn,
                min_size=self._pool_min_size,
                max_size=self._pool_max_size,
            )
        return self._pool

    async def get(self, identifier: ID) -> T | None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f'SELECT data FROM {self._table_name} WHERE id = $1',
                str(identifier),
            )
            if row is None:
                self._miss_count += 1
                return None
            self._hit_count += 1
            return json.loads(row["data"])

    async def add(self, entity: T) -> None:
        pool = await self._ensure_pool()
        entity_dict = self._entity_to_dict(entity)
        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {self._table_name} (id, data, created_at)
                VALUES ($1, $2::jsonb, NOW())
                ON CONFLICT (id) DO UPDATE SET data = $2::jsonb, updated_at = NOW()
                """,
                str(entity_dict["id"]),
                json.dumps(entity_dict),
            )

    async def remove(self, identifier: ID) -> bool:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                f"DELETE FROM {self._table_name} WHERE id = $1",
                str(identifier),
            )
            return result != "DELETE 0"

    async def iter_all(self) -> AsyncIterator[T]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(f"SELECT data FROM {self._table_name}")
            for row in rows:
                yield json.loads(row["data"])

    async def clear(self) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(f"DELETE FROM {self._table_name}")

    async def cleanup_expired(self) -> int:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                f"DELETE FROM {self._table_name} WHERE expires_at < NOW()"
            )
            return int(result.split()[-1]) if result else 0

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    def get_stats(self) -> dict[str, Any]:
        return {
            "type": "postgresql",
            "table": self._table_name,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
        }

    @staticmethod
    def _entity_to_dict(entity: T) -> dict[str, Any]:
        if hasattr(entity, "model_dump"):
            return entity.model_dump()  # type: ignore[attr-defined]
        if hasattr(entity, "__dict__"):
            return entity.__dict__
        return {"id": str(entity)}


__all__ = ["PostgresRepository"]
