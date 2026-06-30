"""Abstract repository contract.

Repositories in EAIP follow a small, deliberate surface area. Concrete
storage adapters (SQL, document, KV, vector) live in their own packages.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Generic, TypeVar

ID_co = TypeVar("ID_co", covariant=True)
T = TypeVar("T")


class AbstractRepository(ABC, Generic[ID_co, T]):
    """Generic async CRUD contract parameterised by identifier and aggregate."""

    @abstractmethod
    async def get(self, identifier: ID_co) -> T | None:
        """Return the aggregate or ``None`` if not found."""

    @abstractmethod
    async def add(self, entity: T) -> None:
        """Persist a new aggregate; must raise on duplicate identifier."""

    @abstractmethod
    async def remove(self, identifier: ID_co) -> bool:
        """Delete the aggregate; return ``True`` if it existed."""

    @abstractmethod
    def iter_all(self) -> AsyncIterator[T]:
        """Stream every aggregate. Implementations should be lazy."""


__all__ = ["AbstractRepository"]
