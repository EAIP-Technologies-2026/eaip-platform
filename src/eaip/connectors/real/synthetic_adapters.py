"""Synthetic connector adapters — fallback when real credentials are unavailable."""

from __future__ import annotations

import random
from typing import Any

from eaip.connectors.real.base import (
    ConnectorCapability,
    ConnectorHealthResult,
    ConnectionStatus,
    RealConnectorAdapter,
)
from eaip.shared.time import utc_now


class SyntheticSalesforceAdapter(RealConnectorAdapter):
    connector_type = "salesforce"
    display_name = "Salesforce CRM (Synthetic)"
    supported_transports = ("http",)
    default_operations = ("query", "create_record", "update_record", "get_record", "list_objects")

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        self._status = ConnectionStatus.SYNTHETIC
        self._credentials_ref = credentials_ref
        return self._status

    async def disconnect(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        return [
            ConnectorCapability(name="query", description="Execute SOQL queries", operations=["query"], data_classes=["account", "contact", "opportunity"], permissions_required=["sf:read"]),
            ConnectorCapability(name="crud", description="Create/read/update records", operations=["create_record", "update_record", "get_record"], data_classes=["account", "contact"], permissions_required=["sf:write"]),
        ]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if operation == "query":
            return {"mode": "SYNTHETIC", "totalSize": 3, "records": [{"Id": f"001xx{i:04d}", "Name": f"Account {i}", "Industry": "Technology"} for i in range(1, 4)]}
        if operation == "create_record":
            return {"mode": "SYNTHETIC", "id": f"001xx{random.randint(1000, 9999)}", "success": True}
        return self._synthetic_result(operation, params)

    async def health(self) -> ConnectorHealthResult:
        return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode — no Salesforce credentials configured")


class SyntheticMicrosoft365Adapter(RealConnectorAdapter):
    connector_type = "microsoft365"
    display_name = "Microsoft 365 (Synthetic)"
    supported_transports = ("http",)
    default_operations = ("list_users", "send_email", "list_events", "get_file", "list_teams")

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        self._status = ConnectionStatus.SYNTHETIC
        return self._status

    async def disconnect(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        return [ConnectorCapability(name="graph_api", description="Microsoft Graph API access", operations=["list_users", "send_email", "list_events"], data_classes=["user", "mail", "calendar"], permissions_required=["graph:read"])]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if operation == "list_users":
            return {"mode": "SYNTHETIC", "value": [{"id": f"user-{i}", "displayName": f"User {i}", "mail": f"user{i}@example.com"} for i in range(1, 4)]}
        return self._synthetic_result(operation, params)

    async def health(self) -> ConnectorHealthResult:
        return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode")


class SyntheticGoogleWorkspaceAdapter(RealConnectorAdapter):
    connector_type = "google_workspace"
    display_name = "Google Workspace (Synthetic)"
    supported_transports = ("http",)
    default_operations = ("list_users", "send_email", "list_events", "list_files")

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        self._status = ConnectionStatus.SYNTHETIC
        return self._status

    async def disconnect(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        return [ConnectorCapability(name="google_apis", description="Google Workspace APIs", operations=["list_users", "send_email"], data_classes=["user", "mail", "drive"], permissions_required=["google:read"])]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        return self._synthetic_result(operation, params)

    async def health(self) -> ConnectorHealthResult:
        return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode")


class SyntheticSlackAdapter(RealConnectorAdapter):
    connector_type = "slack"
    display_name = "Slack (Synthetic)"
    supported_transports = ("http", "sse")
    default_operations = ("list_channels", "send_message", "list_users", "get_history")

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        self._status = ConnectionStatus.SYNTHETIC
        return self._status

    async def disconnect(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        return [ConnectorCapability(name="slack_api", description="Slack Web API", operations=["list_channels", "send_message"], data_classes=["channel", "message", "user"], permissions_required=["slack:read"])]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if operation == "list_channels":
            return {"mode": "SYNTHETIC", "channels": [{"id": f"C{i:04d}", "name": f"channel-{i}", "is_member": True} for i in range(1, 4)]}
        return self._synthetic_result(operation, params)

    async def health(self) -> ConnectorHealthResult:
        return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode")


class SyntheticJiraAdapter(RealConnectorAdapter):
    connector_type = "jira"
    display_name = "Jira (Synthetic)"
    supported_transports = ("http",)
    default_operations = ("list_issues", "create_issue", "update_issue", "list_projects")

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        self._status = ConnectionStatus.SYNTHETIC
        return self._status

    async def disconnect(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        return [ConnectorCapability(name="jira_api", description="Jira REST API", operations=["list_issues", "create_issue"], data_classes=["issue", "project"], permissions_required=["jira:read"])]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if operation == "list_issues":
            return {"mode": "SYNTHETIC", "issues": [{"key": f"PROJ-{i}", "summary": f"Issue {i}", "status": "Open"} for i in range(1, 4)]}
        return self._synthetic_result(operation, params)

    async def health(self) -> ConnectorHealthResult:
        return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode")


class SyntheticGitHubAdapter(RealConnectorAdapter):
    connector_type = "github"
    display_name = "GitHub (Synthetic)"
    supported_transports = ("http",)
    default_operations = ("list_repos", "list_issues", "create_issue", "list_prs")

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        self._status = ConnectionStatus.SYNTHETIC
        return self._status

    async def disconnect(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        return [ConnectorCapability(name="github_api", description="GitHub REST/GraphQL API", operations=["list_repos", "list_issues"], data_classes=["repository", "issue", "pull_request"], permissions_REQUIRED=["github:read"])]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        return self._synthetic_result(operation, params)

    async def health(self) -> ConnectorHealthResult:
        return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode")


class SyntheticServiceNowAdapter(RealConnectorAdapter):
    connector_type = "servicenow"
    display_name = "ServiceNow (Synthetic)"
    supported_transports = ("http",)
    default_operations = ("list_incidents", "create_incident", "list_changes", "list_users")

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        self._status = ConnectionStatus.SYNTHETIC
        return self._status

    async def disconnect(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        return [ConnectorCapability(name="servicenow_api", description="ServiceNow REST API", operations=["list_incidents", "create_incident"], data_classes=["incident", "change_request"], permissions_required=["sn:read"])]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        if operation == "list_incidents":
            return {"mode": "SYNTHETIC", "result": [{"number": f"INC{i:06d}", "short_description": f"Incident {i}", "state": "new"} for i in range(1, 4)]}
        return self._synthetic_result(operation, params)

    async def health(self) -> ConnectorHealthResult:
        return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode")


class SyntheticSAPAdapter(RealConnectorAdapter):
    connector_type = "sap"
    display_name = "SAP ERP (Synthetic)"
    supported_transports = ("http",)
    default_operations = ("list_orders", "get_material", "list_vendors", "get_financials")

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        self._status = ConnectionStatus.SYNTHETIC
        return self._status

    async def disconnect(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        return [ConnectorCapability(name="sap_odata", description="SAP OData/RFC", operations=["list_orders", "get_material"], data_classes=["sales_order", "material", "vendor"], permissions_required=["sap:read"])]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        return self._synthetic_result(operation, params)

    async def health(self) -> ConnectorHealthResult:
        return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode")


class SyntheticOracleAdapter(RealConnectorAdapter):
    connector_type = "oracle"
    display_name = "Oracle (Synthetic)"
    supported_transports = ("http",)
    default_operations = ("list_employees", "get_financials", "list_projects")

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        self._status = ConnectionStatus.SYNTHETIC
        return self._status

    async def disconnect(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        return [ConnectorCapability(name="oracle_api", description="Oracle REST API", operations=["list_employees"], data_classes=["employee", "financial"], permissions_required=["oracle:read"])]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        return self._synthetic_result(operation, params)

    async def health(self) -> ConnectorHealthResult:
        return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode")


class SyntheticWorkdayAdapter(RealConnectorAdapter):
    connector_type = "workday"
    display_name = "Workday (Synthetic)"
    supported_transports = ("http",)
    default_operations = ("list_workers", "get_payroll", "list_positions")

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        self._status = ConnectionStatus.SYNTHETIC
        return self._status

    async def disconnect(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        return [ConnectorCapability(name="workday_api", description="Workday REST/SOAP", operations=["list_workers"], data_classes=["worker", "payroll"], permissions_required=["workday:read"])]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        return self._synthetic_result(operation, params)

    async def health(self) -> ConnectorHealthResult:
        return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode")


class SyntheticZendeskAdapter(RealConnectorAdapter):
    connector_type = "zendesk"
    display_name = "Zendesk (Synthetic)"
    supported_transports = ("http",)
    default_operations = ("list_tickets", "create_ticket", "list_users")

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        self._status = ConnectionStatus.SYNTHETIC
        return self._status

    async def disconnect(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        return [ConnectorCapability(name="zendesk_api", description="Zendesk REST API", operations=["list_tickets", "create_ticket"], data_classes=["ticket", "user"], permissions_required=["zendesk:read"])]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        return self._synthetic_result(operation, params)

    async def health(self) -> ConnectorHealthResult:
        return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode")


class SyntheticSnowflakeAdapter(RealConnectorAdapter):
    connector_type = "snowflake"
    display_name = "Snowflake (Synthetic)"
    supported_transports = ("http",)
    default_operations = ("execute_query", "list_databases", "list_schemas")

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        self._status = ConnectionStatus.SYNTHETIC
        return self._status

    async def disconnect(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        return [ConnectorCapability(name="snowflake_sql", description="Snowflake SQL/REST", operations=["execute_query"], data_classes=["table", "view"], permissions_required=["snowflake:read"])]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        return self._synthetic_result(operation, params)

    async def health(self) -> ConnectorHealthResult:
        return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode")


class SyntheticDatabricksAdapter(RealConnectorAdapter):
    connector_type = "databricks"
    display_name = "Databricks (Synthetic)"
    supported_transports = ("http",)
    default_operations = ("execute_query", "list_clusters", "list_jobs")

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        self._status = ConnectionStatus.SYNTHETIC
        return self._status

    async def disconnect(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        return [ConnectorCapability(name="databricks_api", description="Databricks REST API", operations=["execute_query"], data_classes=["table", "cluster"], permissions_required=["databricks:read"])]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        return self._synthetic_result(operation, params)

    async def health(self) -> ConnectorHealthResult:
        return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode")


class SyntheticRESTAdapter(RealConnectorAdapter):
    connector_type = "rest"
    display_name = "Generic REST (Synthetic)"
    supported_transports = ("http",)
    default_operations = ("get", "post", "put", "delete")

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        self._status = ConnectionStatus.SYNTHETIC
        return self._status

    async def disconnect(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        return [ConnectorCapability(name="rest_api", description="Generic REST API", operations=["get", "post", "put", "delete"])]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        return self._synthetic_result(operation, params)

    async def health(self) -> ConnectorHealthResult:
        return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode")


class SyntheticGraphQLAdapter(RealConnectorAdapter):
    connector_type = "graphql"
    display_name = "Generic GraphQL (Synthetic)"
    supported_transports = ("http",)
    default_operations = ("query", "mutation", "subscription")

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        self._status = ConnectionStatus.SYNTHETIC
        return self._status

    async def disconnect(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        return [ConnectorCapability(name="graphql_api", description="Generic GraphQL API", operations=["query", "mutation"])]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        return self._synthetic_result(operation, params)

    async def health(self) -> ConnectorHealthResult:
        return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode")


class SyntheticWebhookAdapter(RealConnectorAdapter):
    connector_type = "webhook"
    display_name = "Webhook (Synthetic)"
    supported_transports = ("http",)
    default_operations = ("register_webhook", "list_webhooks", "send_event")

    async def connect(self, credentials_ref: str) -> ConnectionStatus:
        self._status = ConnectionStatus.SYNTHETIC
        return self._status

    async def disconnect(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED

    async def discover(self) -> list[ConnectorCapability]:
        return [ConnectorCapability(name="webhook", description="Inbound/outbound webhooks", operations=["register_webhook", "send_event"])]

    async def invoke(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        return self._synthetic_result(operation, params)

    async def health(self) -> ConnectorHealthResult:
        return ConnectorHealthResult(connector_id=self.connector_id, status=ConnectionStatus.SYNTHETIC, healthy=False, message="Synthetic mode")


ALL_SYNTHETIC_ADAPTERS: list[type[RealConnectorAdapter]] = [
    SyntheticSalesforceAdapter,
    SyntheticMicrosoft365Adapter,
    SyntheticGoogleWorkspaceAdapter,
    SyntheticSlackAdapter,
    SyntheticJiraAdapter,
    SyntheticGitHubAdapter,
    SyntheticServiceNowAdapter,
    SyntheticSAPAdapter,
    SyntheticOracleAdapter,
    SyntheticWorkdayAdapter,
    SyntheticZendeskAdapter,
    SyntheticSnowflakeAdapter,
    SyntheticDatabricksAdapter,
    SyntheticRESTAdapter,
    SyntheticGraphQLAdapter,
    SyntheticWebhookAdapter,
]
