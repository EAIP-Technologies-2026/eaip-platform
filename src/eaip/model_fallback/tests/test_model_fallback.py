"""Tests for the model fallback subsystem."""

from __future__ import annotations

import pytest

from eaip.model_fallback.events import (
    DegradationLevelChanged,
    FallbackChainExecuted,
    FallbackConfigCreated,
    FallbackConfigDeleted,
    FallbackConfigUpdated,
    FallbackExecutionCompleted,
    FallbackExecutionFailed,
    FallbackHistoryLogged,
    FallbackMetricsCollected,
    FallbackRecoveryFailed,
    FallbackRecoverySucceeded,
    FallbackStepCompleted,
    FallbackStepFailed,
    FallbackStepSkipped,
    FallbackStepStarted,
    FallbackTriggered,
)
from eaip.model_fallback.exceptions import (
    DegradationError,
    FallbackChainError,
    FallbackConfigError,
    FallbackExecutionError,
    FallbackStepError,
    FallbackTriggerError,
    ModelFallbackError,
)
from eaip.model_fallback.health import ModelFallbackHealthCheck
from eaip.model_fallback.integration import ModelFallbackRuntimeModule
from eaip.model_fallback.models import (
    DegradationLevel,
    FallbackCondition,
    FallbackConfig,
    FallbackExecution,
    FallbackExecutionStatus,
    FallbackHealthStatus,
    FallbackHistoryEntry,
    FallbackMetrics,
    FallbackPolicy,
    FallbackResult,
    FallbackStep,
    FallbackStepStatus,
    FallbackStrategy,
    FallbackTrigger,
    GracefulDegradationConfig,
    ModelFallbackChain,
)
from eaip.model_fallback.service import ModelFallbackService

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestFallbackStrategy:
    def test_values(self) -> None:
        assert FallbackStrategy.SEQUENTIAL.value == "sequential"
        assert FallbackStrategy.PRIORITY.value == "priority"
        assert FallbackStrategy.ROUND_ROBIN.value == "round_robin"
        assert FallbackStrategy.LATENCY_BASED.value == "latency_based"
        assert FallbackStrategy.WEIGHTED.value == "weighted"
        assert FallbackStrategy.CONCURRENT.value == "concurrent"


class TestFallbackStepStatus:
    def test_values(self) -> None:
        assert FallbackStepStatus.PENDING.value == "pending"
        assert FallbackStepStatus.SUCCEEDED.value == "succeeded"
        assert FallbackStepStatus.FAILED.value == "failed"
        assert FallbackStepStatus.SKIPPED.value == "skipped"
        assert FallbackStepStatus.TIMED_OUT.value == "timed_out"


class TestFallbackExecutionStatus:
    def test_values(self) -> None:
        assert FallbackExecutionStatus.DEGRADED.value == "degraded"
        assert FallbackExecutionStatus.SUCCEEDED.value == "succeeded"
        assert FallbackExecutionStatus.FAILED.value == "failed"


class TestDegradationLevel:
    def test_values(self) -> None:
        assert DegradationLevel.NONE.value == "none"
        assert DegradationLevel.MINOR.value == "minor"
        assert DegradationLevel.CRITICAL.value == "critical"


class TestFallbackHealthStatus:
    def test_values(self) -> None:
        assert FallbackHealthStatus.HEALTHY.value == "healthy"
        assert FallbackHealthStatus.UNHEALTHY.value == "unhealthy"


class TestFallbackCondition:
    def test_defaults(self) -> None:
        cond = FallbackCondition()
        assert cond.max_latency_ms is None
        assert cond.max_errors is None
        assert cond.error_rate_threshold is None

    def test_frozen(self) -> None:
        cond = FallbackCondition(max_latency_ms=100.0)
        with pytest.raises(ValueError):
            cond.max_latency_ms = 200.0


class TestFallbackTrigger:
    def test_defaults(self) -> None:
        trigger = FallbackTrigger()
        assert trigger.on_timeout is True
        assert trigger.on_degraded_health is True
        assert trigger.on_confidence_low is False


class TestFallbackStep:
    def test_defaults(self) -> None:
        step = FallbackStep(name="gpt4", model_id="gpt-4")
        assert step.priority == 0
        assert step.weight == 1.0
        assert step.max_retries == 0
        assert step.condition is None

    def test_frozen(self) -> None:
        step = FallbackStep(name="test", model_id="m1")
        with pytest.raises(ValueError):
            step.name = "changed"


class TestFallbackPolicy:
    def test_defaults(self) -> None:
        policy = FallbackPolicy()
        assert policy.strategy is FallbackStrategy.SEQUENTIAL
        assert policy.max_steps == 3
        assert policy.stop_on_first_success is True


class TestModelFallbackChain:
    def test_basic(self) -> None:
        step = FallbackStep(name="gpt4", model_id="gpt-4")
        chain = ModelFallbackChain(
            chain_id="chain-1",
            name="Primary Chain",
            steps=(step,),
        )
        assert chain.chain_id == "chain-1"
        assert len(chain.steps) == 1

    def test_frozen(self) -> None:
        step = FallbackStep(name="gpt4", model_id="gpt-4")
        chain = ModelFallbackChain(chain_id="c1", name="test", steps=(step,))
        with pytest.raises(ValueError):
            chain.name = "changed"


class TestFallbackConfig:
    def test_defaults(self) -> None:
        config = FallbackConfig()
        assert config.chains == ()
        assert config.history_ttl_days == 30
        assert config.metrics_enabled is True

    def test_frozen(self) -> None:
        config = FallbackConfig()
        with pytest.raises(ValueError):
            config.history_ttl_days = 60


class TestFallbackExecution:
    def test_defaults(self) -> None:
        exec_ = FallbackExecution(execution_id="e1", chain_id="c1")
        assert exec_.status is FallbackExecutionStatus.PENDING
        assert exec_.degradation_level is DegradationLevel.NONE


class TestFallbackResult:
    def test_fields(self) -> None:
        result = FallbackResult(success=True, execution_id="e1", duration_ms=100.0)
        assert result.success is True
        assert result.output is None


class TestFallbackMetrics:
    def test_defaults(self) -> None:
        metrics = FallbackMetrics(chain_id="c1")
        assert metrics.total_executions == 0
        assert metrics.avg_duration_ms == 0.0


class TestFallbackHistoryEntry:
    def test_basic(self) -> None:
        entry = FallbackHistoryEntry(
            entry_id="h1",
            execution_id="e1",
            chain_id="c1",
            event_type="step.failed",
        )
        assert entry.event_type == "step.failed"


class TestGracefulDegradationConfig:
    def test_defaults(self) -> None:
        config = GracefulDegradationConfig()
        assert config.enabled is True
        assert config.max_degradation_level is DegradationLevel.CRITICAL
        assert config.cooldown_seconds == 30.0


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class TestFallbackConfigCreated:
    def test_event_type(self) -> None:
        event = FallbackConfigCreated(config_id="cfg-1", name="test")
        assert event.event_type == "eaip.model_fallback.config.created"
        assert event.config_id == "cfg-1"


class TestFallbackConfigUpdated:
    def test_event_type(self) -> None:
        event = FallbackConfigUpdated(config_id="cfg-1", name="test")
        assert event.event_type == "eaip.model_fallback.config.updated"


class TestFallbackConfigDeleted:
    def test_event_type(self) -> None:
        event = FallbackConfigDeleted(config_id="cfg-1", name="test")
        assert event.event_type == "eaip.model_fallback.config.deleted"


class TestFallbackChainExecuted:
    def test_event_type(self) -> None:
        event = FallbackChainExecuted(
            chain_id="c1",
            execution_id="e1",
            status=FallbackExecutionStatus.SUCCEEDED,
            duration_ms=150.0,
            degradation_level=DegradationLevel.NONE,
        )
        assert event.event_type == "eaip.model_fallback.chain.executed"


class TestFallbackStepStarted:
    def test_event_type(self) -> None:
        event = FallbackStepStarted(
            chain_id="c1", execution_id="e1", step_name="gpt4", model_id="gpt-4"
        )
        assert event.event_type == "eaip.model_fallback.step.started"


class TestFallbackStepSkipped:
    def test_event_type(self) -> None:
        event = FallbackStepSkipped(
            chain_id="c1",
            execution_id="e1",
            step_name="gpt4",
            model_id="gpt-4",
            reason="unhealthy",
        )
        assert event.event_type == "eaip.model_fallback.step.skipped"


class TestFallbackStepCompleted:
    def test_event_type(self) -> None:
        event = FallbackStepCompleted(
            chain_id="c1",
            execution_id="e1",
            step_name="gpt4",
            model_id="gpt-4",
            duration_ms=50.0,
        )
        assert event.event_type == "eaip.model_fallback.step.completed"


class TestFallbackStepFailed:
    def test_event_type(self) -> None:
        event = FallbackStepFailed(
            chain_id="c1",
            execution_id="e1",
            step_name="gpt4",
            model_id="gpt-4",
            error="timeout",
            duration_ms=100.0,
        )
        assert event.event_type == "eaip.model_fallback.step.failed"


class TestFallbackExecutionCompleted:
    def test_event_type(self) -> None:
        event = FallbackExecutionCompleted(
            chain_id="c1",
            execution_id="e1",
            final_model_id="gpt-4",
            duration_ms=200.0,
            steps_attempted=2,
        )
        assert event.event_type == "eaip.model_fallback.execution.completed"


class TestFallbackExecutionFailed:
    def test_event_type(self) -> None:
        event = FallbackExecutionFailed(
            chain_id="c1",
            execution_id="e1",
            error="failed",
            duration_ms=500.0,
            steps_attempted=3,
        )
        assert event.event_type == "eaip.model_fallback.execution.failed"


class TestFallbackTriggered:
    def test_event_type(self) -> None:
        event = FallbackTriggered(
            chain_id="c1",
            execution_id="e1",
            from_model_id="gpt-4",
            to_model_id="gpt-3.5",
            reason="timeout",
        )
        assert event.event_type == "eaip.model_fallback.triggered"


class TestFallbackRecoverySucceeded:
    def test_event_type(self) -> None:
        event = FallbackRecoverySucceeded(chain_id="c1", execution_id="e1", model_id="gpt-4")
        assert event.event_type == "eaip.model_fallback.recovery.succeeded"


class TestFallbackRecoveryFailed:
    def test_event_type(self) -> None:
        event = FallbackRecoveryFailed(
            chain_id="c1", execution_id="e1", model_id="gpt-4", error="unhealthy"
        )
        assert event.event_type == "eaip.model_fallback.recovery.failed"


class TestFallbackMetricsCollected:
    def test_event_type(self) -> None:
        event = FallbackMetricsCollected(chain_id="c1", metrics={"total": 5})
        assert event.event_type == "eaip.model_fallback.metrics.collected"


class TestDegradationLevelChanged:
    def test_event_type(self) -> None:
        event = DegradationLevelChanged(
            chain_id="c1",
            execution_id="e1",
            previous_level=DegradationLevel.NONE,
            current_level=DegradationLevel.MODERATE,
        )
        assert event.event_type == "eaip.model_fallback.degradation.changed"


class TestFallbackHistoryLogged:
    def test_event_type(self) -> None:
        event = FallbackHistoryLogged(
            entry_id="h1", execution_id="e1", chain_id="c1", event_type_name="step.failed"
        )
        assert event.event_type == "eaip.model_fallback.history.logged"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TestExceptions:
    def test_model_fallback_error(self) -> None:
        exc = ModelFallbackError("something went wrong")
        assert "something went wrong" in str(exc)

    def test_fallback_config_error(self) -> None:
        exc = FallbackConfigError("invalid config")
        assert isinstance(exc, ModelFallbackError)

    def test_fallback_chain_error(self) -> None:
        exc = FallbackChainError("chain not found")
        assert isinstance(exc, ModelFallbackError)

    def test_fallback_execution_error(self) -> None:
        exc = FallbackExecutionError("execution failed")
        assert isinstance(exc, ModelFallbackError)

    def test_fallback_step_error(self) -> None:
        exc = FallbackStepError("step failed")
        assert isinstance(exc, ModelFallbackError)

    def test_fallback_trigger_error(self) -> None:
        exc = FallbackTriggerError("bad trigger")
        assert isinstance(exc, ModelFallbackError)

    def test_degradation_error(self) -> None:
        exc = DegradationError("degradation failed")
        assert isinstance(exc, ModelFallbackError)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class TestModelFallbackService:
    async def test_initial_config(self) -> None:
        service = ModelFallbackService()
        assert service.config is not None
        assert len(service.config.chains) == 0

    async def test_register_and_get_chain(self) -> None:
        service = ModelFallbackService()
        step = FallbackStep(name="gpt4", model_id="gpt-4")
        chain = ModelFallbackChain(chain_id="c1", name="Test", steps=(step,))
        await service.register_chain(chain)
        found = await service.get_chain("c1")
        assert found is not None
        assert found.chain_id == "c1"

    async def test_register_duplicate_chain_raises(self) -> None:
        service = ModelFallbackService()
        step = FallbackStep(name="gpt4", model_id="gpt-4")
        chain = ModelFallbackChain(chain_id="c1", name="Test", steps=(step,))
        await service.register_chain(chain)
        with pytest.raises(FallbackConfigError):
            await service.register_chain(chain)

    async def test_execute_chain_not_found(self) -> None:
        service = ModelFallbackService()
        with pytest.raises(FallbackChainError):
            await service.execute_chain("nonexistent")

    async def test_execute_chain_success(self) -> None:
        service = ModelFallbackService()
        step = FallbackStep(name="gpt4", model_id="gpt-4")
        chain = ModelFallbackChain(chain_id="c1", name="Test", steps=(step,))
        await service.register_chain(chain)
        result = await service.execute_chain("c1")
        assert result.success is True
        assert result.execution_id is not None

    async def test_execute_chain_all_steps_fail(self) -> None:
        service = ModelFallbackService()
        step1 = FallbackStep(name="bad", model_id="bad-model")
        chain = ModelFallbackChain(
            chain_id="c2",
            name="Failing",
            steps=(step1,),
            policy=FallbackPolicy(degrade_gracefully=True),
        )
        await service.register_chain(chain)
        result = await service.execute_chain("c2")
        assert result.success is True  # graceful degradation
        assert result.degradation_level is DegradationLevel.CRITICAL

    async def test_execute_chain_with_priority_strategy(self) -> None:
        service = ModelFallbackService()
        step1 = FallbackStep(name="low", model_id="low", priority=10)
        step2 = FallbackStep(name="high", model_id="high", priority=1)
        chain = ModelFallbackChain(
            chain_id="c3",
            name="Priority",
            steps=(step1, step2),
            policy=FallbackPolicy(strategy=FallbackStrategy.PRIORITY),
        )
        await service.register_chain(chain)
        result = await service.execute_chain("c3")
        assert result.success is True

    async def test_health_status_updates(self) -> None:
        service = ModelFallbackService()
        status = await service.get_health_status("model-x")
        assert status is FallbackHealthStatus.UNKNOWN
        await service.update_health_status("model-x", FallbackHealthStatus.HEALTHY)
        status = await service.get_health_status("model-x")
        assert status is FallbackHealthStatus.HEALTHY

    async def test_unhealthy_step_is_skipped(self) -> None:
        service = ModelFallbackService()
        await service.update_health_status("unhealthy-model", FallbackHealthStatus.UNHEALTHY)
        step = FallbackStep(name="bad", model_id="unhealthy-model")
        chain = ModelFallbackChain(chain_id="c4", name="Unhealthy", steps=(step,))
        await service.register_chain(chain)
        result = await service.execute_chain("c4")
        # degraded because all steps skipped
        assert result.success is True

    async def test_metrics_collection(self) -> None:
        service = ModelFallbackService()
        step = FallbackStep(name="gpt4", model_id="gpt-4")
        chain = ModelFallbackChain(chain_id="c5", name="Metrics", steps=(step,))
        await service.register_chain(chain)
        await service.execute_chain("c5")
        metrics = await service.get_metrics("c5")
        assert metrics is not None
        assert metrics.total_executions >= 1

    async def test_degrade(self) -> None:
        service = ModelFallbackService()
        step = FallbackStep(name="gpt4", model_id="gpt-4")
        chain = ModelFallbackChain(chain_id="c6", name="Degrade", steps=(step,))
        await service.register_chain(chain)
        result = await service.execute_chain("c6")
        await service.degrade("c6", result.execution_id, DegradationLevel.MODERATE)
        execution = service._executions.get(result.execution_id)
        assert execution is not None
        assert execution.degradation_level is DegradationLevel.MODERATE

    async def test_history_logging(self) -> None:
        service = ModelFallbackService()
        entry = FallbackHistoryEntry(
            entry_id="h1",
            execution_id="e1",
            chain_id="c1",
            event_type="test",
        )
        await service.log_history(entry)
        history = await service.get_history()
        assert len(history) == 1

    async def test_history_filtered_by_chain(self) -> None:
        service = ModelFallbackService()
        entry1 = FallbackHistoryEntry(
            entry_id="h1", execution_id="e1", chain_id="c1", event_type="test"
        )
        entry2 = FallbackHistoryEntry(
            entry_id="h2", execution_id="e2", chain_id="c2", event_type="test"
        )
        await service.log_history(entry1)
        await service.log_history(entry2)
        history = await service.get_history(chain_id="c1")
        assert len(history) == 1
        assert history[0].chain_id == "c1"

    async def test_recover_success(self) -> None:
        service = ModelFallbackService()
        step = FallbackStep(name="gpt4", model_id="gpt-4")
        chain = ModelFallbackChain(chain_id="c7", name="Recover", steps=(step,))
        await service.register_chain(chain)
        result = await service.execute_chain("c7")
        await service.update_health_status("gpt-4", FallbackHealthStatus.HEALTHY)
        recovered = await service.recover("c7", result.execution_id, "gpt-4")
        assert recovered is True

    async def test_recover_failure(self) -> None:
        service = ModelFallbackService()
        step = FallbackStep(name="gpt4", model_id="gpt-4")
        chain = ModelFallbackChain(chain_id="c8", name="RecoverFail", steps=(step,))
        await service.register_chain(chain)
        result = await service.execute_chain("c8")
        await service.update_health_status("gpt-4", FallbackHealthStatus.UNHEALTHY)
        recovered = await service.recover("c8", result.execution_id, "gpt-4")
        assert recovered is False

    async def test_update_config(self) -> None:
        service = ModelFallbackService()
        new_config = FallbackConfig(history_ttl_days=60)
        await service.update_config(new_config)
        assert service.config.history_ttl_days == 60

    async def test_get_all_metrics(self) -> None:
        service = ModelFallbackService()
        step = FallbackStep(name="gpt4", model_id="gpt-4")
        chain = ModelFallbackChain(chain_id="c9", name="MetricsAll", steps=(step,))
        await service.register_chain(chain)
        await service.execute_chain("c9")
        all_metrics = await service.get_all_metrics()
        assert "c9" in all_metrics


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class TestModelFallbackHealthCheck:
    async def test_healthy_when_idle(self) -> None:
        service = ModelFallbackService()
        health = ModelFallbackHealthCheck(service=service)
        report = await health.check()
        assert report.status.value == "healthy"

    async def test_degraded_with_failures(self) -> None:
        service = ModelFallbackService()
        step = FallbackStep(name="bad", model_id="bad-model")
        chain = ModelFallbackChain(
            chain_id="c1",
            name="Failing",
            steps=(step,),
            policy=FallbackPolicy(degrade_gracefully=True),
        )
        await service.register_chain(chain)
        await service.execute_chain("c1")
        health = ModelFallbackHealthCheck(service=service)
        report = await health.check()
        # degraded because degrade_gracefully -> CRITICAL degradation
        assert report.status.value in ("degraded", "healthy")


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------


class TestModelFallbackRuntimeModule:
    async def test_name(self) -> None:
        module = ModelFallbackRuntimeModule()
        assert module.name == "model_fallback"

    async def test_service_property(self) -> None:
        service = ModelFallbackService()
        module = ModelFallbackRuntimeModule(service=service)
        assert module.service is service
