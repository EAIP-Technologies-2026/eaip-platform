"""Hook system for runtime lifecycle hooks with ordered execution."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

AsyncHookFn = Callable[..., Awaitable[None]]


class HookPoint(StrEnum):
    """Enum of recognised lifecycle hook points."""

    PRE_START = "pre_start"
    POST_START = "post_start"
    PRE_STOP = "pre_stop"
    POST_STOP = "post_stop"
    ON_ERROR = "on_error"


@dataclass
class RuntimeHook:
    """A single hook registration with name, function, point, and ordering."""

    name: str
    fn: AsyncHookFn
    hook_point: HookPoint
    order: int = 100
    metadata: dict[str, Any] = field(default_factory=dict)


class HookRegistry:
    """Registry of lifecycle hooks with ordered, failure-isolated execution."""

    def __init__(self) -> None:
        """Initialise an empty hook registry."""
        self._hooks: list[RuntimeHook] = []

    def register(self, hook: RuntimeHook) -> None:
        """Register a new hook."""
        self._hooks.append(hook)

    def unregister(self, name: str) -> bool:
        """Remove all hooks with the given name. Returns True if any were removed."""
        before = len(self._hooks)
        self._hooks = [h for h in self._hooks if h.name != name]
        return len(self._hooks) < before

    def get_for(self, hook_point: HookPoint) -> list[RuntimeHook]:
        """Return hooks for a given point, sorted by order."""
        return sorted(
            (h for h in self._hooks if h.hook_point == hook_point),
            key=lambda h: h.order,
        )

    async def run(self, hook_point: HookPoint, **kwargs: Any) -> list[BaseException]:
        """Execute all hooks for a point. Collects and returns exceptions."""
        failures: list[BaseException] = []
        for hook in self.get_for(hook_point):
            try:
                await hook.fn(**kwargs)
            except BaseException as exc:
                failures.append(exc)
        return failures

    def clear(self) -> None:
        """Remove all registered hooks."""
        self._hooks.clear()

    @property
    def count(self) -> int:
        """Return the number of registered hooks."""
        return len(self._hooks)
