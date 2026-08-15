"""Enterprise Skill Marketplace models & trust hierarchy for EAIP Conductor (Phase 5)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from eaip.copilot.models import RiskTier
from eaip.copilot.skills.models import ConductorSkill


class TrustLevel(StrEnum):
    """Trust boundary hierarchy for marketplace packages."""

    BUILT_IN = "BUILT_IN"
    FIRST_PARTY = "FIRST_PARTY"
    VERIFIED = "VERIFIED"
    THIRD_PARTY = "THIRD_PARTY"


class PackageStatus(StrEnum):
    """Lifecycle status of a marketplace skill package."""

    AVAILABLE = "AVAILABLE"
    INSTALLED = "INSTALLED"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class SkillPackageManifest(BaseModel):
    """Declarative manifest definition for a marketplace skill package."""

    package_id: str
    name: str
    version: str = "1.0.0"
    publisher: str = "EAIP Enterprise Ecosystem"
    description: str
    trust_level: TrustLevel = TrustLevel.VERIFIED
    status: PackageStatus = PackageStatus.AVAILABLE
    skills: list[ConductorSkill] = Field(default_factory=list)
    tool_dependencies: list[str] = Field(default_factory=list)
    platform_compatibility: str = ">=0.0.1"
    required_permissions: list[str] = Field(default_factory=list)
    risk_level: RiskTier = RiskTier.INFORMATIONAL
    documentation_url: str | None = None
