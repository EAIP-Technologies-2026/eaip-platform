"""Tests for GraphRuntimeModule integration."""

from __future__ import annotations

import asyncio

from eaip.kgraph.integration import GraphRuntimeModule


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


class TestGraphRuntimeModule:
    def test_start_stop_lifecycle(self) -> None:
        module = GraphRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert module.startup_duration >= 0
        assert module.graph is not None
        assert module.index is not None
        assert module.semantic is not None
        asyncio.run(module.stop(kernel))

    def test_selector_raises_before_start(self) -> None:
        module = GraphRuntimeModule()
        try:
            _ = module.graph
            raise AssertionError()
        except RuntimeError:
            pass

    def test_graph_available_after_start(self) -> None:
        module = GraphRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        graph = module.graph
        assert graph is not None
        asyncio.run(module.stop(kernel))

    def test_health_check_registered(self) -> None:
        module = GraphRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert "kgraph" in kernel.platform.health.registered()
        asyncio.run(module.stop(kernel))

    def test_capability_registered(self) -> None:
        module = GraphRuntimeModule()
        kernel = _MockKernel()
        asyncio.run(module.start(kernel))
        assert len(kernel.platform._capabilities._caps) == 1
        cap = kernel.platform._capabilities._caps[0]
        assert cap.name == "kgraph:engine"
        asyncio.run(module.stop(kernel))

    def test_create_graph_module(self) -> None:
        from eaip.kgraph.integration import create_graph_module

        module = create_graph_module()
        assert module.name == "kgraph"
