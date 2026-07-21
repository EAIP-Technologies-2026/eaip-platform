"""Cross-Platform Connector Bridge — connect and route messages across heterogeneous platforms."""

from __future__ import annotations

from eaip.xbridge.bridge import ConnectorBridge
from eaip.xbridge.events import (
    ConnectorDeleted,
    ConnectorRegistered,
    ConnectorUpdated,
    MessageReceived,
    MessageSent,
)
from eaip.xbridge.exceptions import (
    BridgeError,
    ConnectorNotFoundError,
    MessageRoutingError,
)
from eaip.xbridge.health import XBridgeHealthCheck
from eaip.xbridge.integration import XBridgeRuntimeModule
from eaip.xbridge.models import (
    BridgeConfig,
    BridgeRoute,
    ConnectorConfig,
    MessageEnvelope,
    ProtocolType,
)

__all__ = [
    "BridgeConfig",
    "BridgeError",
    "BridgeRoute",
    "ConnectorBridge",
    "ConnectorConfig",
    "ConnectorDeleted",
    "ConnectorNotFoundError",
    "ConnectorRegistered",
    "ConnectorUpdated",
    "MessageEnvelope",
    "MessageReceived",
    "MessageRoutingError",
    "MessageSent",
    "ProtocolType",
    "XBridgeHealthCheck",
    "XBridgeRuntimeModule",
]
