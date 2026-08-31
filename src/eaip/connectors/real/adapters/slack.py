"""Slack connector adapter."""

from __future__ import annotations

from typing import Any

from eaip.connectors.real.base import (
    ConnectorCapability,
    ConnectorHealthResult,
    ConnectionStatus,
    RealConnectorAdapter,
)


class SlackConnector(RealConnectorAdapter):
    """Slack API connector with OAuth2/Bot Token."""

    connector_type = "slack"
    display_name = "Slack"
    supported_transports = ("http", "sse")
    default_operations = ("list_channels", "send_message", "list_users", "get_history", "create_channel")

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
            return [ConnectorCapability(name="slack_api", description="[SYNTHETIC] Slack API", operations=["list_channels", "send_message"])]
        return [
            ConnectorCapability(name="channels", description="Channel management", operations=["list_channels", "create_channel"], data_classes=["channel"], permissions_required=["slack:channels:read"]),
            ConnectorCapability(name="messaging", description="Message operations", operations=["send_message", "get_history"], data_classes=["message"], permissions_required=["slack:chat:write"]),
            ConnectorCapability(name="users", description="User directory", operations=["list_users", "get_user"], data_classes=["user"], permissions_required=["slack:users:read"]),
        ]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._status == ConnectionStatus.SYNTHETIC:
            if operation == "list_channels":
                return {"mode": "SYNTHETIC", "channels": [{"id": f"C{i:04d}", "name": f"channel-{i}", "is_member": True} for i in range(1, 4)]}
            return self._synthetic_result(operation, params)
        return {"status": "ok", "operation": operation}

    async def health(self) -> ConnectorHealthResult:
        if self._status == ConnectionStatus.SYNTHETIC:
            return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode — no Slack credentials configured")
        return ConnectorHealthResult(connector_id=self.connector_id, status=self._status, healthy=self._status == ConnectionStatus.CONNECTED)
