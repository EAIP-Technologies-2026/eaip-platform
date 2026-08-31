"""Tool Framework — protocol, registry, and built-in tools.

Tools are callable functions that an LLM can invoke during a chat session.
The framework provides:

* A :class:`Tool` protocol that all tools must satisfy.
* A :class:`ToolRegistry` for registering and discovering tools.
* Built-in reference tools under :mod:`eaip.tools.builtin`.
"""

from __future__ import annotations

from eaip.tools.base import Tool
from eaip.tools.registry import ToolRegistry

__all__ = [
    "Tool",
    "ToolRegistry",
]
