from __future__ import annotations

import pydantic
import pytest

from eaip.exceptions.base import ErrorCode
from eaip.health.checks import HealthStatus
from eaip.retry_orchestration.events import (
    CircuitBreakerHalfOpened,
    CircuitBreakerReset,
    CircuitBreakerTripped,
    RetryAttemptCompleted,
    RetryAttemptFailed,
    RetryAttemptScheduled,
    RetryAttemptStarted,
    RetryExecutionCompleted,
    RetryExecutionFailed,
    RetryExecutionStarted,
    RetryExhausted,
    RetryMetricsCollected,
    RetryPolicyCreated,
    RetryPolicyDeleted,
    RetryPolicyUpdated,
)
from eaip.retry_orchestration.exceptions import (
    CircuitBreakerConfigError,
    CircuitBreakerOpenError,
    RetryConfigError,
    RetryError,
    RetryExecutionError,
    RetryExhaustedError,
    RetryOrchestrationError,
    RetryPolicyNotFoundError,
)
from eaip.retry_orchestration.health import RetryOrchestrationHealthCheck
from eaip.retry_orchestration.integration import RetryOrchestrationRuntimeModule
from eaip.retry_orchestration.models import (
    BackoffStrategy,
    CircuitBreakerConfig,
    CircuitBreakerState,
    RetryExecution,
    RetryMetrics,
    RetryOrchestrationConfig,
    RetryPolicy,
    RetryResult,
    RetryState,
    RetryStateStatus,
    RetryStrategy,
)
from eaip.retry_orchestration.service import RetryOrchestrationService


class TestModels:
    def test_retry_policy_defaults(self) -> None:
        p = RetryPolicy(id="p1", name="Default")
        assert p.max_attempts == 3
        assert p.delay_seconds == 1.0
        assert p.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert p.tags == ()

    def test_retry_policy_frozen(self) -> None:
        p = RetryPolicy(id="p1", name="Policy")
        with pytest.raises(pydantic.ValidationError):
            p.name = "Changed"

    def test_retry_policy_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            RetryPolicy(id="p1", name="P", unknown="x")  # type: ignore[call-arg]

    def test_retry_state_defaults(self) -> None:
        s = RetryState(policy_id="p1", execution_id="e1")
        assert s.attempt == 0
        assert s.status == RetryStateStatus.PENDING
        assert s.last_error == ""

    def test_retry_execution_defaults(self) -> None:
        e = RetryExecution(id="e1", policy_id="p1", target="test")
        assert e.attempt == 0
        assert e.max_attempts == 3
        assert e.status == RetryStateStatus.PENDING
        assert e.attempts == ()

    def test_retry_result_defaults(self) -> None:
        r = RetryResult(execution_id="e1", policy_id="p1", target="test")
        assert r.success is False
        assert r.exhausted is False
        assert r.circuit_broken is False

    def test_retry_metrics_defaults(self) -> None:
        m = RetryMetrics(policy_id="p1")
        assert m.total_attempts == 0
        assert m.failed_attempts == 0
        assert m.circuit_breaker_trips == 0

    def test_circuit_breaker_config_defaults(self) -> None:
        c = CircuitBreakerConfig()
        assert c.failure_threshold == 5
        assert c.open_timeout_seconds == 30.0
        assert c.half_open_max_attempts == 3

    def test_circuit_breaker_state_defaults(self) -> None:
        s = CircuitBreakerState(policy_id="p1")
        assert s.state == "closed"
        assert s.failure_count == 0
        assert s.opened_at is None

    def test_retry_orchestration_config_defaults(self) -> None:
        c = RetryOrchestrationConfig()
        assert c.max_concurrent_executions == 10
        assert c.enable_circuit_breaker is True
        assert c.enable_metrics is True

    def test_backoff_strategy_values(self) -> None:
        assert BackoffStrategy.FIXED.value == "fixed"
        assert BackoffStrategy.EXPONENTIAL.value == "exponential"
        assert BackoffStrategy.DECORRELATED_JITTER.value == "decorrelated_jitter"

    def test_retry_state_status_values(self) -> None:
        assert RetryStateStatus.EXHAUSTED.value == "exhausted"
        assert RetryStateStatus.CANCELLED.value == "cancelled"


class TestEvents:
    def test_retry_policy_created(self) -> None:
        policy = RetryPolicy(id="p1", name="Test")
        e = RetryPolicyCreated(policy=policy)
        assert e.event_type == "eaip.retry_orchestration.policy.created"
        assert e.policy.id == "p1"

    def test_retry_policy_updated(self) -> None:
        policy = RetryPolicy(id="p1", name="Updated")
        e = RetryPolicyUpdated(policy=policy)
        assert e.event_type == "eaip.retry_orchestration.policy.updated"

    def test_retry_policy_deleted(self) -> None:
        e = RetryPolicyDeleted(policy_id="p1", policy_name="Test")
        assert e.event_type == "eaip.retry_orchestration.policy.deleted"
        assert e.policy_id == "p1"

    def test_retry_execution_started(self) -> None:
        execution = RetryExecution(id="e1", policy_id="p1", target="test")
        e = RetryExecutionStarted(execution=execution)
        assert e.event_type == "eaip.retry_orchestration.execution.started"

    def test_retry_execution_completed(self) -> None:
        execution = RetryExecution(id="e1", policy_id="p1", target="test")
        e = RetryExecutionCompleted(execution=execution, result="ok")
        assert e.event_type == "eaip.retry_orchestration.execution.completed"
        assert e.result == "ok"

    def test_retry_execution_failed(self) -> None:
        execution = RetryExecution(id="e1", policy_id="p1", target="test")
        e = RetryExecutionFailed(execution=execution, error="timeout")
        assert e.event_type == "eaip.retry_orchestration.execution.failed"
        assert e.error == "timeout"

    def test_retry_attempt_scheduled(self) -> None:
        e = RetryAttemptScheduled(
            execution_id="e1",
            policy_id="p1",
            attempt=2,
            delay_seconds=2.0,
        )
        assert e.event_type == "eaip.retry_orchestration.attempt.scheduled"
        assert e.delay_seconds == 2.0

    def test_retry_attempt_started(self) -> None:
        state = RetryState(policy_id="p1", execution_id="e1", attempt=1)
        e = RetryAttemptStarted(execution_id="e1", policy_id="p1", attempt=1, state=state)
        assert e.event_type == "eaip.retry_orchestration.attempt.started"

    def test_retry_attempt_completed(self) -> None:
        e = RetryAttemptCompleted(
            execution_id="e1",
            policy_id="p1",
            attempt=1,
            duration_ms=100.0,
            result="ok",
        )
        assert e.event_type == "eaip.retry_orchestration.attempt.completed"
        assert e.duration_ms == 100.0

    def test_retry_attempt_failed(self) -> None:
        e = RetryAttemptFailed(
            execution_id="e1",
            policy_id="p1",
            attempt=1,
            error="err",
            will_retry=True,
            delay_seconds=2.0,
        )
        assert e.event_type == "eaip.retry_orchestration.attempt.failed"
        assert e.will_retry is True

    def test_retry_exhausted(self) -> None:
        e = RetryExhausted(
            execution_id="e1",
            policy_id="p1",
            target="test",
            total_attempts=3,
            last_error="timeout",
        )
        assert e.event_type == "eaip.retry_orchestration.exhausted"
        assert e.total_attempts == 3

    def test_circuit_breaker_tripped(self) -> None:
        e = CircuitBreakerTripped(
            policy_id="p1",
            failure_count=5,
            threshold=5,
            opened_at="2024-01-01T00:00:00",
        )
        assert e.event_type == "eaip.retry_orchestration.circuit_breaker.tripped"
        assert e.failure_count == 5

    def test_circuit_breaker_half_opened(self) -> None:
        e = CircuitBreakerHalfOpened(policy_id="p1", open_duration_seconds=30.0)
        assert e.event_type == "eaip.retry_orchestration.circuit_breaker.half_opened"

    def test_circuit_breaker_reset(self) -> None:
        e = CircuitBreakerReset(policy_id="p1", success_count=2)
        assert e.event_type == "eaip.retry_orchestration.circuit_breaker.reset"

    def test_retry_metrics_collected(self) -> None:
        metrics = RetryMetrics(policy_id="p1", total_attempts=10)
        e = RetryMetricsCollected(metrics=metrics)
        assert e.event_type == "eaip.retry_orchestration.metrics.collected"
        assert e.metrics.total_attempts == 10

    def test_events_frozen(self) -> None:
        policy = RetryPolicy(id="p1", name="Test")
        e = RetryPolicyCreated(policy=policy)
        with pytest.raises(pydantic.ValidationError):
            e.policy = RetryPolicy(id="p2", name="X")


class TestExceptions:
    def test_retry_orchestration_error_base(self) -> None:
        err = RetryOrchestrationError("base error")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_retry_error_base(self) -> None:
        err = RetryError("retry error")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_retry_policy_not_found(self) -> None:
        err = RetryPolicyNotFoundError("p1")
        assert err.code == ErrorCode.NOT_FOUND
        assert "p1" in str(err)

    def test_retry_execution_error(self) -> None:
        err = RetryExecutionError("e1", "something went wrong")
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert err.execution_id == "e1"

    def test_retry_exhausted_error(self) -> None:
        err = RetryExhaustedError("p1", 3, "timeout")
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert err.total_attempts == 3
        assert err.last_error == "timeout"

    def test_retry_config_error(self) -> None:
        err = RetryConfigError("invalid config")
        assert err.code == ErrorCode.VALIDATION_FAILED

    def test_circuit_breaker_open_error(self) -> None:
        err = CircuitBreakerOpenError("p1")
        assert err.code == ErrorCode.GATEWAY_ERROR
        assert err.policy_id == "p1"

    def test_circuit_breaker_config_error(self) -> None:
        err = CircuitBreakerConfigError("bad config")
        assert err.code == ErrorCode.VALIDATION_FAILED

    def test_cause_chaining(self) -> None:
        cause = ValueError("root cause")
        err = RetryOrchestrationError("msg", cause=cause)
        assert err.__cause__ is cause

    def test_to_dict(self) -> None:
        err = RetryPolicyNotFoundError("p1")
        d = err.to_dict()
        assert d["type"] == "RetryPolicyNotFoundError"
        assert d["code"] == "EAIP-0003"

    def test_inheritance(self) -> None:
        assert issubclass(RetryPolicyNotFoundError, RetryError)
        assert issubclass(RetryExecutionError, RetryError)
        assert issubclass(RetryExhaustedError, RetryError)
        assert issubclass(RetryConfigError, RetryError)
        assert issubclass(CircuitBreakerOpenError, RetryError)
        assert issubclass(CircuitBreakerConfigError, RetryError)
        assert issubclass(RetryError, RetryOrchestrationError)


class TestRetryOrchestrationService:
    @pytest.fixture
    async def service(self) -> RetryOrchestrationService:
        return RetryOrchestrationService()

    @pytest.fixture
    def sample_policy(self) -> RetryPolicy:
        return RetryPolicy(
            id="p1",
            name="Sample Policy",
            max_attempts=3,
            delay_seconds=0.1,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        )

    async def test_create_policy(
        self,
        service: RetryOrchestrationService,
        sample_policy: RetryPolicy,
    ) -> None:
        result = await service.create_policy(sample_policy)
        assert result.id == "p1"
        assert len(await service.list_policies()) == 1

    async def test_create_duplicate_raises(
        self,
        service: RetryOrchestrationService,
        sample_policy: RetryPolicy,
    ) -> None:
        await service.create_policy(sample_policy)
        with pytest.raises(RetryConfigError):
            await service.create_policy(sample_policy)

    async def test_get_policy(
        self,
        service: RetryOrchestrationService,
        sample_policy: RetryPolicy,
    ) -> None:
        await service.create_policy(sample_policy)
        retrieved = await service.get_policy("p1")
        assert retrieved.id == "p1"

    async def test_get_nonexistent_policy_raises(
        self,
        service: RetryOrchestrationService,
    ) -> None:
        with pytest.raises(RetryPolicyNotFoundError):
            await service.get_policy("nonexistent")

    async def test_update_policy(
        self,
        service: RetryOrchestrationService,
        sample_policy: RetryPolicy,
    ) -> None:
        await service.create_policy(sample_policy)
        updated = RetryPolicy(
            id="p1",
            name="Updated Policy",
            max_attempts=5,
        )
        result = await service.update_policy(updated)
        assert result.max_attempts == 5
        assert result.name == "Updated Policy"

    async def test_update_nonexistent_policy_raises(
        self,
        service: RetryOrchestrationService,
    ) -> None:
        with pytest.raises(RetryPolicyNotFoundError):
            await service.update_policy(RetryPolicy(id="nx", name="X", max_attempts=1))

    async def test_delete_policy(
        self,
        service: RetryOrchestrationService,
        sample_policy: RetryPolicy,
    ) -> None:
        await service.create_policy(sample_policy)
        await service.delete_policy("p1")
        assert len(await service.list_policies()) == 0

    async def test_delete_nonexistent_policy_raises(
        self,
        service: RetryOrchestrationService,
    ) -> None:
        with pytest.raises(RetryPolicyNotFoundError):
            await service.delete_policy("nonexistent")

    async def test_list_policies(
        self,
        service: RetryOrchestrationService,
    ) -> None:
        p1 = RetryPolicy(id="p1", name="Policy 1")
        p2 = RetryPolicy(id="p2", name="Policy 2")
        await service.create_policy(p1)
        await service.create_policy(p2)
        policies = await service.list_policies()
        assert len(policies) == 2

    async def test_execute_success(
        self,
        service: RetryOrchestrationService,
        sample_policy: RetryPolicy,
    ) -> None:
        await service.create_policy(sample_policy)
        result = await service.execute("p1", "test_target")
        assert result.success is True
        assert result.policy_id == "p1"
        assert result.target == "test_target"

    async def test_execute_nonexistent_policy_raises(
        self,
        service: RetryOrchestrationService,
    ) -> None:
        with pytest.raises(RetryPolicyNotFoundError):
            await service.execute("nonexistent", "target")

    async def test_get_execution(
        self,
        service: RetryOrchestrationService,
        sample_policy: RetryPolicy,
    ) -> None:
        await service.create_policy(sample_policy)
        result = await service.execute("p1", "target")
        execution = await service.get_execution(result.execution_id)
        assert execution.id == result.execution_id

    async def test_get_nonexistent_execution_raises(
        self,
        service: RetryOrchestrationService,
    ) -> None:
        with pytest.raises(RetryExecutionError):
            await service.get_execution("nonexistent")

    async def test_circuit_breaker_state(
        self,
        service: RetryOrchestrationService,
        sample_policy: RetryPolicy,
    ) -> None:
        await service.create_policy(sample_policy)
        state = await service.get_circuit_breaker_state("p1")
        assert state.state == "closed"
        assert state.policy_id == "p1"

    async def test_circuit_breaker_reset(
        self,
        service: RetryOrchestrationService,
        sample_policy: RetryPolicy,
    ) -> None:
        await service.create_policy(sample_policy)
        state = await service.reset_circuit_breaker("p1")
        assert state.state == "closed"

    async def test_metrics_initial(
        self,
        service: RetryOrchestrationService,
        sample_policy: RetryPolicy,
    ) -> None:
        await service.create_policy(sample_policy)
        metrics = await service.get_metrics("p1")
        assert metrics.total_attempts == 0

    async def test_metrics_after_execution(
        self,
        service: RetryOrchestrationService,
        sample_policy: RetryPolicy,
    ) -> None:
        await service.create_policy(sample_policy)
        await service.execute("p1", "target")
        metrics = await service.get_metrics("p1")
        assert metrics.total_attempts > 0
        assert metrics.successful_attempts > 0

    async def test_collect_metrics(
        self,
        service: RetryOrchestrationService,
        sample_policy: RetryPolicy,
    ) -> None:
        await service.create_policy(sample_policy)
        await service.execute("p1", "target")
        collected = await service.collect_metrics()
        assert "p1" in collected

    async def test_policy_validation_max_attempts(
        self,
        service: RetryOrchestrationService,
    ) -> None:
        with pytest.raises(RetryConfigError):
            await service.create_policy(RetryPolicy(id="bad", name="Bad", max_attempts=0))

    async def test_policy_validation_backoff_multiplier(
        self,
        service: RetryOrchestrationService,
    ) -> None:
        with pytest.raises(RetryConfigError):
            await service.create_policy(RetryPolicy(id="bad", name="Bad", backoff_multiplier=0.5))


class TestRetryOrchestrationHealthCheck:
    async def test_healthy_when_no_failures(self) -> None:
        service = RetryOrchestrationService()
        health = RetryOrchestrationHealthCheck(service=service)
        report = await health.check()
        assert report.status == HealthStatus.HEALTHY

    async def test_healthy_details(self) -> None:
        service = RetryOrchestrationService()
        health = RetryOrchestrationHealthCheck(service=service)
        report = await health.check()
        assert "policies_defined" in report.details


class TestRetryOrchestrationRuntimeModule:
    def test_name(self) -> None:
        mod = RetryOrchestrationRuntimeModule()
        assert mod.name == "retry_orchestration"

    def test_service_property(self) -> None:
        svc = RetryOrchestrationService()
        mod = RetryOrchestrationRuntimeModule(service=svc)
        assert mod.service is svc

    def test_default_service(self) -> None:
        mod = RetryOrchestrationRuntimeModule()
        assert isinstance(mod.service, RetryOrchestrationService)
