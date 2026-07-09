"""A fluent service collection that builds into a DI Container."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any, Self, TypeVar

from eaip.dependency_injection.container import Container
from eaip.services.descriptors import ServiceDescriptor, ServiceLifetime

T = TypeVar("T")


class ServiceCollection:
    """Fluent collection for registering services before building the DI container.

    Usage::

        services = ServiceCollection()
        services.add_singleton(Engine)
        services.add_scoped(IWorker, Worker)
        services.add_transient(ILogger, ConsoleLogger)
        services.add_instance(IConfig, config)

        container = services.build_container()
    """

    def __init__(self) -> None:
        """Initialise an empty service collection."""
        self._descriptors: dict[type[Any], ServiceDescriptor] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Registration — fluent
    # ------------------------------------------------------------------

    def add_singleton(
        self,
        service_type: type[T],
        implementation_type: type[T] | None = None,
    ) -> Self:
        """Register a singleton service.

        Args:
            service_type: The service contract.
            implementation_type: Concrete implementation. Defaults to *service_type*.

        Returns:
            Self for chaining.
        """
        return self._add(
            ServiceDescriptor(
                service_type=service_type,
                lifetime=ServiceLifetime.SINGLETON,
                implementation_type=implementation_type or service_type,
            )
        )

    def add_scoped(
        self,
        service_type: type[T],
        implementation_type: type[T] | None = None,
    ) -> Self:
        """Register a scoped service (one instance per child container).

        Args:
            service_type: The service contract.
            implementation_type: Concrete implementation. Defaults to *service_type*.

        Returns:
            Self for chaining.
        """
        return self._add(
            ServiceDescriptor(
                service_type=service_type,
                lifetime=ServiceLifetime.SCOPED,
                implementation_type=implementation_type or service_type,
            )
        )

    def add_transient(
        self,
        service_type: type[T],
        implementation_type: type[T] | None = None,
    ) -> Self:
        """Register a transient service (new instance per resolution).

        Args:
            service_type: The service contract.
            implementation_type: Concrete implementation. Defaults to *service_type*.

        Returns:
            Self for chaining.
        """
        return self._add(
            ServiceDescriptor(
                service_type=service_type,
                lifetime=ServiceLifetime.TRANSIENT,
                implementation_type=implementation_type or service_type,
            )
        )

    def add_instance(self, service_type: type[T], instance: T) -> Self:
        """Register a pre-built singleton instance.

        Args:
            service_type: The service contract.
            instance: The pre-built instance.

        Returns:
            Self for chaining.
        """
        return self._add(
            ServiceDescriptor(
                service_type=service_type,
                lifetime=ServiceLifetime.SINGLETON,
                instance=instance,
            )
        )

    def add_factory(
        self,
        service_type: type[T],
        factory: Callable[[Container], T],
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
    ) -> Self:
        """Register a factory function.

        Args:
            service_type: The service contract.
            factory: A callable ``(container) -> T``.
            lifetime: How long instances live. Defaults to SINGLETON.

        Returns:
            Self for chaining.
        """
        return self._add(
            ServiceDescriptor(
                service_type=service_type,
                lifetime=lifetime,
                factory=factory,
            )
        )

    def add_collection(self, other: ServiceCollection) -> Self:
        """Merge descriptors from another collection (overwrites duplicates).

        Args:
            other: Another service collection.

        Returns:
            Self for chaining.
        """
        with self._lock:
            for descriptor in other._descriptors.values():
                self._descriptors[descriptor.service_type] = descriptor
        return self

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def has(self, service_type: type[Any]) -> bool:
        """Check if a service type is registered."""
        return service_type in self._descriptors

    def get_descriptor(self, service_type: type[Any]) -> ServiceDescriptor | None:
        """Return the descriptor for *service_type*, or None."""
        return self._descriptors.get(service_type)

    @property
    def descriptors(self) -> list[ServiceDescriptor]:
        """Return all registered service descriptors."""
        return list(self._descriptors.values())

    @property
    def count(self) -> int:
        """Return the number of registered service types."""
        return len(self._descriptors)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build_container(self) -> Container:
        """Build a DI Container from the registered service descriptors.

        Returns:
            A configured :class:`Container` instance.
        """
        container = Container()
        for descriptor in self._descriptors.values():
            self._apply(container, descriptor)
        return container

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _add(self, descriptor: ServiceDescriptor) -> Self:
        with self._lock:
            self._descriptors[descriptor.service_type] = descriptor
        return self

    @staticmethod
    def _apply(container: Container, descriptor: ServiceDescriptor) -> None:
        if descriptor.instance is not None:
            container.register_instance(descriptor.service_type, descriptor.instance)
        elif descriptor.factory is not None:
            container.register_factory(
                descriptor.service_type,
                descriptor.factory,
                scope=descriptor.lifetime.to_scope(),
            )
        elif descriptor.implementation_type is not None:
            container.register(
                descriptor.service_type,
                descriptor.implementation_type,
                scope=descriptor.lifetime.to_scope(),
            )
