"""Agent Runtime — orchestrates agent execution with planning, tools, and memory."""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING, Any

from opentelemetry import trace
from opentelemetry.trace import SpanKind, StatusCode

from eaip.adapters.llm.models import RunContext as LLMRunContext
from eaip.agents.base import Guardrail, Planner
from eaip.agents.events import (
    RunCancelled,
    RunCompleted,
    RunFailed,
    RunStarted,
    StepCompleted,
    StepFailed,
    StepStarted,
)
from eaip.agents.exceptions import RunNotFoundError
from eaip.agents.executor import StepExecutor
from eaip.agents.guardrails import NoopGuardrail
from eaip.agents.models import (
    AgentSpec,
    Goal,
    RunRecord,
    RunStatus,
    Step,
    StepStatus,
)
from eaip.agents.planner import SimpleLLMPlanner
from eaip.health.checks import HealthReport, HealthStatus
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now

if TYPE_CHECKING:
    from eaip.adapters.llm.base import LLMAdapter
    from eaip.tools.registry import ToolRegistry


class AgentRunContext:
    """Runtime context for a single agent run.

    Provides access to the LLM adapter, tool registry, memory engine,
    event bus, and telemetry needed during run execution.
    """

    def __init__(  # noqa: D107
        self,
        *,
        llm_adapter: LLMAdapter,
        tool_registry: ToolRegistry,
        memory: Any | None = None,
        event_bus: Any | None = None,
        meter: Any | None = None,
    ) -> None:
        self._llm_adapter = llm_adapter
        self._tool_registry = tool_registry
        self._memory = memory
        self._event_bus = event_bus
        self._meter = meter

    @property
    def llm_adapter(self) -> LLMAdapter:
        """Return the LLM adapter."""
        return self._llm_adapter

    @property
    def tool_registry(self) -> ToolRegistry:
        """Return the tool registry."""
        return self._tool_registry

    @property
    def memory(self) -> Any | None:
        """Return the memory engine if available."""
        return self._memory

    @property
    def event_bus(self) -> Any | None:
        """Return the event bus if available."""
        return self._event_bus

    @property
    def meter(self) -> Any | None:
        """Return the meter if available."""
        return self._meter

    def to_run_context(self) -> LLMRunContext:
        """Convert to an LLMAdapter RunContext."""
        return LLMRunContext(
            tenant_id="",
            run_id="",
            correlation_id="",
        )


class AgentRuntime:
    """Orchestrates agent runs from creation to completion.

    Manages the full lifecycle:
    1. Create a run from a goal and agent spec.
    2. Plan the run (decompose goal into steps).
    3. Execute each step (tool calls, LLM completions).
    4. Run guardrails before/after each step.
    5. Publish events for observability.
    6. Track metrics and telemetry.
    """

    def __init__(  # noqa: D107
        self,
        *,
        llm_adapter: LLMAdapter,
        tool_registry: ToolRegistry,
        memory: Any | None = None,
        event_bus: Any | None = None,
        meter: Any | None = None,
        planner: Planner | None = None,
        guardrail: Guardrail | None = None,
        executor: StepExecutor | None = None,
    ) -> None:
        self._context = AgentRunContext(
            llm_adapter=llm_adapter,
            tool_registry=tool_registry,
            memory=memory,
            event_bus=event_bus,
            meter=meter,
        )
        self._planner = planner or SimpleLLMPlanner()
        self._guardrail = guardrail or NoopGuardrail()
        self._executor = executor or StepExecutor()
        self._runs: dict[str, RunRecord] = {}
        self._log = get_logger("eaip.agents.runtime")

    @property
    def context(self) -> AgentRunContext:
        """Return the shared agent run context."""
        return self._context

    @property
    def planner(self) -> Planner:
        """Return the configured planner."""
        return self._planner

    @property
    def guardrail(self) -> Guardrail:
        """Return the configured guardrail."""
        return self._guardrail

    # ----------------------------------------------------------------
    # Run management
    # ----------------------------------------------------------------

    async def create_run(
        self,
        agent_spec: AgentSpec,
        goal: Goal,
    ) -> RunRecord:
        """Create a new run record for the given agent and goal.

        Args:
            agent_spec: The agent specification.
            goal: The goal to accomplish.

        Returns:
            A pending RunRecord.
        """
        run = RunRecord(
            id=str(uuid.uuid4()),
            agent_id=agent_spec.id,
            goal=goal,
            status=RunStatus.PENDING,
            steps=(),
        )
        self._runs[run.id] = run
        self._log.info("run.created", run_id=run.id, agent_id=agent_spec.id)
        return run

    async def start_run(self, run_id: str) -> RunRecord:
        """Start executing a previously created run.

        Args:
            run_id: The run ID.

        Returns:
            The completed RunRecord.

        Raises:
            RunNotFoundError: If the run ID is unknown.
        """
        run = self._runs.get(run_id)
        if run is None:
            raise RunNotFoundError(run_id)

        if run.status is not RunStatus.PENDING:
            return run

        tracer = trace.get_tracer("eaip.agents.runtime")

        run = run.model_copy(update={"status": RunStatus.RUNNING})
        self._runs[run_id] = run

        start = time.monotonic()

        with tracer.start_as_current_span("agent.run", kind=SpanKind.INTERNAL) as span:
            span.set_attribute("agent.run_id", run_id)
            span.set_attribute("agent.agent_id", run.agent_id)
            span.set_attribute("agent.goal", run.goal.text[:100])

            await self._publish(
                RunStarted(
                    run_id=run_id,
                    agent_id=run.agent_id,
                    goal_text=run.goal.text,
                )
            )

            try:
                plan = await self._planner.create_plan(run.goal, self._context)
            except Exception as exc:
                elapsed = time.monotonic() - start
                return await self._fail_run(run, f"planning failed: {exc}", elapsed, span)

            run = run.model_copy(update={"plan": plan})
            self._runs[run_id] = run

            completed_steps = await self._execute_steps(
                list(plan.steps),
                run,
                tracer,
                run_id,
            )

            run = run.model_copy(update={"steps": tuple(completed_steps)})
            self._runs[run_id] = run

            elapsed = time.monotonic() - start
            run = await self._finalize_run(run, elapsed, span)
            self._runs[run_id] = run
            self._log.info(
                "run.complete",
                run_id=run_id,
                status=str(run.status),
                steps=len(run.steps),
                duration_s=round(elapsed, 3),
            )
            return run

    async def _execute_steps(
        self,
        all_steps: list[Step],
        run: RunRecord,
        tracer: trace.Tracer,
        run_id: str,
    ) -> list[Step]:
        """Execute each step in the plan, applying guardrails."""
        completed_steps: list[Step] = []

        for step in all_steps:
            await self._publish(
                StepStarted(
                    run_id=run_id,
                    step_id=step.id,
                    step_name=step.name,
                    step_type=str(step.type),
                )
            )

            guardrail_result = await self._guardrail.before_step(
                step,
                self._context,
            )

            if guardrail_result.blocked:
                skipped = Step(
                    id=step.id,
                    name=step.name,
                    type=step.type,
                    status=StepStatus.SKIPPED,
                    output="",
                    error=f"blocked by guardrail: {guardrail_result.reason}",
                )
                completed_steps.append(skipped)
                self._log.warning(
                    "step.blocked",
                    step_id=step.id,
                    reason=guardrail_result.reason,
                )
                continue

            final_step = guardrail_result.modified_step or step

            with tracer.start_as_current_span(
                f"agent.step.{step.type.value}",
                kind=SpanKind.CLIENT,
            ) as step_span:
                step_span.set_attribute("agent.step.id", step.id)
                step_span.set_attribute("agent.step.name", step.name)

                executed_step = await self._executor.execute(
                    final_step,
                    run,
                    self._context,
                )

            if executed_step.status is StepStatus.FAILED:
                step_span.set_status(StatusCode.ERROR, executed_step.error or "unknown")
                await self._publish(
                    StepFailed(
                        run_id=run_id,
                        step_id=step.id,
                        step_name=step.name,
                        error=executed_step.error or "unknown",
                        duration_ms=executed_step.duration_ms,
                    )
                )

                after_result = await self._guardrail.after_step(
                    executed_step,
                    self._context,
                )

                completed_steps.append(executed_step)
                if after_result.blocked:
                    break
            else:
                await self._publish(
                    StepCompleted(
                        run_id=run_id,
                        step_id=step.id,
                        step_name=step.name,
                        duration_ms=executed_step.duration_ms,
                    )
                )
                completed_steps.append(executed_step)
                await self._guardrail.after_step(executed_step, self._context)

        return completed_steps

    async def _finalize_run(
        self,
        run: RunRecord,
        elapsed: float,
        span: Any,
    ) -> RunRecord:
        """Determine final status, build result, and publish completion."""
        final_status = self._determine_final_status(list(run.steps))
        final_result = self._build_result(list(run.steps))

        if final_status is RunStatus.COMPLETED:
            run = run.model_copy(
                update={
                    "status": RunStatus.COMPLETED,
                    "result": final_result,
                    "duration_ms": elapsed * 1000,
                    "completed_at": utc_now(),
                },
            )
            span.set_status(StatusCode.OK)
            await self._publish(
                RunCompleted(
                    run_id=run.id,
                    agent_id=run.agent_id,
                    step_count=len(run.steps),
                    duration_ms=elapsed * 1000,
                )
            )
            self._record_metrics(run)
        else:
            run = await self._fail_run(
                run,
                f"run failed after {len(run.steps)} steps",
                elapsed,
                span,
            )

        return run

    async def cancel_run(self, run_id: str) -> RunRecord | None:
        """Cancel a running or pending run.

        Args:
            run_id: The run ID.

        Returns:
            The cancelled RunRecord, or None if not found.
        """
        run = self._runs.get(run_id)
        if run is None:
            return None

        if run.status in {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}:
            return run

        run = run.model_copy(
            update={
                "status": RunStatus.CANCELLED,
                "completed_at": utc_now(),
            },
        )
        self._runs[run_id] = run
        await self._publish(
            RunCancelled(
                run_id=run_id,
                agent_id=run.agent_id,
                step_count=len(run.steps),
            )
        )
        return run

    def get_run(self, run_id: str) -> RunRecord | None:
        """Return a run record by ID.

        Args:
            run_id: The run ID.

        Returns:
            The RunRecord, or None if not found.
        """
        return self._runs.get(run_id)

    def list_runs(
        self,
        agent_id: str | None = None,
        limit: int = 100,
    ) -> list[RunRecord]:
        """List run records, optionally filtered by agent ID.

        Args:
            agent_id: Optional agent ID filter.
            limit: Maximum number of records to return.

        Returns:
            A list of RunRecords.
        """
        runs = list(self._runs.values())
        if agent_id is not None:
            runs = [r for r in runs if r.agent_id == agent_id]
        runs.sort(key=lambda r: r.created_at, reverse=True)
        return runs[:limit]

    async def health(self) -> HealthReport:
        """Return a health report for the agent runtime.

        Returns:
            A HealthReport.
        """
        active_runs = sum(
            1 for r in self._runs.values() if r.status in {RunStatus.PENDING, RunStatus.RUNNING}
        )
        status = HealthStatus.HEALTHY
        return HealthReport(
            component="agent_runtime",
            status=status,
            message=f"{len(self._runs)} total runs, {active_runs} active",
            details={
                "total_runs": len(self._runs),
                "active_runs": active_runs,
            },
        )

    # ----------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------

    async def _publish(self, event: Any) -> None:
        """Publish an event to the event bus if available."""
        bus = self._context.event_bus
        if bus is not None:
            try:
                await bus.publish(event)
            except Exception:
                self._log.warning("event.publish.failed", event_type=type(event).__name__)

    async def _fail_run(
        self,
        run: RunRecord,
        error: str,
        elapsed: float,
        span: Any | None = None,
    ) -> RunRecord:
        """Mark a run as failed and publish the event."""
        if span is not None:
            span.set_status(StatusCode.ERROR, error)
        run = run.model_copy(
            update={
                "status": RunStatus.FAILED,
                "error": error,
                "duration_ms": elapsed * 1000,
                "completed_at": utc_now(),
            },
        )
        await self._publish(
            RunFailed(
                run_id=run.id,
                agent_id=run.agent_id,
                error=error,
                step_count=len(run.steps),
                duration_ms=elapsed * 1000,
            )
        )
        return run

    def _determine_final_status(self, steps: list[Step]) -> RunStatus:
        """Determine the final run status from completed step statuses."""
        if not steps:
            return RunStatus.COMPLETED
        if any(s.status is StepStatus.FAILED for s in steps):
            if all(s.status is StepStatus.FAILED for s in steps):
                return RunStatus.FAILED
            return RunStatus.COMPLETED
        return RunStatus.COMPLETED

    def _build_result(self, steps: list[Step]) -> str:
        """Build a result string from completed steps."""
        parts = [
            f"[{s.name}]: {s.output}"
            for s in steps
            if s.status is StepStatus.COMPLETED and s.output
        ]
        return "\n".join(parts)

    def _record_metrics(self, run: RunRecord) -> None:
        """Record run metrics if a meter is available."""
        meter = self._context.meter
        if meter is None:
            return
        try:
            meter.counter("agent.run.completed", labels={"status": str(run.status)}).inc()
            meter.histogram("agent.run.duration_ms").observe(run.duration_ms)
        except Exception:
            self._log.warning("metrics.record.failed")


__all__ = ["AgentRunContext", "AgentRuntime"]
