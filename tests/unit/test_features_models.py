"""Tests for :mod:`eaip.features.models`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.features.models import (
    Experiment,
    ExperimentResult,
    ExperimentStatus,
    ExperimentVariant,
    FeatureConfig,
    FeatureFlag,
    Operator,
    TargetingRule,
)


class TestTargetingRule:
    def test_create_minimal(self) -> None:
        r = TargetingRule(id="r1", attribute="region", operator=Operator.EQ, values=("us-east",))
        assert r.id == "r1"
        assert r.operator is Operator.EQ

    def test_create_with_multiple_values(self) -> None:
        r = TargetingRule(
            id="r2",
            attribute="country",
            operator=Operator.IN,
            values=("US", "CA", "MX"),
        )
        assert len(r.values) == 3

    def test_operator_enum_values(self) -> None:
        assert Operator.IN.value == "in"
        assert Operator.NOT_IN.value == "not_in"
        assert Operator.CONTAINS.value == "contains"
        assert Operator.EQ.value == "eq"
        assert Operator.NEQ.value == "neq"
        assert Operator.GT.value == "gt"
        assert Operator.GTE.value == "gte"
        assert Operator.LT.value == "lt"
        assert Operator.LTE.value == "lte"

    def test_frozen(self) -> None:
        r = TargetingRule(id="r1", attribute="a", operator=Operator.EQ, values=("v",))
        with pytest.raises(ValidationError):
            r.attribute = "b"


class TestFeatureFlag:
    def test_create_minimal(self) -> None:
        f = FeatureFlag(id="f1", name="Test Flag", key="test-flag")
        assert f.id == "f1"
        assert f.enabled is False
        assert f.rollout_percentage == 0
        assert f.targeting_rules == ()

    def test_create_full(self) -> None:
        now = datetime.now(UTC)
        rules = (
            TargetingRule(id="r1", attribute="region", operator=Operator.IN, values=("us-east",)),
        )
        f = FeatureFlag(
            id="f2",
            name="Full Flag",
            key="full-flag",
            description="A full flag",
            enabled=True,
            rollout_percentage=50,
            targeting_rules=rules,
            variants={"red": "Red Theme", "blue": "Blue Theme"},
            tags=("frontend", "experiment"),
            metadata={"owner": "team-a"},
            created_at=now,
            updated_at=now,
        )
        assert f.enabled is True
        assert f.rollout_percentage == 50
        assert len(f.targeting_rules) == 1
        assert f.variants["red"] == "Red Theme"

    def test_rollout_percentage_bounds(self) -> None:
        with pytest.raises(ValidationError):
            FeatureFlag(id="f1", name="Bad", key="bad", rollout_percentage=-1)

    def test_rollout_percentage_upper_bound(self) -> None:
        with pytest.raises(ValidationError):
            FeatureFlag(id="f2", name="Bad", key="bad", rollout_percentage=101)

    def test_frozen(self) -> None:
        f = FeatureFlag(id="f1", name="Test", key="test")
        with pytest.raises(ValidationError):
            f.name = "Changed"

    def test_default_timestamps(self) -> None:
        f = FeatureFlag(id="f1", name="Test", key="test")
        assert f.created_at is not None
        assert f.updated_at is not None


class TestExperimentVariant:
    def test_create_minimal(self) -> None:
        v = ExperimentVariant(id="v1", name="Control")
        assert v.weight == 0

    def test_create_full(self) -> None:
        v = ExperimentVariant(
            id="v2",
            name="Treatment",
            config={"color": "blue"},
            weight=50,
        )
        assert v.config["color"] == "blue"
        assert v.weight == 50

    def test_weight_bounds(self) -> None:
        with pytest.raises(ValidationError):
            ExperimentVariant(id="v1", name="Bad", weight=150)


class TestExperiment:
    def test_create_minimal(self) -> None:
        e = Experiment(id="e1", name="Test Exp", feature_key="flag-a")
        assert e.status is ExperimentStatus.DRAFT

    def test_create_full(self) -> None:
        variants = (
            ExperimentVariant(id="v1", name="Control", weight=50),
            ExperimentVariant(id="v2", name="Treatment", weight=50),
        )
        now = datetime.now(UTC)
        e = Experiment(
            id="e2",
            name="Full Exp",
            description="Full experiment",
            feature_key="flag-b",
            variants=variants,
            traffic_allocation={"v1": 50, "v2": 50},
            status=ExperimentStatus.RUNNING,
            metrics=("conversion", "clickthrough"),
            start_at=now,
            end_at=now,
            metadata={"owner": "team-b"},
        )
        assert len(e.variants) == 2
        assert e.status is ExperimentStatus.RUNNING

    def test_experiment_status_enum(self) -> None:
        assert ExperimentStatus.DRAFT.value == "draft"
        assert ExperimentStatus.RUNNING.value == "running"
        assert ExperimentStatus.PAUSED.value == "paused"
        assert ExperimentStatus.COMPLETED.value == "completed"

    def test_frozen(self) -> None:
        e = Experiment(id="e1", name="Test", feature_key="fk")
        with pytest.raises(ValidationError):
            e.name = "Changed"


class TestExperimentResult:
    def test_create_minimal(self) -> None:
        r = ExperimentResult(
            id="r1",
            experiment_id="e1",
            variant_id="v1",
            metric_name="conversion",
            metric_value=0.15,
        )
        assert r.sample_size == 0
        assert r.confidence_level is None

    def test_create_full(self) -> None:
        now = datetime.now(UTC)
        r = ExperimentResult(
            id="r2",
            experiment_id="e1",
            variant_id="v2",
            metric_name="conversion",
            metric_value=0.18,
            sample_size=1000,
            confidence_level=0.95,
            significance=True,
            started_at=now,
            completed_at=now,
            metadata={"source": "web"},
        )
        assert r.significance is True
        assert r.sample_size == 1000

    def test_frozen(self) -> None:
        r = ExperimentResult(
            id="r1",
            experiment_id="e1",
            variant_id="v1",
            metric_name="m",
            metric_value=0.1,
        )
        with pytest.raises(ValidationError):
            r.metric_value = 0.2


class TestFeatureConfig:
    def test_defaults(self) -> None:
        c = FeatureConfig()
        assert c.max_flags_per_project == 500
        assert c.enable_experiments is True
        assert c.experiment_min_sample_size == 100
        assert c.default_rollout_step == 10
        assert c.cache_ttl_seconds == 300

    def test_custom(self) -> None:
        c = FeatureConfig(
            max_flags_per_project=100,
            enable_experiments=False,
            experiment_min_sample_size=200,
            default_rollout_step=5,
            cache_ttl_seconds=600,
        )
        assert c.max_flags_per_project == 100
        assert c.enable_experiments is False

    def test_frozen(self) -> None:
        c = FeatureConfig()
        with pytest.raises(ValidationError):
            c.max_flags_per_project = 999


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        FeatureFlag(id="f1", name="Test", key="test", unknown_field="value")
