"""Unit tests for :mod:`eaip.runtime.queries`."""

from __future__ import annotations

import pytest
from pydantic_core import ValidationError

from eaip.exceptions.domain import QueryCacheError, QueryHandlerNotFoundError
from typing import ClassVar

from eaip.runtime.queries import Query, QueryBus, QueryCache, QueryHandler, QueryResult
from eaip.shared.time import Duration


# ---------------------------------------------------------------------------
# Test query types
# ---------------------------------------------------------------------------


class FindUser(Query[str]):
    query_type: ClassVar[str] = "test.find_user"
    user_id: str = ""


class ListOrders(Query[list[str]]):
    query_type: ClassVar[str] = "test.list_orders"
    customer_id: str = ""


# ---------------------------------------------------------------------------
# Test handlers
# ---------------------------------------------------------------------------


class FindUserHandler:
    async def handle(self, query: FindUser) -> str:
        return f"user:{query.user_id}"


class ListOrdersHandler:
    def __init__(self) -> None:
        self.call_count = 0

    async def handle(self, query: ListOrders) -> list[str]:
        self.call_count += 1
        return [f"order-{query.customer_id}-1", f"order-{query.customer_id}-2"]


class FailingHandler:
    async def handle(self, query: Query[str]) -> str:
        raise RuntimeError("handler failed")


# ---------------------------------------------------------------------------
# In-memory cache implementation for testing
# ---------------------------------------------------------------------------


class InMemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, object] = {}
        self._ttls: dict[str, Duration] = {}

    async def get(self, key: str) -> object | None:
        return self._store.get(key)

    async def set(self, key: str, value: object, ttl: Duration | None = None) -> None:
        self._store[key] = value
        if ttl is not None:
            self._ttls[key] = ttl

    async def delete(self, key: str) -> bool:
        self._ttls.pop(key, None)
        return self._store.pop(key, None) is not None

    async def clear(self) -> None:
        self._store.clear()
        self._ttls.clear()


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_create_query_bus() -> None:
    bus = QueryBus()
    assert bus is not None


def test_create_query_bus_with_cache() -> None:
    cache = InMemoryCache()
    bus = QueryBus(cache=cache)
    assert bus is not None


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_register_handler() -> None:
    bus = QueryBus()
    handler = FindUserHandler()
    bus.register(FindUser, handler)
    assert bus.has_handler(FindUser)
    assert bus.get_handler(FindUser) is handler


def test_unregister_handler() -> None:
    bus = QueryBus()
    bus.register(FindUser, FindUserHandler())
    assert bus.unregister(FindUser) is True
    assert not bus.has_handler(FindUser)


def test_unregister_unknown_returns_false() -> None:
    bus = QueryBus()
    assert bus.unregister(FindUser) is False


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_success() -> None:
    bus = QueryBus()
    bus.register(FindUser, FindUserHandler())

    result = await bus.dispatch(FindUser(user_id="abc"))
    assert result.success
    assert result.result == "user:abc"
    assert not result.cached


@pytest.mark.asyncio
async def test_dispatch_no_handler_raises() -> None:
    bus = QueryBus()
    with pytest.raises(QueryHandlerNotFoundError):
        await bus.dispatch(FindUser(user_id="abc"))


@pytest.mark.asyncio
async def test_dispatch_handler_error() -> None:
    bus = QueryBus()
    bus.register(FindUser, FailingHandler())

    result = await bus.dispatch(FindUser(user_id="abc"))
    assert not result.success
    assert result.error is not None


@pytest.mark.asyncio
async def test_dispatch_raise_on_failure() -> None:
    bus = QueryBus()
    bus.register(FindUser, FailingHandler())

    with pytest.raises(RuntimeError):
        await bus.dispatch(FindUser(user_id="abc"), raise_on_failure=True)


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_hit_returns_cached_value() -> None:
    cache = InMemoryCache()
    bus = QueryBus(cache=cache)
    handler = ListOrdersHandler()
    bus.register(ListOrders, handler)

    # First call — should call handler and cache result.
    result1 = await bus.dispatch(
        ListOrders(customer_id="c1"),
        cache_ttl=Duration.from_seconds(60),
    )
    assert result1.success
    assert result1.result == ["order-c1-1", "order-c1-2"]
    assert not result1.cached
    assert handler.call_count == 1

    # Second call — should return cached result.
    result2 = await bus.dispatch(
        ListOrders(customer_id="c1"),
        cache_ttl=Duration.from_seconds(60),
    )
    assert result2.success
    assert result2.result == ["order-c1-1", "order-c1-2"]
    assert result2.cached
    assert handler.call_count == 1  # handler not called again


@pytest.mark.asyncio
async def test_cache_miss_calls_handler() -> None:
    cache = InMemoryCache()
    bus = QueryBus(cache=cache)
    handler = ListOrdersHandler()
    bus.register(ListOrders, handler)

    result = await bus.dispatch(
        ListOrders(customer_id="c1"),
        cache_ttl=Duration.from_seconds(60),
    )
    assert not result.cached
    assert handler.call_count == 1


@pytest.mark.asyncio
async def test_bypass_cache() -> None:
    cache = InMemoryCache()
    bus = QueryBus(cache=cache)
    handler = ListOrdersHandler()
    bus.register(ListOrders, handler)

    # Cache the result.
    await bus.dispatch(ListOrders(customer_id="c1"), cache_ttl=Duration.from_seconds(60))
    assert handler.call_count == 1

    # Bypass cache — handler should be called again.
    result = await bus.dispatch(
        ListOrders(customer_id="c1"),
        cache_ttl=Duration.from_seconds(60),
        bypass_cache=True,
    )
    assert not result.cached
    assert handler.call_count == 2


@pytest.mark.asyncio
async def test_cache_not_used_when_no_ttl() -> None:
    cache = InMemoryCache()
    bus = QueryBus(cache=cache)
    handler = ListOrdersHandler()
    bus.register(ListOrders, handler)

    await bus.dispatch(ListOrders(customer_id="c1"))  # no cache_ttl
    assert handler.call_count == 1

    # Handler should be called again (nothing cached).
    await bus.dispatch(ListOrders(customer_id="c1"))  # no cache_ttl again
    assert handler.call_count == 2


# ---------------------------------------------------------------------------
# Cache invalidation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalidate_cache() -> None:
    cache = InMemoryCache()
    bus = QueryBus(cache=cache)
    handler = ListOrdersHandler()
    bus.register(ListOrders, handler)

    await bus.dispatch(ListOrders(customer_id="c1"), cache_ttl=Duration.from_seconds(60))
    assert handler.call_count == 1

    invalidated = await bus.invalidate(ListOrders(customer_id="c1"))
    assert invalidated

    # Next call should go to handler.
    await bus.dispatch(ListOrders(customer_id="c1"), cache_ttl=Duration.from_seconds(60))
    assert handler.call_count == 2


@pytest.mark.asyncio
async def test_invalidate_no_cache() -> None:
    bus = QueryBus()  # no cache
    result = await bus.invalidate(FindUser(user_id="abc"))
    assert not result


@pytest.mark.asyncio
async def test_clear_cache() -> None:
    cache = InMemoryCache()
    bus = QueryBus(cache=cache)
    handler = ListOrdersHandler()
    bus.register(ListOrders, handler)

    await bus.dispatch(ListOrders(customer_id="c1"), cache_ttl=Duration.from_seconds(60))
    await bus.clear_cache()
    assert cache._store == {}


# ---------------------------------------------------------------------------
# Query model
# ---------------------------------------------------------------------------


def test_query_is_frozen() -> None:
    q = FindUser(user_id="123")
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        q.user_id = "changed"  # type: ignore[misc]


def test_query_extra_fields_forbidden() -> None:
    with pytest.raises((ValueError, TypeError, ValidationError)):
        FindUser(user_id="123", extra="x")  # type: ignore[call-arg]


def test_query_has_occurred_at() -> None:
    q = FindUser(user_id="123")
    assert q.occurred_at is not None


# ---------------------------------------------------------------------------
# QueryCache protocol
# ---------------------------------------------------------------------------


class _MinimalCache:
    """Minimal cache implementing the QueryCache protocol."""

    def __init__(self) -> None:
        self._data: dict[str, object] = {}

    async def get(self, key: str) -> object | None:
        return self._data.get(key)

    async def set(self, key: str, value: object, ttl: Duration | None = None) -> None:
        self._data[key] = value

    async def delete(self, key: str) -> bool:
        return self._data.pop(key, None) is not None

    async def clear(self) -> None:
        self._data.clear()


@pytest.mark.asyncio
async def test_minimal_cache_works_with_query_bus() -> None:
    cache = _MinimalCache()
    bus = QueryBus(cache=cache)
    bus.register(FindUser, FindUserHandler())

    result = await bus.dispatch(FindUser(user_id="abc"), cache_ttl=Duration.from_seconds(30))
    assert result.success
    assert result.result == "user:abc"
