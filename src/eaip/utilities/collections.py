"""Collection helpers used throughout the platform."""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Iterator
from typing import TypeVar

T = TypeVar("T")
H = TypeVar("H", bound=Hashable)


def chunked(items: Iterable[T], size: int) -> Iterator[list[T]]:
    """Yield successive ``size``-sized chunks from ``items``.

    The final chunk may be shorter than ``size``.
    """
    if size < 1:
        raise ValueError("chunk size must be ≥ 1")
    batch: list[T] = []
    for item in items:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def first(items: Iterable[T], default: T | None = None) -> T | None:
    """Return the first item, or ``default`` if the iterable is empty."""
    for item in items:
        return item
    return default


def unique(items: Iterable[H]) -> list[H]:
    """Return a list of unique items, preserving order of first appearance."""
    seen: set[H] = set()
    result: list[H] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


__all__ = ["chunked", "first", "unique"]
