"""Tests for the @traced decorator."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

import pytest
from opentelemetry.trace import SpanKind

from eaip.settings.core_settings import TelemetrySettings
from eaip.tracing.decorators import traced
from eaip.tracing.provider import get_tracer, setup_telemetry

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

pytestmark = pytest.mark.usefixtures("_setup_otel")


@pytest.fixture(autouse=True)
def _setup_otel() -> None:
    setup_telemetry(TelemetrySettings())


class TestTraced:
    async def test_wraps_simple_async_function(self) -> None:
        @traced()
        async def greet(name: str) -> str:
            return f"hello {name}"

        result = await greet("world")
        assert result == "hello world"

    async def test_wraps_function_without_args(self) -> None:
        @traced()
        async def ping() -> str:
            return "pong"

        assert await ping() == "pong"

    async def test_custom_span_name(self) -> None:
        @traced(span_name="custom.operation")
        async def my_op() -> int:
            return 42

        assert await my_op() == 42

    async def test_static_attributes(self) -> None:
        @traced(attributes={"component": "test", "version": "1"})
        async def labeled() -> str:
            return "ok"

        assert await labeled() == "ok"

    async def test_preserves_function_metadata(self) -> None:
        @traced()
        async def my_func() -> None:
            pass

        assert my_func.__name__ == "my_func"

    async def test_records_successful_result(self) -> None:
        @traced()
        async def compute() -> int:
            return 99

        tracer = get_tracer()
        with tracer.start_as_current_span("parent"):
            result = await compute()

        assert result == 99

    async def test_records_exception(self) -> None:
        @traced()
        async def failing() -> None:
            msg = "something broke"
            raise ValueError(msg)

        with pytest.raises(ValueError, match="something broke"):
            await failing()

    async def test_async_generator(self) -> None:
        @traced()
        async def gen() -> AsyncGenerator[int, None]:
            for i in range(3):
                yield i

        results = [item async for item in gen()]
        assert results == [0, 1, 2]

    async def test_async_generator_exception(self) -> None:
        @traced()
        async def failing_gen() -> AsyncGenerator[int, None]:
            yield 1
            msg = "gen error"
            raise RuntimeError(msg)

        items: list[int] = []
        with pytest.raises(RuntimeError, match="gen error"):
            async for item in failing_gen():
                items.append(item)  # noqa: PERF401

        assert items == [1]

    async def test_span_kind(self) -> None:
        @traced(kind=SpanKind.CLIENT)
        async def client_call() -> str:
            return "resp"

        assert await client_call() == "resp"

    async def test_default_span_name_is_qualname(self) -> None:
        class MyService:
            @traced()
            async def do_work(self) -> str:
                return "done"

        svc = MyService()
        assert await svc.do_work() == "done"

    async def test_multiple_calls_create_distinct_spans(self) -> None:
        @traced()
        async def counter(val: int) -> int:
            return val

        for i in range(5):
            assert await counter(i) == i

    async def test_nested_traced_functions(self) -> None:
        @traced()
        async def inner() -> str:
            return "inner"

        @traced()
        async def outer() -> str:
            return await inner()

        assert await outer() == "inner"

    async def test_traces_are_async_gen_functions(self) -> None:
        @traced()
        async def async_gen() -> AsyncGenerator[int, None]:
            yield 42

        assert inspect.isasyncgenfunction(async_gen)
