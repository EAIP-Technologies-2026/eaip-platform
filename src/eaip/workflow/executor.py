"""Workflow execution engine - DAG, sequential, conditional routing, retry, timeout, parallel."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections import deque
from contextlib import suppress
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from eaip.agents.models import AgentSpec, Goal
from eaip.tools.registry import ToolRegistry
from eaip.workflow.base import ApprovalHandler, WorkflowPlugin
from eaip.workflow.events import (
    WorkflowChildCompleted,
    WorkflowChildStarted,
    WorkflowCompleted,
    WorkflowParallelGroupCompleted,
    WorkflowParallelGroupStarted,
    WorkflowPaused,
    WorkflowResumed,
    WorkflowStarted,
    WorkflowStepApprovalRequired,
    WorkflowStepCompleted,
    WorkflowStepFailed,
    WorkflowStepStarted,
    WorkflowStepTimedOut,
    WorkflowTimedOut,
)
from eaip.workflow.exceptions import (
    CircularWorkflowError,
    InvalidWorkflowError,
    WorkflowTimeoutError,
)
from eaip.workflow.models import (
    EdgeCondition,
    ParallelGroup,
    WorkflowContext,
    WorkflowDefinition,
    WorkflowResult,
    WorkflowRun,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepRecord,
    WorkflowStepStatus,
)
from eaip.workflow.state_machine import WorkflowState, WorkflowStateMachine

if TYPE_CHECKING:
    pass


class WorkflowEngine:
    """Core workflow execution engine.

    Executes DAG-based workflows with sequential, parallel, conditional routing,
    retry with backoff, timeout enforcement, cancellation, pause/resume, durable
    execution, and parent/child workflow support.
    """

    def __init__(
        self,
        agent_runtime: Any = None,
        tool_registry: Any = None,
        memory_engine: Any = None,
        event_bus: Any = None,
        approval_handler: ApprovalHandler | None = None,
        plugins: list[WorkflowPlugin] | None = None,
        meter: Any = None,
    ) -> None:
        self._agent_runtime = agent_runtime
        self._tool_registry = tool_registry
        self._memory_engine = memory_engine
        self._event_bus = event_bus
        self._approval_handler = approval_handler
        self._plugins = plugins or []
        self._meter = meter

        self._runs: dict[str, WorkflowRun] = {}
        self._cancel_flags: set[str] = set()
        self._pause_flags: set[str] = set()
        self._state_machines: dict[str, WorkflowStateMachine] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def execute(
        self,
        definition: WorkflowDefinition,
        context: WorkflowContext | None = None,
        parent_run_id: str | None = None,
    ) -> WorkflowResult:
        self._validate(definition)
        run_id = uuid.uuid4().hex[:16]
        ctx = context or WorkflowContext()

        sm = WorkflowStateMachine(WorkflowState.PENDING)
        sm.transition(WorkflowState.RUNNING)
        self._state_machines[run_id] = sm

        run = WorkflowRun(
            id=run_id,
            workflow_id=definition.id,
            definition=definition,
            status=WorkflowStatus.RUNNING,
            context=ctx.variables,
            parent_run_id=parent_run_id,
            state_machine_state=sm.state.value,
        )
        self._runs[run_id] = run
        started_at = time.monotonic()

        await self._publish(
            WorkflowStarted(
                run_id=run_id,
                workflow_id=definition.id,
                definition_name=definition.name,
                context_keys=tuple(ctx.variables.keys()),
                parent_run_id=parent_run_id,
            )
        )
        self._record_metric("workflow.started", {"workflow_id": definition.id})

        tc = definition.timeout_config
        workflow_timeout = tc.workflow_timeout_seconds if tc else 0.0
        try:
            if workflow_timeout > 0:
                result = await asyncio.wait_for(
                    self._execute_internal(run_id, definition, ctx),
                    timeout=workflow_timeout,
                )
            else:
                result = await self._execute_internal(run_id, definition, ctx)
        except TimeoutError:
            sm.transition(WorkflowState.TIMED_OUT)
            result = self._make_result(
                run_id,
                definition,
                started_at,
                WorkflowStatus.TIMED_OUT,
                f"workflow timed out after {workflow_timeout}s",
            )
            await self._publish(
                WorkflowTimedOut(
                    run_id=run_id,
                    workflow_id=definition.id,
                    workflow_name=definition.name,
                    timeout_seconds=workflow_timeout,
                    completed_steps=0,
                )
            )
        except asyncio.CancelledError:
            result = self._make_result(run_id, definition, started_at, WorkflowStatus.CANCELLED)
            self._try_transition(run_id, WorkflowState.CANCELLED)
        except Exception as exc:
            err = str(exc)
            result = self._make_result(run_id, definition, started_at, WorkflowStatus.FAILED, err)
            self._try_transition(run_id, WorkflowState.FAILED)
        else:
            if run_id in self._cancel_flags:
                result = result.model_copy(update={"status": WorkflowStatus.CANCELLED})
                self._try_transition(run_id, WorkflowState.CANCELLED)
            elif run_id in self._pause_flags:
                result = result.model_copy(update={"status": WorkflowStatus.PAUSED})
            else:
                self._try_transition(run_id, WorkflowState.COMPLETED)

        run = WorkflowRun(
            **{
                **run.model_dump(),
                "status": result.status,
                "result": result.result,
                "error": result.error,
                "duration_ms": result.duration_ms,
                "state_machine_state": sm.state.value,
            }
        )
        self._runs[run_id] = run
        self._cancel_flags.discard(run_id)
        self._pause_flags.discard(run_id)

        await self._publish(
            WorkflowCompleted(
                run_id=run_id,
                workflow_id=definition.id,
                status=result.status,
                duration_ms=result.duration_ms,
                result=result.result,
                error=result.error,
                step_count=result.step_count,
                completed_count=result.completed_count,
                failed_count=result.failed_count,
            )
        )
        self._record_metric(
            "workflow.completed",
            {
                "workflow_id": definition.id,
                "status": result.status.value,
            },
        )

        for plugin in self._plugins:
            await plugin.on_workflow_end(run_id=run_id, result=result)
        return result

    async def cancel(self, run_id: str) -> None:
        if run_id in self._runs:
            self._cancel_flags.add(run_id)
            sm = self._state_machines.get(run_id)
            if sm and sm.can_transition(WorkflowState.CANCELLED):
                sm.transition(WorkflowState.CANCELLED)
            r = self._runs[run_id]
            if r.status in (WorkflowStatus.PENDING, WorkflowStatus.RUNNING, WorkflowStatus.PAUSED):
                self._runs[run_id] = WorkflowRun(
                    **{
                        **r.model_dump(),
                        "status": WorkflowStatus.CANCELLED,
                    }
                )
                self._cancel_flags.discard(run_id)

    async def pause(self, run_id: str) -> None:
        if run_id in self._runs:
            self._pause_flags.add(run_id)
            sm = self._state_machines.get(run_id)
            if sm and sm.can_transition(WorkflowState.PAUSED):
                sm.transition(WorkflowState.PAUSED)
            run = self._runs[run_id]
            await self._publish(
                WorkflowPaused(
                    run_id=run_id,
                    workflow_id=run.workflow_id,
                    workflow_name=run.definition.name,
                )
            )

    async def resume(self, run_id: str) -> WorkflowResult:
        if run_id not in self._runs:
            return WorkflowResult(
                run_id=run_id,
                workflow_id="",
                status=WorkflowStatus.FAILED,
                error="run not found",
            )
        run = self._runs[run_id]
        if run.status != WorkflowStatus.PAUSED:
            return WorkflowResult(
                run_id=run_id,
                workflow_id=run.workflow_id,
                status=run.status,
                error="run is not paused",
            )
        self._pause_flags.discard(run_id)
        sm = self._state_machines.get(run_id)
        if sm and sm.can_transition(WorkflowState.RUNNING):
            sm.transition(WorkflowState.RUNNING)
        await self._publish(
            WorkflowResumed(
                run_id=run_id,
                workflow_id=run.workflow_id,
                workflow_name=run.definition.name,
            )
        )
        return await self.execute(run.definition, WorkflowContext(**run.context), run.parent_run_id)

    def get_run(self, run_id: str) -> WorkflowRun | None:
        return self._runs.get(run_id)

    def get_state_machine(self, run_id: str) -> WorkflowStateMachine | None:
        return self._state_machines.get(run_id)

    # ------------------------------------------------------------------
    # Internal execution
    # ------------------------------------------------------------------

    async def _execute_internal(
        self,
        run_id: str,
        definition: WorkflowDefinition,
        ctx: WorkflowContext,
    ) -> WorkflowResult:
        if definition.entry_point and not self._has_edges(definition):
            return await self._execute_sequential(run_id, definition, ctx)
        return await self._execute_dag(run_id, definition, ctx)

    async def _execute_sequential(
        self,
        run_id: str,
        definition: WorkflowDefinition,
        ctx: WorkflowContext,
    ) -> WorkflowResult:
        completed = 0
        failed = 0
        skipped = 0
        timed_out = 0
        step_records: list[WorkflowStepRecord] = []
        start = time.monotonic()

        steps = definition.steps
        if definition.entry_point:
            idx = next((i for i, s in enumerate(steps) if s.id == definition.entry_point), 0)
            steps = definition.steps[idx:]

        for step in steps:
            if run_id in self._cancel_flags:
                break
            while run_id in self._pause_flags and run_id not in self._cancel_flags:
                await asyncio.sleep(0.1)
                if run_id in self._cancel_flags:
                    break
            rec = await self._run_step(run_id, definition, step, ctx)
            step_records.append(rec)
            if rec.status == WorkflowStepStatus.COMPLETED:
                completed += 1
            elif rec.status == WorkflowStepStatus.FAILED:
                failed += 1
                break
            elif rec.status == WorkflowStepStatus.SKIPPED:
                skipped += 1
            elif rec.status == WorkflowStepStatus.TIMED_OUT:
                timed_out += 1
                break

        duration = (time.monotonic() - start) * 1000
        if run_id in self._cancel_flags:
            final_status = WorkflowStatus.CANCELLED
        elif timed_out > 0:
            final_status = WorkflowStatus.TIMED_OUT
        else:
            final_status = WorkflowStatus.COMPLETED

        return WorkflowResult(
            run_id=run_id,
            workflow_id=definition.id,
            status=final_status,
            step_count=len(step_records),
            completed_count=completed,
            failed_count=failed,
            skipped_count=skipped,
            timed_out_count=timed_out,
            duration_ms=duration,
        )

    async def _execute_dag(
        self,
        run_id: str,
        definition: WorkflowDefinition,
        ctx: WorkflowContext,
    ) -> WorkflowResult:
        _, in_deg = self._build_graph(definition)
        if self._has_cycle(definition):
            raise CircularWorkflowError()

        start = time.monotonic()
        completed = 0
        failed = 0
        skipped = 0
        timed_out = 0
        step_records: list[WorkflowStepRecord] = []

        queue: deque[WorkflowStep] = deque()
        ready: dict[str, WorkflowStep] = {}
        for s in definition.steps:
            if in_deg.get(s.id, 0) == 0:
                queue.append(s)

        parallel_groups = {g.id: g for g in definition.parallel_groups}
        completed_groups: set[str] = set()

        while queue:
            if run_id in self._cancel_flags:
                break
            while run_id in self._pause_flags and run_id not in self._cancel_flags:
                await asyncio.sleep(0.1)
                if run_id in self._cancel_flags:
                    break

            # Check for parallel groups
            parallel_tasks = []
            remaining: deque[WorkflowStep] = deque()
            for step in queue:
                group_id = self._find_group_for_step(step.id, parallel_groups)
                if group_id and group_id not in completed_groups:
                    parallel_tasks.append((group_id, step))
                else:
                    remaining.append(step)
            queue = remaining

            if parallel_tasks:
                group_results = await self._execute_parallel_group(
                    run_id,
                    definition,
                    parallel_tasks,
                    ctx,
                    parallel_groups,
                )
                for rec_list, grp_id in group_results:
                    completed_groups.add(grp_id)
                    for rec in rec_list:
                        step_records.append(rec)
                        if rec.status == WorkflowStepStatus.COMPLETED:
                            completed += 1
                            self._decrement_dependents(
                                rec.step_id,
                                in_deg,
                                queue,
                                ready,
                                definition,
                            )
                        elif rec.status == WorkflowStepStatus.FAILED:
                            failed += 1
                        elif rec.status == WorkflowStepStatus.TIMED_OUT:
                            timed_out += 1
                if failed > 0:
                    break
                continue

            if not queue:
                break
            step = queue.popleft()

            if not self._should_run(step, ctx, definition):
                rec = WorkflowStepRecord(
                    step_id=step.id,
                    name=step.name,
                    status=WorkflowStepStatus.SKIPPED,
                )
                step_records.append(rec)
                skipped += 1
                self._decrement_dependents(step.id, in_deg, queue, ready, definition)
                continue

            rec = await self._run_step(run_id, definition, step, ctx)
            step_records.append(rec)

            if rec.status == WorkflowStepStatus.COMPLETED:
                completed += 1
                self._decrement_dependents(step.id, in_deg, queue, ready, definition)
            elif rec.status == WorkflowStepStatus.FAILED:
                failed += 1
                break
            elif rec.status == WorkflowStepStatus.SKIPPED:
                skipped += 1
                self._decrement_dependents(step.id, in_deg, queue, ready, definition)
            elif rec.status == WorkflowStepStatus.TIMED_OUT:
                timed_out += 1
                break

        duration = (time.monotonic() - start) * 1000
        if run_id in self._cancel_flags:
            final_status = WorkflowStatus.CANCELLED
        elif timed_out > 0:
            final_status = WorkflowStatus.TIMED_OUT
        else:
            final_status = WorkflowStatus.COMPLETED

        return WorkflowResult(
            run_id=run_id,
            workflow_id=definition.id,
            status=final_status,
            step_count=len(step_records),
            completed_count=completed,
            failed_count=failed,
            skipped_count=skipped,
            timed_out_count=timed_out,
            duration_ms=duration,
        )

    async def _execute_parallel_group(
        self,
        run_id: str,
        definition: WorkflowDefinition,
        tasks: list[tuple[str, WorkflowStep]],
        ctx: WorkflowContext,
        parallel_groups: dict[str, ParallelGroup],
    ) -> list[tuple[list[WorkflowStepRecord], str]]:
        group_id = tasks[0][0]
        group = parallel_groups[group_id]
        steps_to_run = [t[1] for t in tasks]

        await self._publish(
            WorkflowParallelGroupStarted(
                run_id=run_id,
                workflow_id=definition.id,
                group_id=group_id,
                step_count=len(steps_to_run),
            )
        )

        group_start = time.monotonic()
        step_timeout = group.timeout_seconds if group.timeout_seconds > 0 else None

        async def _run_and_record(step: WorkflowStep) -> WorkflowStepRecord:
            return await self._run_step(run_id, definition, step, ctx)

        coros = [_run_and_record(s) for s in steps_to_run]
        if step_timeout:
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*coros, return_exceptions=True),
                    timeout=step_timeout,
                )
            except TimeoutError:
                for s in steps_to_run:
                    await self._publish(
                        WorkflowStepTimedOut(
                            run_id=run_id,
                            workflow_id=definition.id,
                            step_id=s.id,
                            step_name=s.name,
                            timeout_seconds=group.timeout_seconds,
                        )
                    )
                timed_out_records = [
                    WorkflowStepRecord(
                        step_id=s.id,
                        name=s.name,
                        status=WorkflowStepStatus.TIMED_OUT,
                        error=f"parallel group timed out after {group.timeout_seconds}s",
                    )
                    for s in steps_to_run
                ]
                group_duration = (time.monotonic() - group_start) * 1000
                await self._publish(
                    WorkflowParallelGroupCompleted(
                        run_id=run_id,
                        workflow_id=definition.id,
                        group_id=group_id,
                        completed=0,
                        failed=0,
                        duration_ms=group_duration,
                    )
                )
                return [(timed_out_records, group_id)]
        else:
            results = await asyncio.gather(*coros, return_exceptions=True)

        records: list[WorkflowStepRecord] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                records.append(
                    WorkflowStepRecord(
                        step_id=steps_to_run[i].id,
                        name=steps_to_run[i].name,
                        status=WorkflowStepStatus.FAILED,
                        error=str(result),
                    )
                )
            elif isinstance(result, WorkflowStepRecord):
                records.append(result)

        group_duration = (time.monotonic() - group_start) * 1000
        completed_count = sum(1 for r in records if r.status == WorkflowStepStatus.COMPLETED)
        failed_count = sum(1 for r in records if r.status == WorkflowStepStatus.FAILED)

        await self._publish(
            WorkflowParallelGroupCompleted(
                run_id=run_id,
                workflow_id=definition.id,
                group_id=group_id,
                completed=completed_count,
                failed=failed_count,
                duration_ms=group_duration,
            )
        )

        return [(records, group_id)]

    # ------------------------------------------------------------------
    # Step execution
    # ------------------------------------------------------------------

    async def _run_step(
        self,
        run_id: str,
        definition: WorkflowDefinition,
        step: WorkflowStep,
        ctx: WorkflowContext,
    ) -> WorkflowStepRecord:
        step_start = time.monotonic()
        rec = WorkflowStepRecord(
            step_id=step.id,
            name=step.name,
            status=WorkflowStepStatus.RUNNING,
            agent_id=step.agent_id,
            tool_name=step.tool_name,
            prompt=step.prompt,
            input=step.input,
            attempt=0,
            started_at=datetime.fromtimestamp(step_start, tz=UTC),
        )

        # Approval checkpoint before execution
        if step.requires_approval and self._approval_handler:
            rec = WorkflowStepRecord(
                **{
                    **rec.model_dump(),
                    "status": WorkflowStepStatus.WAITING_APPROVAL,
                }
            )
            sm = self._state_machines.get(run_id)
            if sm and sm.can_transition(WorkflowState.WAITING_APPROVAL):
                sm.transition(WorkflowState.WAITING_APPROVAL)

            approval_timeout = (
                definition.timeout_config.approval_timeout_seconds
                if definition.timeout_config
                else 3600.0
            )
            try:
                token = await self._approval_handler.request_approval(
                    step_id=step.id,
                    run_id=run_id,
                    payload={
                        "step_name": step.name,
                        "step_id": step.id,
                        "prompt": step.approval_prompt or step.prompt,
                        "input": step.input,
                    },
                    timeout_seconds=approval_timeout,
                )
            except Exception as exc:
                rec = WorkflowStepRecord(
                    **{
                        **rec.model_dump(),
                        "status": WorkflowStepStatus.FAILED,
                        "error": f"approval request failed: {exc}",
                        "completed_at": datetime.fromtimestamp(time.monotonic(), tz=UTC),
                    }
                )
                await self._publish(
                    WorkflowStepFailed(
                        run_id=run_id,
                        workflow_id=definition.id,
                        step_id=step.id,
                        step_name=step.name,
                        error=f"approval request failed: {exc}",
                        attempt=0,
                        will_retry=False,
                    )
                )
                return rec

            rec = WorkflowStepRecord(**{**rec.model_dump(), "approval_token": token})

            await self._publish(
                WorkflowStepApprovalRequired(
                    run_id=run_id,
                    workflow_id=definition.id,
                    step_id=step.id,
                    step_name=step.name,
                    payload=rec.input,
                    resume_token=token,
                    approval_prompt=step.approval_prompt,
                )
            )

            if sm and sm.can_transition(WorkflowState.RUNNING):
                sm.transition(WorkflowState.RUNNING)

        await self._publish(
            WorkflowStepStarted(
                run_id=run_id,
                workflow_id=definition.id,
                step_id=step.id,
                step_name=step.name,
                agent_id=step.agent_id,
                tool_name=step.tool_name,
                attempt=0,
            )
        )
        self._record_metric(
            "workflow.step.started",
            {
                "workflow_id": definition.id,
                "step_id": step.id,
            },
        )
        for plugin in self._plugins:
            await plugin.on_step_start(run_id=run_id, step_id=step.id, context=ctx)

        rp = step.retry_policy
        max_attempts = rp.max_attempts if rp else 1
        delay = rp.delay_seconds if rp else 0.0
        backoff = rp.backoff_multiplier if rp else 1.0
        max_delay = rp.max_delay_seconds if rp else 60.0
        jitter = rp.jitter if rp else 0.0

        last_error: str | None = None
        step_timeout = step.timeout_seconds if step.timeout_seconds > 0 else None

        for attempt in range(max_attempts):
            if run_id in self._cancel_flags:
                rec = WorkflowStepRecord(
                    **{
                        **rec.model_dump(),
                        "status": WorkflowStepStatus.SKIPPED,
                        "error": "cancelled",
                    }
                )
                break
            if attempt > 0:
                await asyncio.sleep(delay + (jitter * (time.monotonic() % 1)))
                delay = min(delay * backoff, max_delay)

            try:
                if step_timeout:
                    output = await asyncio.wait_for(
                        self._execute_step_action(step),
                        timeout=step_timeout,
                    )
                else:
                    output = await self._execute_step_action(step)
            except TimeoutError:
                last_error = f"step timed out after {step.timeout_seconds}s"
                rec = WorkflowStepRecord(
                    **{
                        **rec.model_dump(),
                        "attempt": attempt,
                        "error": last_error,
                    }
                )
                await self._publish(
                    WorkflowStepTimedOut(
                        run_id=run_id,
                        workflow_id=definition.id,
                        step_id=step.id,
                        step_name=step.name,
                        timeout_seconds=step.timeout_seconds,
                    )
                )
                continue
            except Exception as exc:
                last_error = str(exc)
                rec = WorkflowStepRecord(
                    **{
                        **rec.model_dump(),
                        "attempt": attempt,
                        "error": last_error,
                    }
                )
                continue

            elapsed = (time.monotonic() - step_start) * 1000
            rec = WorkflowStepRecord(
                step_id=step.id,
                name=step.name,
                status=WorkflowStepStatus.COMPLETED,
                agent_id=step.agent_id,
                tool_name=step.tool_name,
                prompt=step.prompt,
                input=step.input,
                output=output,
                attempt=attempt,
                duration_ms=elapsed,
                started_at=rec.started_at,
                completed_at=datetime.fromtimestamp(time.monotonic(), tz=UTC),
                approval_token=rec.approval_token,
            )
            ctx = ctx.set(step.id, output)
            ctx = ctx.add_agent_output(step.id, output)
            await self._publish(
                WorkflowStepCompleted(
                    run_id=run_id,
                    workflow_id=definition.id,
                    step_id=step.id,
                    step_name=step.name,
                    agent_id=step.agent_id,
                    tool_name=step.tool_name,
                    attempt=attempt,
                    duration_ms=elapsed,
                    output=output,
                )
            )
            self._record_metric(
                "workflow.step.completed",
                {
                    "workflow_id": definition.id,
                    "step_id": step.id,
                    "attempt": str(attempt),
                    "duration_ms": str(elapsed),
                },
            )
            for plugin in self._plugins:
                await plugin.on_step_end(
                    run_id=run_id,
                    step_id=step.id,
                    context=ctx,
                    status="completed",
                )
            return rec

        if last_error and "timed out" in last_error:
            final_status = WorkflowStepStatus.TIMED_OUT
        else:
            final_status = WorkflowStepStatus.FAILED

        rec = WorkflowStepRecord(
            **{
                **rec.model_dump(),
                "status": final_status,
                "error": last_error or "unknown error",
                "completed_at": datetime.fromtimestamp(time.monotonic(), tz=UTC),
            }
        )
        await self._publish(
            WorkflowStepFailed(
                run_id=run_id,
                workflow_id=definition.id,
                step_id=step.id,
                step_name=step.name,
                error=last_error or "unknown error",
                attempt=max_attempts - 1,
                will_retry=False,
            )
        )
        for plugin in self._plugins:
            await plugin.on_step_end(run_id=run_id, step_id=step.id, context=ctx, status="failed")
        return rec

    async def _execute_step_action(
        self,
        step: WorkflowStep,
    ) -> str:
        if step.agent_id and self._agent_runtime:
            runtime: Any = self._agent_runtime
            spec = AgentSpec(id=step.agent_id, name=step.agent_id)
            goal = Goal(text=step.prompt or "")
            run_record = await runtime.create_run(spec, goal)
            completed = await runtime.start_run(run_record.id)
            return completed.result or ""
        if step.tool_name and self._tool_registry:
            registry: ToolRegistry = self._tool_registry
            tool = registry.get(step.tool_name)
            return await tool.execute(**step.input)
        return json.dumps(step.input, default=str)

    # ------------------------------------------------------------------
    # Parent/Child workflow
    # ------------------------------------------------------------------

    async def execute_child(
        self,
        child_definition: WorkflowDefinition,
        parent_run_id: str,
        context: WorkflowContext | None = None,
    ) -> WorkflowResult:
        ctx = context or WorkflowContext()
        parent_cfg = child_definition.parent_child_config

        if parent_cfg and parent_cfg.inherit_context and parent_run_id in self._runs:
            parent_run = self._runs[parent_run_id]
            ctx = WorkflowContext(
                **{
                    **ctx.model_dump(),
                    "variables": {**parent_run.context, **ctx.variables},
                }
            )

        await self._publish(
            WorkflowChildStarted(
                parent_run_id=parent_run_id,
                child_run_id="",
                workflow_id=child_definition.id,
                workflow_name=child_definition.name,
            )
        )

        result = await self.execute(child_definition, ctx, parent_run_id)

        if parent_run_id in self._runs:
            parent_run = self._runs[parent_run_id]
            child_ids = [*parent_run.child_run_ids, result.run_id]
            self._runs[parent_run_id] = WorkflowRun(
                **{
                    **parent_run.model_dump(),
                    "child_run_ids": tuple(child_ids),
                }
            )

        await self._publish(
            WorkflowChildCompleted(
                parent_run_id=parent_run_id,
                child_run_id=result.run_id,
                workflow_id=child_definition.id,
                status=result.status,
                duration_ms=result.duration_ms,
            )
        )

        if parent_cfg and parent_cfg.propagate_failure and result.status == WorkflowStatus.FAILED:
            raise WorkflowTimeoutError(child_definition.id, 0)

        return result

    # ------------------------------------------------------------------
    # Graph utilities
    # ------------------------------------------------------------------

    def _build_graph(
        self,
        definition: WorkflowDefinition,
    ) -> tuple[dict[str, list[str]], dict[str, int]]:
        adj: dict[str, list[str]] = {s.id: [] for s in definition.steps}
        in_deg: dict[str, int] = {s.id: 0 for s in definition.steps}
        for edge in definition.edges:
            if edge.source_id in adj and edge.target_id in adj:
                adj[edge.source_id].append(edge.target_id)
                in_deg[edge.target_id] = in_deg.get(edge.target_id, 0) + 1
        return adj, in_deg

    def _has_cycle(self, definition: WorkflowDefinition) -> bool:
        adj, _ = self._build_graph(definition)
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def _dfs(n: str) -> bool:
            visited.add(n)
            rec_stack.add(n)
            for nb in adj.get(n, []):
                if nb not in visited:
                    if _dfs(nb):
                        return True
                elif nb in rec_stack:
                    return True
            rec_stack.discard(n)
            return False

        return any(n not in visited and _dfs(n) for n in adj)

    def _has_edges(self, definition: WorkflowDefinition) -> bool:
        return len(definition.edges) > 0

    def _find_group_for_step(
        self,
        step_id: str,
        groups: dict[str, ParallelGroup],
    ) -> str | None:
        for gid, group in groups.items():
            if step_id in group.step_ids:
                return gid
        return None

    def _decrement_dependents(
        self,
        step_id: str,
        in_deg: dict[str, int],
        queue: deque[WorkflowStep],
        _ready: dict[str, WorkflowStep],
        definition: WorkflowDefinition,
    ) -> None:
        step_map = {s.id: s for s in definition.steps}
        for edge in definition.edges:
            if edge.source_id == step_id:
                tid = edge.target_id
                in_deg[tid] = in_deg.get(tid, 0) - 1
                if in_deg.get(tid, 0) <= 0 and tid in step_map:
                    queue.append(step_map[tid])

    def _should_run(
        self,
        step: WorkflowStep,
        ctx: WorkflowContext,
        definition: WorkflowDefinition,
    ) -> bool:
        for edge in definition.edges:
            if edge.target_id == step.id and edge.source_id in ctx.variables:
                src = ctx.variables.get(edge.source_id, "")
                if edge.condition == EdgeCondition.ON_SUCCESS and "error" in src.lower():
                    return False
                if edge.condition == EdgeCondition.ON_FAILURE and "error" not in src.lower():
                    return False
                if (
                    edge.condition == EdgeCondition.EXPRESSION
                    and edge.expression
                    and edge.expression not in src
                ):
                    return False
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _validate(self, definition: WorkflowDefinition) -> None:
        if not definition.steps and not definition.edges:
            return
        step_ids = {s.id for s in definition.steps}
        for edge in definition.edges:
            if edge.source_id not in step_ids:
                raise InvalidWorkflowError(f"edge source {edge.source_id!r} not found in steps")
            if edge.target_id not in step_ids:
                raise InvalidWorkflowError(f"edge target {edge.target_id!r} not found in steps")
        if self._has_cycle(definition):
            raise CircularWorkflowError()
        for group in definition.parallel_groups:
            for sid in group.step_ids:
                if sid not in step_ids:
                    raise InvalidWorkflowError(
                        f"parallel group {group.id!r} references unknown step {sid!r}"
                    )

    def _make_result(
        self,
        run_id: str,
        definition: WorkflowDefinition,
        started_at: float,
        status: WorkflowStatus = WorkflowStatus.COMPLETED,
        error: str | None = None,
    ) -> WorkflowResult:
        duration = (time.monotonic() - started_at) * 1000
        return WorkflowResult(
            run_id=run_id,
            workflow_id=definition.id,
            status=status,
            error=error,
            step_count=len(definition.steps),
            duration_ms=duration,
        )

    def _try_transition(self, run_id: str, target: WorkflowState) -> None:
        sm = self._state_machines.get(run_id)
        if sm and sm.can_transition(target):
            sm.transition(target)

    async def _publish(self, event: Any) -> None:
        if self._event_bus:
            await self._event_bus.publish(event)

    def _record_metric(self, name: str, labels: dict[str, str]) -> None:
        if self._meter:
            with suppress(Exception):
                self._meter.counter(f"workflow.{name}", labels=labels).inc()


__all__ = ["WorkflowEngine"]
