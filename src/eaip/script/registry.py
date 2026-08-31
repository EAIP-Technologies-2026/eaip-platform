"""FunctionRegistry — register, get, update, delete, version script functions."""

from __future__ import annotations

from typing import Any

from eaip.script.events import FunctionDeprecated, FunctionRegistered, FunctionUpdated
from eaip.script.exceptions import FunctionNotFoundError
from eaip.script.models import ScriptFunction, ScriptFunctionStatus


class FunctionRegistry:
    def __init__(self, event_bus: Any = None) -> None:
        self._functions: dict[str, ScriptFunction] = {}
        self._versions: dict[str, list[ScriptFunction]] = {}
        self._event_bus = event_bus

    def register(self, function: ScriptFunction) -> ScriptFunction:
        self._functions[function.id] = function
        if function.id not in self._versions:
            self._versions[function.id] = []
        self._versions[function.id].append(function)
        if self._event_bus:
            self._event_bus.publish(
                FunctionRegistered(
                    function_id=function.id,
                    function_name=function.name,
                    language=function.language.value,
                    version=function.version,
                )
            )
        return function

    def get(self, function_id: str) -> ScriptFunction:
        fn = self._functions.get(function_id)
        if fn is None:
            raise FunctionNotFoundError(function_id)
        return fn

    def update(self, function_id: str, **updates: Any) -> ScriptFunction:
        existing = self.get(function_id)
        updated = existing.model_copy(update=updates)
        self._functions[function_id] = updated
        if self._event_bus:
            self._event_bus.publish(
                FunctionUpdated(
                    function_id=function_id,
                    function_name=updated.name,
                    version=updated.version,
                )
            )
        return updated

    def delete(self, function_id: str) -> None:
        if function_id not in self._functions:
            raise FunctionNotFoundError(function_id)
        del self._functions[function_id]

    def list_functions(
        self,
        status: ScriptFunctionStatus | None = None,
        language: str | None = None,
    ) -> list[ScriptFunction]:
        result = list(self._functions.values())
        if status is not None:
            result = [f for f in result if f.status == status]
        if language is not None:
            result = [f for f in result if f.language.value == language]
        return result

    def create_version(
        self, function_id: str, source_code: str, version: str, **extra: Any
    ) -> ScriptFunction:
        existing = self.get(function_id)
        updates = dict(extra, source_code=source_code, version=version)
        new_fn = existing.model_copy(update=updates)
        self._functions[function_id] = new_fn
        self._versions.setdefault(function_id, []).append(new_fn)
        if self._event_bus:
            self._event_bus.publish(
                FunctionUpdated(
                    function_id=function_id,
                    function_name=new_fn.name,
                    version=version,
                )
            )
        return new_fn

    def list_versions(self, function_id: str) -> list[ScriptFunction]:
        if function_id not in self._versions and function_id not in self._functions:
            raise FunctionNotFoundError(function_id)
        return list(self._versions.get(function_id, []))

    def deprecate(self, function_id: str) -> ScriptFunction:
        existing = self.get(function_id)
        updated = existing.model_copy(update={"status": ScriptFunctionStatus.DEPRECATED})
        self._functions[function_id] = updated
        if self._event_bus:
            self._event_bus.publish(
                FunctionDeprecated(
                    function_id=function_id,
                    function_name=updated.name,
                )
            )
        return updated

    def count(self) -> int:
        return len(self._functions)


__all__ = ["FunctionRegistry"]
