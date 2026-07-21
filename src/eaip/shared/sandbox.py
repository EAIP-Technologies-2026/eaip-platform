"""Safe execution sandbox — AST-validated restricted code execution.

Provides :func:`safe_exec` as a drop-in replacement for unsafe ``exec()`` calls.
The sandbox parses the source into an AST, validates every node against an
allowed-node whitelist, and only executes code that passes validation.

**Allowed operations:**
- Simple and augmented assignments (``x = ...``, ``x += ...``)
- Expressions: arithmetic, comparison, boolean, ternary
- Subscript and attribute access (``data[key]``, ``obj.attr``)
- List, dict, tuple, set literals
- Calls to a restricted set of built-in functions
- ``pass``, ``del``

**Rejected operations (partial list):**
- ``import`` / ``from ... import``
- ``class`` / ``def`` / ``lambda`` / ``async def``
- ``raise`` / ``try`` / ``with`` / ``yield``
- ``exec`` / ``eval`` / ``compile`` / ``__import__``
- ``global`` / ``nonlocal``
- ``match`` / ``case``
- Attribute access to dangerous dunder names (``__subclasses__``,
  ``__globals__``, ``__mro__``, ``__bases__``, ``__class__``, ``__code__``,
  ``__func__``, ``__closure__``, ``__self__``, ``__dict__``,
  ``__getattribute__``, ``__reduce__``, ``__reduce_ex__``)
"""

from __future__ import annotations

import ast
from typing import Any

SAFE_BUILTINS: frozenset[str] = frozenset(
    {
        "abs",
        "all",
        "any",
        "bool",
        "chr",
        "dict",
        "divmod",
        "enumerate",
        "filter",
        "float",
        "frozenset",
        "hash",
        "hex",
        "int",
        "isinstance",
        "issubclass",
        "iter",
        "len",
        "list",
        "map",
        "max",
        "min",
        "next",
        "oct",
        "ord",
        "pow",
        "range",
        "repr",
        "reversed",
        "round",
        "set",
        "slice",
        "sorted",
        "str",
        "sum",
        "tuple",
        "type",
        "zip",
    }
)

_ALLOWED_AST_NODES: frozenset[type[ast.AST]] = frozenset(
    {
        # Top-level
        ast.Module,
        ast.Expression,
        # Statements
        ast.Expr,
        ast.Assign,
        ast.AugAssign,
        ast.Pass,
        ast.Delete,
        # Expression leaves
        ast.Constant,
        ast.Name,
        # Expression contexts
        ast.Load,
        ast.Store,
        ast.Del,
        # Containers
        ast.List,
        ast.Tuple,
        ast.Dict,
        ast.Set,
        # Subscript / attribute
        ast.Subscript,
        ast.Attribute,
        ast.Slice,
        # Binary operators
        ast.BinOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.FloorDiv,
        ast.Mod,
        ast.Pow,
        ast.LShift,
        ast.RShift,
        ast.BitOr,
        ast.BitXor,
        ast.BitAnd,
        # Unary operators
        ast.UnaryOp,
        ast.UAdd,
        ast.USub,
        ast.Not,
        ast.Invert,
        # Comparison operators
        ast.Compare,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.Is,
        ast.IsNot,
        ast.In,
        ast.NotIn,
        # Boolean operators
        ast.BoolOp,
        ast.And,
        ast.Or,
        # Conditionals (ternary only)
        ast.IfExp,
        # Calls
        ast.Call,
        ast.keyword,
        # Starred (e.g. ``*args`` in list/dict)
        ast.Starred,
    }
)

_UNSAFE_CALL_NAMES: frozenset[str] = frozenset(
    {
        "exec",
        "eval",
        "compile",
        "__import__",
        "open",
        "input",
        "breakpoint",
    }
)

_DANGEROUS_ATTR_NAMES: frozenset[str] = frozenset(
    {
        # Class hierarchy traversal — enables recovering real builtins
        "__subclasses__",
        "__globals__",
        "__mro__",
        "__bases__",
        "__class__",
        # Code object introspection — enables arbitrary code execution
        "__code__",
        "__func__",
        "__closure__",
        "__self__",
        # Metaprogramming — enables object graph manipulation
        "__dict__",
        "__getattribute__",
        "__reduce__",
        "__reduce_ex__",
    }
)


class _UnsafeCodeError(ValueError):
    """Raised when code fails AST validation."""


def _validate_ast(tree: ast.AST) -> None:
    """Walk the AST and reject disallowed node types, unsafe calls, and dangerous attribute names.

    Raises:
        _UnsafeCodeError: If the code contains unsafe constructs.
    """
    for node in ast.walk(tree):
        node_type = type(node)
        if node_type not in _ALLOWED_AST_NODES:
            raise _UnsafeCodeError(
                f"unsafe construct not allowed: {node_type.__name__} "
                f"(line {getattr(node, 'lineno', '?')})"
            )
        if isinstance(node, ast.Attribute) and node.attr in _DANGEROUS_ATTR_NAMES:
            raise _UnsafeCodeError(
                f"access to dangerous attribute '{node.attr}' is not allowed "
                f"(line {node.lineno})"
            )
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in _UNSAFE_CALL_NAMES:
                raise _UnsafeCodeError(
                    f"call to unsafe function '{func.id}' is not allowed "
                    f"(line {func.lineno})"
                )
            if isinstance(func, ast.Attribute) and func.attr in _UNSAFE_CALL_NAMES:
                raise _UnsafeCodeError(
                    f"call to unsafe method '{func.attr}' is not allowed "
                    f"(line {func.lineno})"
                )


def safe_exec(
    code: str,
    restricted_globals: dict[str, Any] | None = None,
    local_scope: dict[str, Any] | None = None,
) -> None:
    """Execute *code* with AST validation and a restricted builtins scope.

    Args:
        code: Python source code to execute.
        restricted_globals: A restricted globals dict that already has
            ``__builtins__`` configured. If ``None``, a safe default is used.
        local_scope: The local scope dict for assignments.

    Raises:
        ValueError: If the code contains unsafe constructs.
        Any exception raised by the executed code propagates unchanged.
    """
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as exc:
        raise ValueError(f"syntax error in sandboxed code: {exc}") from exc

    _validate_ast(tree)

    if restricted_globals is None:
        restricted_builtins: dict[str, Any] = {name: __builtins__[name] for name in SAFE_BUILTINS}
        restricted_globals = {"__builtins__": restricted_builtins}

    exec(compile(tree, filename="<sandbox>", mode="exec"), restricted_globals, local_scope)  # noqa: S102  # validated by AST walk above


__all__ = ["SAFE_BUILTINS", "safe_exec"]
