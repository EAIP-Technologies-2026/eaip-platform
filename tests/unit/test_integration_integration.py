"""Tests for IntegrationRuntimeModule."""

from __future__ import annotations

from eaip.integration.integration import IntegrationRuntimeModule
from eaip.integration.models import IntegrationConfig


class TestIntegrationRuntimeModule:
    def test_module_name(self) -> None:
        module = IntegrationRuntimeModule()
        assert module.name == "integration"

    def test_default_config(self) -> None:
        module = IntegrationRuntimeModule()
        assert module._config.max_message_size_bytes == 1_048_576

    def test_custom_config(self) -> None:
        config = IntegrationConfig(max_message_size_bytes=2_097_152)
        module = IntegrationRuntimeModule(config=config)
        assert module._config.max_message_size_bytes == 2_097_152

    def test_hub_property(self) -> None:
        module = IntegrationRuntimeModule()
        assert module.hub is not None

    def test_webhook_manager_property(self) -> None:
        module = IntegrationRuntimeModule()
        assert module.webhook_manager is not None

    def test_transform_service_property(self) -> None:
        module = IntegrationRuntimeModule()
        assert module.transform_service is not None

    def test_catalog_property(self) -> None:
        module = IntegrationRuntimeModule()
        assert module.catalog is not None
