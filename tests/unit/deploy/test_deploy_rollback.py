"""Tests for RollbackManager."""

from __future__ import annotations

import pytest

from eaip.deploy.exceptions import RollbackFailedError
from eaip.deploy.rollback import RollbackManager


class TestRollbackManager:
    def test_create_rollback_plan(self) -> None:
        mgr = RollbackManager()
        plan = mgr.create_rollback_plan(
            plan_id="p1",
            deployment_id="d1",
            reason="deployment failed",
            steps=("revert config", "restore previous image"),
        )
        assert plan.plan_id == "p1"
        assert plan.deployment_id == "d1"
        assert plan.reason == "deployment failed"
        assert len(plan.steps) == 2

    def test_create_rollback_plan_no_steps(self) -> None:
        mgr = RollbackManager()
        plan = mgr.create_rollback_plan(
            plan_id="p1",
            deployment_id="d1",
            reason="manual rollback",
        )
        assert plan.steps == ()

    def test_get_rollback_plan_found(self) -> None:
        mgr = RollbackManager()
        mgr.create_rollback_plan(plan_id="p1", deployment_id="d1", reason="r")
        plan = mgr.get_rollback_plan("p1")
        assert plan is not None
        assert plan.plan_id == "p1"

    def test_get_rollback_plan_not_found(self) -> None:
        mgr = RollbackManager()
        plan = mgr.get_rollback_plan("nonexistent")
        assert plan is None

    def test_execute_rollback_success(self) -> None:
        mgr = RollbackManager()
        mgr.create_rollback_plan(
            plan_id="p1",
            deployment_id="d1",
            reason="failure",
            steps=("step1",),
        )
        plan = mgr.execute_rollback("p1")
        assert plan.plan_id == "p1"

    def test_execute_rollback_plan_not_found(self) -> None:
        mgr = RollbackManager()
        with pytest.raises(RollbackFailedError):
            mgr.execute_rollback("nonexistent")

    def test_execute_rollback_no_steps(self) -> None:
        mgr = RollbackManager()
        mgr.create_rollback_plan(
            plan_id="p1",
            deployment_id="d1",
            reason="failure",
        )
        with pytest.raises(RollbackFailedError):
            mgr.execute_rollback("p1")

    def test_plans_property(self) -> None:
        mgr = RollbackManager()
        mgr.create_rollback_plan(plan_id="p1", deployment_id="d1", reason="r")
        mgr.create_rollback_plan(plan_id="p2", deployment_id="d2", reason="r")
        assert len(mgr.plans) == 2
