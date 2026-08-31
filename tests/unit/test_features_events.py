"""Tests for :mod:`eaip.features.events`."""

from __future__ import annotations

import pytest

from eaip.features.events import (
    ExperimentCompleted,
    ExperimentCreated,
    ExperimentResultRecorded,
    ExperimentStarted,
    FlagCreated,
    FlagDisabled,
    FlagEnabled,
    FlagRolloutChanged,
    FlagUpdated,
    VariantAssigned,
)


class TestFlagCreated:
    def test_minimal(self) -> None:
        e = FlagCreated(flag_id="f1", key="test-flag", name="Test Flag", enabled=False)
        assert e.event_type == "eaip.features.flag.created"
        assert e.flag_id == "f1"

    def test_with_tags(self) -> None:
        e = FlagCreated(
            flag_id="f1",
            key="test-flag",
            name="Test Flag",
            enabled=True,
            tags=("frontend", "beta"),
        )
        assert len(e.tags) == 2

    def test_frozen(self) -> None:
        e = FlagCreated(flag_id="f1", key="k", name="n", enabled=False)
        with pytest.raises(ValueError):
            e.flag_id = "f2"


class TestFlagUpdated:
    def test_create(self) -> None:
        e = FlagUpdated(
            flag_id="f1",
            key="test-flag",
            changes={"rollout_percentage": 50},
        )
        assert e.event_type == "eaip.features.flag.updated"
        assert e.changes["rollout_percentage"] == 50


class TestFlagEnabled:
    def test_create(self) -> None:
        e = FlagEnabled(flag_id="f1", key="test-flag", rollout_percentage=50)
        assert e.event_type == "eaip.features.flag.enabled"


class TestFlagDisabled:
    def test_create(self) -> None:
        e = FlagDisabled(flag_id="f1", key="test-flag")
        assert e.event_type == "eaip.features.flag.disabled"


class TestFlagRolloutChanged:
    def test_create(self) -> None:
        e = FlagRolloutChanged(
            flag_id="f1",
            key="test-flag",
            previous_percentage=10,
            new_percentage=50,
        )
        assert e.event_type == "eaip.features.flag.rollout_changed"
        assert e.previous_percentage == 10
        assert e.new_percentage == 50


class TestExperimentCreated:
    def test_create(self) -> None:
        e = ExperimentCreated(
            experiment_id="e1",
            name="Test Exp",
            feature_key="flag-a",
        )
        assert e.event_type == "eaip.features.experiment.created"


class TestExperimentStarted:
    def test_create(self) -> None:
        e = ExperimentStarted(experiment_id="e1", feature_key="flag-a")
        assert e.event_type == "eaip.features.experiment.started"


class TestExperimentCompleted:
    def test_create(self) -> None:
        e = ExperimentCompleted(experiment_id="e1", feature_key="flag-a")
        assert e.event_type == "eaip.features.experiment.completed"


class TestExperimentResultRecorded:
    def test_create(self) -> None:
        e = ExperimentResultRecorded(
            experiment_id="e1",
            result_id="r1",
            metric_name="conversion",
            metric_value=0.15,
        )
        assert e.event_type == "eaip.features.experiment.result_recorded"


class TestVariantAssigned:
    def test_create(self) -> None:
        e = VariantAssigned(
            experiment_id="e1",
            variant_id="v1",
            entity_id="user-1",
        )
        assert e.event_type == "eaip.features.variant.assigned"


def test_all_events_have_unique_types() -> None:
    types = [
        FlagCreated(flag_id="f1", key="k", name="n", enabled=False).event_type,
        FlagUpdated(flag_id="f1", key="k").event_type,
        FlagEnabled(flag_id="f1", key="k", rollout_percentage=50).event_type,
        FlagDisabled(flag_id="f1", key="k").event_type,
        FlagRolloutChanged(
            flag_id="f1", key="k", previous_percentage=0, new_percentage=50
        ).event_type,
        ExperimentCreated(experiment_id="e1", name="n", feature_key="fk").event_type,
        ExperimentStarted(experiment_id="e1", feature_key="fk").event_type,
        ExperimentCompleted(experiment_id="e1", feature_key="fk").event_type,
        ExperimentResultRecorded(
            experiment_id="e1", result_id="r1", metric_name="m", metric_value=1.0
        ).event_type,
        VariantAssigned(experiment_id="e1", variant_id="v1", entity_id="u1").event_type,
    ]
    assert len(types) == len(set(types)), "event types must be unique"
