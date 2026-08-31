"""Model registry — register, discover, and manage AI models."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class ModelStatus(StrEnum):
    """Model operational status."""

    ACTIVE = "active"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


class ModelPrivacyLevel(StrEnum):
    """Model privacy levels."""

    PUBLIC = "public"
    PRIVATE = "private"
    HYBRID = "hybrid"


class ModelLocality(StrEnum):
    """Model locality."""

    CLOUD = "cloud"
    ON_PREMISE = "on_premise"
    EDGE = "edge"


class ModelRecord(BaseModel):
    """Full model record in the registry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    provider: str
    model_name: str
    version: str = "1.0.0"
    capabilities: list[str] = Field(default_factory=list)
    context_limit: int = 4096
    latency_avg_ms: float = 0.0
    cost_per_1k_tokens: float = 0.0
    quality_score: float = Field(ge=0.0, le=1.0, default=0.8)
    availability: float = Field(ge=0.0, le=1.0, default=1.0)
    privacy_level: ModelPrivacyLevel = ModelPrivacyLevel.PRIVATE
    locality: ModelLocality = ModelLocality.CLOUD
    supported_tools: list[str] = Field(default_factory=list)
    supported_modalities: list[str] = Field(default_factory=lambda: ["text"])
    status: ModelStatus = ModelStatus.ACTIVE
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: Any = Field(default_factory=utc_now)
    updated_at: Any = Field(default_factory=utc_now)


class ModelHealthMetrics(BaseModel):
    """Health metrics for a model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str
    availability: float = Field(ge=0.0, le=1.0, default=1.0)
    latency_p50_ms: float = 0.0
    latency_p99_ms: float = 0.0
    error_rate: float = Field(ge=0.0, le=1.0, default=0.0)
    throughput_rps: float = 0.0
    checked_at: Any = Field(default_factory=utc_now)


class ModelRegistry:
    """Registry for AI model records.

    Tenant-scoped. Every model is registered per-tenant.
    """

    def __init__(self) -> None:
        self._models: dict[str, ModelRecord] = {}
        self._health: dict[str, ModelHealthMetrics] = {}
        self._log = get_logger("eaip.provider_routing.model_registry")

    def _key(self, tenant_id: str, model_id: str) -> str:
        return f"{tenant_id}:{model_id}"

    def register_model(self, model: ModelRecord) -> ModelRecord:
        """Register a model in the registry."""
        key = self._key(model.tenant_id, model.id)
        self._models[key] = model
        self._log.info("model.registered", model_id=model.id, provider=model.provider)
        return model

    def get_model(self, model_id: str, tenant_id: str) -> ModelRecord | None:
        """Get a model by ID."""
        return self._models.get(self._key(tenant_id, model_id))

    def list_models(
        self,
        tenant_id: str,
        *,
        provider: str = "",
        status: ModelStatus | None = None,
        privacy_level: ModelPrivacyLevel | None = None,
        capability: str = "",
    ) -> list[ModelRecord]:
        """List models with optional filters."""
        results = [v for k, v in self._models.items() if k.startswith(f"{tenant_id}:")]
        if provider:
            results = [m for m in results if m.provider == provider]
        if status:
            results = [m for m in results if m.status == status]
        if privacy_level:
            results = [m for m in results if m.privacy_level == privacy_level]
        if capability:
            results = [m for m in results if capability in m.capabilities]
        return results

    def update_model_health(self, model_id: str, tenant_id: str, metrics: ModelHealthMetrics) -> None:
        """Update health metrics for a model."""
        key = self._key(tenant_id, model_id)
        self._health[key] = metrics
        model = self._models.get(key)
        if model and metrics.availability < 0.5:
            updated = model.model_copy(update={"status": ModelStatus.DEGRADED, "updated_at": utc_now()})
            self._models[key] = updated

    def get_model_health(self, model_id: str, tenant_id: str) -> ModelHealthMetrics | None:
        """Get health metrics for a model."""
        return self._health.get(self._key(tenant_id, model_id))

    def get_model_capabilities(self, model_id: str, tenant_id: str) -> dict[str, Any]:
        """Get detailed capabilities for a model."""
        model = self.get_model(model_id, tenant_id)
        if model is None:
            return {}
        return {
            "model_id": model.id,
            "capabilities": model.capabilities,
            "supported_tools": model.supported_tools,
            "supported_modalities": model.supported_modalities,
            "context_limit": model.context_limit,
            "privacy_level": model.privacy_level.value,
            "locality": model.locality.value,
        }

    def remove_model(self, model_id: str, tenant_id: str) -> bool:
        """Remove a model from the registry."""
        key = self._key(tenant_id, model_id)
        self._health.pop(key, None)
        return self._models.pop(key, None) is not None


__all__ = [
    "ModelHealthMetrics",
    "ModelLocality",
    "ModelPrivacyLevel",
    "ModelRecord",
    "ModelRegistry",
    "ModelStatus",
]
