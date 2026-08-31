"""Tests for WorkforceRuntimeModule integration."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from eaip.workforce.integration import WorkforceRuntimeModule
from eaip.workforce.orchestrator import WorkforceOrchestrator
from eaip.workforce.scheduler import WorkforceScheduler
from eaip.workforce.worker import WorkerRegistry


class MockKernel:
    def __init__(self) -> None:
        self.platform = MagicMock()
        self.platform.health = MagicMock()
        self.platform.capabilities = MagicMock()
        self._modules: dict[str, Any] = {}

    def register_module(self, name: str, module: Any) -> None:
        self._modules[name] = module


class TestWorkforceRuntimeModule:
    def test_default_construction(self) -> None:
        module = WorkforceRuntimeModule()
        assert module.name == "workforce"
        assert isinstance(module.registry, WorkerRegistry)
        assert isinstance(module.orchestrator, WorkforceOrchestrator)
        assert isinstance(module.scheduler, WorkforceScheduler)

    def test_construction_with_deps(self) -> None:
        registry = WorkerRegistry()
        orchestrator = WorkforceOrchestrator(registry=registry)
        scheduler = WorkforceScheduler(registry=registry, job_scheduler=MagicMock())
        module = WorkforceRuntimeModule(
            registry=registry,
            orchestrator=orchestrator,
            scheduler=scheduler,
        )
        assert module.registry is registry
        assert module.orchestrator is orchestrator
        assert module.scheduler is scheduler

    async def test_start_registers_health_and_capability(self) -> None:
        kernel = MockKernel()
        module = WorkforceRuntimeModule()
        await module.start(kernel)

        kernel.platform.health.register.assert_called_once()
        kernel.platform.capabilities.register.assert_called_once()
        assert "workforce.registry" in kernel._modules
        assert "workforce.orchestrator" in kernel._modules
        assert "workforce.scheduler" in kernel._modules

    async def test_start_and_stop(self) -> None:
        kernel = MockKernel()
        module = WorkforceRuntimeModule()
        await module.start(kernel)
        await module.stop(kernel)
        # No exception means success

    async def test_stop_does_not_raise(self) -> None:
        kernel = MockKernel()
        module = WorkforceRuntimeModule()
        await module.stop(kernel)
        # Stopping before start should not raise
