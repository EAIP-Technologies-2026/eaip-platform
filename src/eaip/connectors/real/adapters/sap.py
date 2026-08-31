"""SAP connector adapter."""

from __future__ import annotations

from typing import Any

from eaip.connectors.real.base import (
    ConnectorCapability,
    ConnectorHealthResult,
    ConnectionStatus,
    RealConnectorAdapter,
)


class SAPConnector(RealConnectorAdapter):
    """SAP RFC/OData connector."""

    connector_type = "sap"
    display_name = "SAP ERP"
    supported_transports = ("http",)
    default_operations = ("list_orders", "get_material", "list_vendors", "get_financials", "list_plants")

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
            return [ConnectorCapability(name="sap_odata", description="[SYNTHETIC] SAP OData", operations=["list_orders"])]
        return [
            ConnectorCapability(name="sales", description="Sales order operations", operations=["list_orders", "create_order"], data_classes=["sales_order"], permissions_REQUIRED=["sap:sales:read"]),
            ConnectorCapability(name="materials", description="Material master data", operations=["get_material", "list_materials"], data_classes=["material"], permissions_required=["sap:material:read"]),
            ConnectorCapability(name="vendors", description="Vendor management", operations=["list_vendors"], data_classes=["vendor"], permissions_required=["sap:vendor:read"]),
            ConnectorCapability(name="finance", description="Financial data", operations=["get_financials"], data_classes=["financial"], permissions_required=["sap:finance:read"]),
        ]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._status == ConnectionStatus.SYNTHETIC:
            return self._synthetic_result(operation, params)
        return {"status": "ok", "operation": operation}

    async def health(self) -> ConnectorHealthResult:
        if self._status == ConnectionStatus.SYNTHETIC:
            return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode — no SAP credentials configured")
        return ConnectorHealthResult(connector_id=self.connector_id, status=self._status, healthy=self._status == ConnectionStatus.CONNECTED)
