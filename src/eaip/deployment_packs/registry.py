"""M7 registries — tenant-isolated, no secrets persisted."""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from eaip.deployment_packs.models import (
    ArtifactType,
    DeploymentConfig,
    DeploymentPack,
    DeploymentValidation,
    LifecycleState,
    MarketplaceArtifact,
    OnboardingSession,
    RiskClass,
    SandboxInstallation,
    TrustState,
)


class ArtifactRegistry:
    def __init__(self) -> None:
        self._store: dict[str, MarketplaceArtifact] = {}
        self._history: dict[str, list[dict[str, Any]]] = {}
        self._signing_secret = "eaip-m7-signing-key"

    def _key(self, tenant_id: str, artifact_id: str) -> str:
        return f"{tenant_id}:{artifact_id}"

    def register(self, artifact: MarketplaceArtifact) -> MarketplaceArtifact:
        if not artifact.signature:
            artifact.signature = artifact.compute_signature(self._signing_secret)
            artifact.trust_state = TrustState.verified
        key = self._key(artifact.tenant_id, artifact.artifact_id)
        self._store[key] = artifact
        self._history.setdefault(artifact.artifact_id, []).append({"version": artifact.version, "artifact_id": artifact.artifact_id})
        return artifact

    def get(self, artifact_id: str, tenant_id: str) -> MarketplaceArtifact | None:
        a = self._store.get(self._key(tenant_id, artifact_id))
        if a:
            return a
        # global scope fallback
        return self._store.get(self._key("global", artifact_id))

    def list_for_tenant(self, tenant_id: str, artifact_type: str | None = None) -> list[MarketplaceArtifact]:
        results = [v for k, v in self._store.items() if k.startswith(f"{tenant_id}:") or k.startswith("global:")]
        if artifact_type:
            results = [r for r in results if r.artifact_type.value == artifact_type]
        return results

    def search(self, tenant_id: str, query: str = "", artifact_type: str | None = None) -> list[MarketplaceArtifact]:
        results = self.list_for_tenant(tenant_id, artifact_type)
        if query:
            q = query.lower()
            results = [r for r in results if q in r.name.lower() or q in r.description.lower()]
        return results

    def update_lifecycle(self, artifact_id: str, tenant_id: str, state: LifecycleState) -> MarketplaceArtifact | None:
        a = self.get(artifact_id, tenant_id)
        if not a:
            return None
        updated = a.model_copy(update={"lifecycle_state": state})
        self._store[self._key(a.tenant_id, artifact_id)] = updated
        return updated

    def verify(self, artifact_id: str, tenant_id: str) -> dict[str, Any]:
        a = self.get(artifact_id, tenant_id)
        if not a:
            return {"verified": False, "reason": "not found"}
        if a.lifecycle_state == LifecycleState.revoked:
            return {"verified": False, "reason": "revoked", "trust_state": TrustState.revoked.value}
        if not a.verify_signature(self._signing_secret):
            return {"verified": False, "reason": "invalid signature", "trust_state": TrustState.invalid_signature.value}
        return {"verified": True, "trust_state": a.trust_state.value, "signature": a.signature}

    def version_history(self, artifact_id: str) -> list[dict[str, Any]]:
        return self._history.get(artifact_id, [])


class DeploymentPackRegistry:
    def __init__(self) -> None:
        self._store: dict[str, DeploymentPack] = {}

    def _key(self, tenant_id: str, pack_id: str) -> str:
        return f"{tenant_id}:{pack_id}"

    def create(self, pack: DeploymentPack) -> DeploymentPack:
        self._store[self._key(pack.tenant_id, pack.pack_id)] = pack
        return pack

    def get(self, pack_id: str, tenant_id: str) -> DeploymentPack | None:
        return self._store.get(self._key(tenant_id, pack_id))

    def list_for_tenant(self, tenant_id: str) -> list[DeploymentPack]:
        return [v for k, v in self._store.items() if k.startswith(f"{tenant_id}:")]

    def delete(self, pack_id: str, tenant_id: str) -> bool:
        return self._store.pop(self._key(tenant_id, pack_id), None) is not None


class SandboxRegistry:
    def __init__(self) -> None:
        self._store: dict[str, SandboxInstallation] = {}

    def create(self, inst: SandboxInstallation) -> SandboxInstallation:
        self._store[inst.installation_id] = inst
        return inst

    def get(self, installation_id: str) -> SandboxInstallation | None:
        return self._store.get(installation_id)

    def list_for_tenant(self, tenant_id: str) -> list[SandboxInstallation]:
        return [v for v in self._store.values() if v.tenant_id == tenant_id]

    def update(self, inst: SandboxInstallation) -> SandboxInstallation:
        self._store[inst.installation_id] = inst
        return inst


class DeploymentConfigRegistry:
    def __init__(self) -> None:
        self._store: dict[str, DeploymentConfig] = {}

    def create(self, cfg: DeploymentConfig) -> DeploymentConfig:
        self._store[cfg.config_id] = cfg
        return cfg

    def get(self, config_id: str, tenant_id: str) -> DeploymentConfig | None:
        c = self._store.get(config_id)
        if c and c.tenant_id == tenant_id:
            return c
        return None

    def list_for_tenant(self, tenant_id: str) -> list[DeploymentConfig]:
        return [v for v in self._store.values() if v.tenant_id == tenant_id]

    def validate(self, config_id: str, tenant_id: str) -> DeploymentValidation:
        cfg = self.get(config_id, tenant_id)
        if not cfg:
            return DeploymentValidation(config_id=config_id, tenant_id=tenant_id, ready=False, status="NOT READY", missing=["config not found"])
        checks: dict[str, Any] = {}
        missing: list[str] = []
        human_required: list[str] = []
        # dependency check
        checks["dependencies"] = "ok" if cfg.deployment_version else "missing version"
        if not cfg.deployment_version:
            missing.append("deployment_version")
        checks["runtime"] = "ok" if cfg.runtime else "missing"
        if not cfg.runtime:
            missing.append("runtime")
        checks["governance"] = "ok" if cfg.governance_policy else "default"
        checks["autonomy"] = "ok" if cfg.autonomy_policy else "default"
        # human infra
        human_required = ["IdP", "secrets vault", "DNS/TLS"] if cfg.environment == "production" else []
        ready = len(missing) == 0
        status = "READY" if ready and not human_required else ("HUMAN CONFIGURATION REQUIRED" if human_required else "NOT READY")
        return DeploymentValidation(config_id=config_id, tenant_id=tenant_id, ready=ready, status=status, checks=checks, missing=missing, human_required=human_required)


class OnboardingRegistry:
    def __init__(self) -> None:
        self._store: dict[str, OnboardingSession] = {}

    def create(self, session: OnboardingSession) -> OnboardingSession:
        self._store[session.session_id] = session
        return session

    def get(self, session_id: str, tenant_id: str) -> OnboardingSession | None:
        s = self._store.get(session_id)
        if s and s.tenant_id == tenant_id:
            return s
        return None

    def list_for_tenant(self, tenant_id: str) -> list[OnboardingSession]:
        return [v for v in self._store.values() if v.tenant_id == tenant_id]

    def advance(self, session_id: str, tenant_id: str, step: str, data: dict[str, Any] | None = None) -> OnboardingSession | None:
        s = self.get(session_id, tenant_id)
        if not s:
            return None
        steps = ["company", "industry", "requirements", "solution_pack", "agents", "workflows", "connectors", "policies", "users", "roles", "simulation", "validation", "activation"]
        try:
            idx = steps.index(s.current_step)
            next_idx = min(idx + 1, len(steps) - 1)
            s.current_step = steps[next_idx]
        except ValueError:
            s.current_step = step
        if data:
            for k, v in data.items():
                if hasattr(s, k):
                    setattr(s, k, v)
        s.progress = int((steps.index(s.current_step) + 1) / len(steps) * 100)
        if s.current_step == "activation":
            s.status = "completed"
        else:
            s.status = "in_progress"
        from datetime import UTC, datetime
        s.updated_at = datetime.now(UTC)
        return s
