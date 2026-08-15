"""ConnectorBridge — connect and route messages across heterogeneous platforms."""

from __future__ import annotations

from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.xbridge.events import (
    ConnectorDeleted,
    ConnectorRegistered,
    ConnectorUpdated,
    MessageReceived,
    MessageSent,
)
from eaip.xbridge.exceptions import (
    ConnectorNotFoundError,
    MessageRoutingError,
)
from eaip.xbridge.models import (
    BridgeConfig,
    BridgeRoute,
    ConnectorConfig,
    MessageEnvelope,
)


class ConnectorBridge:
    """Central service for managing connectors and routing messages between them."""

    def __init__(
        self, config: BridgeConfig | None = None, event_bus: EventBus | None = None
    ) -> None:
        self._config = config or BridgeConfig()
        self._connectors: dict[str, ConnectorConfig] = {}
        self._routes: dict[str, BridgeRoute] = {}
        self._message_log: list[MessageEnvelope] = []
        self._log = get_logger("eaip.xbridge.bridge")
        self._event_bus = event_bus

    @property
    def config(self) -> BridgeConfig:
        return self._config

    async def register_connector(self, connector: ConnectorConfig) -> ConnectorConfig:
        """Register a new connector."""
        self._connectors[connector.id] = connector
        if self._event_bus is not None:
            await self._event_bus.publish(
                ConnectorRegistered(
                    connector_id=connector.id,
                    name=connector.name,
                    protocol=connector.protocol.value,
                )
            )
        self._log.info("xbridge.connector.registered", connector_id=connector.id)
        return connector

    async def get_connector(self, connector_id: str) -> ConnectorConfig:
        """Retrieve a connector by ID."""
        connector = self._connectors.get(connector_id)
        if connector is None:
            raise ConnectorNotFoundError(f"Connector '{connector_id}' not found")
        return connector

    async def list_connectors(self) -> list[ConnectorConfig]:
        """List all registered connectors."""
        return list(self._connectors.values())

    async def update_connector(
        self, connector_id: str, updates: dict[str, object]
    ) -> ConnectorConfig:
        """Update a connector's configuration."""
        existing = await self.get_connector(connector_id)
        updated = existing.model_copy(update=updates, deep=True)
        self._connectors[connector_id] = updated
        if self._event_bus is not None:
            await self._event_bus.publish(
                ConnectorUpdated(
                    connector_id=connector_id,
                    name=updated.name,
                )
            )
        self._log.info("xbridge.connector.updated", connector_id=connector_id)
        return updated

    async def delete_connector(self, connector_id: str) -> None:
        """Delete a connector."""
        connector = await self.get_connector(connector_id)
        del self._connectors[connector_id]
        related_routes = [
            r for r in self._routes.values() if r.source == connector_id or r.target == connector_id
        ]
        for route in related_routes:
            del self._routes[route.id]
        if self._event_bus is not None:
            await self._event_bus.publish(
                ConnectorDeleted(
                    connector_id=connector_id,
                    name=connector.name,
                )
            )
        self._log.info("xbridge.connector.deleted", connector_id=connector_id)

    async def send_message(self, envelope: MessageEnvelope) -> MessageEnvelope:
        """Send a message through the bridge."""
        if envelope.source not in self._connectors:
            raise ConnectorNotFoundError(f"Source connector '{envelope.source}' not found")
        if envelope.target not in self._connectors:
            raise ConnectorNotFoundError(f"Target connector '{envelope.target}' not found")

        if self._config.enable_message_logging:
            self._message_log.append(envelope)

        if self._event_bus is not None:
            await self._event_bus.publish(
                MessageSent(
                    message_id=envelope.id,
                    source=envelope.source,
                    target=envelope.target,
                    content_type=envelope.content_type,
                )
            )
        self._log.info("xbridge.message.sent", message_id=envelope.id)
        return envelope

    async def route_message(self, envelope: MessageEnvelope) -> MessageEnvelope:
        """Route a message based on bridge routes."""
        matching = [
            r
            for r in self._routes.values()
            if r.enabled and r.source == envelope.source and r.target == envelope.target
        ]
        if not matching:
            raise MessageRoutingError(
                f"No enabled route from '{envelope.source}' to '{envelope.target}'",
            )
        if self._config.enable_message_logging:
            self._message_log.append(envelope)
        if self._event_bus is not None:
            await self._event_bus.publish(
                MessageReceived(
                    message_id=envelope.id,
                    source=envelope.source,
                    target=envelope.target,
                    content_type=envelope.content_type,
                )
            )
        self._log.info("xbridge.message.routed", message_id=envelope.id)
        return envelope

    async def get_message_log(self) -> list[MessageEnvelope]:
        """Return the message log."""
        return list(self._message_log)

    async def register_route(self, route: BridgeRoute) -> BridgeRoute:
        """Register a new bridge route."""
        if route.source not in self._connectors:
            raise ConnectorNotFoundError(f"Source connector '{route.source}' not found")
        if route.target not in self._connectors:
            raise ConnectorNotFoundError(f"Target connector '{route.target}' not found")
        self._routes[route.id] = route
        self._log.info("xbridge.route.registered", route_id=route.id)
        return route

    async def list_routes(self) -> list[BridgeRoute]:
        """List all registered bridge routes."""
        return list(self._routes.values())


__all__ = ["ConnectorBridge"]
