"""A typed factory keyed by string identifier."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

from eaip.exceptions.domain import (
    DuplicateRegistrationError,
    NotFoundError,
)

T = TypeVar("T")
Builder = Callable[..., T]


class Factory(Generic[T]):
    """A key-to-builder factory with strict registration semantics.

    Builders may receive arbitrary keyword arguments; the factory does not
    introspect or validate them — that responsibility belongs to the builder.
    """

    __slots__ = ("_builders", "_name")

    def __init__(self, *, name: str) -> None:
        if not name:
            raise ValueError("factory name must be non-empty")
        self._name = name
        self._builders: dict[str, Builder[T]] = {}

    @property
    def name(self) -> str:
        return self._name

    def register(self, key: str, builder: Builder[T], *, replace: bool = False) -> None:
        """Register ``builder`` under ``key``.

        Raises :class:`DuplicateRegistrationError` if the key exists and
        ``replace`` is False.
        """
        if not key:
            raise ValueError("factory key must be non-empty")
        if key in self._builders and not replace:
            raise DuplicateRegistrationError(
                f"factory {self._name!r} already has a builder for key {key!r}",
                context={"factory": self._name, "key": key},
            )
        self._builders[key] = builder

    def unregister(self, key: str) -> bool:
        """Remove the builder for ``key``. Returns True if it existed."""
        return self._builders.pop(key, None) is not None

    def create(self, key: str, /, **kwargs: object) -> T:
        """Invoke the builder registered under ``key``."""
        builder = self._builders.get(key)
        if builder is None:
            raise NotFoundError(
                f"factory {self._name!r} has no builder for key {key!r}",
                context={"factory": self._name, "key": key, "available": sorted(self._builders)},
            )
        return builder(**kwargs)

    def keys(self) -> list[str]:
        return sorted(self._builders)

    def __contains__(self, key: str) -> bool:
        return key in self._builders

    def __len__(self) -> int:
        return len(self._builders)


__all__ = ["Builder", "Factory"]
