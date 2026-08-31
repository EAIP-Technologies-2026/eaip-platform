"""Connector capability registry — discover and manage connector capabilities."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class DataClassification(StrEnum):
    """Data classification levels."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class ConnectorCapabilityRecord(BaseModel):
    """Full capability record for a registered connector."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    connector_id: str
    tenant_id: str
    connector_type: str
    capabilities: list[str] = Field(default_factory=list)
    operations: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    data_classes: list[str] = Field(default_factory=list)
    data_classification: DataClassification = DataClassification.INTERNAL
    cost_estimate: float = 0.0
    latency_estimate_ms: float = 0.0
    health_status: str = "unknown"
    tenant_availability: bool = True
    created_at: Any = Field(default_factory=utc_now)
    updated_at: Any = Field(default_factory=utc_now)


class CapabilityRegistry:
    """Registry for connector capabilities.

    Stores per-tenant connector capability records and provides
    discovery, lookup, and permission checking.
    """

    def __init__(self) -> None:
        self._capabilities: dict[str, ConnectorCapabilityRecord] = {}
        self._log = get_logger("eaip.connectors.capabilities")

    def _key(self, tenant_id: str, connector_id: str) -> str:
        return f"{tenant_id}:{connector_id}"

    def register_capability(self, record: ConnectorCapabilityRecord) -> ConnectorCapabilityRecord:
        """Register or update a connector's capabilities."""
        key = self._key(record.tenant_id, record.connector_id)
        self._capabilities[key] = record
        self._log.info(
            "capability.registered",
            connector_id=record.connector_id,
            tenant_id=record.tenant_id,
        )
        return record

    def get_capability(self, connector_id: str, tenant_id: str) -> ConnectorCapabilityRecord | None:
        """Get capability details for a specific connector."""
        return self._capabilities.get(self._key(tenant_id, connector_id))

    def discover_capabilities(self, connector_type: str, tenant_id: str) -> list[ConnectorCapabilityRecord]:
        """Discover all capabilities for a connector type within a tenant."""
        return [
            v for v in self._capabilities.values()
            if v.connector_type == connector_type and v.tenant_id == tenant_id
        ]

    def list_capabilities(self, tenant_id: str) -> list[ConnectorCapabilityRecord]:
        """List all connector capabilities for a tenant."""
        return [v for v in self._capabilities.values() if v.tenant_id == tenant_id]

    def check_permission(
        self, connector_id: str, operation: str, tenant_id: str
    ) -> bool:
        """Check if an operation is permitted on a connector."""
        cap = self.get_capability(connector_id, tenant_id)
        if cap is None:
            return False
        if not cap.tenant_availability:
            return False
        if operation and operation not in cap.operations:
            return False
        return True

    def get_by_data_classification(
        self, tenant_id: str, classification: DataClassification
    ) -> list[ConnectorCapabilityRecord]:
        """Get connectors matching a data classification level."""
        return [
            v for v in self._capabilities.values()
            if v.tenant_id == tenant_id and v.data_classification == classification
        ]

    def remove_capability(self, connector_id: str, tenant_id: str) -> bool:
        """Remove a connector's capability record."""
        return self._capabilities.pop(self._key(tenant_id, connector_id), None) is not None


__all__ = [
    "CapabilityRegistry",
    "ConnectorCapabilityRecord",
    "DataClassification",
]
