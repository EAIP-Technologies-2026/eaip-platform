"""Generic REST connector adapter."""

from __future__ import annotations

from typing import Any

from eaip.connectors.real.base import (
    ConnectorCapability,
    ConnectorHealthResult,
    ConnectionStatus,
    RealConnectorAdapter,
)


class GenericRESTConnector(RealConnectorAdapter):
    """Configurable generic REST API connector."""

    connector_type = "rest"
    display_name = "Generic REST"
    supported_transports = ("http",)
    default_operations = ("get", "post", "put", "patch", "delete")

    def __init__(self, connector_id: str, tenant_id: str) -> None:
        super().__init__(connector_id, tenant_id)
        self._base_url: str = ""

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
            return [ConnectorCapability(name="rest_api", description="[SYNTHETIC] REST API", operations=["get", "post", "put", "delete"])]
        return [
            ConnectorCapability(name="rest_api", description="REST API operations", operations=["get", "post", "put", "patch", "delete"]),
        ]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._status == ConnectionStatus.SYNTHETIC:
            return self._synthetic_result(operation, params)
        return {"status": "ok", "operation": operation, "base_url": self._base_url}

    async def health(self) -> ConnectorHealthResult:
        if self._status == ConnectionStatus.SYNTHETIC:
            return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode — no REST credentials configured")
        return ConnectorHealthResult(connector_id=self.connector_id, status=self._status, healthy=self._status == ConnectionStatus.CONNECTED)
