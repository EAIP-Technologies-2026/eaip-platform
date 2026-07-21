"""Tests for DatabaseMigrationAssistant."""

from __future__ import annotations

import pytest

from eaip.dbmigrate.assistant import DatabaseMigrationAssistant
from eaip.dbmigrate.exceptions import ScriptNotFoundError
from eaip.dbmigrate.models import DBMigrateConfig, MigrationScript, ScriptStatus


class TestDatabaseMigrationAssistant:
    @pytest.fixture
    def assistant(self) -> DatabaseMigrationAssistant:
        return DatabaseMigrationAssistant()

    @pytest.fixture
    def sample_script(self) -> MigrationScript:
        return MigrationScript(
            id="s1", name="add_users", version="1.0", database_type="postgres", author="alice"
        )

    class TestCreateScript:
        async def test_creates_script(
            self, assistant: DatabaseMigrationAssistant, sample_script: MigrationScript
        ) -> None:
            result = await assistant.create_script(sample_script)
            assert result.id == "s1"
            assert result.name == "add_users"

        async def test_stores_script(
            self, assistant: DatabaseMigrationAssistant, sample_script: MigrationScript
        ) -> None:
            await assistant.create_script(sample_script)
            stored = await assistant.get_script("s1")
            assert stored.id == "s1"

    class TestGetScript:
        async def test_returns_script(
            self, assistant: DatabaseMigrationAssistant, sample_script: MigrationScript
        ) -> None:
            await assistant.create_script(sample_script)
            result = await assistant.get_script("s1")
            assert result.name == "add_users"

        async def test_raises_on_missing(self, assistant: DatabaseMigrationAssistant) -> None:
            with pytest.raises(ScriptNotFoundError):
                await assistant.get_script("nonexistent")

    class TestUpdateScript:
        async def test_updates_script(
            self, assistant: DatabaseMigrationAssistant, sample_script: MigrationScript
        ) -> None:
            await assistant.create_script(sample_script)
            updated = await assistant.update_script("s1", name="updated")
            assert updated.name == "updated"

        async def test_raises_on_missing(self, assistant: DatabaseMigrationAssistant) -> None:
            with pytest.raises(ScriptNotFoundError):
                await assistant.update_script("nonexistent", name="test")

    class TestListScripts:
        async def test_empty_when_none(self, assistant: DatabaseMigrationAssistant) -> None:
            assert await assistant.list_scripts() == []

        async def test_filters_by_status(self, assistant: DatabaseMigrationAssistant) -> None:
            s1 = MigrationScript(
                id="s1",
                name="a",
                version="1",
                database_type="pg",
                author="alice",
                status=ScriptStatus.DRAFT,
            )
            s2 = MigrationScript(
                id="s2",
                name="b",
                version="2",
                database_type="pg",
                author="bob",
                status=ScriptStatus.EXECUTED,
            )
            await assistant.create_script(s1)
            await assistant.create_script(s2)
            result = await assistant.list_scripts(status=ScriptStatus.DRAFT)
            assert len(result) == 1
            assert result[0].id == "s1"

    class TestExecuteScript:
        async def test_executes_script(
            self, assistant: DatabaseMigrationAssistant, sample_script: MigrationScript
        ) -> None:
            await assistant.create_script(sample_script)
            execution = await assistant.execute_script("s1", "prod", "e1")
            assert execution.success is True
            assert execution.script_id == "s1"

        async def test_updates_script_status(
            self, assistant: DatabaseMigrationAssistant, sample_script: MigrationScript
        ) -> None:
            await assistant.create_script(sample_script)
            await assistant.execute_script("s1", "prod", "e1")
            script = await assistant.get_script("s1")
            assert script.status == ScriptStatus.EXECUTED

        async def test_raises_on_missing(self, assistant: DatabaseMigrationAssistant) -> None:
            with pytest.raises(ScriptNotFoundError):
                await assistant.execute_script("nonexistent", "prod", "e1")

    class TestRollbackScript:
        async def test_rolls_back(
            self, assistant: DatabaseMigrationAssistant, sample_script: MigrationScript
        ) -> None:
            await assistant.create_script(sample_script)
            result = await assistant.rollback_script("s1", "prod", reason="issue")
            assert result.status == ScriptStatus.ROLLED_BACK

        async def test_raises_on_missing(self, assistant: DatabaseMigrationAssistant) -> None:
            with pytest.raises(ScriptNotFoundError):
                await assistant.rollback_script("nonexistent", "prod")

    class TestGetExecution:
        async def test_returns_execution(
            self, assistant: DatabaseMigrationAssistant, sample_script: MigrationScript
        ) -> None:
            await assistant.create_script(sample_script)
            await assistant.execute_script("s1", "prod", "e1")
            result = await assistant.get_execution("e1")
            assert result.id == "e1"

    class TestGetStatistics:
        async def test_returns_stats(
            self, assistant: DatabaseMigrationAssistant, sample_script: MigrationScript
        ) -> None:
            await assistant.create_script(sample_script)
            stats = await assistant.get_statistics()
            assert stats["total_scripts"] == 1

    class TestConfig:
        def test_default_config(self) -> None:
            svc = DatabaseMigrationAssistant()
            assert svc.config.require_review is True

        def test_custom_config(self) -> None:
            cfg = DBMigrateConfig(require_review=False)
            svc = DatabaseMigrationAssistant(config=cfg)
            assert svc.config.require_review is False
