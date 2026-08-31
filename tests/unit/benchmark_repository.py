"""Performance benchmarks for repository and cache hot-path operations."""

from __future__ import annotations

import time
from dataclasses import dataclass

from eaip.shared.repository import InMemoryRepository


@dataclass
class _Item:
    id: int
    data: str


class TestRepositoryBenchmarks:
    async def test_get_throughput(self) -> None:
        repo = InMemoryRepository[int, _Item](max_size=100_000)
        for i in range(10_000):
            await repo.add(_Item(id=i, data=f"value{i}"), ttl_seconds=3600)
        start = time.monotonic()
        for i in range(10_000):
            await repo.get(i)
        elapsed = time.monotonic() - start
        ops = 10_000 / elapsed
        assert ops > 10_000, f"get throughput too low: {ops:.0f} ops/s"

    async def test_add_throughput(self) -> None:
        repo = InMemoryRepository[int, _Item](max_size=100_000)
        start = time.monotonic()
        for i in range(10_000):
            await repo.add(_Item(id=i, data=f"value{i}"), ttl_seconds=3600)
        elapsed = time.monotonic() - start
        ops = 10_000 / elapsed
        assert ops > 5_000, f"add throughput too low: {ops:.0f} ops/s"

    async def test_lru_eviction_throughput(self) -> None:
        small = InMemoryRepository[int, _Item](max_size=100)
        start = time.monotonic()
        for i in range(10_000):
            await small.add(_Item(id=i, data=f"v{i}"), ttl_seconds=3600)
        elapsed = time.monotonic() - start
        ops = 10_000 / elapsed
        assert ops > 5_000, f"eviction throughput too low: {ops:.0f} ops/s"
        assert small.eviction_count == 10_000 - 100

    async def test_iter_all_throughput(self) -> None:
        repo = InMemoryRepository[int, _Item](max_size=100_000)
        for i in range(5_000):
            await repo.add(_Item(id=i, data=f"value{i}"), ttl_seconds=3600)
        start = time.monotonic()
        count = 0
        async for _ in repo.iter_all():
            count += 1
        elapsed = time.monotonic() - start
        assert count == 5_000
        ops = 5_000 / elapsed
        assert ops > 5_000, f"iter_all throughput too low: {ops:.0f} items/s"


class TestResponseCacheBenchmarks:
    async def test_cache_get_set_throughput(self) -> None:
        from eaip.apiext.caching import ResponseCache

        cache = ResponseCache(max_size=100_000, default_ttl=300.0)
        start = time.monotonic()
        for i in range(5_000):
            await cache.set(f"key{i}", {"data": f"value{i}"})
        for i in range(5_000):
            await cache.get(f"key{i}")
        elapsed = time.monotonic() - start
        ops = 10_000 / elapsed
        assert ops > 2_000, f"cache throughput too low: {ops:.0f} ops/s"
