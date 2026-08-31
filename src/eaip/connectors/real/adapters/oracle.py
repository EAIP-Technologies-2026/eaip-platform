"""Oracle connector adapter."""

from __future__ import annotations

from typing import Any

from eaip.connectors.real.base import (
    ConnectorCapability,
    ConnectorHealthResult,
    ConnectionStatus,
    RealConnectorAdapter,
)


class OracleConnector(RealConnectorAdapter):
    """Oracle REST API connector."""

    connector_type = "oracle"
    display_name = "Oracle"
    supported_transports = ("http",)
    default_operations = ("list_employees", "get_financials", "list_projects", "list_departments")

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
            return [ConnectorCapability(name="oracle_api", description="[SYNTHETIC] Oracle API", operations=["list_employees"])]
        return [
            ConnectorCapability(name="hr", description="HR operations", operations=["list_employees", "list_departments"], data_classes=["employee"], permissions_required=["oracle:hr:read"]),
            ConnectorCapability(name="finance", description="Financial operations", operations=["get_financials"], data_classes=["financial"], permissions_required=["oracle:finance:read"]),
            ConnectorCapability(name="projects", description="Project management", operations=["list_projects"], data_classes=["project"], permissions_required=["oracle:project:read"]),
        ]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._status == ConnectionStatus.SYNTHETIC:
            return self._synthetic_result(operation, params)
        return {"status": "ok", "operation": operation}

    async def health(self) -> ConnectorHealthResult:
        if self._status == ConnectionStatus.SYNTHETIC:
            return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode — no Oracle credentials configured")
        return ConnectorHealthResult(connector_id=self.connector_id, status=self._status, healthy=self._status == ConnectionStatus.CONNECTED)
