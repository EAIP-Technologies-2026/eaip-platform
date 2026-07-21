"""Tests for Script Runtime models."""

from __future__ import annotations

import pytest

from eaip.script.models import (
    ScriptConfig,
    ScriptExecution,
    ScriptExecutionStatus,
    ScriptFunction,
    ScriptFunctionStatus,
    ScriptLanguage,
)


class TestScriptFunction:
    def test_required_fields(self) -> None:
        fn = ScriptFunction(
            id="fn_1", name="greet", language=ScriptLanguage.PYTHON, source_code="result = 'hello'"
        )
        assert fn.id == "fn_1"
        assert fn.name == "greet"
        assert fn.language is ScriptLanguage.PYTHON
        assert fn.source_code == "result = 'hello'"
        assert fn.version == "1.0.0"
        assert fn.status is ScriptFunctionStatus.ACTIVE

    def test_with_all_fields(self) -> None:
        fn = ScriptFunction(
            id="fn_2",
            name="add",
            language=ScriptLanguage.PYTHON,
            source_code="result = args['a'] + args['b']",
            version="2.0.0",
            description="Adds two numbers",
            parameters=({"name": "a", "type": "int"}, {"name": "b", "type": "int"}),
            timeout_seconds=60.0,
            tags=("math", "utility"),
            status=ScriptFunctionStatus.DEPRECATED,
            metadata={"author": "test"},
        )
        assert fn.version == "2.0.0"
        assert fn.tags == ("math", "utility")
        assert fn.status is ScriptFunctionStatus.DEPRECATED

    def test_frozen(self) -> None:
        fn = ScriptFunction(
            id="f1", name="test", language=ScriptLanguage.PYTHON, source_code="pass"
        )
        with pytest.raises(ValueError):
            fn.name = "changed"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            ScriptFunction(
                id="f1", name="t", language=ScriptLanguage.PYTHON, source_code="pass", unknown=True
            )  # type: ignore[call-arg]

    def test_language_enum_values(self) -> None:
        assert ScriptLanguage.PYTHON.value == "python"
        assert ScriptLanguage.JAVASCRIPT.value == "javascript"
        assert ScriptLanguage.LUA.value == "lua"
        assert ScriptLanguage.RUBY.value == "ruby"

    def test_status_default_active(self) -> None:
        fn = ScriptFunction(id="f1", name="t", language=ScriptLanguage.PYTHON, source_code="pass")
        assert fn.status is ScriptFunctionStatus.ACTIVE

    def test_empty_tags_and_metadata(self) -> None:
        fn = ScriptFunction(id="f1", name="t", language=ScriptLanguage.PYTHON, source_code="pass")
        assert fn.tags == ()
        assert fn.metadata == {}
        assert fn.parameters == ()


class TestScriptExecution:
    def test_required_fields(self) -> None:
        ex = ScriptExecution(id="exec_1", function_id="fn_1")
        assert ex.id == "exec_1"
        assert ex.function_id == "fn_1"
        assert ex.status is ScriptExecutionStatus.PENDING
        assert ex.arguments == {}
        assert ex.result == ""

    def test_frozen(self) -> None:
        ex = ScriptExecution(id="e1", function_id="f1")
        with pytest.raises(ValueError):
            ex.status = ScriptExecutionStatus.COMPLETED

    def test_status_values(self) -> None:
        assert ScriptExecutionStatus.PENDING.value == "pending"
        assert ScriptExecutionStatus.RUNNING.value == "running"
        assert ScriptExecutionStatus.COMPLETED.value == "completed"
        assert ScriptExecutionStatus.FAILED.value == "failed"
        assert ScriptExecutionStatus.TIMEOUT.value == "timeout"

    def test_completed_execution(self) -> None:
        ex = ScriptExecution(
            id="e1",
            function_id="f1",
            result="42",
            status=ScriptExecutionStatus.COMPLETED,
            duration_ms=100.0,
        )
        assert ex.result == "42"
        assert ex.duration_ms == 100.0

    def test_failed_execution_with_error(self) -> None:
        ex = ScriptExecution(
            id="e1",
            function_id="f1",
            error="Something broke",
            status=ScriptExecutionStatus.FAILED,
        )
        assert ex.error == "Something broke"


class TestScriptConfig:
    def test_defaults(self) -> None:
        cfg = ScriptConfig()
        assert cfg.max_execution_time == 30.0
        assert cfg.max_memory_mb == 128
        assert cfg.allowed_imports == ()
        assert cfg.enable_sandbox is True
        assert cfg.max_concurrent_executions == 10

    def test_custom_values(self) -> None:
        cfg = ScriptConfig(
            max_execution_time=60.0,
            max_memory_mb=256,
            allowed_imports=("json", "math"),
            enable_sandbox=False,
            max_concurrent_executions=5,
        )
        assert cfg.max_execution_time == 60.0
        assert cfg.allowed_imports == ("json", "math")
        assert cfg.enable_sandbox is False

    def test_frozen(self) -> None:
        cfg = ScriptConfig()
        with pytest.raises(ValueError):
            cfg.max_execution_time = 10.0

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            ScriptConfig(unknown=True)  # type: ignore[call-arg]
