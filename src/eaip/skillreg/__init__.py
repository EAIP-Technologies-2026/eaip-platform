"""Agent Skill Registry — register, discover, and match agent skills."""

from __future__ import annotations

from eaip.skillreg.events import (
    SkillDeprecated,
    SkillMatched,
    SkillRegistered,
    SkillUpdated,
)
from eaip.skillreg.exceptions import (
    SkillNotFoundError,
    SkillRegistryError,
)
from eaip.skillreg.health import SkillRegistryHealthCheck
from eaip.skillreg.integration import SkillRegistryRuntimeModule
from eaip.skillreg.models import (
    SkillCategory,
    SkillDefinition,
    SkillMatch,
    SkillRegistryConfig,
    SkillRequirement,
)
from eaip.skillreg.registry import SkillRegistry

__all__ = [
    "SkillCategory",
    "SkillDefinition",
    "SkillDeprecated",
    "SkillMatch",
    "SkillMatched",
    "SkillNotFoundError",
    "SkillRegistered",
    "SkillRegistry",
    "SkillRegistryConfig",
    "SkillRegistryError",
    "SkillRegistryHealthCheck",
    "SkillRegistryRuntimeModule",
    "SkillRequirement",
    "SkillUpdated",
]
