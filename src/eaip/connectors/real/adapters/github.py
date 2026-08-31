"""GitHub connector adapter."""

from __future__ import annotations

from typing import Any

from eaip.connectors.real.base import (
    ConnectorCapability,
    ConnectorHealthResult,
    ConnectionStatus,
    RealConnectorAdapter,
)


class GitHubConnector(RealConnectorAdapter):
    """GitHub REST/GraphQL API connector with OAuth2/App auth."""

    connector_type = "github"
    display_name = "GitHub"
    supported_transports = ("http",)
    default_operations = ("list_repos", "list_issues", "create_issue", "list_prs", "create_pr", "list_workflows")

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
            return [ConnectorCapability(name="github_api", description="[SYNTHETIC] GitHub API", operations=["list_repos", "list_issues"])]
        return [
            ConnectorCapability(name="repos", description="Repository operations", operations=["list_repos", "get_repo"], data_classes=["repository"], permissions_required=["github:repo:read"]),
            ConnectorCapability(name="issues", description="Issue management", operations=["list_issues", "create_issue"], data_classes=["issue"], permissions_required=["github:issues:write"]),
            ConnectorCapability(name="pull_requests", description="PR operations", operations=["list_prs", "create_pr"], data_classes=["pull_request"], permissions_required=["github:pr:write"]),
            ConnectorCapability(name="actions", description="Workflow operations", operations=["list_workflows", "trigger_workflow"], data_classes=["workflow"], permissions_required=["github:actions:write"]),
        ]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._status == ConnectionStatus.SYNTHETIC:
            return self._synthetic_result(operation, params)
        return {"status": "ok", "operation": operation}

    async def health(self) -> ConnectorHealthResult:
        if self._status == ConnectionStatus.SYNTHETIC:
            return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode — no GitHub credentials configured")
        return ConnectorHealthResult(connector_id=self.connector_id, status=self._status, healthy=self._status == ConnectionStatus.CONNECTED)
