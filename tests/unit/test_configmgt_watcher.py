"""Tests for configmgt watcher (observer pattern / hot reload)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from eaip.configmgt.models import ConfigChange
from eaip.configmgt.watcher import ConfigWatcher


class TestConfigWatcher:
    @pytest.fixture
    def watcher(self) -> ConfigWatcher:
        return ConfigWatcher()

    async def test_watch_and_notify(self, watcher: ConfigWatcher) -> None:
        callback = AsyncMock()
        change = ConfigChange(id="chg1", entry_id="e1", old_value="old", new_value="new")

        watcher.watch("e1", callback)
        await watcher.notify_watchers(change)

        callback.assert_awaited_once_with(change)

    async def test_unwatch(self, watcher: ConfigWatcher) -> None:
        callback = AsyncMock()
        change = ConfigChange(id="chg1", entry_id="e1")

        watcher.watch("e1", callback)
        watcher.unwatch("e1", callback)
        await watcher.notify_watchers(change)

        callback.assert_not_awaited()

    async def test_multiple_callbacks_per_key(self, watcher: ConfigWatcher) -> None:
        cb1 = AsyncMock()
        cb2 = AsyncMock()
        change = ConfigChange(id="chg1", entry_id="e1")

        watcher.watch("e1", cb1)
        watcher.watch("e1", cb2)
        await watcher.notify_watchers(change)

        cb1.assert_awaited_once_with(change)
        cb2.assert_awaited_once_with(change)

    async def test_wildcard_watcher(self, watcher: ConfigWatcher) -> None:
        callback = AsyncMock()
        change = ConfigChange(id="chg1", entry_id="e1")

        watcher.watch("*", callback)
        await watcher.notify_watchers(change)

        callback.assert_awaited_once_with(change)

    async def test_wildcard_and_specific(self, watcher: ConfigWatcher) -> None:
        specific_cb = AsyncMock()
        wildcard_cb = AsyncMock()
        change = ConfigChange(id="chg1", entry_id="e1")

        watcher.watch("e1", specific_cb)
        watcher.watch("*", wildcard_cb)
        await watcher.notify_watchers(change)

        specific_cb.assert_awaited_once_with(change)
        wildcard_cb.assert_awaited_once_with(change)

    async def test_no_watchers(self, watcher: ConfigWatcher) -> None:
        change = ConfigChange(id="chg1", entry_id="e1")
        await watcher.notify_watchers(change)

    async def test_get_watched_keys(self, watcher: ConfigWatcher) -> None:
        assert await watcher.get_watched_keys() == []

        cb = AsyncMock()
        watcher.watch("e1", cb)
        watcher.watch("e2", cb)

        keys = await watcher.get_watched_keys()
        assert sorted(keys) == ["e1", "e2"]

    async def test_unwatch_removes_key_when_empty(self, watcher: ConfigWatcher) -> None:
        cb = AsyncMock()
        watcher.watch("e1", cb)
        assert "e1" in await watcher.get_watched_keys()

        watcher.unwatch("e1", cb)
        assert "e1" not in await watcher.get_watched_keys()
