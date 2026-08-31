"""Tests for ScriptRuntime."""

from __future__ import annotations

import pytest

from eaip.script.exceptions import ScriptExecutionError
from eaip.script.models import ScriptExecutionStatus, ScriptFunction, ScriptLanguage
from eaip.script.registry import FunctionRegistry
from eaip.script.runtime import ScriptRuntime


class TestScriptRuntime:
    @pytest.fixture
    def registry(self) -> FunctionRegistry:
        return FunctionRegistry()

    @pytest.fixture
    def runtime(self, registry: FunctionRegistry) -> ScriptRuntime:
        return ScriptRuntime(registry=registry)

    @pytest.mark.asyncio
    async def test_execute_python_function(
        self, runtime: ScriptRuntime, registry: FunctionRegistry
    ) -> None:
        fn = ScriptFunction(
            id="fn_add",
            name="add",
            language=ScriptLanguage.PYTHON,
            source_code="result = args['a'] + args['b']",
        )
        registry.register(fn)
        exec_result = await runtime.execute("fn_add", {"a": 1, "b": 2})
        assert exec_result.status is ScriptExecutionStatus.COMPLETED
        assert exec_result.result == "3"
        assert exec_result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_execute_with_inline_result(
        self, runtime: ScriptRuntime, registry: FunctionRegistry
    ) -> None:
        fn = ScriptFunction(
            id="fn_hello",
            name="hello",
            language=ScriptLanguage.PYTHON,
            source_code="result = 'hello ' + args['name']",
        )
        registry.register(fn)
        exec_result = await runtime.execute("fn_hello", {"name": "world"})
        assert exec_result.status is ScriptExecutionStatus.COMPLETED
        assert exec_result.result == "hello world"

    @pytest.mark.asyncio
    async def test_execute_code_directly(self, runtime: ScriptRuntime) -> None:
        result = await runtime.execute_code("result = args['x'] * 2", "python", {"x": 21})
        assert result == 42

    @pytest.mark.asyncio
    async def test_execute_code_unsupported_language(self, runtime: ScriptRuntime) -> None:
        with pytest.raises(ScriptExecutionError):
            await runtime.execute_code("print(1)", "javascript", {})

    @pytest.mark.asyncio
    async def test_get_execution(self, runtime: ScriptRuntime, registry: FunctionRegistry) -> None:
        fn = ScriptFunction(
            id="f1", name="t", language=ScriptLanguage.PYTHON, source_code="result = 42"
        )
        registry.register(fn)
        exec_result = await runtime.execute("f1")
        retrieved = await runtime.get_execution(exec_result.id)
        assert retrieved.id == exec_result.id
        assert retrieved.function_id == "f1"

    @pytest.mark.asyncio
    async def test_get_execution_not_found(self, runtime: ScriptRuntime) -> None:
        with pytest.raises(ScriptExecutionError):
            await runtime.get_execution("nonexistent")

    @pytest.mark.asyncio
    async def test_list_executions(
        self, runtime: ScriptRuntime, registry: FunctionRegistry
    ) -> None:
        fn = ScriptFunction(
            id="f1", name="t", language=ScriptLanguage.PYTHON, source_code="result = 1"
        )
        registry.register(fn)
        await runtime.execute("f1")
        await runtime.execute("f1")
        executions = await runtime.list_executions()
        assert len(executions) == 2

    @pytest.mark.asyncio
    async def test_list_executions_by_function(
        self, runtime: ScriptRuntime, registry: FunctionRegistry
    ) -> None:
        fn1 = ScriptFunction(
            id="f1", name="t1", language=ScriptLanguage.PYTHON, source_code="result = 1"
        )
        fn2 = ScriptFunction(
            id="f2", name="t2", language=ScriptLanguage.PYTHON, source_code="result = 2"
        )
        registry.register(fn1)
        registry.register(fn2)
        await runtime.execute("f1")
        await runtime.execute("f2")
        executions = await runtime.list_executions(function_id="f1")
        assert len(executions) == 1
        assert executions[0].function_id == "f1"

    @pytest.mark.asyncio
    async def test_list_executions_empty(self, runtime: ScriptRuntime) -> None:
        executions = await runtime.list_executions()
        assert executions == []

    @pytest.mark.asyncio
    async def test_execute_function_not_found(self, runtime: ScriptRuntime) -> None:
        with pytest.raises(ScriptExecutionError):
            await runtime.execute("nonexistent")

    @pytest.mark.asyncio
    async def test_cancel_execution(
        self, runtime: ScriptRuntime, registry: FunctionRegistry
    ) -> None:
        fn = ScriptFunction(
            id="f_slow",
            name="slow",
            language=ScriptLanguage.PYTHON,
            source_code="import time; time.sleep(10); result = 1",
            timeout_seconds=30.0,
        )
        registry.register(fn)
        exec_result = await runtime.execute("f_slow")
        cancelled = await runtime.cancel(exec_result.id)
        assert cancelled.status is ScriptExecutionStatus.FAILED
        assert cancelled.error == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_nonexistent(self, runtime: ScriptRuntime) -> None:
        with pytest.raises(ScriptExecutionError):
            await runtime.cancel("nonexistent")

    @pytest.mark.asyncio
    async def test_execute_no_registry(self) -> None:
        runtime = ScriptRuntime()
        with pytest.raises(ScriptExecutionError):
            await runtime.execute("f1")

    @pytest.mark.asyncio
    async def test_execute_code_no_registry(self) -> None:
        runtime = ScriptRuntime()
        with pytest.raises(ScriptExecutionError):
            await runtime.execute("f1")

    @pytest.mark.asyncio
    async def test_execution_creates_execution_record(
        self, runtime: ScriptRuntime, registry: FunctionRegistry
    ) -> None:
        fn = ScriptFunction(
            id="f1", name="t", language=ScriptLanguage.PYTHON, source_code="result = 99"
        )
        registry.register(fn)
        exec_result = await runtime.execute("f1")
        assert exec_result.id.startswith("exec_")
        assert exec_result.function_id == "f1"
        assert exec_result.started_at is not None
        assert exec_result.completed_at is not None
