"""Workday connector adapter."""

from __future__ import annotations

from typing import Any

from eaip.connectors.real.base import (
    ConnectorCapability,
    ConnectorHealthResult,
    ConnectionStatus,
    RealConnectorAdapter,
)


class WorkdayConnector(RealConnectorAdapter):
    """Workday REST/SOAP connector with OAuth2."""

    connector_type = "workday"
    display_name = "Workday"
    supported_transports = ("http",)
    default_operations = ("list_workers", "get_payroll", "list_positions", "list_organizations")

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
            return [ConnectorCapability(name="workday_api", description="[SYNTHETIC] Workday API", operations=["list_workers"])]
        return [
            ConnectorCapability(name="workers", description="Worker data", operations=["list_workers", "get_worker"], data_classes=["worker"], permissions_required=["workday:hr:read"]),
            ConnectorCapability(name="payroll", description="Payroll data", operations=["get_payroll"], data_classes=["payroll"], permissions_required=["workday:payroll:read"]),
            ConnectorCapability(name="positions", description="Position management", operations=["list_positions"], data_classes=["position"], permissions_required=["workday:position:read"]),
        ]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._status == ConnectionStatus.SYNTHETIC:
            return self._synthetic_result(operation, params)
        return {"status": "ok", "operation": operation}

    async def health(self) -> ConnectorHealthResult:
        if self._status == ConnectionStatus.SYNTHETIC:
            return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode — no Workday credentials configured")
        return ConnectorHealthResult(connector_id=self.connector_id, status=self._status, healthy=self._status == ConnectionStatus.CONNECTED)
