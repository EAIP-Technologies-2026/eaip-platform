"""Tests for :mod:`eaip.features.experiments`."""

from __future__ import annotations

import pytest

from eaip.features.events import (
    ExperimentCompleted,
    ExperimentCreated,
    ExperimentResultRecorded,
    ExperimentStarted,
    VariantAssigned,
)
from eaip.features.exceptions import ExperimentCompleteError, ExperimentNotFoundError
from eaip.features.experiments import _HAS_SCIPY, ExperimentService
from eaip.features.models import Experiment, ExperimentResult, ExperimentStatus, ExperimentVariant


@pytest.mark.asyncio
class TestExperimentService:
    async def test_create_experiment(self) -> None:
        svc = ExperimentService()
        exp = await svc.create_experiment(id="e1", name="Test Exp", feature_key="flag-a")
        assert isinstance(exp, Experiment)
        assert exp.status is ExperimentStatus.DRAFT

    async def test_create_experiment_emits_event(self) -> None:
        events: list[object] = []
        svc = ExperimentService(event_callback=events.append)
        await svc.create_experiment(id="e1", name="Test Exp", feature_key="flag-a")
        assert any(isinstance(e, ExperimentCreated) for e in events)

    async def test_get_experiment(self) -> None:
        svc = ExperimentService()
        await svc.create_experiment(id="e1", name="Test Exp", feature_key="flag-a")
        exp = await svc.get_experiment("e1")
        assert exp.name == "Test Exp"

    async def test_get_experiment_not_found(self) -> None:
        svc = ExperimentService()
        with pytest.raises(ExperimentNotFoundError):
            await svc.get_experiment("nonexistent")

    async def test_update_experiment(self) -> None:
        svc = ExperimentService()
        await svc.create_experiment(id="e1", name="Old", feature_key="flag-a")
        updated = await svc.update_experiment("e1", name="New")
        assert updated.name == "New"

    async def test_update_completed_experiment_raises(self) -> None:
        svc = ExperimentService()
        await svc.create_experiment(id="e1", name="Test", feature_key="flag-a")
        await svc.complete_experiment("e1")
        with pytest.raises(ExperimentCompleteError):
            await svc.update_experiment("e1", name="Changed")

    async def test_start_experiment(self) -> None:
        svc = ExperimentService()
        await svc.create_experiment(id="e1", name="Test", feature_key="flag-a")
        exp = await svc.start_experiment("e1")
        assert exp.status is ExperimentStatus.RUNNING

    async def test_start_experiment_emits_event(self) -> None:
        events: list[object] = []
        svc = ExperimentService(event_callback=events.append)
        await svc.create_experiment(id="e1", name="Test", feature_key="flag-a")
        await svc.start_experiment("e1")
        assert any(isinstance(e, ExperimentStarted) for e in events)

    async def test_start_completed_experiment_raises(self) -> None:
        svc = ExperimentService()
        await svc.create_experiment(id="e1", name="Test", feature_key="flag-a")
        await svc.complete_experiment("e1")
        with pytest.raises(ExperimentCompleteError):
            await svc.start_experiment("e1")

    async def test_pause_experiment(self) -> None:
        svc = ExperimentService()
        await svc.create_experiment(id="e1", name="Test", feature_key="flag-a")
        await svc.start_experiment("e1")
        exp = await svc.pause_experiment("e1")
        assert exp.status is ExperimentStatus.PAUSED

    async def test_pause_completed_experiment_raises(self) -> None:
        svc = ExperimentService()
        await svc.create_experiment(id="e1", name="Test", feature_key="flag-a")
        await svc.complete_experiment("e1")
        with pytest.raises(ExperimentCompleteError):
            await svc.pause_experiment("e1")

    async def test_complete_experiment(self) -> None:
        svc = ExperimentService()
        await svc.create_experiment(id="e1", name="Test", feature_key="flag-a")
        exp = await svc.complete_experiment("e1")
        assert exp.status is ExperimentStatus.COMPLETED

    async def test_complete_experiment_emits_event(self) -> None:
        events: list[object] = []
        svc = ExperimentService(event_callback=events.append)
        await svc.create_experiment(id="e1", name="Test", feature_key="flag-a")
        await svc.complete_experiment("e1")
        assert any(isinstance(e, ExperimentCompleted) for e in events)

    async def test_assign_variant(self) -> None:
        svc = ExperimentService()
        variants = (ExperimentVariant(id="v1", name="Control", weight=50),)
        await svc.create_experiment(
            id="e1",
            name="Test",
            feature_key="flag-a",
            variants=variants,
        )
        await svc.start_experiment("e1")
        variant = await svc.assign_variant("e1", "user-1")
        assert variant.id == "v1"

    async def test_assign_variant_from_not_running_raises(self) -> None:
        svc = ExperimentService()
        await svc.create_experiment(id="e1", name="Test", feature_key="flag-a")
        with pytest.raises(ExperimentCompleteError):
            await svc.assign_variant("e1", "user-1")

    async def test_assign_variant_emits_event(self) -> None:
        events: list[object] = []
        svc = ExperimentService(event_callback=events.append)
        variants = (ExperimentVariant(id="v1", name="Control"),)
        await svc.create_experiment(id="e1", name="Test", feature_key="flag-a", variants=variants)
        await svc.start_experiment("e1")
        await svc.assign_variant("e1", "user-1")
        assert any(isinstance(e, VariantAssigned) for e in events)

    async def test_record_result(self) -> None:
        svc = ExperimentService()
        await svc.create_experiment(id="e1", name="Test", feature_key="flag-a")
        result = await svc.record_result(
            id="r1",
            experiment_id="e1",
            variant_id="v1",
            metric_name="conversion",
            metric_value=0.15,
            sample_size=1000,
        )
        assert isinstance(result, ExperimentResult)
        assert result.metric_value == 0.15

    async def test_record_result_emits_event(self) -> None:
        events: list[object] = []
        svc = ExperimentService(event_callback=events.append)
        await svc.create_experiment(id="e1", name="Test", feature_key="flag-a")
        await svc.record_result(
            id="r1",
            experiment_id="e1",
            variant_id="v1",
            metric_name="conversion",
            metric_value=0.15,
        )
        assert any(isinstance(e, ExperimentResultRecorded) for e in events)

    async def test_get_results(self) -> None:
        svc = ExperimentService()
        await svc.create_experiment(id="e1", name="Test", feature_key="flag-a")
        await svc.record_result(
            id="r1",
            experiment_id="e1",
            variant_id="v1",
            metric_name="conversion",
            metric_value=0.15,
        )
        results = await svc.get_results("e1")
        assert len(results) == 1

    async def test_list_experiments(self) -> None:
        svc = ExperimentService()
        await svc.create_experiment(id="e1", name="A", feature_key="fk1")
        await svc.create_experiment(id="e2", name="B", feature_key="fk2")
        assert len(await svc.list_experiments()) == 2

    async def test_analyze_results_no_scipy(self) -> None:
        if _HAS_SCIPY:
            pytest.skip("scipy is installed; skipping fallback test")
        svc = ExperimentService()
        await svc.create_experiment(id="e1", name="Test", feature_key="flag-a")
        result = await svc.analyze_results("e1")
        assert result["conclusive"] is False

    async def test_analyze_results_insufficient_data(self) -> None:
        if not _HAS_SCIPY:
            pytest.skip("scipy not installed")
        svc = ExperimentService()
        await svc.create_experiment(id="e1", name="Test", feature_key="flag-a")
        await svc.record_result(
            id="r1",
            experiment_id="e1",
            variant_id="v1",
            metric_name="conversion",
            metric_value=0.10,
            sample_size=100,
        )
        result = await svc.analyze_results("e1")
        assert result["conclusive"] is False

    async def test_analyze_results_with_data(self) -> None:
        if not _HAS_SCIPY:
            pytest.skip("scipy not installed")
        svc = ExperimentService()
        variants = (
            ExperimentVariant(id="v1", name="Control"),
            ExperimentVariant(id="v2", name="Treatment"),
        )
        await svc.create_experiment(
            id="e1",
            name="Test",
            feature_key="flag-a",
            variants=variants,
        )
        await svc.start_experiment("e1")
        await svc.record_result(
            id="r1",
            experiment_id="e1",
            variant_id="v1",
            metric_name="conversion",
            metric_value=0.10,
            sample_size=1000,
        )
        await svc.record_result(
            id="r2",
            experiment_id="e1",
            variant_id="v2",
            metric_name="conversion",
            metric_value=0.12,
            sample_size=1000,
        )
        result = await svc.analyze_results("e1")
        assert "metrics" in result

    async def test_set_event_callback(self) -> None:
        events: list[object] = []
        svc = ExperimentService()
        svc.set_event_callback(events.append)
        await svc.create_experiment(id="e1", name="Test", feature_key="flag-a")
        assert len(events) == 1
