"""CalculatorTool — evaluates simple arithmetic expressions."""

from __future__ import annotations

import operator
from typing import Any

from pydantic.json_schema import JsonSchemaValue

from eaip.tools.exceptions import ToolExecutionError

_OPERATORS: dict[str, Any] = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "//": operator.floordiv,
    "%": operator.mod,
    "**": operator.pow,
}


class CalculatorTool:
    """A tool that evaluates simple arithmetic expressions.

    Supports: ``+``, ``-``, ``*``, ``/``, ``//``, ``%``, ``**``.
    Uses Python's :func:`operator` module for safe evaluation (no ``eval``).
    """

    name = "calculator"
    description = "Evaluate a simple arithmetic expression. Supports +, -, *, /, //, %, **."

    @property
    def parameters(self) -> JsonSchemaValue:
        """JSON Schema for the expression parameter."""
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Arithmetic expression to evaluate, e.g. '2 + 3 * 4'.",
                },
            },
            "required": ["expression"],
        }

    async def execute(self, **kwargs: object) -> str:
        """Evaluate the expression and return the result as a string."""
        expression = str(kwargs.get("expression", ""))
        try:
            result = self._evaluate(expression)
            return str(result)
        except Exception as exc:
            raise ToolExecutionError(
                f"calculator failed for expression {expression!r}: {exc}"
            ) from exc

    def _evaluate(self, expression: str) -> float:
        """Safe expression evaluator using the shunting-yard algorithm."""
        tokens = self._tokenize(expression)
        if not tokens:
            raise ToolExecutionError("empty expression")
        return self._parse_expression(tokens)

    def _tokenize(self, expression: str) -> list[str]:
        """Tokenize a math expression into numbers, operators, and parens."""
        tokens: list[str] = []
        current: list[str] = []
        i = 0
        while i < len(expression):
            ch = expression[i]
            if ch.isspace():
                if current:
                    tokens.append("".join(current))
                    current = []
                i += 1
            elif (
                ch.isdigit()
                or ch == "."
                or (
                    ch == "-"
                    and not current
                    and (not tokens or tokens[-1] in ("(", "+", "-", "*", "/", "%", "**", "//"))
                )
            ):
                current.append(ch)
                i += 1
            else:
                if current:
                    tokens.append("".join(current))
                    current = []
                if i + 1 < len(expression) and expression[i : i + 2] in ("**", "//"):
                    tokens.append(expression[i : i + 2])
                    i += 2
                else:
                    tokens.append(ch)
                    i += 1
        if current:
            tokens.append("".join(current))
        return tokens

    def _parse_expression(self, tokens: list[str]) -> float:
        """Parse and evaluate a list of tokens using precedence climbing."""
        index = 0

        def parse_primary() -> float:
            nonlocal index
            tok = tokens[index]
            if tok == "(":
                index += 1
                val = parse_add_sub()
                if index >= len(tokens) or tokens[index] != ")":
                    raise ToolExecutionError("mismatched parentheses")
                index += 1
                return val
            try:
                val = float(tok)
                index += 1
                return val
            except ValueError:
                raise ToolExecutionError(f"unexpected token: {tok!r}") from None

        def parse_pow() -> float:
            nonlocal index
            left = parse_primary()
            while index < len(tokens) and tokens[index] == "**":
                index += 1
                right = parse_pow()
                left = _OPERATORS["**"](left, right)
            return left

        def parse_mul_div() -> float:
            nonlocal index
            left = parse_pow()
            while index < len(tokens) and tokens[index] in ("*", "/", "//", "%"):
                op = tokens[index]
                index += 1
                right = parse_pow()
                left = _OPERATORS[op](left, right)
            return left

        def parse_add_sub() -> float:
            nonlocal index
            left = parse_mul_div()
            while index < len(tokens) and tokens[index] in ("+", "-"):
                op = tokens[index]
                index += 1
                right = parse_mul_div()
                left = _OPERATORS[op](left, right)
            return left

        result = parse_add_sub()
        if index < len(tokens):
            raise ToolExecutionError(f"unexpected tokens after expression: {tokens[index:]}")
        return result


__all__ = ["CalculatorTool"]
