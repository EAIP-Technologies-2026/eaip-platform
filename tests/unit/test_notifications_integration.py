"""Tests for NotificationRuntimeModule."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.notifications.integration import NotificationRuntimeModule
from eaip.notifications.models import NotificationConfig


class TestNotificationRuntimeModule:
    def test_module_name(self) -> None:
        module = NotificationRuntimeModule()
        assert module.name == "notifications"

    def test_default_config(self) -> None:
        module = NotificationRuntimeModule()
        assert module._config.max_retries == 3

    def test_custom_config(self) -> None:
        config = NotificationConfig(max_retries=5)
        module = NotificationRuntimeModule(config=config)
        assert module._config.max_retries == 5

    def test_engine_property(self) -> None:
        module = NotificationRuntimeModule()
        assert module.engine is not None

    @pytest.mark.asyncio
    async def test_start_registers_capability_and_health(self) -> None:
        module = NotificationRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        await module.start(kernel)

        kernel.platform.capabilities.register.assert_called_once()
        kernel.platform.health.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_emits_log(self) -> None:
        module = NotificationRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        await module.start(kernel)

    @pytest.mark.asyncio
    async def test_stop(self) -> None:
        module = NotificationRuntimeModule()
        kernel = MagicMock()
        await module.stop(kernel)
