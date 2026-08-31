"""Google Workspace connector adapter."""

from __future__ import annotations

from typing import Any

from eaip.connectors.real.base import (
    ConnectorCapability,
    ConnectorHealthResult,
    ConnectionStatus,
    RealConnectorAdapter,
)


class GoogleWorkspaceConnector(RealConnectorAdapter):
    """Google Workspace APIs connector with OAuth2."""

    connector_type = "google_workspace"
    display_name = "Google Workspace"
    supported_transports = ("http",)
    default_operations = ("list_users", "send_email", "list_events", "list_files", "list_groups")

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
            return [ConnectorCapability(name="google_apis", description="[SYNTHETIC] Google APIs", operations=["list_users", "send_email"])]
        return [
            ConnectorCapability(name="directory", description="User/group directory", operations=["list_users", "list_groups"], data_classes=["user", "group"], permissions_required=["google:admin.directory.readonly"]),
            ConnectorCapability(name="gmail", description="Gmail operations", operations=["send_email", "list_messages"], data_classes=["mail"], permissions_required=["google:gmail.send"]),
            ConnectorCapability(name="calendar", description="Calendar operations", operations=["list_events", "create_event"], data_classes=["calendar"], permissions_required=["google:calendar.readonly"]),
            ConnectorCapability(name="drive", description="Drive file operations", operations=["list_files", "get_file"], data_classes=["file"], permissions_required=["google:drive.readonly"]),
        ]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._status == ConnectionStatus.SYNTHETIC:
            return self._synthetic_result(operation, params)
        return {"status": "ok", "operation": operation}

    async def health(self) -> ConnectorHealthResult:
        if self._status == ConnectionStatus.SYNTHETIC:
            return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode — no Google credentials configured")
        return ConnectorHealthResult(connector_id=self.connector_id, status=self._status, healthy=self._status == ConnectionStatus.CONNECTED)
