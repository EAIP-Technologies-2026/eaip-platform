"""RetryOrchestrationService — manage retry policies, execute retries, circuit breaker."""

from __future__ import annotations

import random
from typing import Any
from uuid import uuid4

from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
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
    RetryExecutionError,
    RetryExhaustedError,
    RetryPolicyNotFoundError,
)
from eaip.retry_orchestration.models import (
    BackoffStrategy,
    CircuitBreakerState,
    RetryExecution,
    RetryMetrics,
    RetryOrchestrationConfig,
    RetryPolicy,
    RetryResult,
    RetryState,
    RetryStateStatus,
)
from eaip.shared.time import utc_now


class RetryOrchestrationService:
    """Central service for managing retry policies and executing retries with circuit breaker."""

    def __init__(
        self,
        config: RetryOrchestrationConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._config = config or RetryOrchestrationConfig()
        self._event_bus = event_bus
        self._log = get_logger("eaip.retry_orchestration.service")
        self._policies: dict[str, RetryPolicy] = {}
        self._executions: dict[str, RetryExecution] = {}
        self._circuit_breakers: dict[str, CircuitBreakerState] = {}
        self._metrics: dict[str, RetryMetrics] = {}

    @property
    def config(self) -> RetryOrchestrationConfig:
        return self._config

    @property
    def policies(self) -> dict[str, RetryPolicy]:
        return dict(self._policies)

    @property
    def executions(self) -> dict[str, RetryExecution]:
        return dict(self._executions)

    # ---- Policy management ----

    async def create_policy(self, policy: RetryPolicy) -> RetryPolicy:
        """Create a new retry policy."""
        if policy.id in self._policies:
            raise RetryConfigError(f"retry policy already exists: {policy.id!r}")
        self._validate_policy(policy)
        self._policies[policy.id] = policy
        if self._config.enable_circuit_breaker:
            self._circuit_breakers[policy.id] = CircuitBreakerState(
                policy_id=policy.id,
            )
        event = RetryPolicyCreated(policy=policy)
        await self._emit(event)
        self._log.info("retry_orchestration.policy.created", policy_id=policy.id)
        return policy

    async def update_policy(self, policy: RetryPolicy) -> RetryPolicy:
        """Update an existing retry policy."""
        if policy.id not in self._policies:
            raise RetryPolicyNotFoundError(policy.id)
        self._validate_policy(policy)
        self._policies[policy.id] = policy
        event = RetryPolicyUpdated(policy=policy)
        await self._emit(event)
        self._log.info("retry_orchestration.policy.updated", policy_id=policy.id)
        return policy

    async def delete_policy(self, policy_id: str) -> None:
        """Delete a retry policy."""
        policy = self._policies.get(policy_id)
        if policy is None:
            raise RetryPolicyNotFoundError(policy_id)
        del self._policies[policy_id]
        self._circuit_breakers.pop(policy_id, None)
        self._metrics.pop(policy_id, None)
        event = RetryPolicyDeleted(policy_id=policy_id, policy_name=policy.name)
        await self._emit(event)
        self._log.info("retry_orchestration.policy.deleted", policy_id=policy_id)

    async def get_policy(self, policy_id: str) -> RetryPolicy:
        """Retrieve a retry policy by ID."""
        policy = self._policies.get(policy_id)
        if policy is None:
            raise RetryPolicyNotFoundError(policy_id)
        return policy

    async def list_policies(self) -> list[RetryPolicy]:
        """List all retry policies."""
        return list(self._policies.values())

    # ---- Execution ----

    async def execute(
        self,
        policy_id: str,
        target: str,
        metadata: dict[str, Any] | None = None,
        correlation_id: str = "",
    ) -> RetryResult:
        """Execute a retry operation against a target using the given policy."""
        policy = await self.get_policy(policy_id)

        await self._check_circuit_breaker(policy_id)

        execution = RetryExecution(
            id=f"retry_{uuid4().hex[:12]}",
            policy_id=policy_id,
            target=target,
            max_attempts=policy.max_attempts,
            metadata=metadata or {},
        )
        self._executions[execution.id] = execution

        event = RetryExecutionStarted(execution=execution)
        await self._emit(event)

        return await self._execute_with_retry(policy, execution, correlation_id)

    async def _execute_with_retry(
        self,
        policy: RetryPolicy,
        execution: RetryExecution,
        _correlation_id: str = "",
    ) -> RetryResult:
        """Execute the retry loop for a given policy and execution."""
        start = utc_now()
        last_error = ""
        attempt_states: list[RetryState] = []

        for attempt in range(1, policy.max_attempts + 1):
            await self._check_circuit_breaker(policy.id)

            delay = self._compute_delay(policy, attempt)
            state = RetryState(
                policy_id=policy.id,
                execution_id=execution.id,
                attempt=attempt,
                status=RetryStateStatus.RUNNING,
                delay_seconds=delay,
                started_at=utc_now(),
            )

            attempt_event = RetryAttemptStarted(
                execution_id=execution.id,
                policy_id=policy.id,
                attempt=attempt,
                state=state,
            )
            await self._emit(attempt_event)

            if attempt > 1:
                scheduled_event = RetryAttemptScheduled(
                    execution_id=execution.id,
                    policy_id=policy.id,
                    attempt=attempt,
                    delay_seconds=delay,
                    scheduled_at=utc_now().isoformat(),
                )
                await self._emit(scheduled_event)

            try:
                result = await self._invoke_target(policy, execution.target, attempt)
                duration = (utc_now() - start).total_seconds() * 1000.0

                completed_state = RetryState(
                    policy_id=state.policy_id,
                    execution_id=state.execution_id,
                    attempt=state.attempt,
                    status=RetryStateStatus.COMPLETED,
                    delay_seconds=state.delay_seconds,
                    started_at=state.started_at,
                    completed_at=utc_now(),
                    last_error="",
                )
                attempt_states.append(completed_state)

                completed_event = RetryAttemptCompleted(
                    execution_id=execution.id,
                    policy_id=policy.id,
                    attempt=attempt,
                    duration_ms=duration,
                    result=result,
                )
                await self._emit(completed_event)

                await self._record_success(policy.id)

                completed_execution = RetryExecution(
                    id=execution.id,
                    policy_id=execution.policy_id,
                    target=execution.target,
                    attempt=attempt,
                    max_attempts=execution.max_attempts,
                    status=RetryStateStatus.COMPLETED,
                    started_at=execution.started_at,
                    completed_at=utc_now(),
                    duration_ms=duration,
                    result=result,
                    attempts=tuple(attempt_states),
                    metadata=execution.metadata,
                )
                self._executions[execution.id] = completed_execution

                completion_event = RetryExecutionCompleted(
                    execution=completed_execution,
                    result=result,
                )
                await self._emit(completion_event)

                return RetryResult(
                    execution_id=execution.id,
                    policy_id=policy.id,
                    target=execution.target,
                    success=True,
                    attempt=attempt,
                    total_attempts=attempt,
                    result=result,
                    duration_ms=duration,
                )

            except CircuitBreakerOpenError:
                raise

            except Exception as exc:
                last_error = str(exc)
                duration = (utc_now() - start).total_seconds() * 1000.0
                will_retry = attempt < policy.max_attempts

                failed_state = RetryState(
                    policy_id=state.policy_id,
                    execution_id=state.execution_id,
                    attempt=state.attempt,
                    status=RetryStateStatus.FAILED,
                    delay_seconds=state.delay_seconds,
                    started_at=state.started_at,
                    completed_at=utc_now(),
                    last_error=last_error,
                )
                attempt_states.append(failed_state)

                failed_event = RetryAttemptFailed(
                    execution_id=execution.id,
                    policy_id=policy.id,
                    attempt=attempt,
                    error=last_error,
                    will_retry=will_retry,
                    delay_seconds=delay,
                )
                await self._emit(failed_event)

                await self._record_failure(policy.id)

                if not will_retry:
                    exhausted_event = RetryExhausted(
                        execution_id=execution.id,
                        policy_id=policy.id,
                        target=execution.target,
                        total_attempts=attempt,
                        last_error=last_error,
                    )
                    await self._emit(exhausted_event)

                    failed_execution = RetryExecution(
                        id=execution.id,
                        policy_id=execution.policy_id,
                        target=execution.target,
                        attempt=attempt,
                        max_attempts=execution.max_attempts,
                        status=RetryStateStatus.EXHAUSTED,
                        started_at=execution.started_at,
                        completed_at=utc_now(),
                        duration_ms=duration,
                        last_error=last_error,
                        attempts=tuple(attempt_states),
                        metadata=execution.metadata,
                    )
                    self._executions[execution.id] = failed_execution

                    failed_exec_event = RetryExecutionFailed(
                        execution=failed_execution,
                        error=last_error,
                    )
                    await self._emit(failed_exec_event)

                    raise RetryExhaustedError(
                        policy.id,
                        attempt,
                        last_error,
                    ) from exc

        raise RetryExhaustedError(
            policy.id,
            policy.max_attempts,
            last_error,
        )

    async def get_execution(self, execution_id: str) -> RetryExecution:
        """Retrieve a retry execution by ID."""
        execution = self._executions.get(execution_id)
        if execution is None:
            raise RetryExecutionError(execution_id, "execution not found")
        return execution

    async def list_executions(self) -> list[RetryExecution]:
        """List all retry executions."""
        return list(self._executions.values())

    # ---- Circuit breaker ----

    async def get_circuit_breaker_state(self, policy_id: str) -> CircuitBreakerState:
        """Get the current circuit breaker state for a policy."""
        state = self._circuit_breakers.get(policy_id)
        if state is None:
            raise CircuitBreakerConfigError(
                f"circuit breaker not configured for policy {policy_id!r}"
            )
        return state

    async def reset_circuit_breaker(self, policy_id: str) -> CircuitBreakerState:
        """Manually reset the circuit breaker for a policy."""
        state = self._circuit_breakers.get(policy_id)
        if state is None:
            raise CircuitBreakerConfigError(
                f"circuit breaker not configured for policy {policy_id!r}"
            )
        new_state = CircuitBreakerState(
            policy_id=policy_id,
            config=state.config,
        )
        self._circuit_breakers[policy_id] = new_state
        event = CircuitBreakerReset(policy_id=policy_id, success_count=0)
        await self._emit(event)
        return new_state

    # ---- Metrics ----

    async def get_metrics(self, policy_id: str) -> RetryMetrics:
        """Get retry metrics for a policy."""
        metrics = self._metrics.get(policy_id)
        if metrics is None:
            return RetryMetrics(policy_id=policy_id)
        return metrics

    async def collect_metrics(self) -> dict[str, RetryMetrics]:
        """Collect and emit metrics for all policies."""
        collected: dict[str, RetryMetrics] = {}
        for policy_id in self._policies:
            metrics = await self.get_metrics(policy_id)
            collected[policy_id] = metrics
            event = RetryMetricsCollected(metrics=metrics)
            await self._emit(event)
        return collected

    # ---- Internal helpers ----

    def _validate_policy(self, policy: RetryPolicy) -> None:
        if policy.max_attempts < 1:
            raise RetryConfigError("max_attempts must be >= 1")
        if policy.delay_seconds < 0:
            raise RetryConfigError("delay_seconds must be >= 0")
        if policy.backoff_multiplier < 1.0:
            raise RetryConfigError("backoff_multiplier must be >= 1.0")
        if policy.max_delay_seconds < policy.delay_seconds:
            raise RetryConfigError("max_delay_seconds must be >= delay_seconds")

    def _compute_delay(self, policy: RetryPolicy, attempt: int) -> float:
        if attempt <= 1:
            return 0.0
        base_delay = policy.delay_seconds
        delay = base_delay
        strategy = BackoffStrategy(policy.strategy.value)

        if strategy is BackoffStrategy.FIXED:
            delay = base_delay
        elif strategy is BackoffStrategy.EXPONENTIAL:
            delay = base_delay * (policy.backoff_multiplier ** (attempt - 2))
        elif strategy is BackoffStrategy.LINEAR:
            delay = base_delay + (policy.backoff_multiplier * (attempt - 2))
        elif strategy is BackoffStrategy.JITTER:
            delay = base_delay * (policy.backoff_multiplier ** (attempt - 2))
            delay = delay * (1.0 + policy.jitter * (random.random() * 2.0 - 1.0))  # noqa: S311
        elif strategy is BackoffStrategy.DECORRELATED_JITTER:
            delay = base_delay * (policy.backoff_multiplier ** (attempt - 2))
            delay = delay + random.random() * policy.jitter * delay  # noqa: S311

        return min(delay, policy.max_delay_seconds)

    async def _invoke_target(
        self,
        _policy: RetryPolicy,
        _target: str,
        _attempt: int,
    ) -> str:
        """Invoke the target function.

        Subclasses should override this to provide actual invocation logic.
        """
        return ""

    async def _check_circuit_breaker(self, policy_id: str) -> None:
        if not self._config.enable_circuit_breaker:
            return
        cb_state = self._circuit_breakers.get(policy_id)
        if cb_state is None:
            return

        if cb_state.state == "open":
            now = utc_now()
            if cb_state.opened_at is not None:
                elapsed = (now - cb_state.opened_at).total_seconds()
                if elapsed >= cb_state.config.open_timeout_seconds:
                    new_state = CircuitBreakerState(
                        policy_id=cb_state.policy_id,
                        state="half_open",
                        failure_count=cb_state.failure_count,
                        success_count=cb_state.success_count,
                        last_failure_at=cb_state.last_failure_at,
                        last_success_at=cb_state.last_success_at,
                        opened_at=cb_state.opened_at,
                        half_opened_at=now,
                        config=cb_state.config,
                        metadata=cb_state.metadata,
                    )
                    self._circuit_breakers[policy_id] = new_state
                    event = CircuitBreakerHalfOpened(
                        policy_id=policy_id,
                        open_duration_seconds=elapsed,
                    )
                    await self._emit(event)
                    return
            raise CircuitBreakerOpenError(policy_id)

        if cb_state.state == "half_open" and cb_state.half_opened_at is not None:
            pass

    async def _record_success(self, policy_id: str) -> None:
        if not self._config.enable_circuit_breaker:
            return
        cb_state = self._circuit_breakers.get(policy_id)
        if cb_state is None:
            return

        new_success = cb_state.success_count + 1
        new_failure = 0 if cb_state.state == "half_open" else cb_state.failure_count

        new_state: CircuitBreakerState
        if new_success >= cb_state.config.success_threshold and cb_state.state == "half_open":
            new_state = CircuitBreakerState(
                policy_id=policy_id,
                state="closed",
                config=cb_state.config,
                last_success_at=utc_now(),
            )
            self._circuit_breakers[policy_id] = new_state
            event = CircuitBreakerReset(policy_id=policy_id, success_count=new_success)
            await self._emit(event)
        else:
            new_state = CircuitBreakerState(
                policy_id=cb_state.policy_id,
                state="half_open" if cb_state.state == "half_open" else "closed",
                failure_count=new_failure,
                success_count=new_success,
                last_failure_at=cb_state.last_failure_at,
                last_success_at=utc_now(),
                opened_at=cb_state.opened_at,
                half_opened_at=cb_state.half_opened_at,
                config=cb_state.config,
                metadata=cb_state.metadata,
            )
            self._circuit_breakers[policy_id] = new_state

        self._update_metrics(policy_id, success=True)

    async def _record_failure(self, policy_id: str) -> None:
        if not self._config.enable_circuit_breaker:
            return
        cb_state = self._circuit_breakers.get(policy_id)
        if cb_state is None:
            return

        if cb_state.state == "half_open":
            new_state = CircuitBreakerState(
                policy_id=cb_state.policy_id,
                state="open",
                failure_count=cb_state.failure_count + 1,
                success_count=cb_state.success_count,
                last_failure_at=utc_now(),
                last_success_at=cb_state.last_success_at,
                opened_at=utc_now(),
                half_opened_at=None,
                config=cb_state.config,
                metadata=cb_state.metadata,
            )
            self._circuit_breakers[policy_id] = new_state
            event = CircuitBreakerTripped(
                policy_id=policy_id,
                failure_count=new_state.failure_count,
                threshold=cb_state.config.failure_threshold,
                opened_at=utc_now().isoformat(),
            )
            await self._emit(event)
        elif cb_state.state == "closed":
            new_failure = cb_state.failure_count + 1
            if new_failure >= cb_state.config.failure_threshold:
                new_state = CircuitBreakerState(
                    policy_id=cb_state.policy_id,
                    state="open",
                    failure_count=new_failure,
                    success_count=0,
                    last_failure_at=utc_now(),
                    last_success_at=cb_state.last_success_at,
                    opened_at=utc_now(),
                    half_opened_at=None,
                    config=cb_state.config,
                    metadata=cb_state.metadata,
                )
                self._circuit_breakers[policy_id] = new_state
                event = CircuitBreakerTripped(
                    policy_id=policy_id,
                    failure_count=new_failure,
                    threshold=cb_state.config.failure_threshold,
                    opened_at=utc_now().isoformat(),
                )
                await self._emit(event)
            else:
                new_state = CircuitBreakerState(
                    policy_id=cb_state.policy_id,
                    state=cb_state.state,
                    failure_count=new_failure,
                    success_count=cb_state.success_count,
                    last_failure_at=utc_now(),
                    last_success_at=cb_state.last_success_at,
                    opened_at=cb_state.opened_at,
                    half_opened_at=cb_state.half_opened_at,
                    config=cb_state.config,
                    metadata=cb_state.metadata,
                )
                self._circuit_breakers[policy_id] = new_state

        self._update_metrics(policy_id, success=False)

    def _update_metrics(self, policy_id: str, success: bool) -> None:
        if not self._config.enable_metrics:
            return
        current = self._metrics.get(policy_id, RetryMetrics(policy_id=policy_id))
        self._metrics[policy_id] = RetryMetrics(
            policy_id=policy_id,
            total_attempts=current.total_attempts + 1,
            successful_attempts=current.successful_attempts + (1 if success else 0),
            failed_attempts=current.failed_attempts + (0 if success else 1),
            exhausted_count=current.exhausted_count,
            circuit_breaker_trips=current.circuit_breaker_trips,
            circuit_breaker_resets=current.circuit_breaker_resets,
            avg_duration_ms=current.avg_duration_ms,
            max_duration_ms=current.max_duration_ms,
            min_duration_ms=current.min_duration_ms,
            metadata=current.metadata,
        )

    async def _emit(self, event: Any) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)


__all__ = ["RetryOrchestrationService"]
