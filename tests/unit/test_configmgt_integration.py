"""Tests for ConfigMgtRuntimeModule and ConfigMgtHealthCheck."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.configmgt.health import ConfigMgtHealthCheck
from eaip.configmgt.integration import ConfigMgtRuntimeModule
from eaip.configmgt.manager import ConfigManager
from eaip.configmgt.models import ConfigEntry, ConfigMgtConfig
from eaip.health.checks import HealthStatus


class TestConfigMgtRuntimeModule:
    def test_module_name(self) -> None:
        module = ConfigMgtRuntimeModule()
        assert module.name == "configmgt"

    def test_default_config(self) -> None:
        module = ConfigMgtRuntimeModule()
        assert module.config.enable_audit_logging is True
        assert module.config.cache_ttl_seconds == 300

    def test_custom_config(self) -> None:
        config = ConfigMgtConfig(enable_audit_logging=False, cache_ttl_seconds=600)
        module = ConfigMgtRuntimeModule(config=config)
        assert module.config.enable_audit_logging is False
        assert module.config.cache_ttl_seconds == 600

    def test_manager_property(self) -> None:
        module = ConfigMgtRuntimeModule()
        assert module.manager is not None

    def test_custom_manager(self) -> None:
        manager = ConfigManager()
        module = ConfigMgtRuntimeModule(manager=manager)
        assert module.manager is manager

    async def test_start_stop(self) -> None:
        module = ConfigMgtRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        await module.start(kernel)
        kernel.platform.capabilities.register.assert_called_once()
        kernel.platform.health.register.assert_called_once()

        await module.stop(kernel)


class TestConfigMgtHealthCheck:
    @pytest.fixture
    def manager(self) -> ConfigManager:
        return ConfigManager()

    async def test_healthy_with_entries(self, manager: ConfigManager) -> None:
        await manager.set_entry(ConfigEntry(id="e1", key="k", value="v"))
        await manager.set_entry(ConfigEntry(id="e2", key="k2", value="v2"))
        check = ConfigMgtHealthCheck(manager)
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY
        assert report.details["entries_total"] == 2

    async def test_degraded_without_entries(self, manager: ConfigManager) -> None:
        check = ConfigMgtHealthCheck(manager)
        report = await check.check()
        assert report.status is HealthStatus.DEGRADED
        assert "No config entries registered" in report.message

    async def test_component_name(self, manager: ConfigManager) -> None:
        check = ConfigMgtHealthCheck(manager)
        assert check.name == "configmgt"

    async def test_details_include_config_flags(self, manager: ConfigManager) -> None:
        check = ConfigMgtHealthCheck(manager)
        report = await check.check()
        assert "hot_reload_enabled" in report.details
        assert "audit_logging_enabled" in report.details
        assert "versioning_enabled" in report.details
