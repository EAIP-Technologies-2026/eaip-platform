"""Tests for :mod:`eaip.admin.config_manager`."""

from __future__ import annotations

import pytest

from eaip.admin.config_manager import ConfigManager
from eaip.admin.exceptions import ConfigNotFoundError
from eaip.events.bus import EventBus
from eaip.settings.core_settings import PlatformSettings


@pytest.fixture
def settings() -> PlatformSettings:
    return PlatformSettings()


@pytest.fixture
def manager(settings: PlatformSettings) -> ConfigManager:
    return ConfigManager(settings)


class TestConfigManager:
    def test_get_from_settings(self, manager: ConfigManager) -> None:
        value = manager.get("core.app_name")
        assert value == "eaip-platform"

    def test_get_from_overlay(self, manager: ConfigManager) -> None:
        manager.set("core.app_name", "overridden")
        value = manager.get("core.app_name")
        assert value == "overridden"

    def test_get_nonexistent_key_raises(self, manager: ConfigManager) -> None:
        with pytest.raises(ConfigNotFoundError, match="not found"):
            manager.get("nonexistent.key")

    def test_set_overwrites(self, manager: ConfigManager) -> None:
        manager.set("logging.level", "DEBUG")
        assert manager.get("logging.level") == "DEBUG"
        manager.set("logging.level", "INFO")
        assert manager.get("logging.level") == "INFO"

    def test_list_contains_settings_keys(self, manager: ConfigManager) -> None:
        entries = manager.list()
        assert "core.app_name" in entries
        assert "logging.level" in entries
        assert entries["core.app_name"] == "eaip-platform"

    def test_list_includes_overlay(self, manager: ConfigManager) -> None:
        manager.set("custom.key", "custom_value")
        entries = manager.list()
        assert entries["custom.key"] == "custom_value"

    def test_reload_clears_overlay(self, manager: ConfigManager) -> None:
        import asyncio

        manager.set("core.app_name", "overridden")
        asyncio.run(manager.reload())
        assert manager.get("core.app_name") == "eaip-platform"

    def test_reload_refreshes_settings(self, manager: ConfigManager) -> None:
        import asyncio

        manager.set("logging.level", "DEBUG")
        asyncio.run(manager.reload())
        assert manager.get("logging.level") == "INFO"

    def test_set_without_event_bus(self, manager: ConfigManager) -> None:
        manager.set("test.key", 123)
        assert manager.get("test.key") == 123

    def test_set_with_event_bus(self, settings: PlatformSettings) -> None:
        bus = EventBus()
        mgr = ConfigManager(settings, event_bus=bus)
        mgr.set("core.app_name", "from-bus", changed_by="test")
        assert mgr.get("core.app_name") == "from-bus"

    def test_list_empty_manager(self) -> None:
        mgr = ConfigManager()
        entries = mgr.list()
        assert isinstance(entries, dict)
        assert len(entries) > 0
