from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.queue.integration import QueueRuntimeModule
from eaip.queue.manager import QueueManager
from eaip.queue.models import QueueConfig


class TestQueueIntegration:
    def test_default_initialization(self) -> None:
        mod = QueueRuntimeModule()
        assert mod.name == "queue"
        assert isinstance(mod.manager, QueueManager)

    def test_create_queue(self) -> None:
        mod = QueueRuntimeModule()
        config = QueueConfig(name="test")
        queue = mod.create_queue(config)
        assert queue is not None

    @pytest.mark.asyncio
    async def test_start_with_kernel(self) -> None:
        mod = QueueRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        kernel.platform.capabilities.register = MagicMock()
        await mod.start(kernel)
        kernel.platform.health.register.assert_called_once()
        kernel.platform.capabilities.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self) -> None:
        mod = QueueRuntimeModule()
        kernel = MagicMock()
        await mod.start(kernel)
        await mod.stop(kernel)

    @pytest.mark.asyncio
    async def test_health_check_registration(self) -> None:
        mod = QueueRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        kernel.platform.capabilities.register = MagicMock()
        await mod.start(kernel)
        registered = kernel.platform.health.register.call_args[0][0]
        assert registered.name == "eaip.queue"
