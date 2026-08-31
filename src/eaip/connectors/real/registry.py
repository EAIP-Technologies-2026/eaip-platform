"""Real connector adapter registry."""

from __future__ import annotations

from typing import Any

from eaip.connectors.real.base import RealConnectorAdapter
from eaip.logging.context import get_logger

SUPPORTED_CONNECTOR_TYPES = (
    "salesforce",
    "microsoft365",
    "google_workspace",
    "slack",
    "jira",
    "github",
    "servicenow",
    "sap",
    "oracle",
    "workday",
    "zendesk",
    "snowflake",
    "databricks",
    "rest",
    "graphql",
    "webhook",
)


class RealConnectorRegistry:
    """Registry for real connector adapter classes.

    Adapters register by connector_type string. Instances are created
    per (connector_id, tenant_id) pair.
    """

    def __init__(self) -> None:
        self._adapter_classes: dict[str, type[RealConnectorAdapter]] = {}
        self._instances: dict[str, RealConnectorAdapter] = {}
        self._log = get_logger("eaip.connectors.real.registry")

    def register_adapter(self, connector_type: str, adapter_cls: type[RealConnectorAdapter]) -> None:
        """Register an adapter class for a connector type."""
        self._adapter_classes[connector_type] = adapter_cls
        self._log.info("real_connector.adapter_registered", connector_type=connector_type)

    def get_adapter(self, connector_type: str) -> type[RealConnectorAdapter] | None:
        """Get an adapter class by connector type."""
        return self._adapter_classes.get(connector_type)

    def list_adapters(self) -> list[str]:
        """List all registered adapter types."""
        return list(self._adapter_classes.keys())

    def create_instance(
        self, connector_type: str, connector_id: str, tenant_id: str
    ) -> RealConnectorAdapter | None:
        """Create an adapter instance for a specific connector."""
        cls = self._adapter_classes.get(connector_type)
        if cls is None:
            return None
        key = f"{tenant_id}:{connector_id}"
        instance = cls(connector_id=connector_id, tenant_id=tenant_id)
        self._instances[key] = instance
        return instance

    def get_instance(self, connector_id: str, tenant_id: str) -> RealConnectorAdapter | None:
        """Get an existing adapter instance."""
        return self._instances.get(f"{tenant_id}:{connector_id}")

    def list_instances(self, tenant_id: str) -> list[RealConnectorAdapter]:
        """List all adapter instances for a tenant."""
        return [v for k, v in self._instances.items() if k.startswith(f"{tenant_id}:")]

    def remove_instance(self, connector_id: str, tenant_id: str) -> bool:
        """Remove an adapter instance."""
        key = f"{tenant_id}:{connector_id}"
        return self._instances.pop(key, None) is not None


__all__ = ["RealConnectorRegistry", "SUPPORTED_CONNECTOR_TYPES"]
