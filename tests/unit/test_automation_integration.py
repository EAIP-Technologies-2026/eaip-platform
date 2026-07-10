"""Tests for AutomationRuntimeModule."""

from __future__ import annotations

import pytest

from eaip.automation.integration import AutomationRuntimeModule
from eaip.automation.models import AutomationConfig


class TestAutomationRuntimeModule:
    @pytest.fixture
    def module(self) -> AutomationRuntimeModule:
        return AutomationRuntimeModule()

    def test_module_name(self) -> None:
        module = AutomationRuntimeModule()
        assert module.name == "automation"

    def test_default_config(self) -> None:
        module = AutomationRuntimeModule()
        assert module._config.max_concurrent_executions == 10

    def test_custom_config(self) -> None:
        config = AutomationConfig(max_concurrent_executions=5)
        module = AutomationRuntimeModule(config=config)
        assert module._config.max_concurrent_executions == 5

    def test_engine_property(self) -> None:
        module = AutomationRuntimeModule()
        assert module.engine is not None

    def test_engine_with_custom_config(self) -> None:
        config = AutomationConfig(max_concurrent_executions=5)
        module = AutomationRuntimeModule(config=config)
        assert module.engine._config.max_concurrent_executions == 5
