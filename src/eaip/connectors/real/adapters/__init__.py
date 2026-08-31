"""Real connector adapters package."""

from eaip.connectors.real.adapters.databricks import DatabricksConnector
from eaip.connectors.real.adapters.github import GitHubConnector
from eaip.connectors.real.adapters.google_workspace import GoogleWorkspaceConnector
from eaip.connectors.real.adapters.graphql import GenericGraphQLConnector
from eaip.connectors.real.adapters.jira import JiraConnector
from eaip.connectors.real.adapters.microsoft365 import Microsoft365Connector
from eaip.connectors.real.adapters.oracle import OracleConnector
from eaip.connectors.real.adapters.rest import GenericRESTConnector
from eaip.connectors.real.adapters.salesforce import SalesforceConnector
from eaip.connectors.real.adapters.servicenow import ServiceNowConnector
from eaip.connectors.real.adapters.slack import SlackConnector
from eaip.connectors.real.adapters.sap import SAPConnector
from eaip.connectors.real.adapters.snowflake import SnowflakeConnector
from eaip.connectors.real.adapters.webhook import WebhookConnector
from eaip.connectors.real.adapters.workday import WorkdayConnector
from eaip.connectors.real.adapters.zendesk import ZendeskConnector

__all__ = [
    "DatabricksConnector",
    "GenericGraphQLConnector",
    "GenericRESTConnector",
    "GitHubConnector",
    "GoogleWorkspaceConnector",
    "JiraConnector",
    "Microsoft365Connector",
    "OracleConnector",
    "SAPConnector",
    "SalesforceConnector",
    "ServiceNowConnector",
    "SlackConnector",
    "SnowflakeConnector",
    "WebhookConnector",
    "WorkdayConnector",
    "ZendeskConnector",
]
