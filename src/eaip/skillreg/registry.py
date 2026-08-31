"""SkillRegistry — register, discover, and match agent skills."""

from __future__ import annotations

from eaip.logging.context import get_logger
from eaip.skillreg.events import SkillDeprecated, SkillMatched, SkillRegistered, SkillUpdated
from eaip.skillreg.exceptions import SkillNotFoundError
from eaip.skillreg.models import (
    SkillCategory,
    SkillDefinition,
    SkillMatch,
    SkillRegistryConfig,
)


class SkillRegistry:
    def __init__(self, config: SkillRegistryConfig | None = None) -> None:
        self._config = config or SkillRegistryConfig()
        self._skills: dict[str, SkillDefinition] = {}
        self._log = get_logger("eaip.skillreg.registry")

    @property
    def config(self) -> SkillRegistryConfig:
        return self._config

    async def register_skill(self, skill: SkillDefinition) -> SkillDefinition:
        self._skills[skill.id] = skill
        SkillRegistered(skill_id=skill.id, name=skill.name, category=skill.category.value)
        self._log.info("skillreg.skill.registered", skill_id=skill.id, name=skill.name)
        return skill

    async def get_skill(self, skill_id: str) -> SkillDefinition:
        skill = self._skills.get(skill_id)
        if skill is None:
            raise SkillNotFoundError(f"Skill '{skill_id}' not found")
        return skill

    async def list_skills(self) -> list[SkillDefinition]:
        return list(self._skills.values())

    async def search_skills(
        self, query: str, category: SkillCategory | None = None
    ) -> list[SkillDefinition]:
        results: list[SkillDefinition] = []
        for skill in self._skills.values():
            if skill.deprecated:
                continue
            if category is not None and skill.category != category:
                continue
            if (
                query.lower() in skill.name.lower()
                or query.lower() in skill.description.lower()
                or any(query.lower() in tag.lower() for tag in skill.tags)
            ):
                results.append(skill)
        results.sort(key=lambda s: s.name)
        return results[: self._config.max_results]

    async def find_matching_skills(self, requirements: list[str]) -> list[SkillMatch]:
        matches: list[SkillMatch] = []
        for skill in self._skills.values():
            if skill.deprecated:
                continue
            matched = sum(
                1
                for req in requirements
                if req.lower() in skill.name.lower() or req.lower() in skill.description.lower()
            )
            if matched > 0:
                score = min(matched / len(requirements), 1.0)
                if score >= self._config.min_score:
                    matches.append(SkillMatch(skill_id=skill.id, score=score, confidence=score))
        matches.sort(key=lambda m: m.score, reverse=True)
        matches = matches[: self._config.max_results]
        SkillMatched(
            query=", ".join(requirements),
            results=tuple(m.model_dump() for m in matches),
        )
        return matches

    async def update_skill(self, skill_id: str, **updates: str) -> SkillDefinition:
        skill = await self.get_skill(skill_id)
        updated = skill.model_copy(update=updates, deep=True)
        self._skills[skill_id] = updated
        SkillUpdated(skill_id=skill_id, changes=updates)
        self._log.info("skillreg.skill.updated", skill_id=skill_id)
        return updated

    async def deprecate_skill(self, skill_id: str) -> SkillDefinition:
        skill = await self.get_skill(skill_id)
        updated = skill.model_copy(update={"deprecated": True}, deep=True)
        self._skills[skill_id] = updated
        SkillDeprecated(skill_id=skill_id)
        self._log.info("skillreg.skill.deprecated", skill_id=skill_id)
        return updated


__all__ = ["SkillRegistry"]
