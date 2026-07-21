"""Tests for IntegrationCatalog."""

from __future__ import annotations

import pytest

from eaip.integration.catalog import IntegrationCatalog
from eaip.integration.hub import IntegrationHub
from eaip.integration.models import ConnectorDefinition


class TestIntegrationCatalog:
    @pytest.fixture
    def hub(self) -> IntegrationHub:
        return IntegrationHub()

    @pytest.fixture
    def catalog(self, hub: IntegrationHub) -> IntegrationCatalog:
        return IntegrationCatalog(hub=hub)


class TestRegisterConnectorTypes(TestIntegrationCatalog):
    def test_register_connector_type(self, catalog: IntegrationCatalog) -> None:
        catalog.register_connector_type(
            {"id": "http", "name": "HTTP", "description": "HTTP connector"}
        )
        types = catalog.list_connector_types()
        assert len(types) == 1
        assert types[0]["id"] == "http"

    def test_register_duplicate_overwrites(self, catalog: IntegrationCatalog) -> None:
        catalog.register_connector_type({"id": "http", "version": 1})
        catalog.register_connector_type({"id": "http", "version": 2})
        types = catalog.list_connector_types()
        assert len(types) == 1
        assert types[0]["version"] == 2

    def test_list_types_empty(self, catalog: IntegrationCatalog) -> None:
        assert catalog.list_connector_types() == []

    def test_register_multiple_types(self, catalog: IntegrationCatalog) -> None:
        catalog.register_connector_type({"id": "http"})
        catalog.register_connector_type({"id": "mq"})
        catalog.register_connector_type({"id": "grpc"})
        assert len(catalog.list_connector_types()) == 3


class TestSearchConnectors(TestIntegrationCatalog):
    def test_search_by_name(self, hub: IntegrationHub, catalog: IntegrationCatalog) -> None:
        hub.register_connector(
            ConnectorDefinition(
                id="c1", name="Salesforce", type="http", endpoint_url="https://sf.com"
            )
        )
        hub.register_connector(
            ConnectorDefinition(
                id="c2", name="Shopify", type="http", endpoint_url="https://shop.com"
            )
        )
        results = catalog.search_connectors("sales")
        assert len(results) == 1
        assert results[0].id == "c1"

    def test_search_by_id(self, hub: IntegrationHub, catalog: IntegrationCatalog) -> None:
        hub.register_connector(
            ConnectorDefinition(
                id="c-sap-01", name="SAP", type="http", endpoint_url="https://sap.com"
            )
        )
        results = catalog.search_connectors("sap")
        assert len(results) == 1

    def test_search_no_results(self, hub: IntegrationHub, catalog: IntegrationCatalog) -> None:
        hub.register_connector(
            ConnectorDefinition(id="c1", name="Alpha", type="http", endpoint_url="https://ex.com")
        )
        results = catalog.search_connectors("nonexistent")
        assert len(results) == 0

    def test_search_without_hub(self) -> None:
        catalog = IntegrationCatalog()
        results = catalog.search_connectors("anything")
        assert results == []


class TestConnectorDocs(TestIntegrationCatalog):
    def test_get_docs_existing(self, catalog: IntegrationCatalog) -> None:
        catalog.register_connector_type(
            {
                "id": "http",
                "name": "HTTP",
                "description": "Generic HTTP connector",
                "config_schema": {"url": "string"},
                "auth_schema": {"api_key": "string"},
            }
        )
        docs = catalog.get_connector_docs("http")
        assert docs["name"] == "HTTP"
        assert docs["description"] == "Generic HTTP connector"
        assert docs["config_schema"] == {"url": "string"}
        assert docs["auth_schema"] == {"api_key": "string"}

    def test_get_docs_missing(self, catalog: IntegrationCatalog) -> None:
        docs = catalog.get_connector_docs("nonexistent")
        assert "No documentation available" in docs["docs"]


class TestIntegrationStats(TestIntegrationCatalog):
    def test_stats_empty(self, hub: IntegrationHub, catalog: IntegrationCatalog) -> None:
        stats = catalog.get_integration_stats()
        assert stats["total_connectors"] == 0
        assert stats["enabled_connectors"] == 0
        assert stats["disabled_connectors"] == 0
        assert stats["registered_types"] == 0

    def test_stats_with_data(self, hub: IntegrationHub, catalog: IntegrationCatalog) -> None:
        hub.register_connector(
            ConnectorDefinition(id="c1", name="C1", type="http", endpoint_url="https://ex.com")
        )
        hub.register_connector(
            ConnectorDefinition(
                id="c2", name="C2", type="mq", endpoint_url="amqp://ex.com", enabled=False
            )
        )
        catalog.register_connector_type({"id": "http"})
        stats = catalog.get_integration_stats()
        assert stats["total_connectors"] == 2
        assert stats["enabled_connectors"] == 1
        assert stats["disabled_connectors"] == 1
        assert stats["registered_types"] == 1
        assert "timestamp" in stats
