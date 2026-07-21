"""IntegrationHub — central orchestrator for connectors, routes, and message delivery."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from eaip.integration.events import (
    ConnectorRegistered,
    ConnectorUnregistered,
    MessageReceived,
    MessageRouted,
    MessageSent,
    RouteRegistered,
)
from eaip.integration.exceptions import (
    ConnectorNotFoundError,
    MessageDeliveryError,
)
from eaip.integration.models import (
    ConnectorDefinition,
    IntegrationMessage,
    MessageRoute,
    Transformation,
)
from eaip.logging.context import get_logger


class IntegrationHub:
    def __init__(self, event_bus: Any | None = None) -> None:
        self._connectors: dict[str, ConnectorDefinition] = {}
        self._routes: dict[str, MessageRoute] = {}
        self._transformations: dict[str, Transformation] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.integration.hub")

    # ------------------------------------------------------------------
    # Connectors
    # ------------------------------------------------------------------
    def register_connector(self, connector: ConnectorDefinition) -> None:
        self._connectors[connector.id] = connector
        self._log.info(
            "integration.connector.registered", connector_id=connector.id, name=connector.name
        )
        if self._event_bus is not None:
            import asyncio

            asyncio.ensure_future(self._event_bus.publish(ConnectorRegistered(connector=connector)))

    def unregister_connector(self, connector_id: str) -> ConnectorDefinition | None:
        connector = self._connectors.pop(connector_id, None)
        if connector is not None:
            self._log.info("integration.connector.unregistered", connector_id=connector_id)
            if self._event_bus is not None:
                import asyncio

                asyncio.ensure_future(
                    self._event_bus.publish(
                        ConnectorUnregistered(
                            connector_id=connector_id, connector_name=connector.name
                        )
                    )
                )
        return connector

    def get_connector(self, connector_id: str) -> ConnectorDefinition:
        connector = self._connectors.get(connector_id)
        if connector is None:
            raise ConnectorNotFoundError(
                f"Connector {connector_id!r} not found",
                context={"connector_id": connector_id},
            )
        return connector

    def list_connectors(self, type: str | None = None) -> Sequence[ConnectorDefinition]:
        if type is None:
            return list(self._connectors.values())
        return [c for c in self._connectors.values() if c.type == type]

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------
    def register_route(self, route: MessageRoute) -> None:
        self._routes[route.id] = route
        self._log.info("integration.route.registered", route_id=route.id, name=route.name)
        if self._event_bus is not None:
            import asyncio

            asyncio.ensure_future(self._event_bus.publish(RouteRegistered(route=route)))

    def unregister_route(self, route_id: str) -> MessageRoute | None:
        return self._routes.pop(route_id, None)

    def list_routes(self) -> Sequence[MessageRoute]:
        return list(self._routes.values())

    # ------------------------------------------------------------------
    # Transformations
    # ------------------------------------------------------------------
    def register_transformation(self, transform: Transformation) -> None:
        self._transformations[transform.id] = transform
        self._log.info("integration.transformation.registered", transformation_id=transform.id)

    # ------------------------------------------------------------------
    # Message flow
    # ------------------------------------------------------------------
    async def send_message(self, message: IntegrationMessage) -> None:
        self._log.info("integration.message.send", message_id=message.id)
        if self._event_bus is not None:
            await self._event_bus.publish(MessageSent(message=message))

    async def receive_message(self, message: IntegrationMessage) -> None:
        self._log.info("integration.message.receive", message_id=message.id)
        if self._event_bus is not None:
            await self._event_bus.publish(MessageReceived(message=message))
        await self.route_message(message)

    async def route_message(self, message: IntegrationMessage) -> None:
        matching = [
            r
            for r in self._routes.values()
            if r.enabled and self._match_pattern(message.source, r.source_pattern)
        ]
        if not matching:
            self._log.warning("integration.message.no_routes", message_id=message.id)
            return

        matching.sort(key=lambda r: r.priority, reverse=True)
        route = matching[0]

        if self._event_bus is not None:
            await self._event_bus.publish(
                MessageRouted(message=message, route_id=route.id, route_name=route.name)
            )

        if route.error_handling == "retry":
            try:
                await self._deliver_with_retry(message, route)
            except (MessageDeliveryError, ConnectorNotFoundError) as exc:
                self._log.error(
                    "integration.message.retry_exhausted",
                    message_id=message.id,
                    route_id=route.id,
                    error=str(exc),
                )
        else:
            try:
                await self._deliver_to_connector(message, route.destination_pattern)
            except (MessageDeliveryError, ConnectorNotFoundError) as exc:
                if route.error_handling == "dead_letter":
                    self._log.error(
                        "integration.message.dead_letter",
                        message_id=message.id,
                        route_id=route.id,
                        error=str(exc),
                    )

    # ------------------------------------------------------------------
    # Internal delivery helpers
    # ------------------------------------------------------------------
    async def _deliver_to_connector(self, message: IntegrationMessage, destination: str) -> None:
        connector_id = destination
        connector = self._connectors.get(connector_id)
        if connector is None:
            raise ConnectorNotFoundError(
                f"Destination connector {connector_id!r} not found",
                context={"connector_id": connector_id},
            )
        if not connector.enabled:
            raise MessageDeliveryError(
                f"Connector {connector_id!r} is disabled",
                context={"connector_id": connector_id},
            )
        self._log.info(
            "integration.message.delivered", message_id=message.id, connector_id=connector_id
        )

    async def _deliver_with_retry(self, message: IntegrationMessage, route: MessageRoute) -> None:
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                await self._deliver_to_connector(message, route.destination_pattern)
                return
            except MessageDeliveryError as e:
                last_error = e
                self._log.warning(
                    "integration.message.retry",
                    message_id=message.id,
                    attempt=attempt,
                )
        if last_error is not None:
            raise last_error

    @staticmethod
    def _match_pattern(source: str, pattern: str) -> bool:
        if pattern in ("*", source):
            return True
        if pattern.endswith("*") and source.startswith(pattern[:-1]):
            return True
        return bool(pattern.startswith("*") and source.endswith(pattern[1:]))


__all__ = ["IntegrationHub"]
