"""Script runtime domain events."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class FunctionRegistered(DomainEvent):
    event_type: ClassVar[str] = "eaip.script.function.registered"
    function_id: str = ""
    function_name: str = ""
    language: str = ""
    version: str = ""


class FunctionUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.script.function.updated"
    function_id: str = ""
    function_name: str = ""
    version: str = ""


class FunctionDeprecated(DomainEvent):
    event_type: ClassVar[str] = "eaip.script.function.deprecated"
    function_id: str = ""
    function_name: str = ""


class ScriptExecutionStarted(DomainEvent):
    event_type: ClassVar[str] = "eaip.script.execution.started"
    execution_id: str = ""
    function_id: str = ""


class ScriptExecutionCompleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.script.execution.completed"
    execution_id: str = ""
    function_id: str = ""
    duration_ms: float = 0.0


class ScriptExecutionFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.script.execution.failed"
    execution_id: str = ""
    function_id: str = ""
    error: str = ""


class ScriptExecutionTimedOut(DomainEvent):
    event_type: ClassVar[str] = "eaip.script.execution.timed_out"
    execution_id: str = ""
    function_id: str = ""
    timeout_seconds: float = 0.0


ScriptEvent = (
    FunctionRegistered
    | FunctionUpdated
    | FunctionDeprecated
    | ScriptExecutionStarted
    | ScriptExecutionCompleted
    | ScriptExecutionFailed
    | ScriptExecutionTimedOut
)

__all__ = [
    "FunctionDeprecated",
    "FunctionRegistered",
    "FunctionUpdated",
    "ScriptEvent",
    "ScriptExecutionCompleted",
    "ScriptExecutionFailed",
    "ScriptExecutionStarted",
    "ScriptExecutionTimedOut",
]
