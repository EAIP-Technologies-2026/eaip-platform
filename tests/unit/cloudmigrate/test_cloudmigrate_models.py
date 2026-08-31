"""Tests for cloud migration Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.cloudmigrate.models import (
    MigrationAssessment,
    MigrationConfig,
    MigrationPlan,
    MigrationTask,
)


class TestMigrationAssessment:
    def test_default_values(self) -> None:
        a = MigrationAssessment(id="a1", source="aws", target="azure")
        assert a.id == "a1"
        assert a.source == "aws"
        assert a.target == "azure"
        assert a.resources == ()
        assert a.estimated_cost == 0.0
        assert a.risks == ()
        assert a.score == 0.0

    def test_frozen(self) -> None:
        a = MigrationAssessment(id="a1", source="aws", target="azure")
        with pytest.raises(ValidationError):
            a.source = "gcp"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            MigrationAssessment(id="a1", source="aws", target="azure", unknown="x")  # type: ignore[call-arg]

    def test_custom_values(self) -> None:
        a = MigrationAssessment(
            id="a1",
            source="aws",
            target="azure",
            resources=("r1", "r2"),
            estimated_cost=50000.0,
            risks=("downtime",),
            score=0.85,
        )
        assert a.resources == ("r1", "r2")
        assert a.estimated_cost == 50000.0
        assert a.score == 0.85


class TestMigrationPlan:
    def test_default_values(self) -> None:
        p = MigrationPlan(id="p1", assessment_id="a1")
        assert p.steps == ()
        assert p.timeline == ""

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            MigrationPlan(id="p1", assessment_id="a1", unknown=True)  # type: ignore[call-arg]


class TestMigrationTask:
    def test_default_values(self) -> None:
        t = MigrationTask(id="t1", plan_id="p1", name="setup")
        assert t.status == "pending"
        assert t.order == 0

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            MigrationTask(id="t1", plan_id="p1", name="setup", unknown=True)  # type: ignore[call-arg]


class TestMigrationConfig:
    def test_default_values(self) -> None:
        cfg = MigrationConfig()
        assert cfg.max_concurrent_tasks == 5
        assert cfg.default_region == "eastus"
        assert cfg.enable_validation is True
        assert cfg.rollback_on_failure is False

    def test_custom_values(self) -> None:
        cfg = MigrationConfig(
            max_concurrent_tasks=10,
            default_region="westus",
            enable_validation=False,
            rollback_on_failure=True,
        )
        assert cfg.max_concurrent_tasks == 10
        assert cfg.rollback_on_failure is True
