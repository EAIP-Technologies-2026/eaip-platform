"""Webhook connector adapter."""

from __future__ import annotations

from typing import Any

from eaip.connectors.real.base import (
    ConnectorCapability,
    ConnectorHealthResult,
    ConnectionStatus,
    RealConnectorAdapter,
)


class WebhookConnector(RealConnectorAdapter):
    """Inbound/outbound webhook connector."""

    connector_type = "webhook"
    display_name = "Webhook"
    supported_transports = ("http",)
    default_operations = ("register_webhook", "list_webhooks", "send_event", "delete_webhook")

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        if not self._validate_credentials_ref(credentials_ref):
            self._status = ConnectionStatus.SYNTHETIC
            return self._status
        self._credentials_ref = credentials_ref
        self._status = ConnectionStatus.CONNECTED
        return self._status

    async def disconnect(self) -> None:
        self._connection = None
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        if self._status == ConnectionStatus.SYNTHETIC:
            return [ConnectorCapability(name="webhook", description="[SYNTHETIC] Webhook", operations=["register_webhook", "send_event"])]
        return [
            ConnectorCapability(name="webhook_management", description="Webhook lifecycle", operations=["register_webhook", "list_webhooks", "delete_webhook"]),
            ConnectorCapability(name="event_dispatch", description="Event dispatch", operations=["send_event"]),
        ]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._status == ConnectionStatus.SYNTHETIC:
            if operation == "register_webhook":
                return {"mode": "SYNTHETIC", "webhook_id": "wh-synthetic-001", "url": "https://example.com/webhook", "status": "active"}
            return self._synthetic_result(operation, params)
        return {"status": "ok", "operation": operation}

    async def health(self) -> ConnectorHealthResult:
        if self._status == ConnectionStatus.SYNTHETIC:
            return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode — no webhook credentials configured")
        return ConnectorHealthResult(connector_id=self.connector_id, status=self._status, healthy=self._status == ConnectionStatus.CONNECTED)
