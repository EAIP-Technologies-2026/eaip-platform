"""IntegrationCatalog — connector type registry, search, and integration statistics."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from eaip.integration.models import ConnectorDefinition
from eaip.logging.context import get_logger


class IntegrationCatalog:
    def __init__(self, hub: Any = None) -> None:
        self._connector_types: dict[str, dict[str, Any]] = {}
        self._hub = hub
        self._log = get_logger("eaip.integration.catalog")

    def register_connector_type(self, type_def: dict[str, Any]) -> None:
        type_id = type_def.get("id", type_def.get("type", "unknown"))
        self._connector_types[type_id] = type_def
        self._log.info("integration.catalog.type_registered", type_id=type_id)

    def list_connector_types(self) -> Sequence[dict[str, Any]]:
        return list(self._connector_types.values())

    def search_connectors(self, query: str) -> Sequence[ConnectorDefinition]:
        if self._hub is None:
            return []
        q = query.lower()
        all_connectors = self._hub.list_connectors()
        return [
            c
            for c in all_connectors
            if q in c.name.lower() or q in c.id.lower() or q in c.type.lower()
        ]

    def get_connector_docs(self, connector_id: str) -> dict[str, Any]:
        type_def = self._connector_types.get(connector_id)
        if type_def is None:
            return {"id": connector_id, "docs": "No documentation available"}
        return {
            "id": connector_id,
            "name": type_def.get("name", connector_id),
            "description": type_def.get("description", ""),
            "config_schema": type_def.get("config_schema", {}),
            "auth_schema": type_def.get("auth_schema", {}),
        }

    def get_integration_stats(self) -> dict[str, Any]:
        connectors = self._hub.list_connectors() if self._hub else []
        enabled = [c for c in connectors if c.enabled]
        return {
            "total_connectors": len(connectors),
            "enabled_connectors": len(enabled),
            "disabled_connectors": len(connectors) - len(enabled),
            "registered_types": len(self._connector_types),
            "timestamp": datetime.now(UTC).isoformat(),
        }


__all__ = ["IntegrationCatalog"]
