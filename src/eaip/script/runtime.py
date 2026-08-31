"""ScriptRuntime — async sandboxed script execution engine."""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from typing import Any

from eaip.script.events import (
    ScriptExecutionCompleted,
    ScriptExecutionFailed,
    ScriptExecutionStarted,
    ScriptExecutionTimedOut,
)
from eaip.script.exceptions import (
    FunctionNotFoundError,
    ScriptExecutionError,
    ScriptTimeoutError,
)
from eaip.script.models import (
    ScriptExecution,
    ScriptExecutionStatus,
    ScriptFunction,
    ScriptLanguage,
)

_RESTRICTED_GLOBALS: dict[str, Any] = {
    "__builtins__": {
        "abs": abs,
        "all": all,
        "any": any,
        "bool": bool,
        "chr": chr,
        "dict": dict,
        "divmod": divmod,
        "enumerate": enumerate,
        "filter": filter,
        "float": float,
        "format": format,
        "frozenset": frozenset,
        "hash": hash,
        "hex": hex,
        "int": int,
        "isinstance": isinstance,
        "issubclass": issubclass,
        "iter": iter,
        "len": len,
        "list": list,
        "map": map,
        "max": max,
        "min": min,
        "next": next,
        "oct": oct,
        "ord": ord,
        "pow": pow,
        "range": range,
        "repr": repr,
        "reversed": reversed,
        "round": round,
        "set": set,
        "slice": slice,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "type": type,
        "zip": zip,
    },
}


class ScriptRuntime:
    def __init__(self, registry: Any = None, event_bus: Any = None) -> None:
        self._registry = registry
        self._event_bus = event_bus
        self._executions: dict[str, ScriptExecution] = {}
        self._tasks: dict[str, asyncio.Task[Any]] = {}

    async def execute(
        self, function_id: str, args: dict[str, Any] | None = None
    ) -> ScriptExecution:
        if self._registry is None:
            raise ScriptExecutionError("none", "no function registry available")
        try:
            fn = self._registry.get(function_id)
        except FunctionNotFoundError:
            raise ScriptExecutionError(function_id, "function not found in registry")
        exec_id = f"exec_{function_id}_{int(time.monotonic() * 1_000_000)}"
        exec_obj = ScriptExecution(
            id=exec_id,
            function_id=function_id,
            arguments=args or {},
            status=ScriptExecutionStatus.RUNNING,
            started_at=datetime.now(UTC),
        )
        self._executions[exec_id] = exec_obj

        if self._event_bus:
            self._event_bus.publish(
                ScriptExecutionStarted(
                    execution_id=exec_id,
                    function_id=function_id,
                )
            )

        task = asyncio.create_task(self._run_execution(exec_id, fn, args or {}))
        self._tasks[exec_id] = task

        try:
            result = await asyncio.wait_for(task, timeout=fn.timeout_seconds)
        except TimeoutError:
            task.cancel()
            return await self._handle_timeout(exec_id, function_id, fn.timeout_seconds)
        except Exception as exc:
            return await self._handle_failure(exec_id, function_id, str(exc))

        completed_at = datetime.now(UTC)
        duration_ms = (
            (completed_at - exec_obj.started_at).total_seconds() * 1000
            if exec_obj.started_at
            else 0
        )
        exec_obj = exec_obj.model_copy(
            update={
                "status": ScriptExecutionStatus.COMPLETED,
                "result": str(result),
                "completed_at": completed_at,
                "duration_ms": duration_ms,
            }
        )
        self._executions[exec_id] = exec_obj

        if self._event_bus:
            self._event_bus.publish(
                ScriptExecutionCompleted(
                    execution_id=exec_id,
                    function_id=function_id,
                    duration_ms=duration_ms,
                )
            )
        return exec_obj

    async def execute_code(
        self, code: str, language: str, args: dict[str, Any] | None = None
    ) -> Any:
        if language != ScriptLanguage.PYTHON.value:
            raise ScriptExecutionError(
                "direct", f"unsupported language for direct execution: {language}"
            )
        return await asyncio.to_thread(self._run_python_code, code, args or {})

    async def cancel(self, execution_id: str) -> ScriptExecution:
        task = self._tasks.get(execution_id)
        if task and not task.done():
            task.cancel()
        exec_obj = self._executions.get(execution_id)
        if exec_obj is None:
            raise ScriptExecutionError(execution_id, "execution not found")
        updated = exec_obj.model_copy(
            update={
                "status": ScriptExecutionStatus.FAILED,
                "error": "cancelled",
                "completed_at": datetime.now(UTC),
            }
        )
        self._executions[execution_id] = updated
        return updated

    async def get_execution(self, execution_id: str) -> ScriptExecution:
        exec_obj = self._executions.get(execution_id)
        if exec_obj is None:
            raise ScriptExecutionError(execution_id, "execution not found")
        return exec_obj

    async def list_executions(
        self, function_id: str | None = None, limit: int = 50
    ) -> list[ScriptExecution]:
        result = list(self._executions.values())
        if function_id is not None:
            result = [e for e in result if e.function_id == function_id]
        result.sort(key=lambda e: e.started_at or datetime.min.replace(tzinfo=UTC), reverse=True)
        return result[:limit]

    async def _run_execution(self, exec_id: str, fn: ScriptFunction, args: dict[str, Any]) -> str:
        if fn.language != ScriptLanguage.PYTHON:
            raise ScriptExecutionError(exec_id, f"unsupported runtime language: {fn.language}")

        def run() -> str:
            restricted = dict(_RESTRICTED_GLOBALS)
            local_scope: dict[str, Any] = {"args": args}
            exec(fn.source_code, restricted, local_scope)
            result = local_scope.get("result", local_scope.get("main"))
            return str(result) if result is not None else ""

        return await asyncio.to_thread(run)

    def _run_python_code(self, code: str, args: dict[str, Any]) -> Any:
        restricted = dict(_RESTRICTED_GLOBALS)
        local_scope: dict[str, Any] = {"args": args}
        exec(code, restricted, local_scope)
        return local_scope.get("result", local_scope.get("main"))

    async def _handle_timeout(
        self, exec_id: str, function_id: str, timeout_seconds: float
    ) -> ScriptExecution:
        self._tasks.pop(exec_id, None)
        exec_obj = self._executions.get(exec_id)
        if exec_obj:
            updated = exec_obj.model_copy(
                update={
                    "status": ScriptExecutionStatus.TIMEOUT,
                    "error": f"timed out after {timeout_seconds}s",
                    "completed_at": datetime.now(UTC),
                    "duration_ms": timeout_seconds * 1000,
                }
            )
            self._executions[exec_id] = updated
            if self._event_bus:
                self._event_bus.publish(
                    ScriptExecutionTimedOut(
                        execution_id=exec_id,
                        function_id=function_id,
                        timeout_seconds=timeout_seconds,
                    )
                )
            return updated
        raise ScriptTimeoutError(function_id, timeout_seconds)

    async def _handle_failure(self, exec_id: str, function_id: str, error: str) -> ScriptExecution:
        self._tasks.pop(exec_id, None)
        exec_obj = self._executions.get(exec_id)
        if exec_obj:
            updated = exec_obj.model_copy(
                update={
                    "status": ScriptExecutionStatus.FAILED,
                    "error": error,
                    "completed_at": datetime.now(UTC),
                }
            )
            self._executions[exec_id] = updated
            if self._event_bus:
                self._event_bus.publish(
                    ScriptExecutionFailed(
                        execution_id=exec_id,
                        function_id=function_id,
                        error=error,
                    )
                )
            return updated
        raise ScriptExecutionError(exec_id, error)


__all__ = ["ScriptRuntime"]
