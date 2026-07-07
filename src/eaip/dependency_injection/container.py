"""A minimal, explicit dependency-injection container.

Design tenets
-------------
* **Explicit, not magical.** Bindings are registered by hand. There is no
  classpath scanning, no annotation-driven autowire.
* **Type-keyed.** Every binding is keyed by a concrete ``type`` so that
  resolution is statically analysable.
* **Scoped.** Three scopes — ``SINGLETON``, ``TRANSIENT``, ``SCOPED`` —
  cover every real-world need without ad-hoc lifetimes.
* **Cycle-safe.** Cyclic resolutions raise :class:`DependencyCycleError`
  rather than blowing the recursion stack.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar, cast

from eaip.dependency_injection.scope import Scope
from eaip.exceptions.domain import (
    DependencyCycleError,
    DuplicateRegistrationError,
    NotFoundError,
    RegistryTypeMismatchError,
)

T = TypeVar("T")

Factory = Callable[["Container"], Any]


@dataclass(slots=True)
class Provider:
    """Internal record describing how to build a binding."""

    key: type[Any]
    factory: Factory
    scope: Scope
    instance: Any = None
    _has_instance: bool = False



class _ResolveStack:
    """Per-thread re-entrancy tracker used to detect cycles."""

    __slots__ = ("frames",)

    def __init__(self) -> None:
        """Initialize an empty resolution stack."""
        self.frames: list[type[Any]] = []


class Container:
    """The DI container.

    Use :meth:`register`, :meth:`register_instance`, or :meth:`register_factory`
    to add bindings; :meth:`resolve` to retrieve them; :meth:`create_scope`
    to build a child container that shares singletons with the parent but
    holds its own scoped instances.
    """

    def __init__(self, *, parent: Container | None = None) -> None:
        """Initialize a new DI container.

        Args:
            parent: An optional parent container, whose singletons will be shared.
        """
        self._providers: dict[type[Any], Provider] = {}
        self._lock = threading.RLock()
        self._stack = _ResolveStack()
        self._parent = parent

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register_instance(self, key: type[T], instance: T) -> None:
        """Bind ``key`` to a pre-built singleton instance."""
        if not isinstance(instance, key):
            raise RegistryTypeMismatchError(
                f"instance is not an instance of {key.__name__}",
                context={"key": key.__name__, "instance_type": type(instance).__name__},
            )
        with self._lock:
            self._ensure_unique(key)
            provider = Provider(key=key, factory=lambda _c: instance, scope=Scope.SINGLETON)
            provider.instance = instance
            provider._has_instance = True
            self._providers[key] = provider

    def register_factory(
        self,
        key: type[T],
        factory: Callable[[Container], T],
        *,
        scope: Scope = Scope.SINGLETON,
    ) -> None:
        """Bind ``key`` to ``factory(container) -> T`` under ``scope``."""
        with self._lock:
            self._ensure_unique(key)
            self._providers[key] = Provider(key=key, factory=factory, scope=scope)

    def register(
        self,
        key: type[T],
        impl: type[T] | None = None,
        *,
        scope: Scope = Scope.SINGLETON,
    ) -> None:
        """Bind ``key`` to ``impl()`` — the most common case.

        If ``impl`` is omitted, ``key`` is its own implementation.
        """
        target = impl or key
        if not (isinstance(target, type) and issubclass(target, key)):
            raise RegistryTypeMismatchError(
                f"{target.__name__} is not a subclass of {key.__name__}",
                context={"key": key.__name__, "impl": target.__name__},
            )
        self.register_factory(key, lambda _c: target(), scope=scope)

    def _ensure_unique(self, key: type[Any]) -> None:
        if key in self._providers:
            raise DuplicateRegistrationError(
                f"container already has a binding for {key.__name__}",
                context={"key": key.__name__},
            )

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------
    def resolve(self, key: type[T]) -> T:
        """Return an instance bound to ``key``, building it as needed."""
        provider = self._find(key)
        if provider is None:
            raise NotFoundError(
                f"no binding registered for {key.__name__}",
                context={"key": key.__name__},
            )

        if key in self._stack.frames:
            raise DependencyCycleError(
                f"dependency cycle detected while resolving {key.__name__}",
                context={
                    "key": key.__name__,
                    "cycle": [k.__name__ for k in self._stack.frames] + [key.__name__],
                },
            )

        self._stack.frames.append(key)
        try:
            return cast(T, self._build(provider))
        finally:
            self._stack.frames.pop()

    def try_resolve(self, key: type[T]) -> T | None:
        """Like :meth:`resolve` but returns ``None`` for unknown bindings."""
        if self._find(key) is None:
            return None
        return self.resolve(key)

    def _find(self, key: type[Any]) -> Provider | None:
        provider = self._providers.get(key)
        if provider is not None:
            return provider
        if self._parent is not None:
            return self._parent._find(key)
        return None

    def _build(self, provider: Provider) -> Any:
        with self._lock:
            if provider.scope is Scope.SINGLETON and provider._has_instance:
                return provider.instance
            if (
                provider.scope is Scope.SCOPED
                and provider in self._providers.values()
                and provider._has_instance
            ):
                return provider.instance

            instance = provider.factory(self)
            if not isinstance(instance, provider.key):
                raise RegistryTypeMismatchError(
                    f"factory for {provider.key.__name__} produced {type(instance).__name__}",
                    context={"key": provider.key.__name__, "produced": type(instance).__name__},
                )
            if provider.scope is Scope.SINGLETON or (
                provider.scope is Scope.SCOPED and provider in self._providers.values()
            ):
                provider.instance = instance
                provider._has_instance = True
            return instance

    # ------------------------------------------------------------------
    # Introspection & lifecycle
    # ------------------------------------------------------------------
    def has(self, key: type[Any]) -> bool:
        """Check if a binding is registered for ``key``.

        Args:
            key: The type to check.

        Returns:
            True if a binding exists, False otherwise.
        """
        return self._find(key) is not None

    def keys(self) -> list[type[Any]]:
        """Return the list of all registered keys.

        Returns:
            A list of all registered types.
        """
        return list(self._providers)

    def create_scope(self) -> Container:
        """Build a child container sharing this container's singletons.

        Singletons resolved through the child still live in this (parent)
        container; only ``SCOPED`` providers re-registered in the child get a
        fresh instance per scope.
        """
        return Container(parent=self)


__all__ = ["Container", "Factory", "Provider"]
