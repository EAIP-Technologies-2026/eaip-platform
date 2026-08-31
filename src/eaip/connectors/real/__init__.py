"""Real connector framework — adapters, registry, health, policy."""

from eaip.connectors.real.base import ConnectionStatus, RealConnectorAdapter
from eaip.connectors.real.registry import RealConnectorRegistry

__all__ = [
    "ConnectionStatus",
    "RealConnectorAdapter",
    "RealConnectorRegistry",
]
