"""Tests for the Prompt Registry service."""

from __future__ import annotations

from typing import Any

import pytest

from eaip.prompt_registry.events import (
    PromptApproved,
    PromptArchived,
    PromptCreated,
    PromptDeleted,
    PromptPublished,
    PromptRegistered,
    PromptRejected,
    PromptSearched,
    PromptUnregistered,
    PromptUpdated,
    PromptVersionActivated,
    PromptVersionArchived,
    PromptVersionCompared,
    PromptVersionCreated,
    PromptVersionDeactivated,
    PromptVersionRolledBack,
)
from eaip.prompt_registry.exceptions import (
    PromptApprovalError,
    PromptArchivalError,
    PromptNotFoundError,
    PromptValidationError,
    PromptVersionConflictError,
    PromptVersionNotFoundError,
)
from eaip.prompt_registry.models import (
    PromptApprovalStatus,
    PromptCategory,
    PromptDiffResult,
    PromptStatus,
    PromptVersionStatus,
)
from eaip.prompt_registry.service import PromptRegistryService


@pytest.fixture
def service() -> PromptRegistryService:
    return PromptRegistryService()


@pytest.fixture
async def seeded_service(service: PromptRegistryService) -> PromptRegistryService:
    await service.create_prompt("test-prompt", "A test prompt", category=PromptCategory.AGENT)
    return service


class TestPromptCRUD:
    async def test_create_prompt(self, service: PromptRegistryService) -> None:
        prompt = await service.create_prompt("my-prompt", "My description")
        assert prompt.name == "my-prompt"
        assert prompt.description == "My description"
        assert prompt.status == PromptStatus.DRAFT

    async def test_create_prompt_requires_name(self, service: PromptRegistryService) -> None:
        with pytest.raises(PromptValidationError, match="name is required"):
            await service.create_prompt("")

    async def test_get_prompt(self, seeded_service: PromptRegistryService) -> None:
        all_prompts = await seeded_service.list_prompts()
        prompt = await seeded_service.get_prompt(all_prompts[0].prompt_id)
        assert prompt.name == "test-prompt"

    async def test_get_prompt_not_found(self, service: PromptRegistryService) -> None:
        with pytest.raises(PromptNotFoundError, match="not found"):
            await service.get_prompt("nonexistent")

    async def test_update_prompt_name(self, seeded_service: PromptRegistryService) -> None:
        all_prompts = await seeded_service.list_prompts()
        updated = await seeded_service.update_prompt(
            all_prompts[0].prompt_id,
            name="renamed-prompt",
        )
        assert updated.name == "renamed-prompt"

    async def test_update_prompt_no_changes(self, seeded_service: PromptRegistryService) -> None:
        all_prompts = await seeded_service.list_prompts()
        unchanged = await seeded_service.update_prompt(all_prompts[0].prompt_id)
        assert unchanged.name == "test-prompt"

    async def test_delete_prompt(self, seeded_service: PromptRegistryService) -> None:
        all_prompts = await seeded_service.list_prompts()
        await seeded_service.delete_prompt(all_prompts[0].prompt_id)
        assert await seeded_service.list_prompts() == []

    async def test_delete_prompt_not_found(self, service: PromptRegistryService) -> None:
        with pytest.raises(PromptNotFoundError):
            await service.delete_prompt("nonexistent")

    async def test_list_prompts_by_category(
        self,
        seeded_service: PromptRegistryService,
    ) -> None:
        results = await seeded_service.list_prompts(category=PromptCategory.AGENT)
        assert len(results) == 1
        results = await seeded_service.list_prompts(category=PromptCategory.SYSTEM)
        assert len(results) == 0


class TestVersionManagement:
    async def test_create_version(self, seeded_service: PromptRegistryService) -> None:
        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        pv = await seeded_service.create_version(pid, "1.0.0", "Hello world", author="tester")
        assert pv.version == "1.0.0"
        assert pv.content == "Hello world"
        assert pv.author == "tester"

    async def test_create_version_requires_content(
        self,
        seeded_service: PromptRegistryService,
    ) -> None:
        all_prompts = await seeded_service.list_prompts()
        with pytest.raises(PromptValidationError, match="content is required"):
            await seeded_service.create_version(all_prompts[0].prompt_id, "1.0.0", "")

    async def test_create_version_duplicate(
        self,
        seeded_service: PromptRegistryService,
    ) -> None:
        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        await seeded_service.create_version(pid, "1.0.0", "First")
        with pytest.raises(PromptVersionConflictError):
            await seeded_service.create_version(pid, "1.0.0", "Duplicate")

    async def test_get_version(self, seeded_service: PromptRegistryService) -> None:
        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        await seeded_service.create_version(pid, "1.0.0", "Hello")
        pv = await seeded_service.get_version(pid, "1.0.0")
        assert pv.content == "Hello"

    async def test_get_version_not_found(
        self,
        seeded_service: PromptRegistryService,
    ) -> None:
        all_prompts = await seeded_service.list_prompts()
        with pytest.raises(PromptVersionNotFoundError):
            await seeded_service.get_version(all_prompts[0].prompt_id, "99.99.99")

    async def test_list_versions(self, seeded_service: PromptRegistryService) -> None:
        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        await seeded_service.create_version(pid, "1.0.0", "v1")
        await seeded_service.create_version(pid, "2.0.0", "v2")
        versions = await seeded_service.list_versions(pid)
        assert len(versions) == 2

    async def test_activate_version(self, seeded_service: PromptRegistryService) -> None:
        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        await seeded_service.create_version(pid, "1.0.0", "First")
        activated = await seeded_service.activate_version(pid, "1.0.0")
        assert activated.status == PromptVersionStatus.ACTIVE
        prompt = await seeded_service.get_prompt(pid)
        assert prompt.current_version == "1.0.0"
        assert prompt.status == PromptStatus.ACTIVE

    async def test_deactivate_version(self, seeded_service: PromptRegistryService) -> None:
        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        await seeded_service.create_version(pid, "1.0.0", "First")
        await seeded_service.activate_version(pid, "1.0.0")
        deactivated = await seeded_service.deactivate_version(pid, "1.0.0")
        assert deactivated.status == PromptVersionStatus.DEACTIVATED

    async def test_archive_version(self, seeded_service: PromptRegistryService) -> None:
        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        await seeded_service.create_version(pid, "1.0.0", "First")
        archived = await seeded_service.archive_version(pid, "1.0.0")
        assert archived.status == PromptVersionStatus.ARCHIVED

    async def test_rollback_version(self, seeded_service: PromptRegistryService) -> None:
        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        await seeded_service.create_version(pid, "1.0.0", "v1")
        await seeded_service.create_version(pid, "2.0.0", "v2")
        await seeded_service.activate_version(pid, "2.0.0")
        rolled = await seeded_service.rollback_version(pid, "1.0.0")
        assert rolled.status == PromptVersionStatus.ACTIVE
        prompt = await seeded_service.get_prompt(pid)
        assert prompt.current_version == "1.0.0"

    async def test_compare_versions(self, seeded_service: PromptRegistryService) -> None:
        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        await seeded_service.create_version(pid, "1.0.0", "Hello World")
        await seeded_service.create_version(pid, "2.0.0", "Hello Universe")
        diff = await seeded_service.compare_versions(pid, "1.0.0", "2.0.0")
        assert isinstance(diff, PromptDiffResult)
        assert diff.version_a == "1.0.0"
        assert diff.version_b == "2.0.0"

    async def test_compare_identical_versions(
        self,
        seeded_service: PromptRegistryService,
    ) -> None:
        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        await seeded_service.create_version(pid, "1.0.0", "Same")
        await seeded_service.create_version(pid, "2.0.0", "Same")
        diff = await seeded_service.compare_versions(pid, "1.0.0", "2.0.0")
        assert diff.summary == "no changes"


class TestLifecycle:
    async def test_publish_prompt(self, seeded_service: PromptRegistryService) -> None:
        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        await seeded_service.create_version(pid, "1.0.0", "Content")
        published = await seeded_service.publish_prompt(pid, "1.0.0")
        assert published.status == PromptStatus.ACTIVE
        assert published.current_version == "1.0.0"

    async def test_archive_prompt(self, seeded_service: PromptRegistryService) -> None:
        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        archived = await seeded_service.archive_prompt(pid)
        assert archived.status == PromptStatus.ARCHIVED

    async def test_archive_already_archived(
        self,
        seeded_service: PromptRegistryService,
    ) -> None:
        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        await seeded_service.archive_prompt(pid)
        with pytest.raises(PromptArchivalError, match="already archived"):
            await seeded_service.archive_prompt(pid)

    async def test_approve_prompt(self, seeded_service: PromptRegistryService) -> None:
        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        await seeded_service.create_version(pid, "1.0.0", "Content")
        approved = await seeded_service.approve_prompt(pid, "1.0.0", reviewer="admin")
        assert approved.status == PromptStatus.ACTIVE

    async def test_reject_prompt(self, seeded_service: PromptRegistryService) -> None:
        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        await seeded_service.create_version(pid, "1.0.0", "Content")
        rejected = await seeded_service.reject_prompt(
            pid,
            "1.0.0",
            reviewer="admin",
            reason="Needs work",
        )
        assert rejected.metadata.get("approval_status") == PromptApprovalStatus.REJECTED.value

    async def test_reject_prompt_no_reason(
        self,
        seeded_service: PromptRegistryService,
    ) -> None:
        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        await seeded_service.create_version(pid, "1.0.0", "Content")
        with pytest.raises(PromptApprovalError, match="reason is required"):
            await seeded_service.reject_prompt(pid, "1.0.0", reviewer="admin", reason="")


class TestSearch:
    async def test_search_by_name(self, seeded_service: PromptRegistryService) -> None:
        result = await seeded_service.search_prompts(query="test-prompt")
        assert result.total == 1

    async def test_search_no_match(self, seeded_service: PromptRegistryService) -> None:
        result = await seeded_service.search_prompts(query="nonexistent")
        assert result.total == 0

    async def test_search_with_pagination(
        self,
        seeded_service: PromptRegistryService,
    ) -> None:
        result = await seeded_service.search_prompts(page=1, page_size=10)
        assert result.total >= 1
        assert result.page == 1
        assert result.page_size == 10


class TestEventEmission:
    async def test_create_prompt_emits_events(
        self,
        service: PromptRegistryService,
    ) -> None:
        events: list[Any] = []
        service._event_bus.subscribe(PromptCreated, events.append)
        service._event_bus.subscribe(PromptRegistered, events.append)
        await service.create_prompt("event-test")
        assert any(isinstance(e, PromptCreated) for e in events)
        assert any(isinstance(e, PromptRegistered) for e in events)

    async def test_delete_prompt_emits_events(
        self,
        seeded_service: PromptRegistryService,
    ) -> None:
        events: list[Any] = []
        seeded_service._event_bus.subscribe(PromptDeleted, events.append)
        seeded_service._event_bus.subscribe(PromptUnregistered, events.append)
        all_prompts = await seeded_service.list_prompts()
        await seeded_service.delete_prompt(all_prompts[0].prompt_id)
        assert any(isinstance(e, PromptDeleted) for e in events)
        assert any(isinstance(e, PromptUnregistered) for e in events)

    async def test_version_lifecycle_emits_events(
        self,
        seeded_service: PromptRegistryService,
    ) -> None:
        events: list[Any] = []
        seeded_service._event_bus.subscribe(PromptVersionCreated, events.append)
        seeded_service._event_bus.subscribe(PromptVersionActivated, events.append)
        seeded_service._event_bus.subscribe(PromptVersionDeactivated, events.append)
        seeded_service._event_bus.subscribe(PromptVersionArchived, events.append)
        seeded_service._event_bus.subscribe(PromptVersionRolledBack, events.append)

        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        await seeded_service.create_version(pid, "1.0.0", "v1")
        await seeded_service.create_version(pid, "2.0.0", "v2")
        await seeded_service.activate_version(pid, "2.0.0")
        await seeded_service.archive_version(pid, "1.0.0")
        await seeded_service.rollback_version(pid, "1.0.0")

        assert any(isinstance(e, PromptVersionCreated) for e in events)
        assert any(isinstance(e, PromptVersionActivated) for e in events)
        assert any(isinstance(e, PromptVersionArchived) for e in events)
        assert any(isinstance(e, PromptVersionRolledBack) for e in events)

    async def test_compare_emits_event(
        self,
        seeded_service: PromptRegistryService,
    ) -> None:
        events: list[Any] = []
        seeded_service._event_bus.subscribe(PromptVersionCompared, events.append)
        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        await seeded_service.create_version(pid, "1.0.0", "A")
        await seeded_service.create_version(pid, "2.0.0", "B")
        await seeded_service.compare_versions(pid, "1.0.0", "2.0.0")
        assert any(isinstance(e, PromptVersionCompared) for e in events)

    async def test_search_emits_event(
        self,
        seeded_service: PromptRegistryService,
    ) -> None:
        events: list[Any] = []
        seeded_service._event_bus.subscribe(PromptSearched, events.append)
        await seeded_service.search_prompts(query="test")
        assert any(isinstance(e, PromptSearched) for e in events)

    async def test_publish_approve_reject_emit_events(
        self,
        seeded_service: PromptRegistryService,
    ) -> None:
        events: list[Any] = []
        seeded_service._event_bus.subscribe(PromptPublished, events.append)
        seeded_service._event_bus.subscribe(PromptApproved, events.append)
        seeded_service._event_bus.subscribe(PromptRejected, events.append)
        seeded_service._event_bus.subscribe(PromptArchived, events.append)
        seeded_service._event_bus.subscribe(PromptUpdated, events.append)

        all_prompts = await seeded_service.list_prompts()
        pid = all_prompts[0].prompt_id
        await seeded_service.create_version(pid, "1.0.0", "C")
        await seeded_service.publish_prompt(pid, "1.0.0")
        await seeded_service.approve_prompt(pid, "1.0.0", reviewer="admin")
        await seeded_service.reject_prompt(pid, "1.0.0", reviewer="admin", reason="Reason")
        await seeded_service.archive_prompt(pid)

        assert any(isinstance(e, PromptPublished) for e in events)
        assert any(isinstance(e, PromptApproved) for e in events)
        assert any(isinstance(e, PromptRejected) for e in events)
        assert any(isinstance(e, PromptArchived) for e in events)
