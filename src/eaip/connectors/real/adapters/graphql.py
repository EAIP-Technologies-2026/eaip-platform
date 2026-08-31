"""Generic GraphQL connector adapter."""

from __future__ import annotations

from typing import Any

from eaip.connectors.real.base import (
    ConnectorCapability,
    ConnectorHealthResult,
    ConnectionStatus,
    RealConnectorAdapter,
)


class GenericGraphQLConnector(RealConnectorAdapter):
    """Configurable generic GraphQL connector."""

    connector_type = "graphql"
    display_name = "Generic GraphQL"
    supported_transports = ("http",)
    default_operations = ("query", "mutation", "subscription")

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
            return [ConnectorCapability(name="graphql_api", description="[SYNTHETIC] GraphQL API", operations=["query", "mutation"])]
        return [
            ConnectorCapability(name="graphql_api", description="GraphQL API operations", operations=["query", "mutation", "subscription"]),
        ]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._status == ConnectionStatus.SYNTHETIC:
            return self._synthetic_result(operation, params)
        return {"status": "ok", "operation": operation}

    async def health(self) -> ConnectorHealthResult:
        if self._status == ConnectionStatus.SYNTHETIC:
            return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode — no GraphQL credentials configured")
        return ConnectorHealthResult(connector_id=self.connector_id, status=self._status, healthy=self._status == ConnectionStatus.CONNECTED)
