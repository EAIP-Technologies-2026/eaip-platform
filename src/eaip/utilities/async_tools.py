"""Asyncio helpers used widely by Foundation services."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Iterable
from typing import TypeVar

T = TypeVar("T")


async def gather_with_concurrency(
    awaitables: Iterable[Awaitable[T]],
    *,
    limit: int,
) -> list[T]:
    """Like :func:`asyncio.gather` but bounded to ``limit`` concurrent tasks.

    Parameters
    ----------
    awaitables:
        Iterable of awaitables to run.
    limit:
        Maximum number of concurrently-running awaitables. Must be ≥ 1.
    """
    if limit < 1:
        raise ValueError("limit must be ≥ 1")

    semaphore = asyncio.Semaphore(limit)

    async def _bounded(awaitable: Awaitable[T]) -> T:
        async with semaphore:
            return await awaitable

    return await asyncio.gather(*(_bounded(a) for a in awaitables))


async def run_with_timeout(
    awaitable: Awaitable[T],
    *,
    seconds: float,
) -> T:
    """Run ``awaitable`` with a deadline; raises :class:`TimeoutError` on expiry.

    Wraps :func:`asyncio.wait_for` so callers get a stable import surface
    even if the underlying mechanism changes.
    """
    if seconds <= 0:
        raise ValueError("timeout must be positive")
    return await asyncio.wait_for(awaitable, timeout=seconds)


__all__ = ["gather_with_concurrency", "run_with_timeout"]
