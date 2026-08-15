"""Declarative Skill Registry for EAIP Conductor (Phase 4)."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from eaip.copilot.skills.models import ConductorSkill

logger = logging.getLogger("eaip.copilot.skills.registry")


class SkillRegistry:
    """Registry managing enterprise Conductor skills."""

    def __init__(self) -> None:
        """Initialize the skill registry."""
        self._skills: dict[str, ConductorSkill] = {}

    def register(self, skill: ConductorSkill) -> None:
        """Register a new enterprise skill definition."""
        if not self.validate(skill):
            raise ValueError(f"Invalid skill definition: {skill.id}")
        self._skills[skill.id] = skill
        logger.info("Registered skill %s v%s", skill.id, skill.version)

    def get(self, skill_id: str) -> ConductorSkill | None:
        """Retrieve a registered skill by ID."""
        return self._skills.get(skill_id)

    def list_skills(self, category: str | None = None) -> Sequence[ConductorSkill]:
        """List registered skills, optionally filtered by category."""
        results = list(self._skills.values())
        if category:
            results = [s for s in results if s.category.upper() == category.upper()]
        return results

    def resolve(self, intent: str) -> ConductorSkill | None:
        """Resolve user intent text to a matching skill."""
        intent_lower = intent.lower()
        for skill in self._skills.values():
            if skill.id in intent_lower or skill.name.lower() in intent_lower:
                return skill
            # Check key phrases
            for tool in skill.allowed_tools:
                if tool.replace("_", " ") in intent_lower:
                    return skill
        return None

    def validate(self, skill: ConductorSkill) -> bool:
        """Validate skill schema and metadata constraints."""
        return bool(skill.id and skill.name and skill.description)
