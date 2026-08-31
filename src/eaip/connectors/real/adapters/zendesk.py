"""Zendesk connector adapter."""

from __future__ import annotations

from typing import Any

from eaip.connectors.real.base import (
    ConnectorCapability,
    ConnectorHealthResult,
    ConnectionStatus,
    RealConnectorAdapter,
)


class ZendeskConnector(RealConnectorAdapter):
    """Zendesk REST API connector."""

    connector_type = "zendesk"
    display_name = "Zendesk"
    supported_transports = ("http",)
    default_operations = ("list_tickets", "create_ticket", "list_users", "list_organizations")

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
            return [ConnectorCapability(name="zendesk_api", description="[SYNTHETIC] Zendesk API", operations=["list_tickets", "create_ticket"])]
        return [
            ConnectorCapability(name="tickets", description="Ticket management", operations=["list_tickets", "create_ticket", "update_ticket"], data_classes=["ticket"], permissions_required=["zendesk:tickets:read"]),
            ConnectorCapability(name="users", description="User directory", operations=["list_users"], data_classes=["user"], permissions_required=["zendesk:users:read"]),
        ]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._status == ConnectionStatus.SYNTHETIC:
            return self._synthetic_result(operation, params)
        return {"status": "ok", "operation": operation}

    async def health(self) -> ConnectorHealthResult:
        if self._status == ConnectionStatus.SYNTHETIC:
            return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode — no Zendesk credentials configured")
        return ConnectorHealthResult(connector_id=self.connector_id, status=self._status, healthy=self._status == ConnectionStatus.CONNECTED)
