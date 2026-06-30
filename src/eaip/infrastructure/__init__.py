"""Default, dependency-free adapters for the Foundation's own ports.

These are the implementations the platform wires by default. Hosts may swap
any of them for environment-specific alternatives via the DI container.
"""

from __future__ import annotations

from eaip.infrastructure.clock import SystemClock
from eaip.infrastructure.id_generator import UuidIdGenerator
from eaip.infrastructure.secret_provider import EnvSecretProvider

__all__ = ["EnvSecretProvider", "SystemClock", "UuidIdGenerator"]
