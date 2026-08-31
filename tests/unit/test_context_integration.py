"""Tests for ContextRuntimeModule integration."""

from __future__ import annotations

import asyncio

from eaip.context.builder import ContextBuilder
from eaip.context.compression import ContextCompressor
from eaip.context.integration import ContextRuntimeModule, create_context_integration
from eaip.context.registry import PromptRegistry
from eaip.context.templates import PromptManager


class _MockHealth:
    def __init__(self) -> None:
        self._checks: dict = {}

    def register(self, check: object) -> None:
        self._checks[check.name] = check

    def registered(self) -> list[str]:
        return sorted(self._checks)


class _MockCapabilities:
    def __init__(self) -> None:
        self._caps: list = []

    def register(self, cap: object) -> None:
        self._caps.append(cap)


class _MockContainer:
    def try_resolve(self, key: type) -> object | None:
        return None

    def has(self, key: type) -> bool:
        return False


class _MockPlatform:
    def __init__(self) -> None:
        self._health = _MockHealth()
        self._capabilities = _MockCapabilities()
        self._container = _MockContainer()

    @property
    def health(self) -> _MockHealth:
        return self._health

    @property
    def capabilities(self) -> _MockCapabilities:
        return self._capabilities

    @property
    def container(self) -> _MockContainer:
        return self._container


class _MockKernel:
    def __init__(self) -> None:
        self._platform = _MockPlatform()

    @property
    def platform(self) -> _MockPlatform:
        return self._platform


class TestContextRuntimeModule:
    def test_start_stop_lifecycle(self) -> None:
        module = ContextRuntimeModule(
            registry=PromptRegistry(),
            builder=ContextBuilder(),
            compressor=ContextCompressor(),
        )
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert module.startup_duration >= 0
        assert module.registry is not None
        assert module.manager is not None
        asyncio.run(module.stop(kernel))

    def test_builder_raises_before_start(self) -> None:
        module = ContextRuntimeModule()
        try:
            _ = module.builder
            raise AssertionError()
        except RuntimeError:
            pass

    def test_compressor_raises_before_start(self) -> None:
        module = ContextRuntimeModule()
        try:
            _ = module.compressor
            raise AssertionError()
        except RuntimeError:
            pass

    def test_builder_available_after_start(self) -> None:
        module = ContextRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert module.builder is not None
        asyncio.run(module.stop(kernel))

    def test_compressor_available_after_start(self) -> None:
        module = ContextRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert module.compressor is not None
        asyncio.run(module.stop(kernel))

    def test_health_check_registered(self) -> None:
        module = ContextRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        registered = kernel.platform.health.registered()
        assert "context" in registered
        asyncio.run(module.stop(kernel))

    def test_capability_registered(self) -> None:
        module = ContextRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert len(kernel.platform._capabilities._caps) == 1
        cap = kernel.platform._capabilities._caps[0]
        assert cap.name == "context:engine"
        asyncio.run(module.stop(kernel))

    def test_constructor_with_registry(self) -> None:
        reg = PromptRegistry()
        module = ContextRuntimeModule(registry=reg)
        assert module.registry is reg

    def test_constructor_with_manager(self) -> None:
        reg = PromptRegistry()
        mgr = PromptManager(registry=reg)
        module = ContextRuntimeModule(registry=reg, manager=mgr)
        assert module.manager is mgr

    def test_startup_duration(self) -> None:
        module = ContextRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert module.startup_duration >= 0
        asyncio.run(module.stop(kernel))

    def test_create_context_integration(self) -> None:
        module = create_context_integration()
        assert isinstance(module, ContextRuntimeModule)

    def test_create_context_integration_with_components(self) -> None:
        reg = PromptRegistry()
        builder = ContextBuilder()
        compressor = ContextCompressor()
        mgr = PromptManager(registry=reg)
        module = create_context_integration(
            registry=reg,
            builder=builder,
            compressor=compressor,
            manager=mgr,
        )
        assert module.registry is reg
        assert module.manager is mgr
