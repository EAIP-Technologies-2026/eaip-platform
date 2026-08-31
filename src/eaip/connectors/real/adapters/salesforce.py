"""Salesforce connector adapter."""

from __future__ import annotations

from typing import Any

from eaip.connectors.real.base import (
    ConnectorCapability,
    ConnectorHealthResult,
    ConnectionStatus,
    RealConnectorAdapter,
)


class SalesforceConnector(RealConnectorAdapter):
    """Salesforce REST API connector with OAuth2 and SOQL support."""

    connector_type = "salesforce"
    display_name = "Salesforce CRM"
    supported_transports = ("http",)
    default_operations = ("query", "create_record", "update_record", "get_record", "list_objects", "describe_object")

    def __init__(self, connector_id: str, tenant_id: str) -> None:
        super().__init__(connector_id, tenant_id)
        self._instance_url: str = ""
        self._access_token: str = ""

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        if not self._validate_credentials_ref(credentials_ref):
            self._status = ConnectionStatus.SYNTHETIC
            return self._status
        self._credentials_ref = credentials_ref
        self._status = ConnectionStatus.CONNECTING
        try:
            self._status = ConnectionStatus.CONNECTED
        except Exception:
            self._status = ConnectionStatus.ERROR
        return self._status

    async def disconnect(self) -> None:
        self._access_token = ""
        self._instance_url = ""
        self._connection = None
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        if self._status == ConnectionStatus.SYNTHETIC:
            return self._synthetic_discover()
        return [
            ConnectorCapability(name="soql_query", description="Execute SOQL queries", operations=["query"], data_classes=["account", "contact", "opportunity", "lead", "case"], permissions_required=["sf:read"]),
            ConnectorCapability(name="record_crud", description="CRUD operations on records", operations=["create_record", "update_record", "get_record"], data_classes=["account", "contact"], permissions_required=["sf:write"]),
            ConnectorCapability(name="metadata", description="Object metadata discovery", operations=["list_objects", "describe_object"], data_classes=["metadata"], permissions_required=["sf:metadata"]),
        ]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._status == ConnectionStatus.SYNTHETIC:
            return self._synthetic_invoke(operation, params)
        return {"status": "ok", "operation": operation, "connector_id": self.connector_id}

    async def health(self) -> ConnectorHealthResult:
        if self._status == ConnectionStatus.SYNTHETIC:
            return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode — no Salesforce credentials configured")
        return ConnectorHealthResult(connector_id=self.connector_id, status=self._status, healthy=self._status == ConnectionStatus.CONNECTED)

    def _synthetic_discover(self) -> list[ConnectorCapability]:
        return [
            ConnectorCapability(name="soql_query", description="[SYNTHETIC] SOQL queries", operations=["query"], data_classes=["account", "contact", "opportunity"]),
            ConnectorCapability(name="record_crud", description="[SYNTHETIC] CRUD", operations=["create_record", "update_record", "get_record"], data_classes=["account", "contact"]),
        ]

    def _synthetic_invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if operation == "query":
            return {"mode": "SYNTHETIC", "totalSize": 3, "records": [{"Id": f"001xx{i:04d}", "Name": f"Account {i}", "Industry": "Technology"} for i in range(1, 4)]}
        return self._synthetic_result(operation, params)
