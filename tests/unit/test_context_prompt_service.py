from __future__ import annotations

import pytest

from eaip.context.exceptions import PromptNotFoundError
from eaip.context.prompt_service import PromptService
from eaip.context.registry import PromptRegistry


class TestPromptService:
    @pytest.fixture
    def service(self) -> PromptService:
        return PromptService(PromptRegistry())

    def test_create_and_get_prompt(self, service: PromptService) -> None:
        service.create_prompt("p1", "greeting", "Hello {name}!")
        result = service.get_prompt("p1")
        assert result.name == "greeting"
        assert result.content == "Hello {name}!"

    def test_get_nonexistent_raises(self, service: PromptService) -> None:
        with pytest.raises(PromptNotFoundError):
            service.get_prompt("nonexistent")

    def test_list_prompts(self, service: PromptService) -> None:
        service.create_prompt("p1", "a", "content a")
        service.create_prompt("p2", "b", "content b")
        prompts = service.list_prompts()
        assert len(prompts) == 2

    def test_add_version(self, service: PromptService) -> None:
        service.create_prompt("p1", "test", "v1")
        result = service.add_version("p1", "v2 content", change_log="updated")
        assert result is not None
        versions = service.list_versions("p1")
        assert len(versions) == 2

    def test_compare_versions(self, service: PromptService) -> None:
        service.create_prompt("p1", "test", "original content")
        service.add_version("p1", "updated content")
        versions = service.list_versions("p1")
        v1 = versions[0]
        v2 = versions[1]
        result = service.compare_versions("p1", v1.version, v2.version)
        assert result["content_changed"] is True
        assert result["prompt_id"] == "p1"

    def test_rollback(self, service: PromptService) -> None:
        service.create_prompt("p1", "test", "original")
        service.add_version("p1", "modified")
        versions = service.list_versions("p1")
        target = versions[0]
        restored = service.rollback("p1", target.version)
        assert restored is not None

    def test_search_prompts(self, service: PromptService) -> None:
        service.create_prompt("p1", "welcome message", "Welcome!")
        service.create_prompt("p2", "farewell", "Goodbye!")
        results = service.search_prompts("welcome")
        assert len(results) == 1
        assert results[0].template_id == "p1"

    def test_get_version(self, service: PromptService) -> None:
        service.create_prompt("p1", "test", "original")
        service.add_version("p1", "v2")
        version = service.get_version("p1", "1.0.0")
        assert version.content == "original"
