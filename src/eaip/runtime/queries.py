"""Runtime Query Bus — CQRS query dispatch with caching and async support.

The :class:`QueryBus` provides a type-routed query dispatch mechanism:

1. Queries are frozen Pydantic models that describe *what* to fetch.
2. Handlers are registered per query type and return typed results.
3. A caching layer may be injected to avoid redundant execution.

Usage::

    class GetOrder(Query[Order]):
        order_id: str

    class GetOrderHandler:
        async def handle(self, query: GetOrder) -> Order:
            ...

    bus = QueryBus()
    bus.register(GetOrder, GetOrderHandler())
    result = await bus.dispatch(GetOrder(order_id="123"))
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Protocol, TypeVar, runtime_checkable

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from eaip.exceptions.domain import QueryCacheError, QueryHandlerNotFoundError
from eaip.logging.context import get_logger
from eaip.shared.time import Duration, utc_now

# ---------------------------------------------------------------------------
# Query message base
# ---------------------------------------------------------------------------


QRes = TypeVar("QRes")


class Query(BaseModel, Generic[QRes]):
    """Base class for all query messages.

    Subclasses declare their payload as Pydantic fields and specify the
    return type via ``Generic[QRes]``.

    Example::

        class FindUser(Query[User]):
            user_id: str
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    query_type: ClassVar[str] = "eaip.query"
    occurred_at: datetime = Field(default_factory=utc_now)
    correlation_id: str | None = Field(default=None)


# ---------------------------------------------------------------------------
# Handler protocol
# ---------------------------------------------------------------------------


Q = TypeVar("Q", bound=Query[Any])


@runtime_checkable
class QueryHandler(Protocol, Generic[Q]):
    """Protocol for query handlers.

    A handler receives a query instance and returns the result of type ``QRes``.
    """

    async def handle(self, query: Q) -> Any: ...


# ---------------------------------------------------------------------------
# Cache abstraction
# ---------------------------------------------------------------------------


@runtime_checkable
class QueryCache(Protocol):
    """Protocol for query result caches.

    Implementations must be thread-safe and should handle serialisation
    transparently.
    """

    async def get(self, key: str) -> Any | None:
        """Return the cached value for *key*, or ``None`` if absent."""
        ...

    async def set(self, key: str, value: Any, ttl: Duration | None = None) -> None:
        """Store *value* under *key* with an optional TTL."""
        ...

    async def delete(self, key: str) -> bool:
        """Remove *key* from the cache.  Returns ``True`` if it existed."""
        ...

    async def clear(self) -> None:
        """Remove all entries from the cache."""
        ...


# ---------------------------------------------------------------------------
# Query result
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class QueryResult(Generic[QRes]):
    """Result of a query dispatch.

    Attributes
    ----------
    success:
        Whether the query completed without error.
    result:
        The handler's return value, if successful.
    error:
        The exception that was raised, if any.
    cached:
        ``True`` if the result was served from cache.
    """
    success: bool
    result: QRes | None = None
    error: BaseException | None = None
    cached: bool = False


# ---------------------------------------------------------------------------
# Query Bus
# ---------------------------------------------------------------------------


class QueryBus:
    """Type-routed query bus with optional caching.

    Usage::

        bus = QueryBus()
        bus.register(FindUser, FindUserHandler())

        # Without cache
        result = await bus.dispatch(FindUser(user_id="abc"))

        # With cache (TTL-based)
        bus = QueryBus(cache=InMemoryCache())

        result = await bus.dispatch(
            FindUser(user_id="abc"),
            cache_ttl=Duration.from_seconds(30),
        )
    """

    def __init__(self, cache: QueryCache | None = None) -> None:
        self._handlers: dict[str, QueryHandler[Any]] = {}
        self._cache: QueryCache | None = cache
        self._log = get_logger("eaip.runtime.queries")

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        query_type: type[Q],
        handler: QueryHandler[Q],
    ) -> None:
        """Register *handler* for *query_type*.

        Args:
            query_type:
                The query class to handle.
            handler:
                An object satisfying the :class:`QueryHandler` protocol.
        """
        key = self._key(query_type)
        if key in self._handlers:
            self._log.warning(
                "queries.handler_replaced",
                query_type=query_type.__name__,
            )
        self._handlers[key] = handler

    def unregister(self, query_type: type[Q]) -> bool:
        """Remove the handler for *query_type*.  Returns ``True`` if present."""
        key = self._key(query_type)
        return self._handlers.pop(key, None) is not None

    def has_handler(self, query_type: type[Q]) -> bool:
        return self._key(query_type) in self._handlers

    def get_handler(self, query_type: type[Q]) -> QueryHandler[Q] | None:
        key = self._key(query_type)
        return self._handlers.get(key)

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    async def dispatch(
        self,
        query: Q,
        *,
        cache_ttl: Duration | None = None,
        bypass_cache: bool = False,
        raise_on_failure: bool = False,
    ) -> QueryResult[QRes]:
        """Dispatch *query* to its registered handler.

        Args:
            query:
                The query instance to dispatch.
            cache_ttl:
                If set (and a cache is configured), the result is cached with
                this TTL and subsequent identical queries return the cached
                value.
            bypass_cache:
                If ``True``, skip the cache and execute the handler directly.
            raise_on_failure:
                If ``True``, re-raise the underlying exception instead of
                returning a :class:`QueryResult`.

        Returns:
            A :class:`QueryResult` with the handler's result.

        Raises:
            QueryHandlerNotFoundError:
                If no handler is registered for the query type.
        """
        key = self._key(type(query))
        handler = self._handlers.get(key)
        if handler is None:
            raise QueryHandlerNotFoundError(
                f"no handler registered for {type(query).__name__}",
                context={"query_type": type(query).__name__},
            )

        # Resolve identity (cache key) from the query.
        cache_key = await self._resolve_cache_key(query)

        # Check cache.
        if self._cache is not None and cache_ttl is not None and not bypass_cache:
            try:
                cached = await self._cache.get(cache_key)
                if cached is not None:
                    return QueryResult(success=True, result=cached, cached=True)
            except BaseException as exc:
                self._log.warning(
                    "queries.cache.get_failed",
                    error=repr(exc),
                )

        # Execute handler.
        try:
            result = handler.handle(query)
            if inspect.isawaitable(result):
                result = await result
        except BaseException as exc:
            if raise_on_failure:
                raise
            return QueryResult(success=False, error=exc)

        # Store in cache.
        if self._cache is not None and cache_ttl is not None and not bypass_cache:
            try:
                await self._cache.set(cache_key, result, ttl=cache_ttl)
            except BaseException as exc:
                self._log.warning(
                    "queries.cache.set_failed",
                    error=repr(exc),
                )

        return QueryResult(success=True, result=result)

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    async def invalidate(self, query: Q) -> bool:
        """Remove a specific query result from the cache.

        Returns ``True`` if the key existed.
        """
        if self._cache is None:
            return False
        key = await self._resolve_cache_key(query)
        try:
            return await self._cache.delete(key)
        except BaseException as exc:
            raise QueryCacheError(
                f"failed to invalidate cache for {type(query).__name__}",
                context={"query_type": type(query).__name__},
                cause=exc,
            ) from exc

    async def clear_cache(self) -> None:
        """Remove all entries from the cache."""
        if self._cache is not None:
            try:
                await self._cache.clear()
            except BaseException as exc:
                raise QueryCacheError(
                    "failed to clear cache",
                    cause=exc,
                ) from exc

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _key(query_type: type[Query[Any]]) -> str:
        return f"{query_type.__module__}.{query_type.__qualname__}"

    @staticmethod
    async def _resolve_cache_key(query: Query[Any]) -> str:
        """Produce a deterministic cache key for a query instance.

        Override in a subclass for custom key generation.
        """
        model_dump = query.model_dump(exclude={"occurred_at", "correlation_id"})
        return f"{type(query).__qualname__}:{hash(frozenset(model_dump.items()))}"


__all__ = [
    "Query",
    "QueryBus",
    "QueryCache",
    "QueryHandler",
    "QueryResult",
]
