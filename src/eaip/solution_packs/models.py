from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class SolutionPackIndustry(StrEnum):
    healthcare = "healthcare"
    financial = "financial"
    consultancy = "consultancy"
    manufacturing = "manufacturing"
    retail = "retail"


class SolutionPackStatus(StrEnum):
    draft = "draft"
    published = "published"
    installed = "installed"


class SolutionPackDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    pack_id: str
    industry: SolutionPackIndustry
    name: str
    description: str = ""
    version: str = "1.0.0"
    agents: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    workflows: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    missions: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    knowledge_collections: tuple[str, ...] = Field(default_factory=tuple)
    policies: tuple[str, ...] = Field(default_factory=tuple)
    dashboards: tuple[str, ...] = Field(default_factory=tuple)
    kpis: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    simulation_scenarios: tuple[str, ...] = Field(default_factory=tuple)
    marketplace_integrations: tuple[str, ...] = Field(default_factory=tuple)
    recommended_schedules: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    role_templates: tuple[str, ...] = Field(default_factory=tuple)
    permissions: tuple[str, ...] = Field(default_factory=tuple)
    status: SolutionPackStatus = SolutionPackStatus.published
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SolutionPackInstallation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    installation_id: str
    pack_id: str
    tenant_id: str
    industry: SolutionPackIndustry
    status: str = "installed"
    installed_at: datetime = Field(default_factory=utc_now)
    config: dict[str, Any] = Field(default_factory=dict)
