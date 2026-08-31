"""Tests for the experiment tracking package."""

from __future__ import annotations

import pytest

from eaip.experiment_tracking.events import (
    ExperimentActivated,
    ExperimentAssignmentLogged,
    ExperimentCancelled,
    ExperimentComparisonComputed,
    ExperimentCompleted,
    ExperimentCreated,
    ExperimentDeleted,
    ExperimentHypothesisTested,
    ExperimentPaused,
    ExperimentReportGenerated,
    ExperimentRunCompleted,
    ExperimentRunFailed,
    ExperimentRunStarted,
    ExperimentUpdated,
    ExperimentVariantAdded,
    ExperimentVariantRemoved,
)
from eaip.experiment_tracking.exceptions import (
    ExperimentActivationError,
    ExperimentAnalysisError,
    ExperimentAssignmentError,
    ExperimentConfigError,
    ExperimentNotFoundError,
    ExperimentRunError,
    ExperimentTrackingError,
)
from eaip.experiment_tracking.health import ExperimentTrackingHealthCheck
from eaip.experiment_tracking.integration import ExperimentTrackingRuntimeModule
from eaip.experiment_tracking.models import (
    Experiment,
    ExperimentAssignment,
    ExperimentAuditLog,
    ExperimentComparison,
    ExperimentConfig,
    ExperimentGroup,
    ExperimentHypothesis,
    ExperimentMetric,
    ExperimentParameter,
    ExperimentReport,
    ExperimentResult,
    ExperimentRunStatus,
    ExperimentStatus,
    ExperimentVariant,
)
from eaip.experiment_tracking.service import ExperimentTrackingService


class TestModels:
    def test_experiment_defaults(self) -> None:
        exp = Experiment(id="exp-1", name="Test")
        assert exp.status == ExperimentStatus.DRAFT
        assert exp.variants == ()
        assert exp.metrics == ()
        assert exp.config.min_sample_size == 100

    def test_experiment_frozen(self) -> None:
        exp = Experiment(id="exp-1", name="Test")
        with pytest.raises(ValueError, match="frozen"):
            exp.name = "Changed"

    def test_variant_traffic_percent_validation(self) -> None:
        with pytest.raises(ValueError, match=r"ge 0\.0"):
            ExperimentVariant(id="v1", name="V1", traffic_percent=-1.0)

        with pytest.raises(ValueError, match=r"le 100\.0"):
            ExperimentVariant(id="v1", name="V1", traffic_percent=101.0)

        v = ExperimentVariant(id="v1", name="V1", traffic_percent=50.0)
        assert v.traffic_percent == 50.0

    def test_experiment_status_enum(self) -> None:
        assert ExperimentStatus.DRAFT.value == "draft"
        assert ExperimentStatus.ACTIVE.value == "active"
        assert ExperimentStatus.PAUSED.value == "paused"
        assert ExperimentStatus.COMPLETED.value == "completed"
        assert ExperimentStatus.CANCELLED.value == "cancelled"

    def test_experiment_run_status_enum(self) -> None:
        assert ExperimentRunStatus.PENDING.value == "pending"
        assert ExperimentRunStatus.RUNNING.value == "running"
        assert ExperimentRunStatus.COMPLETED.value == "completed"
        assert ExperimentRunStatus.FAILED.value == "failed"

    def test_experiment_comparison_defaults(self) -> None:
        cmp = ExperimentComparison(
            id="cmp-1",
            experiment_id="exp-1",
            control_variant_id="v1",
            treatment_variant_id="v2",
            metric_id="m1",
        )
        assert cmp.lift == 0.0
        assert cmp.p_value == 0.0
        assert not cmp.significant
        assert cmp.confidence_level == 0.95

    def test_experiment_report_frozen(self) -> None:
        rpt = ExperimentReport(id="rpt-1", experiment_id="exp-1", title="Report")
        with pytest.raises(ValueError, match="frozen"):
            rpt.title = "Changed"

    def test_experiment_audit_log_defaults(self) -> None:
        log = ExperimentAuditLog(id="log-1", experiment_id="exp-1", action="created")
        assert log.actor == ""
        assert log.details == {}

    def test_experiment_group_defaults(self) -> None:
        g = ExperimentGroup(id="g1", name="Group A", traffic_percent=50.0)
        assert g.variants == ()
        assert g.description == ""

    def test_experiment_hypothesis_frozen(self) -> None:
        h = ExperimentHypothesis(id="h1", description="Test hypothesis", metric_id="m1")
        with pytest.raises(ValueError, match="frozen"):
            h.tested = True

    def test_experiment_parameter_defaults(self) -> None:
        p = ExperimentParameter(key="k", value="v")
        assert p.description == ""

    def test_experiment_config_defaults(self) -> None:
        c = ExperimentConfig()
        assert c.min_sample_size == 100
        assert c.confidence_level == 0.95
        assert c.auto_stop

    def test_experiment_assignment_frozen(self) -> None:
        a = ExperimentAssignment(experiment_id="exp-1", variant_id="v1", entity_id="user-1")
        with pytest.raises(ValueError, match="frozen"):
            a.entity_id = "changed"

    def test_experiment_result_defaults(self) -> None:
        r = ExperimentResult(variant_id="v1", metric_id="m1")
        assert r.mean == 0.0
        assert r.sample_size == 0
        assert r.sum_value == 0.0


class TestEvents:
    def test_experiment_created_event_type(self) -> None:
        event = ExperimentCreated(experiment_id="exp-1", name="Test")
        assert event.event_type == "eaip.experiment_tracking.experiment.created"

    def test_experiment_updated_event_type(self) -> None:
        event = ExperimentUpdated(experiment_id="exp-1")
        assert event.event_type == "eaip.experiment_tracking.experiment.updated"

    def test_experiment_deleted_event_type(self) -> None:
        event = ExperimentDeleted(experiment_id="exp-1")
        assert event.event_type == "eaip.experiment_tracking.experiment.deleted"

    def test_experiment_activated_event_type(self) -> None:
        event = ExperimentActivated(experiment_id="exp-1")
        assert event.event_type == "eaip.experiment_tracking.experiment.activated"

    def test_experiment_paused_event_type(self) -> None:
        event = ExperimentPaused(experiment_id="exp-1")
        assert event.event_type == "eaip.experiment_tracking.experiment.paused"

    def test_experiment_completed_event_type(self) -> None:
        event = ExperimentCompleted(experiment_id="exp-1")
        assert event.event_type == "eaip.experiment_tracking.experiment.completed"

    def test_experiment_cancelled_event_type(self) -> None:
        event = ExperimentCancelled(experiment_id="exp-1")
        assert event.event_type == "eaip.experiment_tracking.experiment.cancelled"

    def test_experiment_run_started_event_type(self) -> None:
        event = ExperimentRunStarted(run_id="r1", experiment_id="exp-1", variant_id="v1")
        assert event.event_type == "eaip.experiment_tracking.run.started"

    def test_experiment_run_completed_event_type(self) -> None:
        event = ExperimentRunCompleted(run_id="r1", experiment_id="exp-1", variant_id="v1")
        assert event.event_type == "eaip.experiment_tracking.run.completed"

    def test_experiment_run_failed_event_type(self) -> None:
        event = ExperimentRunFailed(run_id="r1", experiment_id="exp-1", variant_id="v1")
        assert event.event_type == "eaip.experiment_tracking.run.failed"

    def test_experiment_comparison_computed_event_type(self) -> None:
        event = ExperimentComparisonComputed(
            comparison_id="c1", experiment_id="exp-1", metric_id="m1"
        )
        assert event.event_type == "eaip.experiment_tracking.comparison.computed"

    def test_experiment_report_generated_event_type(self) -> None:
        event = ExperimentReportGenerated(report_id="rpt-1", experiment_id="exp-1", title="Report")
        assert event.event_type == "eaip.experiment_tracking.report.generated"

    def test_experiment_hypothesis_tested_event_type(self) -> None:
        event = ExperimentHypothesisTested(
            hypothesis_id="h1", experiment_id="exp-1", metric_id="m1"
        )
        assert event.event_type == "eaip.experiment_tracking.hypothesis.tested"

    def test_experiment_variant_added_event_type(self) -> None:
        event = ExperimentVariantAdded(experiment_id="exp-1", variant_id="v1", variant_name="V1")
        assert event.event_type == "eaip.experiment_tracking.variant.added"

    def test_experiment_variant_removed_event_type(self) -> None:
        event = ExperimentVariantRemoved(experiment_id="exp-1", variant_id="v1", variant_name="V1")
        assert event.event_type == "eaip.experiment_tracking.variant.removed"

    def test_experiment_assignment_logged_event_type(self) -> None:
        event = ExperimentAssignmentLogged(
            experiment_id="exp-1", variant_id="v1", entity_id="user-1"
        )
        assert event.event_type == "eaip.experiment_tracking.assignment.logged"

    def test_events_are_frozen(self) -> None:
        event = ExperimentCreated(experiment_id="exp-1")
        with pytest.raises(ValueError, match="frozen"):
            event.experiment_id = "changed"


class TestExceptions:
    def test_experiment_tracking_error(self) -> None:
        err = ExperimentTrackingError("test error")
        assert "test error" in str(err)

    def test_experiment_not_found_error(self) -> None:
        err = ExperimentNotFoundError("exp-1")
        assert "exp-1" in str(err)
        assert err.experiment_id == "exp-1"

    def test_experiment_config_error(self) -> None:
        err = ExperimentConfigError("invalid config")
        assert "invalid config" in str(err)

    def test_experiment_run_error(self) -> None:
        err = ExperimentRunError("run failed")
        assert "run failed" in str(err)

    def test_experiment_activation_error(self) -> None:
        err = ExperimentActivationError("cannot activate")
        assert "cannot activate" in str(err)

    def test_experiment_analysis_error(self) -> None:
        err = ExperimentAnalysisError("analysis failed")
        assert "analysis failed" in str(err)

    def test_experiment_assignment_error(self) -> None:
        err = ExperimentAssignmentError("assignment failed")
        assert "assignment failed" in str(err)


class TestService:
    @pytest.fixture
    def service(self) -> ExperimentTrackingService:
        return ExperimentTrackingService()

    @pytest.fixture
    def variant_a(self) -> ExperimentVariant:
        return ExperimentVariant(id="v-a", name="Control", traffic_percent=50.0)

    @pytest.fixture
    def variant_b(self) -> ExperimentVariant:
        return ExperimentVariant(id="v-b", name="Treatment", traffic_percent=50.0)

    @pytest.fixture
    def metric(self) -> ExperimentMetric:
        return ExperimentMetric(id="m-1", name="Conversion Rate", higher_is_better=True)

    @pytest.mark.asyncio
    async def test_create_and_get_experiment(self, service: ExperimentTrackingService) -> None:
        exp = await service.create_experiment(name="Test Experiment")
        assert exp.id.startswith("exp_")
        assert exp.name == "Test Experiment"
        assert exp.status == ExperimentStatus.DRAFT

        fetched = await service.get_experiment(exp.id)
        assert fetched.id == exp.id

    @pytest.mark.asyncio
    async def test_get_experiment_not_found(self, service: ExperimentTrackingService) -> None:
        with pytest.raises(ExperimentNotFoundError, match="not found"):
            await service.get_experiment("nonexistent")

    @pytest.mark.asyncio
    async def test_list_experiments(self, service: ExperimentTrackingService) -> None:
        await service.create_experiment(name="Exp 1")
        await service.create_experiment(name="Exp 2")
        all_exps = await service.list_experiments()
        assert len(all_exps) == 2

    @pytest.mark.asyncio
    async def test_list_experiments_filter_by_status(
        self, service: ExperimentTrackingService
    ) -> None:
        exp1 = await service.create_experiment(name="Exp 1")
        await service.create_experiment(name="Exp 2")
        await service.activate_experiment(exp1.id)
        active = await service.list_experiments(status=ExperimentStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].id == exp1.id

    @pytest.mark.asyncio
    async def test_update_experiment(self, service: ExperimentTrackingService) -> None:
        exp = await service.create_experiment(name="Original")
        updated = await service.update_experiment(exp.id, name="Updated")
        assert updated.name == "Updated"
        assert updated.updated_at > exp.updated_at

    @pytest.mark.asyncio
    async def test_delete_experiment(self, service: ExperimentTrackingService) -> None:
        exp = await service.create_experiment(name="To Delete")
        await service.delete_experiment(exp.id)
        with pytest.raises(ExperimentNotFoundError):
            await service.get_experiment(exp.id)

    @pytest.mark.asyncio
    async def test_delete_experiment_not_found(self, service: ExperimentTrackingService) -> None:
        with pytest.raises(ExperimentNotFoundError):
            await service.delete_experiment("nonexistent")

    @pytest.mark.asyncio
    async def test_activate_experiment(
        self,
        service: ExperimentTrackingService,
        variant_a: ExperimentVariant,
        variant_b: ExperimentVariant,
        metric: ExperimentMetric,
    ) -> None:
        exp = await service.create_experiment(
            name="Test",
            variants=(variant_a, variant_b),
            metrics=(metric,),
        )
        activated = await service.activate_experiment(exp.id)
        assert activated.status == ExperimentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_activate_experiment_no_variants(
        self, service: ExperimentTrackingService, metric: ExperimentMetric
    ) -> None:
        exp = await service.create_experiment(name="Test", metrics=(metric,))
        with pytest.raises(ExperimentActivationError, match="at least one variant"):
            await service.activate_experiment(exp.id)

    @pytest.mark.asyncio
    async def test_activate_experiment_no_metrics(
        self, service: ExperimentTrackingService, variant_a: ExperimentVariant
    ) -> None:
        exp = await service.create_experiment(name="Test", variants=(variant_a,))
        with pytest.raises(ExperimentActivationError, match="at least one metric"):
            await service.activate_experiment(exp.id)

    @pytest.mark.asyncio
    async def test_activate_experiment_wrong_status(
        self, service: ExperimentTrackingService
    ) -> None:
        exp = await service.create_experiment(name="Test")
        await service.activate_experiment(exp.id)
        with pytest.raises(ExperimentActivationError, match="cannot activate"):
            await service.activate_experiment(exp.id)

    @pytest.mark.asyncio
    async def test_experiment_lifecycle(
        self,
        service: ExperimentTrackingService,
        variant_a: ExperimentVariant,
        variant_b: ExperimentVariant,
        metric: ExperimentMetric,
    ) -> None:
        exp = await service.create_experiment(
            name="Lifecycle",
            variants=(variant_a, variant_b),
            metrics=(metric,),
        )
        assert exp.status == ExperimentStatus.DRAFT

        exp = await service.activate_experiment(exp.id)
        assert exp.status == ExperimentStatus.ACTIVE

        exp = await service.pause_experiment(exp.id)
        assert exp.status == ExperimentStatus.PAUSED

        exp = await service.complete_experiment(exp.id)
        assert exp.status == ExperimentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_cancel_experiment(
        self,
        service: ExperimentTrackingService,
        variant_a: ExperimentVariant,
        variant_b: ExperimentVariant,
        metric: ExperimentMetric,
    ) -> None:
        exp = await service.create_experiment(
            name="Cancel Test",
            variants=(variant_a, variant_b),
            metrics=(metric,),
        )
        cancelled = await service.cancel_experiment(exp.id)
        assert cancelled.status == ExperimentStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_completed_experiment(
        self,
        service: ExperimentTrackingService,
        variant_a: ExperimentVariant,
        variant_b: ExperimentVariant,
        metric: ExperimentMetric,
    ) -> None:
        exp = await service.create_experiment(
            name="Cancel Test",
            variants=(variant_a, variant_b),
            metrics=(metric,),
        )
        await service.activate_experiment(exp.id)
        await service.complete_experiment(exp.id)
        with pytest.raises(ExperimentActivationError, match="cannot cancel"):
            await service.cancel_experiment(exp.id)

    @pytest.mark.asyncio
    async def test_add_variant(
        self, service: ExperimentTrackingService, variant_a: ExperimentVariant
    ) -> None:
        exp = await service.create_experiment(name="Test")
        exp = await service.add_variant(exp.id, variant_a)
        assert len(exp.variants) == 1
        assert exp.variants[0].id == "v-a"

    @pytest.mark.asyncio
    async def test_add_duplicate_variant(
        self, service: ExperimentTrackingService, variant_a: ExperimentVariant
    ) -> None:
        exp = await service.create_experiment(name="Test")
        await service.add_variant(exp.id, variant_a)
        with pytest.raises(ExperimentConfigError, match="already exists"):
            await service.add_variant(exp.id, variant_a)

    @pytest.mark.asyncio
    async def test_remove_variant(
        self,
        service: ExperimentTrackingService,
        variant_a: ExperimentVariant,
        variant_b: ExperimentVariant,
    ) -> None:
        exp = await service.create_experiment(name="Test", variants=(variant_a, variant_b))
        exp = await service.remove_variant(exp.id, "v-a")
        assert len(exp.variants) == 1
        assert exp.variants[0].id == "v-b"

    @pytest.mark.asyncio
    async def test_start_run(
        self,
        service: ExperimentTrackingService,
        variant_a: ExperimentVariant,
        variant_b: ExperimentVariant,
        metric: ExperimentMetric,
    ) -> None:
        exp = await service.create_experiment(
            name="Run Test",
            variants=(variant_a, variant_b),
            metrics=(metric,),
        )
        await service.activate_experiment(exp.id)
        run = await service.start_run(exp.id, "v-a")
        assert run.status == ExperimentRunStatus.RUNNING
        assert run.variant_id == "v-a"

    @pytest.mark.asyncio
    async def test_start_run_not_active(
        self, service: ExperimentTrackingService, variant_a: ExperimentVariant
    ) -> None:
        exp = await service.create_experiment(name="Run Test", variants=(variant_a,))
        with pytest.raises(ExperimentRunError, match="not active"):
            await service.start_run(exp.id, "v-a")

    @pytest.mark.asyncio
    async def test_complete_run(
        self,
        service: ExperimentTrackingService,
        variant_a: ExperimentVariant,
        variant_b: ExperimentVariant,
        metric: ExperimentMetric,
    ) -> None:
        exp = await service.create_experiment(
            name="Run Test",
            variants=(variant_a, variant_b),
            metrics=(metric,),
        )
        await service.activate_experiment(exp.id)
        run = await service.start_run(exp.id, "v-a")
        results = (ExperimentResult(variant_id="v-a", metric_id="m-1", mean=0.5, sample_size=10),)
        completed = await service.complete_run(exp.id, run.id, results)
        assert completed.status == ExperimentRunStatus.COMPLETED
        assert len(completed.results) == 1

    @pytest.mark.asyncio
    async def test_fail_run(
        self,
        service: ExperimentTrackingService,
        variant_a: ExperimentVariant,
        variant_b: ExperimentVariant,
        metric: ExperimentMetric,
    ) -> None:
        exp = await service.create_experiment(
            name="Run Test",
            variants=(variant_a, variant_b),
            metrics=(metric,),
        )
        await service.activate_experiment(exp.id)
        run = await service.start_run(exp.id, "v-a")
        failed = await service.fail_run(exp.id, run.id, "Unexpected error")
        assert failed.status == ExperimentRunStatus.FAILED
        assert failed.error_message == "Unexpected error"

    @pytest.mark.asyncio
    async def test_log_assignment(
        self,
        service: ExperimentTrackingService,
        variant_a: ExperimentVariant,
        variant_b: ExperimentVariant,
        metric: ExperimentMetric,
    ) -> None:
        exp = await service.create_experiment(
            name="Assignment Test",
            variants=(variant_a, variant_b),
            metrics=(metric,),
        )
        await service.activate_experiment(exp.id)
        assignment = await service.log_assignment(exp.id, "v-a", "user-1", {"browser": "chrome"})
        assert assignment.entity_id == "user-1"
        assert assignment.variant_id == "v-a"
        assert assignment.context["browser"] == "chrome"

    @pytest.mark.asyncio
    async def test_log_assignment_not_active(
        self, service: ExperimentTrackingService, variant_a: ExperimentVariant
    ) -> None:
        exp = await service.create_experiment(name="Test", variants=(variant_a,))
        with pytest.raises(ExperimentAssignmentError, match="not active"):
            await service.log_assignment(exp.id, "v-a", "user-1")

    @pytest.mark.asyncio
    async def test_generate_report(
        self,
        service: ExperimentTrackingService,
        variant_a: ExperimentVariant,
        variant_b: ExperimentVariant,
        metric: ExperimentMetric,
    ) -> None:
        exp = await service.create_experiment(
            name="Report Test",
            variants=(variant_a, variant_b),
            metrics=(metric,),
        )
        await service.activate_experiment(exp.id)
        run = await service.start_run(exp.id, "v-a")
        results = (ExperimentResult(variant_id="v-a", metric_id="m-1", mean=0.5, sample_size=10),)
        await service.complete_run(exp.id, run.id, results)
        report = await service.generate_report(exp.id)
        assert report.experiment_id == exp.id
        assert "Report Test" in report.title

    @pytest.mark.asyncio
    async def test_audit_log(self, service: ExperimentTrackingService) -> None:
        exp = await service.create_experiment(name="Audit Test")
        log = await service.log_audit(exp.id, "created", "test-user")
        assert log.action == "created"
        assert log.actor == "test-user"

        logs = await service.get_audit_logs(exp.id)
        assert len(logs) == 1
        assert logs[0].id == log.id

    @pytest.mark.asyncio
    async def test_compute_comparison(
        self,
        service: ExperimentTrackingService,
        variant_a: ExperimentVariant,
        variant_b: ExperimentVariant,
        metric: ExperimentMetric,
    ) -> None:
        exp = await service.create_experiment(
            name="Comparison Test",
            variants=(variant_a, variant_b),
            metrics=(metric,),
        )
        await service.activate_experiment(exp.id)
        run_a = await service.start_run(exp.id, "v-a")
        await service.complete_run(
            exp.id,
            run_a.id,
            (ExperimentResult(variant_id="v-a", metric_id="m-1", mean=0.4, sample_size=50),),
        )
        run_b = await service.start_run(exp.id, "v-b")
        await service.complete_run(
            exp.id,
            run_b.id,
            (ExperimentResult(variant_id="v-b", metric_id="m-1", mean=0.6, sample_size=50),),
        )
        comparison = await service.compute_comparison(exp.id, "v-a", "v-b", "m-1")
        assert comparison.experiment_id == exp.id
        assert comparison.control_variant_id == "v-a"
        assert comparison.treatment_variant_id == "v-b"
        assert comparison.metric_id == "m-1"

    @pytest.mark.asyncio
    async def test_compute_comparison_insufficient_data(
        self,
        service: ExperimentTrackingService,
        variant_a: ExperimentVariant,
        variant_b: ExperimentVariant,
        metric: ExperimentMetric,
    ) -> None:
        exp = await service.create_experiment(
            name="Comparison Test",
            variants=(variant_a, variant_b),
            metrics=(metric,),
        )
        await service.activate_experiment(exp.id)
        with pytest.raises(ExperimentAnalysisError, match="insufficient data"):
            await service.compute_comparison(exp.id, "v-a", "v-b", "m-1")

    @pytest.mark.asyncio
    async def test_test_hypothesis(
        self,
        service: ExperimentTrackingService,
        variant_a: ExperimentVariant,
        variant_b: ExperimentVariant,
        metric: ExperimentMetric,
    ) -> None:
        hypothesis = ExperimentHypothesis(
            id="h-1",
            description="Treatment increases conversion",
            metric_id="m-1",
        )
        exp = await service.create_experiment(
            name="Hypothesis Test",
            variants=(variant_a, variant_b),
            metrics=(metric,),
            hypothesis=hypothesis,
        )
        await service.activate_experiment(exp.id)
        run_a = await service.start_run(exp.id, "v-a")
        await service.complete_run(
            exp.id,
            run_a.id,
            (ExperimentResult(variant_id="v-a", metric_id="m-1", mean=0.4, sample_size=50),),
        )
        run_b = await service.start_run(exp.id, "v-b")
        await service.complete_run(
            exp.id,
            run_b.id,
            (ExperimentResult(variant_id="v-b", metric_id="m-1", mean=0.6, sample_size=50),),
        )
        result = await service.test_hypothesis(exp.id)
        assert result.tested
        assert result.p_value is not None


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_check_degraded(self) -> None:
        service = ExperimentTrackingService()
        check = ExperimentTrackingHealthCheck(service=service)
        report = await check.check()
        assert report.status.value == "degraded"
        assert report.details["experiments_total"] == 0

    @pytest.mark.asyncio
    async def test_health_check_healthy(self) -> None:
        service = ExperimentTrackingService()
        await service.create_experiment(name="Test")
        check = ExperimentTrackingHealthCheck(service=service)
        report = await check.check()
        assert report.status.value == "healthy"
        assert report.details["experiments_total"] == 1


class TestIntegration:
    def test_module_name(self) -> None:
        module = ExperimentTrackingRuntimeModule()
        assert module.name == "experiment_tracking"

    def test_module_service_access(self) -> None:
        service = ExperimentTrackingService()
        module = ExperimentTrackingRuntimeModule(service=service)
        assert module.service is service

    def test_module_creates_service_by_default(self) -> None:
        module = ExperimentTrackingRuntimeModule()
        assert module.service is not None
        assert isinstance(module.service, ExperimentTrackingService)


class TestExports:
    def test_models_exported(self) -> None:
        from eaip.experiment_tracking import models as m

        assert hasattr(m, "Experiment")
        assert hasattr(m, "ExperimentStatus")
        assert hasattr(m, "ExperimentVariant")
        assert hasattr(m, "ExperimentMetric")
        assert hasattr(m, "ExperimentResult")
        assert hasattr(m, "ExperimentConfig")
        assert hasattr(m, "ExperimentRun")
        assert hasattr(m, "ExperimentRunStatus")
        assert hasattr(m, "ExperimentComparison")
        assert hasattr(m, "ExperimentReport")
        assert hasattr(m, "ExperimentHypothesis")
        assert hasattr(m, "ExperimentParameter")
        assert hasattr(m, "ExperimentGroup")
        assert hasattr(m, "ExperimentAssignment")
        assert hasattr(m, "ExperimentAuditLog")

    def test_events_exported(self) -> None:
        from eaip.experiment_tracking import events as e

        assert hasattr(e, "ExperimentCreated")
        assert hasattr(e, "ExperimentUpdated")
        assert hasattr(e, "ExperimentDeleted")
        assert hasattr(e, "ExperimentActivated")
        assert hasattr(e, "ExperimentPaused")
        assert hasattr(e, "ExperimentCompleted")
        assert hasattr(e, "ExperimentCancelled")
        assert hasattr(e, "ExperimentRunStarted")
        assert hasattr(e, "ExperimentRunCompleted")
        assert hasattr(e, "ExperimentRunFailed")
        assert hasattr(e, "ExperimentComparisonComputed")
        assert hasattr(e, "ExperimentReportGenerated")
        assert hasattr(e, "ExperimentHypothesisTested")
        assert hasattr(e, "ExperimentVariantAdded")
        assert hasattr(e, "ExperimentVariantRemoved")
        assert hasattr(e, "ExperimentAssignmentLogged")

    def test_exceptions_exported(self) -> None:
        from eaip.experiment_tracking import exceptions as ex

        assert hasattr(ex, "ExperimentTrackingError")
        assert hasattr(ex, "ExperimentNotFoundError")
        assert hasattr(ex, "ExperimentConfigError")
        assert hasattr(ex, "ExperimentRunError")
        assert hasattr(ex, "ExperimentActivationError")
        assert hasattr(ex, "ExperimentAnalysisError")
        assert hasattr(ex, "ExperimentAssignmentError")

    def test_health_exported(self) -> None:
        from eaip.experiment_tracking import health as h

        assert hasattr(h, "ExperimentTrackingHealthCheck")

    def test_integration_exported(self) -> None:
        from eaip.experiment_tracking import integration as i

        assert hasattr(i, "ExperimentTrackingRuntimeModule")

    def test_service_exported(self) -> None:
        from eaip.experiment_tracking import service as s

        assert hasattr(s, "ExperimentTrackingService")

    def test_package_init_exports(self) -> None:
        import eaip.experiment_tracking as pkg

        attrs = [
            "Experiment",
            "ExperimentStatus",
            "ExperimentVariant",
            "ExperimentMetric",
            "ExperimentResult",
            "ExperimentConfig",
            "ExperimentRun",
            "ExperimentRunStatus",
            "ExperimentComparison",
            "ExperimentReport",
            "ExperimentHypothesis",
            "ExperimentParameter",
            "ExperimentGroup",
            "ExperimentAssignment",
            "ExperimentAuditLog",
            "ExperimentCreated",
            "ExperimentUpdated",
            "ExperimentDeleted",
            "ExperimentActivated",
            "ExperimentPaused",
            "ExperimentCompleted",
            "ExperimentCancelled",
            "ExperimentRunStarted",
            "ExperimentRunCompleted",
            "ExperimentRunFailed",
            "ExperimentComparisonComputed",
            "ExperimentReportGenerated",
            "ExperimentHypothesisTested",
            "ExperimentVariantAdded",
            "ExperimentVariantRemoved",
            "ExperimentAssignmentLogged",
            "ExperimentTrackingError",
            "ExperimentNotFoundError",
            "ExperimentConfigError",
            "ExperimentRunError",
            "ExperimentActivationError",
            "ExperimentAnalysisError",
            "ExperimentAssignmentError",
            "ExperimentTrackingHealthCheck",
            "ExperimentTrackingRuntimeModule",
            "ExperimentTrackingService",
        ]
        for attr in attrs:
            assert hasattr(pkg, attr), f"missing export: {attr}"
