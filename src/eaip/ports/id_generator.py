"""Identifier-generator port."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class IdGeneratorPort(Protocol):
    """Produces opaque, globally-unique string identifiers."""

    def new_id(self) -> str: ...


__all__ = ["IdGeneratorPort"]
