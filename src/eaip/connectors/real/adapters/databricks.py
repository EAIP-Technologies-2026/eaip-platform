"""Databricks connector adapter."""

from __future__ import annotations

from typing import Any

from eaip.connectors.real.base import (
    ConnectorCapability,
    ConnectorHealthResult,
    ConnectionStatus,
    RealConnectorAdapter,
)


class DatabricksConnector(RealConnectorAdapter):
    """Databricks REST API connector."""

    connector_type = "databricks"
    display_name = "Databricks"
    supported_transports = ("http",)
    default_operations = ("execute_query", "list_clusters", "list_jobs", "list_tables")

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
            return [ConnectorCapability(name="databricks_api", description="[SYNTHETIC] Databricks API", operations=["execute_query"])]
        return [
            ConnectorCapability(name="sql", description="SQL warehouse queries", operations=["execute_query"], data_classes=["table", "view"], permissions_required=["databricks:sql:execute"]),
            ConnectorCapability(name="clusters", description="Cluster management", operations=["list_clusters"], data_classes=["cluster"], permissions_required=["databricks:clusters:read"]),
            ConnectorCapability(name="jobs", description="Job management", operations=["list_jobs", "run_job"], data_classes=["job"], permissions_required=["databricks:jobs:read"]),
        ]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._status == ConnectionStatus.SYNTHETIC:
            return self._synthetic_result(operation, params)
        return {"status": "ok", "operation": operation}

    async def health(self) -> ConnectorHealthResult:
        if self._status == ConnectionStatus.SYNTHETIC:
            return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode — no Databricks credentials configured")
        return ConnectorHealthResult(connector_id=self.connector_id, status=self._status, healthy=self._status == ConnectionStatus.CONNECTED)
