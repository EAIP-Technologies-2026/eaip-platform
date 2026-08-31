"""Tests for FunctionRegistry."""

from __future__ import annotations

from typing import Any

import pytest

from eaip.script.exceptions import FunctionNotFoundError
from eaip.script.models import ScriptFunction, ScriptFunctionStatus, ScriptLanguage
from eaip.script.registry import FunctionRegistry


class FakeEventBus:
    def __init__(self) -> None:
        self.events: list[Any] = []

    def publish(self, event: Any) -> None:
        self.events.append(event)


class TestFunctionRegistry:
    def test_register_and_get(self) -> None:
        reg = FunctionRegistry()
        fn = ScriptFunction(
            id="f1", name="greet", language=ScriptLanguage.PYTHON, source_code="pass"
        )
        reg.register(fn)
        assert reg.get("f1") == fn

    def test_get_not_found(self) -> None:
        reg = FunctionRegistry()
        with pytest.raises(FunctionNotFoundError):
            reg.get("nonexistent")

    def test_update(self) -> None:
        reg = FunctionRegistry()
        fn = ScriptFunction(
            id="f1", name="greet", language=ScriptLanguage.PYTHON, source_code="pass"
        )
        reg.register(fn)
        updated = reg.update("f1", description="new description")
        assert updated.description == "new description"
        assert updated.name == "greet"

    def test_update_not_found(self) -> None:
        reg = FunctionRegistry()
        with pytest.raises(FunctionNotFoundError):
            reg.update("f1", description="test")

    def test_delete(self) -> None:
        reg = FunctionRegistry()
        fn = ScriptFunction(
            id="f1", name="greet", language=ScriptLanguage.PYTHON, source_code="pass"
        )
        reg.register(fn)
        reg.delete("f1")
        with pytest.raises(FunctionNotFoundError):
            reg.get("f1")

    def test_delete_not_found(self) -> None:
        reg = FunctionRegistry()
        with pytest.raises(FunctionNotFoundError):
            reg.delete("nonexistent")

    def test_list_functions(self) -> None:
        reg = FunctionRegistry()
        fn1 = ScriptFunction(id="f1", name="a", language=ScriptLanguage.PYTHON, source_code="pass")
        fn2 = ScriptFunction(id="f2", name="b", language=ScriptLanguage.PYTHON, source_code="pass")
        reg.register(fn1)
        reg.register(fn2)
        assert len(reg.list_functions()) == 2

    def test_list_functions_empty(self) -> None:
        reg = FunctionRegistry()
        assert reg.list_functions() == []

    def test_list_functions_filter_by_status(self) -> None:
        reg = FunctionRegistry()
        fn1 = ScriptFunction(id="f1", name="a", language=ScriptLanguage.PYTHON, source_code="pass")
        fn2 = ScriptFunction(
            id="f2",
            name="b",
            language=ScriptLanguage.PYTHON,
            source_code="pass",
            status=ScriptFunctionStatus.DEPRECATED,
        )
        reg.register(fn1)
        reg.register(fn2)
        result = reg.list_functions(status=ScriptFunctionStatus.DEPRECATED)
        assert len(result) == 1
        assert result[0].id == "f2"

    def test_list_functions_filter_by_language(self) -> None:
        reg = FunctionRegistry()
        fn1 = ScriptFunction(id="f1", name="a", language=ScriptLanguage.PYTHON, source_code="pass")
        fn2 = ScriptFunction(
            id="f2", name="b", language=ScriptLanguage.JAVASCRIPT, source_code="pass"
        )
        reg.register(fn1)
        reg.register(fn2)
        result = reg.list_functions(language="python")
        assert len(result) == 1
        assert result[0].id == "f1"

    def test_create_version(self) -> None:
        reg = FunctionRegistry()
        fn = ScriptFunction(id="f1", name="greet", language=ScriptLanguage.PYTHON, source_code="v1")
        reg.register(fn)
        new_fn = reg.create_version("f1", source_code="v2", version="2.0.0")
        assert new_fn.version == "2.0.0"
        assert new_fn.source_code == "v2"
        assert reg.get("f1").version == "2.0.0"

    def test_list_versions(self) -> None:
        reg = FunctionRegistry()
        fn = ScriptFunction(id="f1", name="greet", language=ScriptLanguage.PYTHON, source_code="v1")
        reg.register(fn)
        reg.create_version("f1", source_code="v2", version="2.0.0")
        versions = reg.list_versions("f1")
        assert len(versions) == 2

    def test_list_versions_not_found(self) -> None:
        reg = FunctionRegistry()
        with pytest.raises(FunctionNotFoundError):
            reg.list_versions("nonexistent")

    def test_deprecate(self) -> None:
        reg = FunctionRegistry()
        fn = ScriptFunction(
            id="f1", name="greet", language=ScriptLanguage.PYTHON, source_code="pass"
        )
        reg.register(fn)
        deprecated = reg.deprecate("f1")
        assert deprecated.status is ScriptFunctionStatus.DEPRECATED
        assert reg.get("f1").status is ScriptFunctionStatus.DEPRECATED

    def test_deprecate_not_found(self) -> None:
        reg = FunctionRegistry()
        with pytest.raises(FunctionNotFoundError):
            reg.deprecate("nonexistent")

    def test_count(self) -> None:
        reg = FunctionRegistry()
        assert reg.count() == 0
        fn = ScriptFunction(id="f1", name="t", language=ScriptLanguage.PYTHON, source_code="pass")
        reg.register(fn)
        assert reg.count() == 1

    def test_event_publishing_on_register(self) -> None:
        bus = FakeEventBus()
        reg = FunctionRegistry(event_bus=bus)
        fn = ScriptFunction(
            id="f1", name="greet", language=ScriptLanguage.PYTHON, source_code="pass"
        )
        reg.register(fn)
        assert len(bus.events) == 1
        assert bus.events[0].function_id == "f1"

    def test_event_publishing_on_update(self) -> None:
        bus = FakeEventBus()
        reg = FunctionRegistry(event_bus=bus)
        fn = ScriptFunction(
            id="f1", name="greet", language=ScriptLanguage.PYTHON, source_code="pass"
        )
        reg.register(fn)
        reg.update("f1", description="updated")
        assert len(bus.events) == 2
        assert bus.events[1].function_id == "f1"

    def test_event_publishing_on_deprecate(self) -> None:
        bus = FakeEventBus()
        reg = FunctionRegistry(event_bus=bus)
        fn = ScriptFunction(
            id="f1", name="greet", language=ScriptLanguage.PYTHON, source_code="pass"
        )
        reg.register(fn)
        reg.deprecate("f1")
        assert len(bus.events) == 2
        assert bus.events[1].function_id == "f1"
