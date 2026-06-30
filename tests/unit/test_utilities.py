"""Tests for :mod:`eaip.utilities`."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable

import pytest

from eaip.utilities import (
    camel_to_snake,
    chunked,
    first,
    gather_with_concurrency,
    run_with_timeout,
    snake_to_camel,
    truncate,
    unique,
)


def test_chunked_evenly() -> None:
    assert list(chunked(range(6), 2)) == [[0, 1], [2, 3], [4, 5]]


def test_chunked_uneven_tail() -> None:
    assert list(chunked(range(5), 2)) == [[0, 1], [2, 3], [4]]


def test_chunked_zero_size_rejected() -> None:
    with pytest.raises(ValueError):
        list(chunked([1], 0))


def test_first_returns_default() -> None:
    assert first([], default=42) == 42
    assert first([1, 2]) == 1


def test_unique_preserves_order() -> None:
    assert unique([3, 1, 3, 2, 1]) == [3, 1, 2]


@pytest.mark.parametrize(
    "src,expected",
    [("camelCase", "camel_case"), ("PascalCase", "pascal_case"), ("ABTest", "a_b_test")],
)
def test_camel_to_snake(src: str, expected: str) -> None:
    assert camel_to_snake(src) == expected


def test_snake_to_camel_roundtrip() -> None:
    assert snake_to_camel("hello_world") == "helloWorld"
    assert snake_to_camel("hello_world", upper_first=True) == "HelloWorld"


def test_truncate() -> None:
    assert truncate("abcdef", max_length=4) == "abc…"
    assert truncate("abc", max_length=10) == "abc"


def test_truncate_short_max_rejected() -> None:
    with pytest.raises(ValueError):
        truncate("x", max_length=0)


@pytest.mark.asyncio
async def test_gather_with_concurrency_respects_limit() -> None:
    inflight = 0
    max_seen = 0
    lock = asyncio.Lock()

    async def task(_i: int) -> int:
        nonlocal inflight, max_seen
        async with lock:
            inflight += 1
            max_seen = max(max_seen, inflight)
        await asyncio.sleep(0.01)
        async with lock:
            inflight -= 1
        return _i

    coros: list[Awaitable[int]] = [task(i) for i in range(10)]
    results = await gather_with_concurrency(coros, limit=3)
    assert sorted(results) == list(range(10))
    assert max_seen <= 3


@pytest.mark.asyncio
async def test_gather_rejects_zero_limit() -> None:
    with pytest.raises(ValueError):
        await gather_with_concurrency([], limit=0)


@pytest.mark.asyncio
async def test_run_with_timeout_fires() -> None:
    async def slow() -> None:
        await asyncio.sleep(0.5)

    with pytest.raises(asyncio.TimeoutError):
        await run_with_timeout(slow(), seconds=0.01)
