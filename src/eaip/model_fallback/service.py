"""ModelFallbackService — orchestrate fallback chains, track execution, collect metrics."""

from __future__ import annotations

import time
import uuid
from typing import Any

from eaip.logging.context import get_logger
from eaip.model_fallback.events import (
    DegradationLevelChanged,
    FallbackChainExecuted,
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
    FallbackChainError,
    FallbackConfigError,
    FallbackExecutionError,
)
from eaip.model_fallback.models import (
    DegradationLevel,
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
    ModelFallbackChain,
)
from eaip.shared.time import utc_now


class ModelFallbackService:
    """Central service for managing model fallback chains and execution."""

    def __init__(
        self,
        config: FallbackConfig | None = None,
        event_bus: Any = None,
    ) -> None:
        """Initialize the fallback service with an optional config and event bus."""
        self._config = config or FallbackConfig()
        self._event_bus = event_bus
        self._executions: dict[str, FallbackExecution] = {}
        self._metrics: dict[str, FallbackMetrics] = {}
        self._history: list[FallbackHistoryEntry] = []
        self._health_status: dict[str, FallbackHealthStatus] = {}
        self._log = get_logger("eaip.model_fallback.service")

    @property
    def config(self) -> FallbackConfig:
        """Return the active fallback configuration."""
        return self._config

    # ------------------------------------------------------------------
    # Config management
    # ------------------------------------------------------------------

    async def update_config(self, config: FallbackConfig) -> None:
        """Replace the active fallback configuration."""
        self._config = config
        self._log.info("model_fallback.config.updated")

    async def get_chain(self, chain_id: str) -> ModelFallbackChain | None:
        """Look up a fallback chain by ID."""
        for chain in self._config.chains:
            if chain.chain_id == chain_id:
                return chain
        return None

    async def register_chain(self, chain: ModelFallbackChain) -> None:
        """Register a new fallback chain."""
        if any(c.chain_id == chain.chain_id for c in self._config.chains):
            raise FallbackConfigError(f"Chain '{chain.chain_id}' already registered", code=None)
        new_chains = (*self._config.chains, chain)
        await self.update_config(self._config.model_copy(update={"chains": new_chains}))
        self._log.info("model_fallback.chain.registered", chain_id=chain.chain_id)

    # ------------------------------------------------------------------
    # Chain execution
    # ------------------------------------------------------------------

    async def execute_chain(
        self,
        chain_id: str,
        override_policy: FallbackPolicy | None = None,
    ) -> FallbackResult:
        """Execute a fallback chain against the given input."""
        chain = await self.get_chain(chain_id)
        if chain is None:
            raise FallbackChainError(f"Chain '{chain_id}' not found", code=None)

        execution_id = str(uuid.uuid4())
        policy = override_policy or chain.policy
        execution = FallbackExecution(
            execution_id=execution_id,
            chain_id=chain_id,
            status=FallbackExecutionStatus.RUNNING,
            started_at=utc_now(),
        )
        self._executions[execution_id] = execution

        t0 = time.monotonic()
        steps = list(chain.steps)
        attempted = 0
        succeeded = 0
        failed = 0
        final_model_id: str | None = None
        final_output: object | None = None
        degradation = DegradationLevel.NONE
        last_error: str | None = None
        steps_to_try = self._resolve_steps(steps, policy)

        for step in steps_to_try:
            if attempted >= policy.max_steps:
                break

            attempted += 1
            step_status = await self._execute_step(step, execution_id, chain_id, t0)

            if step_status == FallbackStepStatus.SUCCEEDED:
                succeeded += 1
                final_model_id = step.model_id
                if policy.stop_on_first_success:
                    break
            elif step_status == FallbackStepStatus.SKIPPED:
                continue
            else:
                failed += 1
                last_error = f"Step '{step.name}' failed"

        elapsed = (time.monotonic() - t0) * 1000

        exec_status, degradation = self._resolve_execution_status(
            final_model_id,
            succeeded,
            attempted,
            policy,
        )

        completed_execution = execution.model_copy(
            update={
                "status": exec_status,
                "completed_at": utc_now(),
                "total_duration_ms": elapsed,
                "steps_attempted": attempted,
                "steps_succeeded": succeeded,
                "steps_failed": failed,
                "final_model_id": final_model_id,
                "degradation_level": degradation,
                "error": last_error,
            }
        )
        self._executions[execution_id] = completed_execution

        await self._emit_event(
            FallbackChainExecuted(
                chain_id=chain_id,
                execution_id=execution_id,
                status=exec_status,
                duration_ms=elapsed,
                degradation_level=degradation,
            )
        )

        if exec_status is FallbackExecutionStatus.SUCCEEDED:
            await self._emit_event(
                FallbackExecutionCompleted(
                    chain_id=chain_id,
                    execution_id=execution_id,
                    final_model_id=final_model_id,
                    duration_ms=elapsed,
                    steps_attempted=attempted,
                )
            )
        else:
            await self._emit_event(
                FallbackExecutionFailed(
                    chain_id=chain_id,
                    execution_id=execution_id,
                    error=last_error or "All fallback steps exhausted",
                    duration_ms=elapsed,
                    steps_attempted=attempted,
                )
            )

        await self._collect_metrics(chain_id)

        success = exec_status in (
            FallbackExecutionStatus.SUCCEEDED,
            FallbackExecutionStatus.DEGRADED,
        )
        return FallbackResult(
            success=success,
            output=final_output,
            model_id=final_model_id,
            execution_id=execution_id,
            duration_ms=elapsed,
            degradation_level=degradation,
            error=last_error,
        )

    def _resolve_execution_status(
        self,
        final_model_id: str | None,
        succeeded: int,
        attempted: int,
        policy: FallbackPolicy,
    ) -> tuple[FallbackExecutionStatus, DegradationLevel]:
        """Determine execution status and degradation level after chain run."""
        if final_model_id is not None:
            if succeeded == 0 and attempted > 1:
                return FallbackExecutionStatus.DEGRADED, DegradationLevel.MODERATE
            return FallbackExecutionStatus.SUCCEEDED, DegradationLevel.NONE
        if policy.degrade_gracefully:
            return FallbackExecutionStatus.DEGRADED, DegradationLevel.CRITICAL
        return FallbackExecutionStatus.FAILED, DegradationLevel.NONE

    def _resolve_steps(
        self,
        steps: list[FallbackStep],
        policy: FallbackPolicy,
    ) -> list[FallbackStep]:
        """Resolve step order based on the configured strategy."""
        if policy.strategy is FallbackStrategy.PRIORITY:
            return sorted(steps, key=lambda s: s.priority)
        if policy.strategy is FallbackStrategy.WEIGHTED:
            return sorted(steps, key=lambda s: s.weight, reverse=True)
        if policy.strategy is FallbackStrategy.ROUND_ROBIN:
            return steps
        if policy.strategy is FallbackStrategy.CONCURRENT:
            return steps
        return steps

    async def _execute_step(
        self,
        step: FallbackStep,
        execution_id: str,
        chain_id: str,
        start_monotonic: float,
    ) -> FallbackStepStatus:
        """Execute (or skip) a single fallback step."""
        health = self._health_status.get(step.model_id, FallbackHealthStatus.UNKNOWN)
        if health is FallbackHealthStatus.UNHEALTHY:
            await self._emit_event(
                FallbackStepSkipped(
                    chain_id=chain_id,
                    execution_id=execution_id,
                    step_name=step.name,
                    model_id=step.model_id,
                    reason="Model health is UNHEALTHY",
                )
            )
            return FallbackStepStatus.SKIPPED

        await self._emit_event(
            FallbackStepStarted(
                chain_id=chain_id,
                execution_id=execution_id,
                step_name=step.name,
                model_id=step.model_id,
            )
        )

        step_t0 = time.monotonic()
        try:
            if step.timeout_ms is not None:
                elapsed_so_far = (time.monotonic() - start_monotonic) * 1000
                if elapsed_so_far > step.timeout_ms:
                    raise TimeoutError(f"Step '{step.name}' timed out")

            self._log.info(
                "model_fallback.step.executing",
                step=step.name,
                model=step.model_id,
            )

            step_duration = (time.monotonic() - step_t0) * 1000
            await self._emit_event(
                FallbackStepCompleted(
                    chain_id=chain_id,
                    execution_id=execution_id,
                    step_name=step.name,
                    model_id=step.model_id,
                    duration_ms=step_duration,
                )
            )
            return FallbackStepStatus.SUCCEEDED

        except Exception as exc:
            step_duration = (time.monotonic() - step_t0) * 1000
            error = str(exc)
            await self._emit_event(
                FallbackStepFailed(
                    chain_id=chain_id,
                    execution_id=execution_id,
                    step_name=step.name,
                    model_id=step.model_id,
                    error=error,
                    duration_ms=step_duration,
                )
            )

            await self._emit_event(
                FallbackTriggered(
                    chain_id=chain_id,
                    execution_id=execution_id,
                    from_model_id=step.model_id,
                    to_model_id="next",
                    reason=error,
                )
            )
            return FallbackStepStatus.FAILED

    # ------------------------------------------------------------------
    # Health tracking
    # ------------------------------------------------------------------

    async def update_health_status(
        self,
        model_id: str,
        status: FallbackHealthStatus,
    ) -> None:
        """Update the health status of a model."""
        self._health_status[model_id] = status
        self._log.info(
            "model_fallback.health.updated",
            model_id=model_id,
            status=status.value,
        )

    async def get_health_status(self, model_id: str) -> FallbackHealthStatus:
        """Get the health status of a model."""
        return self._health_status.get(model_id, FallbackHealthStatus.UNKNOWN)

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    async def _collect_metrics(self, chain_id: str) -> None:
        """Collect and store metrics for a chain."""
        chain_executions = [
            ex
            for ex in self._executions.values()
            if ex.chain_id == chain_id and ex.total_duration_ms is not None
        ]
        if not chain_executions:
            return

        durations = [
            ex.total_duration_ms for ex in chain_executions if ex.total_duration_ms is not None
        ]
        if not durations:
            return

        p95_min = 20
        p99_min = 100
        sorted_durations = sorted(durations)
        n = len(sorted_durations)
        avg = sum(sorted_durations) / n
        p95 = sorted_durations[int(n * 0.95)] if n >= p95_min else sorted_durations[-1]
        p99 = sorted_durations[int(n * 0.99)] if n >= p99_min else sorted_durations[-1]

        metrics = FallbackMetrics(
            chain_id=chain_id,
            total_executions=n,
            successful_executions=sum(
                1 for ex in chain_executions if ex.status is FallbackExecutionStatus.SUCCEEDED
            ),
            failed_executions=sum(
                1 for ex in chain_executions if ex.status is FallbackExecutionStatus.FAILED
            ),
            degraded_executions=sum(
                1 for ex in chain_executions if ex.status is FallbackExecutionStatus.DEGRADED
            ),
            avg_duration_ms=avg,
            p95_duration_ms=p95,
            p99_duration_ms=p99,
        )
        self._metrics[chain_id] = metrics

        await self._emit_event(
            FallbackMetricsCollected(
                chain_id=chain_id,
                metrics=metrics.model_dump(),
            )
        )

    async def get_metrics(self, chain_id: str) -> FallbackMetrics | None:
        """Get collected metrics for a chain."""
        return self._metrics.get(chain_id)

    async def get_all_metrics(self) -> dict[str, FallbackMetrics]:
        """Get metrics for all chains."""
        return dict(self._metrics)

    # ------------------------------------------------------------------
    # Degradation
    # ------------------------------------------------------------------

    async def degrade(
        self,
        chain_id: str,
        execution_id: str,
        level: DegradationLevel,
    ) -> None:
        """Apply a degradation level to an execution."""
        execution = self._executions.get(execution_id)
        if execution is None:
            raise FallbackExecutionError(f"Execution '{execution_id}' not found", code=None)

        degradation_config = self._config.degradation
        if degradation_config and level.value > degradation_config.max_degradation_level.value:
            level = degradation_config.max_degradation_level

        previous = execution.degradation_level
        if previous != level:
            updated = execution.model_copy(update={"degradation_level": level})
            self._executions[execution_id] = updated

            await self._emit_event(
                DegradationLevelChanged(
                    chain_id=chain_id,
                    execution_id=execution_id,
                    previous_level=previous,
                    current_level=level,
                )
            )

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    async def log_history(self, entry: FallbackHistoryEntry) -> None:
        """Log a fallback history entry."""
        self._history.append(entry)
        await self._emit_event(
            FallbackHistoryLogged(
                entry_id=entry.entry_id,
                execution_id=entry.execution_id,
                chain_id=entry.chain_id,
                event_type_name=entry.event_type,
            )
        )

    async def get_history(
        self,
        chain_id: str | None = None,
        limit: int = 100,
    ) -> list[FallbackHistoryEntry]:
        """Retrieve fallback history, optionally filtered by chain ID."""
        entries = self._history
        if chain_id is not None:
            entries = [e for e in entries if e.chain_id == chain_id]
        return entries[-limit:]

    # ------------------------------------------------------------------
    # Recovery
    # ------------------------------------------------------------------

    async def recover(
        self,
        chain_id: str,
        execution_id: str,
        model_id: str,
    ) -> bool:
        """Attempt to recover a degraded execution by retrying a model."""
        execution = self._executions.get(execution_id)
        if execution is None:
            raise FallbackExecutionError(f"Execution '{execution_id}' not found", code=None)

        health = self._health_status.get(model_id, FallbackHealthStatus.UNKNOWN)
        if health is FallbackHealthStatus.UNHEALTHY:
            await self._emit_event(
                FallbackRecoveryFailed(
                    chain_id=chain_id,
                    execution_id=execution_id,
                    model_id=model_id,
                    error="Model is UNHEALTHY",
                )
            )
            return False

        await self._emit_event(
            FallbackRecoverySucceeded(
                chain_id=chain_id,
                execution_id=execution_id,
                model_id=model_id,
            )
        )
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _emit_event(self, event: object) -> None:
        """Publish an event if an event bus is available."""
        if self._event_bus is not None:
            try:
                await self._event_bus.publish(event)
            except Exception:
                event_type = type(event).__name__
                self._log.warning("model_fallback.event.publish.failed", event_type=event_type)


__all__ = ["ModelFallbackService"]
