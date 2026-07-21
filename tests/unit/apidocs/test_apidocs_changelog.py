"""Tests for DocChangelogService."""

from __future__ import annotations

import pytest

from eaip.apidocs.changelog import DocChangelogService
from eaip.apidocs.exceptions import ChangelogError


class TestDocChangelogService:
    @pytest.fixture
    def service(self) -> DocChangelogService:
        return DocChangelogService()

    @pytest.mark.asyncio
    async def test_create_entry(self, service: DocChangelogService) -> None:
        entry = await service.create_entry("1.1.0", ("Added endpoint", "Fixed bug"))
        assert entry.version == "1.1.0"
        assert len(entry.changes) == 2
        assert entry.id.startswith("cl_")

    @pytest.mark.asyncio
    async def test_create_entry_empty_version_raises(self, service: DocChangelogService) -> None:
        with pytest.raises(ChangelogError):
            await service.create_entry("", ("change",))

    @pytest.mark.asyncio
    async def test_get_changelog(self, service: DocChangelogService) -> None:
        entry = await service.create_entry("1.1.0", ("change",))
        retrieved = await service.get_changelog(entry.id)
        assert retrieved is not None
        assert retrieved.id == entry.id

    @pytest.mark.asyncio
    async def test_get_changelog_not_found(self, service: DocChangelogService) -> None:
        result = await service.get_changelog("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_changelogs(self, service: DocChangelogService) -> None:
        await service.create_entry("1.0.0", ("Initial",))
        await service.create_entry("1.1.0", ("Update",))
        entries = await service.list_changelogs()
        assert len(entries) == 2

    @pytest.mark.asyncio
    async def test_list_changelogs_empty(self, service: DocChangelogService) -> None:
        entries = await service.list_changelogs()
        assert entries == []

    @pytest.mark.asyncio
    async def test_list_changelogs_ordered_by_date(self, service: DocChangelogService) -> None:
        await service.create_entry("1.0.0", ("Initial",))
        await service.create_entry("1.1.0", ("Update",))
        entries = await service.list_changelogs()
        assert entries[0].version == "1.1.0"
        assert entries[1].version == "1.0.0"

    @pytest.mark.asyncio
    async def test_list_by_version(self, service: DocChangelogService) -> None:
        await service.create_entry("1.0.0", ("Initial",))
        await service.create_entry("1.0.0", ("Second",))
        entries = await service.list_by_version("1.0.0")
        assert len(entries) == 2

    @pytest.mark.asyncio
    async def test_list_by_version_empty(self, service: DocChangelogService) -> None:
        entries = await service.list_by_version("9.9.9")
        assert entries == []
