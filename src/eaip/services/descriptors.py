"""Service descriptor model and lifetime enumeration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from eaip.dependency_injection.scope import Scope


class ServiceLifetime(StrEnum):
    """How long a service instance lives.

    Maps directly to :class:`eaip.dependency_injection.scope.Scope`.
    """

    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"

    def to_scope(self) -> Scope:
        """Convert to the equivalent DI container Scope."""
        mapping: dict[ServiceLifetime, Scope] = {
            ServiceLifetime.SINGLETON: Scope.SINGLETON,
            ServiceLifetime.SCOPED: Scope.SCOPED,
            ServiceLifetime.TRANSIENT: Scope.TRANSIENT,
        }
        return mapping[self]


@dataclass(frozen=True)
class ServiceDescriptor:
    """Describes a single service registration.

    One of *implementation_type*, *instance*, or *factory* must be
    provided; the others should be left as None.
    """

    service_type: type[Any]
    """The service contract (abstract type, protocol, or concrete class)."""

    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    """How long instances live."""

    implementation_type: type[Any] | None = None
    """Concrete implementation type (used with ``add_singleton`` etc.)."""

    instance: Any = field(default=None, compare=False)
    """Pre-built instance (used with ``add_instance``)."""

    factory: Callable[[Any], Any] | None = field(default=None, compare=False)
    """Factory function ``(container) -> T`` (used with ``add_factory``)."""
