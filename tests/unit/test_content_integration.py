"""Tests for ContentRuntimeModule."""

from __future__ import annotations

from unittest.mock import MagicMock

from eaip.content.health import ContentHealthCheck
from eaip.content.integration import ContentRuntimeModule
from eaip.content.models import ContentConfig
from eaip.content.registry import ContentRegistry
from eaip.content.versioning import ContentVersioning
from eaip.content.workflow import PublishingWorkflowEngine


class TestContentRuntimeModule:
    def test_default_construction(self) -> None:
        module = ContentRuntimeModule()
        assert module.name == "content"
        assert isinstance(module.registry, ContentRegistry)
        assert isinstance(module.versioning, ContentVersioning)
        assert isinstance(module.workflow_engine, PublishingWorkflowEngine)

    def test_custom_construction(self) -> None:
        config = ContentConfig(max_versions_per_item=3)
        registry = ContentRegistry(config=config)
        versioning = ContentVersioning(config=config)
        workflow = PublishingWorkflowEngine()
        module = ContentRuntimeModule(
            config=config,
            registry=registry,
            versioning=versioning,
            workflow_engine=workflow,
        )
        assert module.registry.config.max_versions_per_item == 3
        assert module.versioning.config.max_versions_per_item == 3

    async def test_start_registers_capability(self) -> None:
        module = ContentRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        await module.start(kernel)

        kernel.platform.capabilities.register.assert_called_once()
        kernel.platform.health.register.assert_called_once()

    async def test_start_registers_health_check(self) -> None:
        module = ContentRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        await module.start(kernel)

        call_args = kernel.platform.health.register.call_args
        registered = call_args[0][0]
        assert isinstance(registered, ContentHealthCheck)

    async def test_stop(self) -> None:
        module = ContentRuntimeModule()
        kernel = MagicMock()
        await module.stop(kernel)

    def test_properties(self) -> None:
        module = ContentRuntimeModule()
        assert isinstance(module.registry, ContentRegistry)
        assert isinstance(module.versioning, ContentVersioning)
        assert isinstance(module.workflow_engine, PublishingWorkflowEngine)

    async def test_start_with_capability_tags(self) -> None:
        module = ContentRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        await module.start(kernel)

        call_args = kernel.platform.capabilities.register.call_args
        capability = call_args[0][0]
        assert capability.name == "eaip.content"
        assert "content" in capability.tags
        assert "registry" in capability.tags
        assert "versioning" in capability.tags
