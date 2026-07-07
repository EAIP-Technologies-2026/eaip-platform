"""A typed, observable, key→value registry.

Three concrete registries in the Foundation are built atop this generic
implementation:

* :class:`eaip.capabilities.CapabilityRegistry`
* :class:`eaip.plugins.PluginRegistry`
* The DI container's binding table (`Container._providers`).

A `Registry` is *not* a `dict`: it enforces uniqueness, broadcasts changes
via callbacks, and validates that every value satisfies a declared base
type. These extras are cheap and pay back richly in operability.
"""

from __future__ import annotations

import contextlib
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import StrEnum
from typing import Generic, Self, TypeVar

from eaip.exceptions.domain import (
    DuplicateRegistrationError,
    NotFoundError,
    RegistryTypeMismatchError,
)

T = TypeVar("T")


class RegistryEvent(StrEnum):
    """Registry events."""

    REGISTERED = "registered"
    """Entry registered."""
    UNREGISTERED = "unregistered"
    """Entry unregistered."""
    REPLACED = "replaced"
    """Entry replaced."""


@dataclass(frozen=True, slots=True)
class RegistryChange(Generic[T]):
    """Payload delivered to registry observers.

    Attributes:
        event: The event type.
        key: The key involved in the event.
        value: The value involved in the event.
    """

    event: RegistryEvent
    key: str
    value: T


Observer = Callable[[RegistryChange[T]], None]


class Registry(Generic[T]):
    """Type-safe, observable, name-keyed registry."""

    __slots__ = ("_items", "_lock", "_name", "_observers", "_value_type")

    def __init__(self: Self, *, name: str, value_type: type[T]) -> None:
        """Initialize a new Registry instance.

        Args:
            name: The name of the registry.
            value_type: The type of values allowed in the registry.

        Raises:
            ValueError: If the registry name is empty.
        """
        if not name:
            raise ValueError("registry name must be non-empty")
        self._name = name
        self._value_type = value_type
        self._items: dict[str, T] = {}
        self._observers: list[Observer[T]] = []
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def name(self: Self) -> str:
        """Return the name of the registry."""
        return self._name

    @property
    def value_type(self: Self) -> type[T]:
        """Return the declared value type."""
        return self._value_type

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------
    def register(self: Self, key: str, value: T, *, replace: bool = False) -> None:
        """Register ``value`` under ``key``.

        Args:
            key: The key to register the value under.
            value: The value to register.
            replace: If True, replace an existing entry.

        Raises:
            ValueError: If the key is empty or whitespace.
            RegistryTypeMismatchError: If the value type does not match.
            DuplicateRegistrationError: If the key already exists and replace is False.
        """
        if not key or not key.strip():
            raise ValueError("registry key must be non-empty")
        if not isinstance(value, self._value_type):
            raise RegistryTypeMismatchError(
                f"value of type {type(value).__name__} is not a {self._value_type.__name__}",
                context={"registry": self._name, "key": key},
            )
        with self._lock:
            existed = key in self._items
            if existed and not replace:
                raise DuplicateRegistrationError(
                    f"registry {self._name!r} already contains {key!r}",
                    context={"registry": self._name, "key": key},
                )
            self._items[key] = value
            change = RegistryChange(
                event=RegistryEvent.REPLACED if existed else RegistryEvent.REGISTERED,
                key=key,
                value=value,
            )
        self._notify(change)

    def unregister(self: Self, key: str) -> bool:
        """Remove ``key``.

        Args:
            key: The key to remove.

        Returns:
            True if the key existed, False otherwise.
        """
        with self._lock:
            value = self._items.pop(key, None)
            removed = value is not None
        if removed:
            self._notify(RegistryChange(event=RegistryEvent.UNREGISTERED, key=key, value=value))  # type: ignore[arg-type]
        return removed

    def clear(self: Self) -> None:
        """Remove every entry from the registry."""
        with self._lock:
            self._items.clear()

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------
    def get(self: Self, key: str) -> T:
        """Return the value for ``key``.

        Args:
            key: The key to look up.

        Returns:
            The value associated with the key.

        Raises:
            NotFoundError: If the key is not in the registry.
        """
        try:
            return self._items[key]
        except KeyError as exc:
            raise NotFoundError(
                f"{self._name!r} has no entry for {key!r}",
                context={"registry": self._name, "key": key, "available": sorted(self._items)},
            ) from exc

    def try_get(self: Self, key: str) -> T | None:
        """Return the value for ``key``, or None if not found.

        Args:
            key: The key to look up.

        Returns:
            The value associated with the key, or None.
        """
        return self._items.get(key)

    def has(self: Self, key: str) -> bool:
        """Check if the key is in the registry.

        Args:
            key: The key to check.

        Returns:
            True if the key exists, False otherwise.
        """
        return key in self._items

    def keys(self: Self) -> list[str]:
        """Return a sorted list of keys.

        Returns:
            A sorted list of keys in the registry.
        """
        return sorted(self._items)

    def values(self: Self) -> list[T]:
        """Return a list of values.

        Returns:
            A list of values in the registry.
        """
        return list(self._items.values())

    def items(self: Self) -> list[tuple[str, T]]:
        """Return a list of (key, value) pairs.

        Returns:
            A list of (key, value) pairs in the registry.
        """
        return list(self._items.items())

    def __iter__(self: Self) -> Iterator[str]:
        """Return an iterator over the sorted keys.

        Returns:
            An iterator over the sorted keys.
        """
        return iter(sorted(self._items))

    def __len__(self: Self) -> int:
        """Return the number of items in the registry.

        Returns:
            The number of items in the registry.
        """
        return len(self._items)

    def __contains__(self: Self, key: str) -> bool:
        """Check if the key is in the registry.

        Args:
            key: The key to check.

        Returns:
            True if the key exists, False otherwise.
        """
        return key in self._items

    # ------------------------------------------------------------------
    # Observation
    # ------------------------------------------------------------------
    def observe(self: Self, observer: Observer[T]) -> Callable[[], None]:
        """Register an observer.

        Args:
            observer: The observer function to register.

        Returns:
            A function that removes the observer.
        """
        with self._lock:
            self._observers.append(observer)

        def _remove() -> None:
            with self._lock, contextlib.suppress(ValueError):
                self._observers.remove(observer)

        return _remove

    def _notify(self, change: RegistryChange[T]) -> None:
        for obs in list(self._observers):
            with contextlib.suppress(BaseException):
                obs(change)


__all__ = ["Observer", "Registry", "RegistryChange", "RegistryEvent"]
