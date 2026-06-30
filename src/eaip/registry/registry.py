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

import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import StrEnum
from typing import Generic, TypeVar

from eaip.exceptions.domain import (
    DuplicateRegistrationError,
    NotFoundError,
    RegistryTypeMismatchError,
)

T = TypeVar("T")


class RegistryEvent(StrEnum):
    REGISTERED = "registered"
    UNREGISTERED = "unregistered"
    REPLACED = "replaced"


@dataclass(frozen=True, slots=True)
class RegistryChange(Generic[T]):
    """Payload delivered to registry observers."""

    event: RegistryEvent
    key: str
    value: T


Observer = Callable[[RegistryChange[T]], None]


class Registry(Generic[T]):
    """Type-safe, observable, name-keyed registry."""

    __slots__ = ("_items", "_lock", "_name", "_observers", "_value_type")

    def __init__(self, *, name: str, value_type: type[T]) -> None:
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
    def name(self) -> str:
        return self._name

    @property
    def value_type(self) -> type[T]:
        return self._value_type

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------
    def register(self, key: str, value: T, *, replace: bool = False) -> None:
        """Register ``value`` under ``key``.

        Raises :class:`DuplicateRegistrationError` if ``key`` exists unless
        ``replace=True`` is set. Type-checks ``value`` against the declared
        ``value_type``.
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

    def unregister(self, key: str) -> bool:
        """Remove ``key``. Returns ``True`` if it existed."""
        with self._lock:
            value = self._items.pop(key, None)
            removed = value is not None
        if removed:
            self._notify(RegistryChange(event=RegistryEvent.UNREGISTERED, key=key, value=value))  # type: ignore[arg-type]
        return removed

    def clear(self) -> None:
        """Remove every entry. Observers are not notified per item."""
        with self._lock:
            self._items.clear()

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------
    def get(self, key: str) -> T:
        """Return the value for ``key``; raises :class:`NotFoundError` if absent."""
        try:
            return self._items[key]
        except KeyError as exc:
            raise NotFoundError(
                f"{self._name!r} has no entry for {key!r}",
                context={"registry": self._name, "key": key, "available": sorted(self._items)},
            ) from exc

    def try_get(self, key: str) -> T | None:
        return self._items.get(key)

    def has(self, key: str) -> bool:
        return key in self._items

    def keys(self) -> list[str]:
        return sorted(self._items)

    def values(self) -> list[T]:
        return list(self._items.values())

    def items(self) -> list[tuple[str, T]]:
        return list(self._items.items())

    def __iter__(self) -> Iterator[str]:
        return iter(sorted(self._items))

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, key: str) -> bool:
        return key in self._items

    # ------------------------------------------------------------------
    # Observation
    # ------------------------------------------------------------------
    def observe(self, observer: Observer[T]) -> Callable[[], None]:
        """Register an observer; returns a function that removes it."""
        with self._lock:
            self._observers.append(observer)

        def _remove() -> None:
            with self._lock:
                try:
                    self._observers.remove(observer)
                except ValueError:
                    pass

        return _remove

    def _notify(self, change: RegistryChange[T]) -> None:
        for obs in list(self._observers):
            try:
                obs(change)
            except BaseException:  # noqa: BLE001 — observers must not break registry
                pass


__all__ = ["Observer", "Registry", "RegistryChange", "RegistryEvent"]
