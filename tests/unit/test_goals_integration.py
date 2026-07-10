"""Tests for GoalRuntimeModule integration."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from eaip.goals.engine import GoalEngine
from eaip.goals.integration import GoalRuntimeModule
from eaip.goals.tracker import GoalTracker


class MockKernel:
    def __init__(self) -> None:
        self.platform = MagicMock()
        self.platform.health = MagicMock()
        self.platform.capabilities = MagicMock()
        self._modules: dict[str, Any] = {}

    def register_module(self, name: str, module: Any) -> None:
        self._modules[name] = module


class TestGoalRuntimeModule:
    def test_default_construction(self) -> None:
        module = GoalRuntimeModule()
        assert module.name == "goals"
        assert isinstance(module.engine, GoalEngine)
        assert isinstance(module.tracker, GoalTracker)

    def test_construction_with_deps(self) -> None:
        tracker = GoalTracker()
        engine = GoalEngine(tracker=tracker)
        module = GoalRuntimeModule(engine=engine, tracker=tracker)
        assert module.engine is engine
        assert module.tracker is tracker

    async def test_start_registers_health_and_capability(self) -> None:
        kernel = MockKernel()
        module = GoalRuntimeModule()
        await module.start(kernel)

        kernel.platform.health.register.assert_called_once()
        kernel.platform.capabilities.register.assert_called_once()
        assert "goals.engine" in kernel._modules
        assert "goals.tracker" in kernel._modules

    async def test_start_and_stop(self) -> None:
        kernel = MockKernel()
        module = GoalRuntimeModule()
        await module.start(kernel)
        await module.stop(kernel)

    async def test_stop_does_not_raise(self) -> None:
        kernel = MockKernel()
        module = GoalRuntimeModule()
        await module.stop(kernel)
