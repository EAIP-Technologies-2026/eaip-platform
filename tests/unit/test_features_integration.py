"""Tests for :mod:`eaip.features.integration`."""

from __future__ import annotations

import pytest

from eaip.features.experiments import ExperimentService
from eaip.features.health import FeatureHealthCheck
from eaip.features.integration import FeatureRuntimeModule
from eaip.features.manager import FeatureManager
from eaip.features.models import FeatureConfig
from eaip.features.rollout import RolloutManager


class TestFeatureRuntimeModule:
    def test_instantiation(self) -> None:
        module = FeatureRuntimeModule()
        assert module.name == "features"
        assert isinstance(module.config, FeatureConfig)
        assert isinstance(module.manager, FeatureManager)
        assert isinstance(module.experiment_service, ExperimentService)
        assert isinstance(module.rollout_manager, RolloutManager)
        assert isinstance(module.health_check, FeatureHealthCheck)

    def test_custom_services(self) -> None:
        config = FeatureConfig(max_flags_per_project=100)
        manager = FeatureManager()
        exp_service = ExperimentService()
        rollout = RolloutManager(manager)
        module = FeatureRuntimeModule(
            config=config,
            manager=manager,
            experiment_service=exp_service,
            rollout_manager=rollout,
        )
        assert module.config.max_flags_per_project == 100
        assert module.manager is manager
        assert module.experiment_service is exp_service
        assert module.rollout_manager is rollout

    def test_services_share_manager(self) -> None:
        module = FeatureRuntimeModule()
        assert module.rollout_manager._manager is module.manager


class TestFeatureHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_healthy(self) -> None:
        module = FeatureRuntimeModule()
        report = await module.health_check.check()
        assert report.component == "features"
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_details(self) -> None:
        module = FeatureRuntimeModule()
        await module.manager.create_flag(id="f1", name="Test", key="test-flag")
        report = await module.health_check.check()
        assert "flag_count" in report.details
        assert report.details["flag_count"] == 1

    @pytest.mark.asyncio
    async def test_health_check_message(self) -> None:
        module = FeatureRuntimeModule()
        report = await module.health_check.check()
        assert "healthy" in report.message
