"""DocChangelogService — manages API documentation changelogs by version."""

from __future__ import annotations

import time
from typing import Any

from eaip.apidocs.events import ChangelogCreated
from eaip.apidocs.exceptions import ChangelogError
from eaip.apidocs.models import DocChangelog


class DocChangelogService:
    def __init__(self, event_bus: Any = None) -> None:
        self._changelogs: dict[str, DocChangelog] = {}
        self._counter: int = 0
        self._event_bus = event_bus

    async def create_entry(self, version: str, changes: tuple[str, ...]) -> DocChangelog:
        if not version:
            raise ChangelogError("version is required")
        self._counter += 1
        entry = DocChangelog(
            id=f"cl_{version}_{int(time.monotonic() * 1_000_000)}_{self._counter}",
            version=version,
            changes=changes,
        )
        self._changelogs[entry.id] = entry
        if self._event_bus:
            self._event_bus.publish(
                ChangelogCreated(
                    changelog_id=entry.id,
                    version=version,
                    change_count=len(changes),
                )
            )
        return entry

    async def get_changelog(self, changelog_id: str) -> DocChangelog | None:
        return self._changelogs.get(changelog_id)

    async def list_changelogs(self, limit: int = 20) -> list[DocChangelog]:
        result = sorted(self._changelogs.values(), key=lambda c: c.date, reverse=True)
        return result[:limit]

    async def list_by_version(self, version: str) -> list[DocChangelog]:
        return [c for c in self._changelogs.values() if c.version == version]


__all__ = ["DocChangelogService"]
