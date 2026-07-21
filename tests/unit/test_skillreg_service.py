"""Tests for SkillRegistry service."""

from __future__ import annotations

import pytest

from eaip.skillreg.exceptions import SkillNotFoundError
from eaip.skillreg.models import (
    SkillCategory,
    SkillDefinition,
    SkillRegistryConfig,
)
from eaip.skillreg.registry import SkillRegistry


class TestSkillRegistry:
    @pytest.fixture
    def registry(self) -> SkillRegistry:
        return SkillRegistry()

    @pytest.fixture
    def nlp_skill(self) -> SkillDefinition:
        return SkillDefinition(
            id="s1",
            name="Text Classifier",
            category=SkillCategory.NLP,
            description="Classifies text into categories",
            tags=("nlp", "text"),
        )

    @pytest.fixture
    def vision_skill(self) -> SkillDefinition:
        return SkillDefinition(
            id="s2",
            name="Image Recognizer",
            category=SkillCategory.VISION,
            description="Recognizes objects in images",
            tags=("vision", "ml"),
        )

    class TestRegisterSkill:
        async def test_register_skill(
            self, registry: SkillRegistry, nlp_skill: SkillDefinition
        ) -> None:
            result = await registry.register_skill(nlp_skill)
            assert result.id == "s1"
            assert result.name == "Text Classifier"

        async def test_list_skills(
            self, registry: SkillRegistry, nlp_skill: SkillDefinition
        ) -> None:
            await registry.register_skill(nlp_skill)
            skills = await registry.list_skills()
            assert len(skills) == 1

    class TestGetSkill:
        async def test_get_skill(self, registry: SkillRegistry, nlp_skill: SkillDefinition) -> None:
            await registry.register_skill(nlp_skill)
            skill = await registry.get_skill("s1")
            assert skill.name == "Text Classifier"

        async def test_get_skill_not_found(self, registry: SkillRegistry) -> None:
            with pytest.raises(SkillNotFoundError):
                await registry.get_skill("nonexistent")

    class TestSearchSkills:
        async def test_search_by_name(
            self, registry: SkillRegistry, nlp_skill: SkillDefinition
        ) -> None:
            await registry.register_skill(nlp_skill)
            results = await registry.search_skills("Text")
            assert len(results) == 1

        async def test_search_by_category(
            self, registry: SkillRegistry, nlp_skill: SkillDefinition, vision_skill: SkillDefinition
        ) -> None:
            await registry.register_skill(nlp_skill)
            await registry.register_skill(vision_skill)
            results = await registry.search_skills("", category=SkillCategory.VISION)
            assert len(results) == 1
            assert results[0].id == "s2"

        async def test_search_no_results(self, registry: SkillRegistry) -> None:
            results = await registry.search_skills("nonexistent")
            assert results == []

    class TestFindMatchingSkills:
        async def test_find_matching(
            self, registry: SkillRegistry, nlp_skill: SkillDefinition
        ) -> None:
            await registry.register_skill(nlp_skill)
            matches = await registry.find_matching_skills(["text", "classify"])
            assert len(matches) == 1
            assert matches[0].skill_id == "s1"
            assert matches[0].score > 0

        async def test_no_matches(self, registry: SkillRegistry) -> None:
            matches = await registry.find_matching_skills(["unknown"])
            assert matches == []

    class TestUpdateSkill:
        async def test_update_name(
            self, registry: SkillRegistry, nlp_skill: SkillDefinition
        ) -> None:
            await registry.register_skill(nlp_skill)
            updated = await registry.update_skill("s1", name="New Name")
            assert updated.name == "New Name"

        async def test_update_not_found(self, registry: SkillRegistry) -> None:
            with pytest.raises(SkillNotFoundError):
                await registry.update_skill("nonexistent", name="X")

    class TestDeprecateSkill:
        async def test_deprecate(self, registry: SkillRegistry, nlp_skill: SkillDefinition) -> None:
            await registry.register_skill(nlp_skill)
            deprecated = await registry.deprecate_skill("s1")
            assert deprecated.deprecated is True

        async def test_deprecated_hidden_from_search(
            self, registry: SkillRegistry, nlp_skill: SkillDefinition
        ) -> None:
            await registry.register_skill(nlp_skill)
            await registry.deprecate_skill("s1")
            results = await registry.search_skills("Text")
            assert len(results) == 0

    class TestConfig:
        def test_default_config(self) -> None:
            r = SkillRegistry()
            assert r.config.max_results == 20
            assert r.config.min_score == 0.0

        def test_custom_config(self) -> None:
            config = SkillRegistryConfig(max_results=10, min_score=0.5)
            r = SkillRegistry(config=config)
            assert r.config.max_results == 10
            assert r.config.min_score == 0.5
