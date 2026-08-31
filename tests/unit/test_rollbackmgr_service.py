"""Tests for RollbackManager."""

from __future__ import annotations

import pytest

from eaip.rollbackmgr.exceptions import DeploymentNotFoundError
from eaip.rollbackmgr.manager import RollbackManager
from eaip.rollbackmgr.models import (
    Deployment,
    RollbackConfig,
    RollbackPlan,
    RollbackStrategy,
)


class TestRollbackManager:
    @pytest.fixture
    def manager(self) -> RollbackManager:
        return RollbackManager()

    @pytest.fixture
    def sample_deployment(self) -> Deployment:
        return Deployment(
            id="d1", name="app-v2", version="2.0", environment="prod", deployed_by="alice"
        )

    @pytest.fixture
    def sample_plan(self, sample_deployment: Deployment) -> RollbackPlan:
        return RollbackPlan(
            id="p1",
            deployment_id=sample_deployment.id,
            strategy=RollbackStrategy.IMMEDIATE,
            steps=("step1", "step2"),
            estimated_duration=120,
        )

    class TestRecordDeployment:
        async def test_records_deployment(
            self, manager: RollbackManager, sample_deployment: Deployment
        ) -> None:
            result = await manager.record_deployment(sample_deployment)
            assert result.id == "d1"
            assert result.name == "app-v2"

        async def test_stores_deployment(
            self, manager: RollbackManager, sample_deployment: Deployment
        ) -> None:
            await manager.record_deployment(sample_deployment)
            stored = await manager.get_deployment("d1")
            assert stored.id == "d1"

    class TestGetDeployment:
        async def test_returns_deployment(
            self, manager: RollbackManager, sample_deployment: Deployment
        ) -> None:
            await manager.record_deployment(sample_deployment)
            result = await manager.get_deployment("d1")
            assert result.name == "app-v2"

        async def test_raises_on_missing(self, manager: RollbackManager) -> None:
            with pytest.raises(DeploymentNotFoundError):
                await manager.get_deployment("nonexistent")

    class TestUpdateDeployment:
        async def test_updates_deployment(
            self, manager: RollbackManager, sample_deployment: Deployment
        ) -> None:
            await manager.record_deployment(sample_deployment)
            updated = await manager.update_deployment("d1", status="rolled_back")
            assert updated.status == "rolled_back"

        async def test_raises_on_missing(self, manager: RollbackManager) -> None:
            with pytest.raises(DeploymentNotFoundError):
                await manager.update_deployment("nonexistent", status="done")

    class TestListDeployments:
        async def test_empty_when_none(self, manager: RollbackManager) -> None:
            assert await manager.list_deployments() == []

        async def test_filters_by_environment(self, manager: RollbackManager) -> None:
            d1 = Deployment(id="d1", name="a", version="1", environment="prod", deployed_by="alice")
            d2 = Deployment(
                id="d2", name="b", version="2", environment="staging", deployed_by="bob"
            )
            await manager.record_deployment(d1)
            await manager.record_deployment(d2)
            result = await manager.list_deployments(environment="prod")
            assert len(result) == 1

    class TestCreatePlan:
        async def test_creates_plan(
            self, manager: RollbackManager, sample_deployment: Deployment, sample_plan: RollbackPlan
        ) -> None:
            await manager.record_deployment(sample_deployment)
            result = await manager.create_plan(sample_plan)
            assert result.id == "p1"
            assert result.strategy == RollbackStrategy.IMMEDIATE

        async def test_raises_on_missing_deployment(self, manager: RollbackManager) -> None:
            plan = RollbackPlan(id="p1", deployment_id="nonexistent")
            with pytest.raises(DeploymentNotFoundError):
                await manager.create_plan(plan)

    class TestExecuteRollback:
        async def test_executes_rollback(
            self, manager: RollbackManager, sample_deployment: Deployment, sample_plan: RollbackPlan
        ) -> None:
            await manager.record_deployment(sample_deployment)
            await manager.create_plan(sample_plan)
            result = await manager.execute_rollback("p1", "e1")
            assert result.success is True
            assert result.deployment_id == "d1"

        async def test_updates_deployment_status(
            self, manager: RollbackManager, sample_deployment: Deployment, sample_plan: RollbackPlan
        ) -> None:
            await manager.record_deployment(sample_deployment)
            await manager.create_plan(sample_plan)
            await manager.execute_rollback("p1", "e1")
            deployment = await manager.get_deployment("d1")
            assert deployment.status == "rolled_back"

        async def test_raises_on_missing_plan(self, manager: RollbackManager) -> None:
            with pytest.raises(DeploymentNotFoundError):
                await manager.execute_rollback("nonexistent", "e1")

    class TestFailRollback:
        async def test_fails_rollback(
            self, manager: RollbackManager, sample_deployment: Deployment, sample_plan: RollbackPlan
        ) -> None:
            await manager.record_deployment(sample_deployment)
            await manager.create_plan(sample_plan)
            result = await manager.fail_rollback("e1", "p1", error_message="error")
            assert result.success is False
            assert result.error_message == "error"

    class TestListExecutions:
        async def test_lists_executions(
            self, manager: RollbackManager, sample_deployment: Deployment, sample_plan: RollbackPlan
        ) -> None:
            await manager.record_deployment(sample_deployment)
            await manager.create_plan(sample_plan)
            await manager.execute_rollback("p1", "e1")
            executions = await manager.list_executions(deployment_id="d1")
            assert len(executions) == 1

    class TestGetStatistics:
        async def test_returns_stats(
            self, manager: RollbackManager, sample_deployment: Deployment
        ) -> None:
            await manager.record_deployment(sample_deployment)
            stats = await manager.get_statistics()
            assert stats["total_deployments"] == 1

    class TestConfig:
        def test_default_config(self) -> None:
            svc = RollbackManager()
            assert svc.config.require_approval is True

        def test_custom_config(self) -> None:
            cfg = RollbackConfig(require_approval=False)
            svc = RollbackManager(config=cfg)
            assert svc.config.require_approval is False
