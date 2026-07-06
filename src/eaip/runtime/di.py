"""Runtime DI container — runtime-level dependency injection integration.

The :class:`RuntimeContainer` wraps the platform
:class:`~eaip.dependency_injection.container.Container` and adds
module-scoped lifecycle tracking.

This enables runtime modules to:

* **Resolve** platform-level services (event bus, health reporter, settings).
* **Declare module-scoped bindings** that live only as long as the module.
* **Scope cleanup** — when a module stops, its scoped bindings are discarded.

Design
------
The ``RuntimeContainer`` is **not** a replacement for the platform DI
container.  It is a thin runtime layer that:

1. Delegates ``resolve`` / ``try_resolve`` to the platform container.
2. Provides ``create_module_scope(module_name)`` → child
   :class:`~eaip.dependency_injection.container.Container`.
3. Provides ``drop_module_scope(module_name)`` for cleanup on module stop.

Module-scoped containers are **child containers** — they share singletons
with the root container but hold their own ``SCOPED`` and ``TRANSIENT``
instances.
"""

from __future__ import annotations

from typing import TypeVar

from eaip.dependency_injection.container import Container

T = TypeVar("T")


class RuntimeContainer:
    """Runtime-level DI with module-scoped lifecycle tracking.

    Parameters
    ----------
    container:
        The root platform :class:`~eaip.dependency_injection.container.Container`.
    """

    def __init__(self, container: Container) -> None:
        self._container = container
        self._module_scopes: dict[str, Container] = {}

    # ------------------------------------------------------------------
    # Resolution — delegated to the root container
    # ------------------------------------------------------------------

    def resolve(self, key: type[T]) -> T:
        """Resolve ``key`` from the root container.

        Delegates to :meth:`eaip.dependency_injection.container.Container.resolve`.
        """
        return self._container.resolve(key)

    def try_resolve(self, key: type[T]) -> T | None:
        """Resolve ``key`` or return ``None``.

        Delegates to :meth:`eaip.dependency_injection.container.Container.try_resolve`.
        """
        return self._container.try_resolve(key)

    # ------------------------------------------------------------------
    # Module-scope management
    # ------------------------------------------------------------------

    def create_module_scope(self, module_name: str) -> Container:
        """Create a child container scoped to ``module_name``.

        The child shares singletons with the root container.  Call
        :meth:`drop_module_scope` when the module stops to release its
        scoped resources.
        """
        scope = self._container.create_scope()
        self._module_scopes[module_name] = scope
        return scope

    def get_module_scope(self, module_name: str) -> Container | None:
        """Return the existing module scope for ``module_name``, or ``None``."""
        return self._module_scopes.get(module_name)

    def drop_module_scope(self, module_name: str) -> None:
        """Remove the module scope for ``module_name``.

        All ``SCOPED`` bindings in that scope become eligible for garbage
        collection once no references remain.
        """
        self._module_scopes.pop(module_name, None)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def active_module_scopes(self) -> list[str]:
        """Names of modules with active scoped containers."""
        return list(self._module_scopes.keys())

    @property
    def has_active_scopes(self) -> bool:
        """``True`` if any module scopes are currently active."""
        return bool(self._module_scopes)

    @property
    def root(self) -> Container:
        """The root platform container."""
        return self._container


__all__ = ["RuntimeContainer"]
