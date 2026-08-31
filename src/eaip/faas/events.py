"""Domain events for Function as a Service runtime."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class FunctionDeployed(DomainEvent):
    event_type: ClassVar[str] = "eaip.faas.deployed"

    function_id: str
    name: str
    runtime: str


class FunctionExecuted(DomainEvent):
    event_type: ClassVar[str] = "eaip.faas.executed"

    execution_id: str
    function_id: str
    duration_ms: int


class FunctionFailed(DomainEvent):
    event_type: ClassVar[str] = "eaip.faas.failed"

    execution_id: str
    function_id: str
    error: str


class FunctionScaled(DomainEvent):
    event_type: ClassVar[str] = "eaip.faas.scaled"

    function_id: str
    previous_instances: int
    new_instances: int


__all__ = [
    "FunctionDeployed",
    "FunctionExecuted",
    "FunctionFailed",
    "FunctionScaled",
]
