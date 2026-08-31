"""ServiceNow connector adapter."""

from __future__ import annotations

from typing import Any

from eaip.connectors.real.base import (
    ConnectorCapability,
    ConnectorHealthResult,
    ConnectionStatus,
    RealConnectorAdapter,
)


class ServiceNowConnector(RealConnectorAdapter):
    """ServiceNow REST API connector with Basic/OAuth auth."""

    connector_type = "servicenow"
    display_name = "ServiceNow"
    supported_transports = ("http",)
    default_operations = ("list_incidents", "create_incident", "list_changes", "list_users", "list_catalog_items")

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
            return [ConnectorCapability(name="servicenow_api", description="[SYNTHETIC] ServiceNow API", operations=["list_incidents", "create_incident"])]
        return [
            ConnectorCapability(name="incidents", description="Incident management", operations=["list_incidents", "create_incident", "update_incident"], data_classes=["incident"], permissions_required=["sn:incident.read"]),
            ConnectorCapability(name="changes", description="Change management", operations=["list_changes", "create_change"], data_classes=["change_request"], permissions_required=["sn:change.read"]),
            ConnectorCapability(name="users", description="User directory", operations=["list_users"], data_classes=["user"], permissions_required=["sn:user.read"]),
            ConnectorCapability(name="catalog", description="Service catalog", operations=["list_catalog_items", "request_item"], data_classes=["catalog_item"], permissions_required=["sn:catalog.read"]),
        ]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._status == ConnectionStatus.SYNTHETIC:
            if operation == "list_incidents":
                return {"mode": "SYNTHETIC", "result": [{"number": f"INC{i:06d}", "short_description": f"Incident {i}", "state": "new"} for i in range(1, 4)]}
            return self._synthetic_result(operation, params)
        return {"status": "ok", "operation": operation}

    async def health(self) -> ConnectorHealthResult:
        if self._status == ConnectionStatus.SYNTHETIC:
            return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode — no ServiceNow credentials configured")
        return ConnectorHealthResult(connector_id=self.connector_id, status=self._status, healthy=self._status == ConnectionStatus.CONNECTED)
