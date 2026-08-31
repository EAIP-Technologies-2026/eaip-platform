"""Tests for EventSourcingRuntimeModule."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.eventsourcing.integration import EventSourcingRuntimeModule
from eaip.eventsourcing.models import EventSourcingConfig, ProjectionConfig


class TestEventSourcingRuntimeModule:
    def test_module_name(self) -> None:
        module = EventSourcingRuntimeModule()
        assert module.name == "eventsourcing"

    def test_default_config(self) -> None:
        module = EventSourcingRuntimeModule()
        assert module._config.max_events_per_aggregate == 10_000

    def test_custom_config(self) -> None:
        config = EventSourcingConfig(max_events_per_aggregate=5_000)
        module = EventSourcingRuntimeModule(config=config)
        assert module._config.max_events_per_aggregate == 5_000

    def test_custom_projection_config(self) -> None:
        pconfig = ProjectionConfig(batch_size=50)
        module = EventSourcingRuntimeModule(projection_config=pconfig)
        assert module._projection_config.batch_size == 50

    def test_store_property(self) -> None:
        module = EventSourcingRuntimeModule()
        assert module.store is not None

    def test_projection_builder_property(self) -> None:
        module = EventSourcingRuntimeModule()
        assert module.projection_builder is not None

    def test_replay_service_property(self) -> None:
        module = EventSourcingRuntimeModule()
        assert module.replay_service is not None

    def test_snapshot_service_property(self) -> None:
        module = EventSourcingRuntimeModule()
        assert module.snapshot_service is not None

    @pytest.mark.asyncio
    async def test_start_stop(self) -> None:
        module = EventSourcingRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        await module.start(kernel)
        kernel.platform.capabilities.register.assert_called_once()
        kernel.platform.health.register.assert_called_once()

        await module.stop(kernel)
