"""Tests for Script Runtime domain events."""

from __future__ import annotations

import pytest

from eaip.events.event import DomainEvent
from eaip.script.events import (
    FunctionDeprecated,
    FunctionRegistered,
    FunctionUpdated,
    ScriptEvent,
    ScriptExecutionCompleted,
    ScriptExecutionFailed,
    ScriptExecutionStarted,
    ScriptExecutionTimedOut,
)


class TestBaseEvent:
    def test_all_events_are_domain_events(self) -> None:
        assert issubclass(FunctionRegistered, DomainEvent)
        assert issubclass(FunctionUpdated, DomainEvent)
        assert issubclass(FunctionDeprecated, DomainEvent)
        assert issubclass(ScriptExecutionStarted, DomainEvent)
        assert issubclass(ScriptExecutionCompleted, DomainEvent)
        assert issubclass(ScriptExecutionFailed, DomainEvent)
        assert issubclass(ScriptExecutionTimedOut, DomainEvent)

    def test_event_type_namespace(self) -> None:
        assert FunctionRegistered.event_type == "eaip.script.function.registered"
        assert FunctionUpdated.event_type == "eaip.script.function.updated"
        assert FunctionDeprecated.event_type == "eaip.script.function.deprecated"
        assert ScriptExecutionStarted.event_type == "eaip.script.execution.started"
        assert ScriptExecutionCompleted.event_type == "eaip.script.execution.completed"
        assert ScriptExecutionFailed.event_type == "eaip.script.execution.failed"
        assert ScriptExecutionTimedOut.event_type == "eaip.script.execution.timed_out"

    def test_script_event_union(self) -> None:
        evt: ScriptEvent = FunctionRegistered(
            function_id="f1", function_name="test", language="python"
        )
        assert isinstance(evt, FunctionRegistered)

        evt2: ScriptEvent = ScriptExecutionCompleted(
            execution_id="e1", function_id="f1", duration_ms=10.0
        )
        assert isinstance(evt2, ScriptExecutionCompleted)


class TestFunctionRegistered:
    def test_fields(self) -> None:
        evt = FunctionRegistered(
            function_id="f1", function_name="greet", language="python", version="1.0.0"
        )
        assert evt.function_id == "f1"
        assert evt.function_name == "greet"
        assert evt.language == "python"
        assert evt.version == "1.0.0"

    def test_frozen(self) -> None:
        evt = FunctionRegistered(function_id="f1", function_name="test", language="python")
        with pytest.raises(ValueError):
            evt.function_id = "f2"


class TestFunctionUpdated:
    def test_fields(self) -> None:
        evt = FunctionUpdated(function_id="f1", function_name="greet", version="2.0.0")
        assert evt.function_id == "f1"
        assert evt.version == "2.0.0"


class TestFunctionDeprecated:
    def test_fields(self) -> None:
        evt = FunctionDeprecated(function_id="f1", function_name="greet")
        assert evt.function_id == "f1"
        assert evt.function_name == "greet"


class TestScriptExecutionStarted:
    def test_fields(self) -> None:
        evt = ScriptExecutionStarted(execution_id="e1", function_id="f1")
        assert evt.execution_id == "e1"
        assert evt.function_id == "f1"


class TestScriptExecutionCompleted:
    def test_fields(self) -> None:
        evt = ScriptExecutionCompleted(execution_id="e1", function_id="f1", duration_ms=42.5)
        assert evt.execution_id == "e1"
        assert evt.duration_ms == 42.5


class TestScriptExecutionFailed:
    def test_fields(self) -> None:
        evt = ScriptExecutionFailed(execution_id="e1", function_id="f1", error="oops")
        assert evt.error == "oops"


class TestScriptExecutionTimedOut:
    def test_fields(self) -> None:
        evt = ScriptExecutionTimedOut(execution_id="e1", function_id="f1", timeout_seconds=30.0)
        assert evt.timeout_seconds == 30.0
