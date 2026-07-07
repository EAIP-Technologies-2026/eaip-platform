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
        """Initializes a new Factory.

        Args:
            name: The name of the factory.
        """
        if not name:
            raise ValueError("factory name must be non-empty")
        self._name = name
        self._builders: dict[str, Builder[T]] = {}

    @property
    def name(self) -> str:
        """Returns the name of the factory.

        Returns:
            The factory name.
        """
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
        """Invoke the builder registered under ``key``.

        Args:
            key: The key under which the builder is registered.
            **kwargs: Keyword arguments to pass to the builder.

        Returns:
            The object created by the builder.

        Raises:
            NotFoundError: If no builder is registered under ``key``.
        """
        builder = self._builders.get(key)
        if builder is None:
            raise NotFoundError(
                f"factory {self._name!r} has no builder for key {key!r}",
                context={"factory": self._name, "key": key, "available": sorted(self._builders)},
            )
        return builder(**kwargs)

    def keys(self) -> list[str]:
        """Returns the registered keys in alphabetical order.

        Returns:
            A list of keys.
        """
        return sorted(self._builders)

    def __contains__(self, key: str) -> bool:
        """Checks if a key is registered.

        Args:
            key: The key to check.

        Returns:
            True if the key is registered, False otherwise.
        """
        return key in self._builders

    def __len__(self) -> int:
        """Returns the number of registered builders.

        Returns:
            The number of builders.
        """
        return len(self._builders)


__all__ = ["Builder", "Factory"]
