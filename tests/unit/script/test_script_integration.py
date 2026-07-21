"""Tests for ScriptRuntimeModule integration."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.script.health import ScriptHealthCheck
from eaip.script.integration import ScriptRuntimeModule
from eaip.script.registry import FunctionRegistry
from eaip.script.runtime import ScriptRuntime


class FakePlatform:
    def __init__(self) -> None:
        self.health = MagicMock()
        self.capabilities = MagicMock()


class FakeKernel:
    def __init__(self) -> None:
        self.platform = FakePlatform()
        self._modules: dict[str, object] = {}

    def register_module(self, name: str, module: object) -> None:
        self._modules[name] = module


class TestScriptRuntimeModule:
    def test_initialization(self) -> None:
        module = ScriptRuntimeModule()
        assert module.name == "script"
        assert isinstance(module.registry, FunctionRegistry)
        assert isinstance(module.runtime, ScriptRuntime)

    def test_initialization_with_deps(self) -> None:
        reg = FunctionRegistry()
        rt = ScriptRuntime(registry=reg)
        module = ScriptRuntimeModule(registry=reg, runtime=rt)
        assert module.registry is reg
        assert module.runtime is rt

    @pytest.mark.asyncio
    async def test_start(self) -> None:
        kernel = FakeKernel()
        module = ScriptRuntimeModule()
        await module.start(kernel)  # type: ignore[arg-type]
        assert "script.registry" in kernel._modules
        assert "script.runtime" in kernel._modules

    @pytest.mark.asyncio
    async def test_start_registers_health_check(self) -> None:
        kernel = FakeKernel()
        module = ScriptRuntimeModule()
        await module.start(kernel)  # type: ignore[arg-type]
        kernel.platform.health.register.assert_called_once()
        registered_check = kernel.platform.health.register.call_args[0][0]
        assert isinstance(registered_check, ScriptHealthCheck)

    @pytest.mark.asyncio
    async def test_start_registers_capability(self) -> None:
        kernel = FakeKernel()
        module = ScriptRuntimeModule()
        await module.start(kernel)  # type: ignore[arg-type]
        kernel.platform.capabilities.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self) -> None:
        module = ScriptRuntimeModule()
        kernel = FakeKernel()
        await module.stop(kernel)  # type: ignore[arg-type]
