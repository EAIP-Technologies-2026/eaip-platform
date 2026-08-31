"""Tests for WebhookRuntimeModule."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.webhooks.integration import WebhookRuntimeModule
from eaip.webhooks.models import WebhookConfig


class TestWebhookRuntimeModule:
    def test_module_name(self) -> None:
        module = WebhookRuntimeModule()
        assert module.name == "webhooks"

    def test_default_config(self) -> None:
        module = WebhookRuntimeModule()
        assert module._config.default_max_attempts == 3

    def test_custom_config(self) -> None:
        config = WebhookConfig(default_max_attempts=5)
        module = WebhookRuntimeModule(config=config)
        assert module._config.default_max_attempts == 5

    def test_dispatcher_property(self) -> None:
        module = WebhookRuntimeModule()
        assert module.dispatcher is not None

    @pytest.mark.asyncio
    async def test_start_registers_capability_and_health(self) -> None:
        module = WebhookRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        await module.start(kernel)

        kernel.platform.capabilities.register.assert_called_once()
        kernel.platform.health.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self) -> None:
        module = WebhookRuntimeModule()
        kernel = MagicMock()
        await module.stop(kernel)
