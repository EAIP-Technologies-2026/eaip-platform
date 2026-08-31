"""Jira connector adapter."""

from __future__ import annotations

from typing import Any

from eaip.connectors.real.base import (
    ConnectorCapability,
    ConnectorHealthResult,
    ConnectionStatus,
    RealConnectorAdapter,
)


class JiraConnector(RealConnectorAdapter):
    """Jira REST API connector with API Token auth."""

    connector_type = "jira"
    display_name = "Jira"
    supported_transports = ("http",)
    default_operations = ("list_issues", "create_issue", "update_issue", "list_projects", "add_comment")

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
            return [ConnectorCapability(name="jira_api", description="[SYNTHETIC] Jira API", operations=["list_issues", "create_issue"])]
        return [
            ConnectorCapability(name="issues", description="Issue management", operations=["list_issues", "create_issue", "update_issue", "add_comment"], data_classes=["issue"], permissions_required=["jira:read"]),
            ConnectorCapability(name="projects", description="Project listing", operations=["list_projects"], data_classes=["project"], permissions_required=["jira:project:read"]),
        ]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._status == ConnectionStatus.SYNTHETIC:
            if operation == "list_issues":
                return {"mode": "SYNTHETIC", "issues": [{"key": f"PROJ-{i}", "summary": f"Issue {i}", "status": "Open"} for i in range(1, 4)]}
            return self._synthetic_result(operation, params)
        return {"status": "ok", "operation": operation}

    async def health(self) -> ConnectorHealthResult:
        if self._status == ConnectionStatus.SYNTHETIC:
            return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode — no Jira credentials configured")
        return ConnectorHealthResult(connector_id=self.connector_id, status=self._status, healthy=self._status == ConnectionStatus.CONNECTED)
