"""Extension methods that register common platform services into a ServiceCollection."""

from __future__ import annotations

from eaip.health.checks import HealthCheck
from eaip.metrics.metrics import Meter
from eaip.registry.registry import Registry
from eaip.services.collection import ServiceCollection
from eaip.services.descriptors import ServiceLifetime


def add_default_services(services: ServiceCollection) -> ServiceCollection:
    """Register EAIP platform services that every application needs.

    Adds the following service types:

    * ``Meter`` (singleton) — metrics factory.
    * ``Registry[HealthCheck]`` (singleton) — health check registry.

    Args:
        services: The service collection to extend.

    Returns:
        The same collection for chaining.
    """
    services.add_factory(
        Meter,
        lambda _c: Meter(namespace="eaip"),
        lifetime=ServiceLifetime.SINGLETON,
    )
    services.add_factory(
        Registry[HealthCheck],
        lambda _c: Registry[HealthCheck](name="health_checks", value_type=HealthCheck),  # type: ignore[type-abstract]
        lifetime=ServiceLifetime.SINGLETON,
    )
    return services
