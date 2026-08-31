"""M7 Deployment Packs — EAIP Core → Industry Pack → Deployment Pack → Customer Environment."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    agent = "agent"
    agent_team = "agent_team"
    workflow = "workflow"
    mission = "mission"
    connector = "connector"
    methodology = "methodology"
    industry_pack = "industry_pack"
    solution_pack = "solution_pack"
    simulation_pack = "simulation_pack"
    governance_pack = "governance_pack"
    deployment_pack = "deployment_pack"
    dashboard = "dashboard"
    policy = "policy"
    model_config = "model_config"


class TrustState(str, Enum):
    verified = "verified"
    unverified = "unverified"
    revoked = "revoked"
    invalid_signature = "invalid_signature"
    incompatible = "incompatible"


class LifecycleState(str, Enum):
    draft = "draft"
    published = "published"
    deprecated = "deprecated"
    revoked = "revoked"
    archived = "archived"


class RiskClass(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class MarketplaceArtifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: f"art-{uuid.uuid4().hex[:8]}")
    name: str
    artifact_type: ArtifactType = ArtifactType.agent
    version: str = "1.0.0"
    publisher: str = "eaip"
    tenant_scope: str = "global"
    capabilities: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    compatibility: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    risk_class: RiskClass = RiskClass.low
    signature: str = ""
    trust_state: TrustState = TrustState.unverified
    lifecycle_state: LifecycleState = LifecycleState.draft
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str = "default"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def compute_signature(self, secret: str = "eaip-signing-key") -> str:
        payload = f"{self.artifact_id}:{self.version}:{self.publisher}:{self.name}"
        return hashlib.sha256(f"{payload}:{secret}".encode()).hexdigest()[:32]

    def verify_signature(self, secret: str = "eaip-signing-key") -> bool:
        if not self.signature:
            return False
        expected = self.compute_signature(secret)
        return self.signature == expected


class VersionHistory(BaseModel):
    artifact_id: str
    version: str
    changelog: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    publisher: str = ""
    deprecated: bool = False
    revoked: bool = False


class DeploymentPack(BaseModel):
    pack_id: str = Field(default_factory=lambda: f"dep-{uuid.uuid4().hex[:8]}")
    name: str
    version: str = "1.0.0"
    industry: str = "general"
    base_pack_id: str = ""
    artifacts: list[str] = Field(default_factory=list)
    agents: list[dict[str, Any]] = Field(default_factory=list)
    workflows: list[dict[str, Any]] = Field(default_factory=list)
    missions: list[dict[str, Any]] = Field(default_factory=list)
    policies: list[dict[str, Any]] = Field(default_factory=list)
    connectors: list[dict[str, Any]] = Field(default_factory=list)
    dashboards: list[dict[str, Any]] = Field(default_factory=list)
    kpis: list[dict[str, Any]] = Field(default_factory=list)
    methodologies: list[dict[str, Any]] = Field(default_factory=list)
    simulations: list[dict[str, Any]] = Field(default_factory=list)
    terminology: dict[str, str] = Field(default_factory=dict)
    governance: dict[str, Any] = Field(default_factory=dict)
    onboarding_state: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str = "default"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SandboxInstallation(BaseModel):
    installation_id: str = Field(default_factory=lambda: f"sbox-{uuid.uuid4().hex[:8]}")
    artifact_id: str
    tenant_id: str
    status: str = "pending"
    verified: bool = False
    dependency_check: dict[str, Any] = Field(default_factory=dict)
    security_check: dict[str, Any] = Field(default_factory=dict)
    test_result: dict[str, Any] = Field(default_factory=dict)
    governance_check: dict[str, Any] = Field(default_factory=dict)
    approval_required: bool = False
    installed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DeploymentConfig(BaseModel):
    config_id: str = Field(default_factory=lambda: f"dcfg-{uuid.uuid4().hex[:8]}")
    tenant_id: str
    environment: str = "development"
    region: str = "us-east-1"
    runtime: str = "local-1"
    model_policy: dict[str, Any] = Field(default_factory=dict)
    connector_policy: dict[str, Any] = Field(default_factory=dict)
    autonomy_policy: dict[str, Any] = Field(default_factory=dict)
    governance_policy: dict[str, Any] = Field(default_factory=dict)
    industry_config: dict[str, Any] = Field(default_factory=dict)
    deployment_version: str = "1.0.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DeploymentValidation(BaseModel):
    config_id: str
    tenant_id: str
    ready: bool = False
    status: str = "NOT READY"
    checks: dict[str, Any] = Field(default_factory=dict)
    missing: list[str] = Field(default_factory=list)
    human_required: list[str] = Field(default_factory=list)


class OnboardingSession(BaseModel):
    session_id: str = Field(default_factory=lambda: f"obs-{uuid.uuid4().hex[:8]}")
    tenant_id: str
    company_name: str = ""
    industry: str = ""
    requirements: dict[str, Any] = Field(default_factory=dict)
    solution_pack_id: str = ""
    agents: list[str] = Field(default_factory=list)
    workflows: list[str] = Field(default_factory=list)
    connectors: list[str] = Field(default_factory=list)
    policies: list[str] = Field(default_factory=list)
    users: list[dict[str, Any]] = Field(default_factory=list)
    roles: list[dict[str, Any]] = Field(default_factory=list)
    simulation_id: str = ""
    validation: dict[str, Any] = Field(default_factory=dict)
    status: str = "created"
    current_step: str = "company"
    progress: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
