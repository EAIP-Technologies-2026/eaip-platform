"""Type-safe service provider wrapping the DI Container."""

from __future__ import annotations

from typing import Any, TypeVar

from eaip.dependency_injection.container import Container
from eaip.exceptions.domain import NotFoundError

T = TypeVar("T")


class ServiceProvider:
    """Provides services from a DI Container with type-safe resolution.

    Usage::

        provider = ServiceProvider(container)
        engine = provider.get_required_service(Engine)
        logger = provider.get_service(ILogger)
    """

    __slots__ = ("_container",)

    def __init__(self, container: Container) -> None:
        """Wrap a DI *container* for service resolution.

        Args:
            container: The DI container to resolve from.
        """
        self._container = container

    @property
    def container(self) -> Container:
        """Return the underlying DI container."""
        return self._container

    def get_service(self, service_type: type[T]) -> T | None:
        """Resolve *service_type* or return None if not registered.

        Args:
            service_type: The service contract type.

        Returns:
            An instance of *service_type*, or None.
        """
        return self._container.try_resolve(service_type)

    def get_required_service(self, service_type: type[T]) -> T:
        """Resolve *service_type* or raise NotFoundError.

        Args:
            service_type: The service contract type.

        Returns:
            An instance of *service_type*.

        Raises:
            NotFoundError: If no binding exists for *service_type*.
        """
        instance = self._container.try_resolve(service_type)
        if instance is None:
            raise NotFoundError(
                f"no service registered for {service_type.__name__}",
                context={"service_type": service_type.__name__},
            )
        return instance

    def has_service(self, service_type: type[Any]) -> bool:
        """Check if *service_type* can be resolved.

        Args:
            service_type: The service contract type.

        Returns:
            True if registered, False otherwise.
        """
        return self._container.has(service_type)
