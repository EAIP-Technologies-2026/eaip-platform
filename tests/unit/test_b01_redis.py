"""B01 — Redis cache provider verification (mocked; Redis optional)."""

from __future__ import annotations

import json
import sys
from types import ModuleType

import pytest

from eaip.infrastructure.redis_cache import RedisCacheProvider


class FakeRedisClient:
    def __init__(self) -> None:
        self.deleted: list[str] = []
        self.flushed = False
        self._store: dict[str, str] = {}
        self.ping_ok = True

    async def ping(self) -> bool:
        if not self.ping_ok:
            raise ConnectionError("down")
        return True

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def setex(self, key: str, _ttl: int, value: str) -> None:
        self._store[key] = value

    async def keys(self, pattern: str) -> list[str]:
        prefix = pattern.split("*")[0]
        return [k for k in self._store if k.startswith(prefix)]

    async def delete(self, *keys: str) -> int:
        self.deleted.extend(keys)
        for key in keys:
            self._store.pop(key, None)
        return len(keys)

    async def flushdb(self) -> None:
        self.flushed = True
        self._store.clear()

    async def info(self, _section: str) -> dict[str, int]:
        return {"keyspace_hits": 3, "keyspace_misses": 1}

    async def close(self) -> None:
        return


class FakeRedisModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("redis.asyncio")
        self._client = FakeRedisClient()

    def from_url(self, *_args: object, **_kwargs: object) -> FakeRedisClient:
        return self._client


@pytest.fixture
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> FakeRedisClient:
    module = FakeRedisModule()
    monkeypatch.setitem(sys.modules, "redis", ModuleType("redis"))
    monkeypatch.setitem(sys.modules, "redis.asyncio", module)
    return module._client


class TestRedisCacheProvider:
    def test_tenant_key(self) -> None:
        assert (
            RedisCacheProvider.tenant_key("acme", "knowledge", "doc-1")
            == "tenant:acme:knowledge:doc-1"
        )

    async def test_get_hit(self, fake_redis: FakeRedisClient) -> None:
        fake_redis._store["k"] = json.dumps({"value": 42})
        cache = RedisCacheProvider()
        assert await cache.get("k") == {"value": 42}

    async def test_get_miss(self, fake_redis: FakeRedisClient) -> None:
        cache = RedisCacheProvider()
        assert await cache.get("missing") is None

    async def test_set_then_get(self, fake_redis: FakeRedisClient) -> None:
        cache = RedisCacheProvider()
        await cache.set("k", {"a": 1}, ttl=60)
        assert await cache.get("k") == {"a": 1}

    async def test_invalidate(self, fake_redis: FakeRedisClient) -> None:
        fake_redis._store["tenant:acme:kb:a"] = "x"
        fake_redis._store["tenant:acme:kb:b"] = "y"
        cache = RedisCacheProvider()
        removed = await cache.invalidate("tenant:acme:kb:*")
        assert removed == 2
        assert set(fake_redis.deleted) == {"tenant:acme:kb:a", "tenant:acme:kb:b"}

    async def test_clear(self, fake_redis: FakeRedisClient) -> None:
        cache = RedisCacheProvider()
        await cache.clear()
        assert fake_redis.flushed

    async def test_degraded_when_ping_fails(self, fake_redis: FakeRedisClient) -> None:
        fake_redis.ping_ok = False
        cache = RedisCacheProvider()
        assert await cache.get("k") is None
        await cache.set("k", 1, ttl=10)
        await cache.clear()
        stats = await cache.get_stats()
        assert stats["degraded"] is True
        assert stats["miss_count"] >= 1

    async def test_degraded_when_package_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setitem(sys.modules, "redis", ModuleType("redis"))
        monkeypatch.setitem(
            sys.modules, "redis.asyncio", ModuleType("redis.asyncio")
        )  # importable but has no from_url
        cache = RedisCacheProvider()
        assert await cache.get("k") is None
        await cache.set("k", 1, ttl=10)  # must not raise
        assert await cache.ping() is False

    async def test_get_stats(self, fake_redis: FakeRedisClient) -> None:
        cache = RedisCacheProvider()
        await cache.set("k", 1, ttl=10)
        await cache.get("k")
        await cache.get("nope")
        stats = await cache.get_stats()
        assert stats["type"] == "redis"
        assert stats["hit_count"] == 1
        assert stats["miss_count"] == 1
        assert stats["redis_keyspace_hits"] == 3