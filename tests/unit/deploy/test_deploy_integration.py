"""Tests for DeployRuntimeModule."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from eaip.deploy.deployer import Deployer
from eaip.deploy.environment import EnvironmentManager
from eaip.deploy.integration import DeployRuntimeModule
from eaip.deploy.release_manager import ReleaseManager
from eaip.deploy.rollback import RollbackManager


class TestDeployRuntimeModule:
    def test_default_initialization(self) -> None:
        module = DeployRuntimeModule()
        assert module.name == "deploy"
        assert isinstance(module.release_manager, ReleaseManager)
        assert isinstance(module.deployer, Deployer)
        assert isinstance(module.rollback_manager, RollbackManager)
        assert isinstance(module.environment_manager, EnvironmentManager)

    def test_custom_initialization(self) -> None:
        rm = ReleaseManager()
        dep = Deployer()
        rbm = RollbackManager()
        em = EnvironmentManager()
        module = DeployRuntimeModule(
            release_manager=rm,
            deployer=dep,
            rollback_manager=rbm,
            environment_manager=em,
        )
        assert module.release_manager is rm
        assert module.deployer is dep
        assert module.rollback_manager is rbm
        assert module.environment_manager is em

    @pytest.mark.asyncio
    async def test_start(self) -> None:
        module = DeployRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()
        await module.start(kernel)
        kernel.platform.capabilities.register.assert_called_once()
        kernel.platform.health.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self) -> None:
        module = DeployRuntimeModule()
        kernel = AsyncMock()
        await module.stop(kernel)
