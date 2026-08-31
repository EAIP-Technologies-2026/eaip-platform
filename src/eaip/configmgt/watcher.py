"""Observer-pattern watcher for hot-reload configuration changes."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from eaip.configmgt.models import ConfigChange

ConfigChangeCallback = Callable[[ConfigChange], Coroutine[Any, Any, None]]


class ConfigWatcher:
    def __init__(self) -> None:
        self._watchers: dict[str, list[ConfigChangeCallback]] = {}

    def watch(self, key: str, callback: ConfigChangeCallback) -> None:
        if key not in self._watchers:
            self._watchers[key] = []
        self._watchers[key].append(callback)

    def unwatch(self, key: str, callback: ConfigChangeCallback) -> None:
        if key in self._watchers:
            self._watchers[key] = [cb for cb in self._watchers[key] if cb is not callback]
            if not self._watchers[key]:
                del self._watchers[key]

    async def notify_watchers(self, change: ConfigChange) -> None:
        watchers = self._watchers.get(change.entry_id, []) + self._watchers.get("*", [])
        for callback in watchers:
            await callback(change)

    async def get_watched_keys(self) -> list[str]:
        return list(self._watchers.keys())


__all__ = ["ConfigChangeCallback", "ConfigWatcher"]
