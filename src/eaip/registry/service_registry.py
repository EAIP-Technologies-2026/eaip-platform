"""Runtime service registry — tracks running service instances with status and metadata."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from typing import Any

from eaip.registry.registry import Observer, Registry
from eaip.shared.time import utc_now


class ServiceStatus(StrEnum):
    """Lifecycle status of a registered service instance."""

    REGISTERED = "registered"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"


class ServiceInstance:
    """A running service instance tracked by the ServiceRegistry.

    Attributes:
        service_type: Dot-separated type/interface name the instance provides.
        instance: The actual service object.
        status: Current lifecycle status.
        registered_at: Timestamp of registration.
        metadata: Arbitrary key-value metadata (version, tags, health, etc.).
    """

    __slots__ = ("instance", "metadata", "registered_at", "service_type", "status")

    def __init__(
        self,
        service_type: str,
        instance: object,
        status: ServiceStatus = ServiceStatus.REGISTERED,
        registered_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a ServiceInstance.

        Args:
            service_type: The type/interface name.
            instance: The service object.
            status: Initial lifecycle status.
            registered_at: Optional registration timestamp.
            metadata: Optional key-value metadata.
        """
        self.service_type = service_type
        self.instance = instance
        self.status = status
        self.registered_at = registered_at or utc_now()
        self.metadata = metadata or {}


class ServiceRegistry:
    """Tracks running service instances by type name.

    Provides observe() by delegating to the underlying Registry.
    """

    def __init__(self) -> None:
        """Initialize an empty ServiceRegistry."""
        self._inner: Registry[ServiceInstance] = Registry(
            name="services",
            value_type=ServiceInstance,
        )

    def register(
        self,
        service_type: str,
        instance: object,
        *,
        replace: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> ServiceInstance:
        """Register a service instance.

        Args:
            service_type: Dot-separated type/interface name.
            instance: The service object.
            replace: Whether to replace an existing registration.
            metadata: Optional metadata.

        Returns:
            The created ServiceInstance.
        """
        svc = ServiceInstance(service_type=service_type, instance=instance, metadata=metadata)
        self._inner.register(service_type, svc, replace=replace)
        return svc

    def unregister(self, service_type: str) -> bool:
        """Unregister a service by type name.

        Returns:
            True if the service was found and removed.
        """
        return self._inner.unregister(service_type)

    def get(self, service_type: str) -> ServiceInstance:
        """Get a service instance by type name.

        Raises:
            NotFoundError: If the service is not registered.
        """
        return self._inner.get(service_type)

    def try_get(self, service_type: str) -> ServiceInstance | None:
        """Get a service instance, or None if not found."""
        return self._inner.try_get(service_type)

    def has(self, service_type: str) -> bool:
        """Check if a service is registered."""
        return self._inner.has(service_type)

    def all(self) -> list[ServiceInstance]:
        """Return all registered service instances."""
        return self._inner.values()

    def set_status(self, service_type: str, status: ServiceStatus) -> ServiceInstance:
        """Set the status of a service instance.

        Raises:
            NotFoundError: If the service is not registered.
        """
        svc = self._inner.get(service_type)
        svc.status = status
        return svc

    def observe(self, observer: Observer[ServiceInstance]) -> Callable[[], None]:
        """Register an observer for registry changes.

        Returns:
            A callable that removes the observer.
        """
        return self._inner.observe(observer)

    @property
    def count(self) -> int:
        """Return the number of registered services."""
        return len(self._inner)

    def __len__(self) -> int:
        """Return the number of registered services."""
        return len(self._inner)

    def __contains__(self, service_type: str) -> bool:
        """Check if a service type is registered."""
        return service_type in self._inner


__all__ = ["ServiceInstance", "ServiceRegistry", "ServiceStatus"]
