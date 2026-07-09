"""Tests for built-in reference tools."""

from __future__ import annotations

import pytest

from eaip.tools.base import Tool
from eaip.tools.builtin import CalculatorTool, CurrentTimeTool, EchoTool
from eaip.tools.exceptions import ToolExecutionError


class TestEchoTool:
    @pytest.fixture
    def tool(self) -> EchoTool:
        return EchoTool()

    def test_protocol_compliance(self, tool: EchoTool) -> None:
        assert isinstance(tool, Tool)

    def test_metadata(self, tool: EchoTool) -> None:
        assert tool.name == "echo"
        assert "echo" in tool.description.lower()

    def test_parameters_schema(self, tool: EchoTool) -> None:
        params = tool.parameters
        assert params["type"] == "object"
        assert "message" in params["properties"]
        assert "message" in params["required"]

    async def test_execute_with_message(self, tool: EchoTool) -> None:
        result = await tool.execute(message="hello world")
        assert result == "echo: hello world"

    async def test_execute_empty_message(self, tool: EchoTool) -> None:
        result = await tool.execute(message="")
        assert result == "echo: "

    async def test_execute_without_message(self, tool: EchoTool) -> None:
        result = await tool.execute()
        assert result == "echo: "

    async def test_execute_with_special_characters(self, tool: EchoTool) -> None:
        result = await tool.execute(message="a=b&c=d")
        assert result == "echo: a=b&c=d"


class TestCalculatorTool:
    @pytest.fixture
    def tool(self) -> CalculatorTool:
        return CalculatorTool()

    def test_protocol_compliance(self, tool: CalculatorTool) -> None:
        assert isinstance(tool, Tool)

    def test_metadata(self, tool: CalculatorTool) -> None:
        assert tool.name == "calculator"
        assert "arithmetic" in tool.description.lower()

    def test_parameters_schema(self, tool: CalculatorTool) -> None:
        params = tool.parameters
        assert params["type"] == "object"
        assert "expression" in params["properties"]
        assert "expression" in params["required"]

    async def test_addition(self, tool: CalculatorTool) -> None:
        result = await tool.execute(expression="2 + 3")
        assert float(result) == 5.0

    async def test_multiplication(self, tool: CalculatorTool) -> None:
        result = await tool.execute(expression="4 * 5")
        assert float(result) == 20.0

    async def test_division(self, tool: CalculatorTool) -> None:
        result = await tool.execute(expression="10 / 2")
        assert float(result) == 5.0

    async def test_complex_expression(self, tool: CalculatorTool) -> None:
        result = await tool.execute(expression="2 + 3 * 4")
        assert float(result) == 14.0

    async def test_parentheses(self, tool: CalculatorTool) -> None:
        result = await tool.execute(expression="(2 + 3) * 4")
        assert float(result) == 20.0

    async def test_power(self, tool: CalculatorTool) -> None:
        result = await tool.execute(expression="2 ** 3")
        assert float(result) == 8.0

    async def test_modulo(self, tool: CalculatorTool) -> None:
        result = await tool.execute(expression="10 % 3")
        assert float(result) == 1.0

    async def test_floor_division(self, tool: CalculatorTool) -> None:
        result = await tool.execute(expression="10 // 3")
        assert float(result) == 3.0

    async def test_negative_number(self, tool: CalculatorTool) -> None:
        result = await tool.execute(expression="-5 + 3")
        assert float(result) == -2.0

    async def test_decimal(self, tool: CalculatorTool) -> None:
        result = await tool.execute(expression="3.5 + 2.5")
        assert float(result) == 6.0

    async def test_invalid_expression_raises(self, tool: CalculatorTool) -> None:
        with pytest.raises(ToolExecutionError):
            await tool.execute(expression="hello")

    async def test_empty_expression_raises(self, tool: CalculatorTool) -> None:
        with pytest.raises(ToolExecutionError):
            await tool.execute(expression="")

    async def test_mismatched_parentheses_raises(self, tool: CalculatorTool) -> None:
        with pytest.raises(ToolExecutionError):
            await tool.execute(expression="(2 + 3")

    async def test_division_by_zero(self, tool: CalculatorTool) -> None:
        with pytest.raises(ToolExecutionError):
            await tool.execute(expression="1 / 0")


class TestCurrentTimeTool:
    @pytest.fixture
    def tool(self) -> CurrentTimeTool:
        return CurrentTimeTool()

    def test_protocol_compliance(self, tool: CurrentTimeTool) -> None:
        assert isinstance(tool, Tool)

    def test_metadata(self, tool: CurrentTimeTool) -> None:
        assert tool.name == "current_time"
        assert "UTC" in tool.description

    def test_parameters_schema(self, tool: CurrentTimeTool) -> None:
        params = tool.parameters
        assert params["type"] == "object"
        assert "format" in params["properties"]

    async def test_default_format(self, tool: CurrentTimeTool) -> None:
        result = await tool.execute()
        assert result.endswith("Z")

    async def test_custom_format(self, tool: CurrentTimeTool) -> None:
        result = await tool.execute(format="%Y")
        assert len(result) == 4
        assert result.isdigit()

    async def test_returns_utc(self, tool: CurrentTimeTool) -> None:
        result = await tool.execute(format="%z")
        assert result in ("+0000", "UTC")

    async def test_without_arguments(self, tool: CurrentTimeTool) -> None:
        result = await tool.execute()
        assert isinstance(result, str)
        assert len(result) > 0
