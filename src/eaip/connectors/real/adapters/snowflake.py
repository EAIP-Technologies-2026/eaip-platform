"""Snowflake connector adapter."""

from __future__ import annotations

from typing import Any

from eaip.connectors.real.base import (
    ConnectorCapability,
    ConnectorHealthResult,
    ConnectionStatus,
    RealConnectorAdapter,
)


class SnowflakeConnector(RealConnectorAdapter):
    """Snowflake SQL/REST connector."""

    connector_type = "snowflake"
    display_name = "Snowflake"
    supported_transports = ("http",)
    default_operations = ("execute_query", "list_databases", "list_schemas", "list_tables")

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
            return [ConnectorCapability(name="snowflake_sql", description="[SYNTHETIC] Snowflake SQL", operations=["execute_query"])]
        return [
            ConnectorCapability(name="sql", description="SQL query execution", operations=["execute_query"], data_classes=["table", "view"], permissions_required=["snowflake:read"]),
            ConnectorCapability(name="metadata", description="Database metadata", operations=["list_databases", "list_schemas", "list_tables"], data_classes=["metadata"], permissions_required=["snowflake:metadata"]),
        ]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._status == ConnectionStatus.SYNTHETIC:
            return self._synthetic_result(operation, params)
        return {"status": "ok", "operation": operation}

    async def health(self) -> ConnectorHealthResult:
        if self._status == ConnectionStatus.SYNTHETIC:
            return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode — no Snowflake credentials configured")
        return ConnectorHealthResult(connector_id=self.connector_id, status=self._status, healthy=self._status == ConnectionStatus.CONNECTED)
