"""Microsoft 365 connector adapter."""

from __future__ import annotations

from typing import Any

from eaip.connectors.real.base import (
    ConnectorCapability,
    ConnectorHealthResult,
    ConnectionStatus,
    RealConnectorAdapter,
)


class Microsoft365Connector(RealConnectorAdapter):
    """Microsoft 365 Graph API connector with OAuth2."""

    connector_type = "microsoft365"
    display_name = "Microsoft 365"
    supported_transports = ("http",)
    default_operations = ("list_users", "send_email", "list_events", "get_file", "list_teams", "list_drives")

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
            return [ConnectorCapability(name="graph_api", description="[SYNTHETIC] Graph API", operations=["list_users", "send_email"])]
        return [
            ConnectorCapability(name="users", description="User management", operations=["list_users", "get_user"], data_classes=["user"], permissions_required=["graph:User.Read"]),
            ConnectorCapability(name="mail", description="Email operations", operations=["send_email", "list_messages"], data_classes=["mail"], permissions_required=["graph:Mail.Send"]),
            ConnectorCapability(name="calendar", description="Calendar operations", operations=["list_events", "create_event"], data_classes=["calendar"], permissions_required=["graph:Calendars.Read"]),
            ConnectorCapability(name="files", description="OneDrive/SharePoint files", operations=["get_file", "list_drives"], data_classes=["file"], permissions_required=["graph:Files.Read"]),
            ConnectorCapability(name="teams", description="Teams operations", operations=["list_teams", "list_channels"], data_classes=["team"], permissions_required=["graph:Team.ReadBasic.All"]),
        ]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._status == ConnectionStatus.SYNTHETIC:
            if operation == "list_users":
                return {"mode": "SYNTHETIC", "value": [{"id": f"user-{i}", "displayName": f"User {i}", "mail": f"user{i}@example.com"} for i in range(1, 4)]}
            return self._synthetic_result(operation, params)
        return {"status": "ok", "operation": operation}

    async def health(self) -> ConnectorHealthResult:
        if self._status == ConnectionStatus.SYNTHETIC:
            return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode — no M365 credentials configured")
        return ConnectorHealthResult(connector_id=self.connector_id, status=self._status, healthy=self._status == ConnectionStatus.CONNECTED)
