"""Service registration and resolution layer built atop the DI container."""

from __future__ import annotations

from eaip.services.collection import ServiceCollection
from eaip.services.descriptors import ServiceDescriptor, ServiceLifetime
from eaip.services.extensions import add_default_services
from eaip.services.provider import ServiceProvider

__all__ = [
    "ServiceCollection",
    "ServiceDescriptor",
    "ServiceLifetime",
    "ServiceProvider",
    "add_default_services",
]
