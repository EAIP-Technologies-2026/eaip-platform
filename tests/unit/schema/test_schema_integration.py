"""Tests for SchemaRuntimeModule."""

from __future__ import annotations

from unittest.mock import MagicMock

from eaip.schema.integration import SchemaRuntimeModule
from eaip.schema.models import SchemaConfig


class TestSchemaRuntimeModule:
    def test_module_name(self) -> None:
        module = SchemaRuntimeModule()
        assert module.name == "schema"

    def test_default_config(self) -> None:
        module = SchemaRuntimeModule()
        assert module._config.enable_validation is True
        assert module._config.default_compatibility.value == "backward"

    def test_custom_config(self) -> None:
        config = SchemaConfig(max_versions=5, enable_validation=False)
        module = SchemaRuntimeModule(config=config)
        assert module._config.max_versions == 5
        assert module._config.enable_validation is False

    def test_registry_property(self) -> None:
        module = SchemaRuntimeModule()
        assert module.registry is not None

    def test_validator_property(self) -> None:
        module = SchemaRuntimeModule()
        assert module.validator is not None

    def test_compatibility_checker_property(self) -> None:
        module = SchemaRuntimeModule()
        assert module.compatibility_checker is not None

    async def test_start_stop(self) -> None:
        module = SchemaRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        await module.start(kernel)
        await module.stop(kernel)

        kernel.platform.capabilities.register.assert_called_once()
        kernel.platform.health.register.assert_called_once()
