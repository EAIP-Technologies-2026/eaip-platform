"""FaaS runtime — deploy, execute, and manage serverless functions."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from eaip.faas.events import (
    FunctionDeployed,
    FunctionExecuted,
    FunctionFailed,
    FunctionScaled,
)
from eaip.faas.exceptions import FunctionNotFoundError
from eaip.faas.models import (
    ExecutionStatus,
    FaaSConfig,
    Function,
    FunctionExecution,
    FunctionRuntime,
    FunctionStatus,
)
from eaip.shared.time import utc_now

EventCallback = Callable[[Any], Any]


class FaaSRuntime:
    def __init__(
        self,
        config: FaaSConfig | None = None,
        event_callback: EventCallback | None = None,
    ) -> None:
        self._config = config or FaaSConfig()
        self._functions: dict[str, Function] = {}
        self._executions: dict[str, FunctionExecution] = {}
        self._instance_counts: dict[str, int] = {}
        self._event_callback = event_callback

    def set_event_callback(self, callback: EventCallback | None) -> None:
        self._event_callback = callback

    def _emit(self, event: Any) -> None:
        if self._event_callback:
            self._event_callback(event)

    # -- Function management -------------------------------------------------

    async def deploy(
        self,
        name: str,
        runtime: FunctionRuntime,
        handler: str,
        code_ref: str,
        *,
        timeout_seconds: int | None = None,
        memory_mb: int | None = None,
    ) -> Function:
        fn = Function(
            id=str(uuid.uuid4()),
            name=name,
            runtime=runtime,
            handler=handler,
            code_ref=code_ref,
            timeout_seconds=timeout_seconds or self._config.default_timeout_seconds,
            memory_mb=memory_mb or self._config.default_memory_mb,
        )
        self._functions[fn.id] = fn
        self._instance_counts[fn.id] = 0
        self._emit(
            FunctionDeployed(
                function_id=fn.id,
                name=name,
                runtime=runtime.value,
            )
        )
        return fn

    async def get_function(self, function_id: str) -> Function:
        if function_id not in self._functions:
            raise FunctionNotFoundError(
                f"Function not found: {function_id}",
                context={"function_id": function_id},
            )
        return self._functions[function_id]

    async def list_functions(
        self,
        status: FunctionStatus | None = None,
    ) -> list[Function]:
        all_fns = list(self._functions.values())
        if status:
            all_fns = [f for f in all_fns if f.status == status]
        return all_fns

    async def set_function_status(
        self,
        function_id: str,
        status: FunctionStatus,
    ) -> Function:
        fn = await self.get_function(function_id)
        updated = Function(
            id=fn.id,
            name=fn.name,
            runtime=fn.runtime,
            handler=fn.handler,
            code_ref=fn.code_ref,
            timeout_seconds=fn.timeout_seconds,
            memory_mb=fn.memory_mb,
            status=status,
        )
        self._functions[function_id] = updated
        return updated

    # -- Execution -----------------------------------------------------------

    async def execute(
        self,
        function_id: str,
        payload: str = "",
    ) -> FunctionExecution:
        fn = await self.get_function(function_id)
        if fn.status != FunctionStatus.ACTIVE:
            raise RuntimeError(f"Function '{fn.name}' is not active (status: {fn.status.value})")

        execution = FunctionExecution(
            id=str(uuid.uuid4()),
            function_id=function_id,
            status=ExecutionStatus.PENDING,
        )
        self._executions[execution.id] = execution

        started = utc_now()
        running = FunctionExecution(
            id=execution.id,
            function_id=function_id,
            status=ExecutionStatus.RUNNING,
            started_at=started,
        )
        self._executions[execution.id] = running

        try:
            result = await self._invoke_handler(fn, payload)
            completed = utc_now()
            duration = int((completed - started).total_seconds() * 1000)
            finished = FunctionExecution(
                id=execution.id,
                function_id=function_id,
                status=ExecutionStatus.COMPLETED,
                started_at=started,
                completed_at=completed,
                duration_ms=duration,
                output=result,
            )
            self._executions[execution.id] = finished
            self._emit(
                FunctionExecuted(
                    execution_id=execution.id,
                    function_id=function_id,
                    duration_ms=duration,
                )
            )
            return finished
        except Exception as exc:
            completed = utc_now()
            duration = int((completed - started).total_seconds() * 1000)
            failed = FunctionExecution(
                id=execution.id,
                function_id=function_id,
                status=ExecutionStatus.FAILED,
                started_at=started,
                completed_at=completed,
                duration_ms=duration,
                error=str(exc),
            )
            self._executions[execution.id] = failed
            self._emit(
                FunctionFailed(
                    execution_id=execution.id,
                    function_id=function_id,
                    error=str(exc),
                )
            )
            return failed

    async def _invoke_handler(self, fn: Function, payload: str) -> str:
        return f"Executed {fn.name} ({fn.runtime.value}) with payload: {payload}"

    async def get_execution(self, execution_id: str) -> FunctionExecution:
        if execution_id not in self._executions:
            raise RuntimeError(f"Execution not found: {execution_id}")
        return self._executions[execution_id]

    async def list_executions(
        self,
        function_id: str | None = None,
        status: ExecutionStatus | None = None,
    ) -> list[FunctionExecution]:
        result = list(self._executions.values())
        if function_id:
            result = [e for e in result if e.function_id == function_id]
        if status:
            result = [e for e in result if e.status == status]
        return result

    # -- Scaling -------------------------------------------------------------

    async def scale(
        self,
        function_id: str,
        instances: int,
    ) -> int:
        fn = await self.get_function(function_id)
        instances = max(self._config.min_instances, min(instances, self._config.max_instances))
        previous = self._instance_counts.get(function_id, 0)
        self._instance_counts[function_id] = instances
        self._emit(
            FunctionScaled(
                function_id=function_id,
                previous_instances=previous,
                new_instances=instances,
            )
        )
        return instances

    async def get_instance_count(self, function_id: str) -> int:
        return self._instance_counts.get(function_id, 0)


__all__ = ["FaaSRuntime"]
