"""Model router — intelligent model selection based on task requirements."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.logging.context import get_logger
from eaip.provider_routing.model_registry import (
    ModelLocality,
    ModelPrivacyLevel,
    ModelRecord,
    ModelRegistry,
    ModelStatus,
)
from eaip.shared.time import utc_now


class TaskRequirements(BaseModel):
    """Requirements for a task that needs model routing."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    task_type: str = ""
    required_capabilities: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    required_modalities: list[str] = Field(default_factory=lambda: ["text"])
    min_context_limit: int = 0
    max_latency_ms: float = 0.0
    max_cost_per_1k: float = 0.0
    min_quality_score: float = 0.0
    data_classification: str = "internal"
    privacy_requirement: str = ""
    preferred_provider: str = ""
    locality_requirement: str = ""


class RoutingDecision(BaseModel):
    """Result of a model routing decision."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    selected_model_id: str
    reason: str
    score: float = 0.0
    alternatives: list[dict[str, Any]] = Field(default_factory=list)
    factors: dict[str, float] = Field(default_factory=dict)
    routed_at: Any = Field(default_factory=utc_now)


DATA_CLASS_TO_PRIVACY = {
    "public": ModelPrivacyLevel.PUBLIC,
    "internal": ModelPrivacyLevel.PRIVATE,
    "confidential": ModelPrivacyLevel.PRIVATE,
    "restricted": ModelPrivacyLevel.PRIVATE,
}

WEIGHT_CAPABILITY = 0.30
WEIGHT_COST = 0.15
WEIGHT_LATENCY = 0.15
WEIGHT_QUALITY = 0.20
WEIGHT_AVAILABILITY = 0.10
WEIGHT_PRIVACY = 0.10


class ModelRouter:
    """Intelligent model router.

    Selects the best model for a task based on capability, cost, latency,
    quality, availability, privacy, and policy constraints.
    """

    def __init__(self, registry: ModelRegistry) -> None:
        self._registry = registry
        self._log = get_logger("eaip.provider_routing.model_router")

    async def route(
        self,
        requirements: TaskRequirements,
        tenant_id: str,
        policy_context: dict[str, Any] | None = None,
    ) -> RoutingDecision:
        """Route a task to the best available model."""
        candidates = self._registry.list_models(tenant_id, status=ModelStatus.ACTIVE)
        if not candidates:
            return RoutingDecision(
                selected_model_id="",
                reason="No active models available for tenant",
            )

        candidates = self._filter_candidates(candidates, requirements)
        if not candidates:
            return RoutingDecision(
                selected_model_id="",
                reason="No models match the task requirements",
            )

        scored = []
        for model in candidates:
            score = self._score_model(model, requirements)
            scored.append((model, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        best_model, best_score = scored[0]

        alternatives = [
            {"model_id": m.id, "score": round(s, 3), "provider": m.provider}
            for m, s in scored[1:4]
        ]

        reason = self._explain_selection(best_model, requirements, best_score)

        self._log.info(
            "model.routed",
            selected_model=best_model.id,
            score=round(best_score, 3),
            tenant_id=tenant_id,
        )

        return RoutingDecision(
            selected_model_id=best_model.id,
            reason=reason,
            score=round(best_score, 3),
            alternatives=alternatives,
            factors={
                "capability": round(self._capability_score(best_model, requirements), 3),
                "cost": round(self._cost_score(best_model, requirements), 3),
                "latency": round(self._latency_score(best_model, requirements), 3),
                "quality": round(best_model.quality_score, 3),
                "availability": round(best_model.availability, 3),
            },
        )

    def _filter_candidates(
        self, models: list[ModelRecord], requirements: TaskRequirements
    ) -> list[ModelRecord]:
        """Filter models that cannot meet requirements."""
        filtered = []
        for model in models:
            if requirements.required_capabilities:
                if not all(c in model.capabilities for c in requirements.required_capabilities):
                    continue
            if requirements.required_tools:
                if not all(t in model.supported_tools for t in requirements.required_tools):
                    continue
            if requirements.min_context_limit and model.context_limit < requirements.min_context_limit:
                continue
            if requirements.privacy_requirement == "private" and model.privacy_level == ModelPrivacyLevel.PUBLIC:
                continue
            if requirements.data_classification in ("confidential", "restricted") and model.privacy_level == ModelPrivacyLevel.PUBLIC:
                continue
            if requirements.locality_requirement and model.locality.value != requirements.locality_requirement:
                continue
            filtered.append(model)
        return filtered

    def _score_model(self, model: ModelRecord, requirements: TaskRequirements) -> float:
        """Score a model against requirements."""
        cap_score = self._capability_score(model, requirements)
        cost_score = self._cost_score(model, requirements)
        lat_score = self._latency_score(model, requirements)
        qual_score = model.quality_score
        avail_score = model.availability
        priv_score = self._privacy_score(model, requirements)
        return (
            WEIGHT_CAPABILITY * cap_score
            + WEIGHT_COST * cost_score
            + WEIGHT_LATENCY * lat_score
            + WEIGHT_QUALITY * qual_score
            + WEIGHT_AVAILABILITY * avail_score
            + WEIGHT_PRIVACY * priv_score
        )

    @staticmethod
    def _capability_score(model: ModelRecord, requirements: TaskRequirements) -> float:
        if not requirements.required_capabilities:
            return 1.0
        matched = sum(1 for c in requirements.required_capabilities if c in model.capabilities)
        return matched / len(requirements.required_capabilities)

    @staticmethod
    def _cost_score(model: ModelRecord, requirements: TaskRequirements) -> float:
        if requirements.max_cost_per_1k and model.cost_per_1k_tokens > 0:
            if model.cost_per_1k_tokens <= requirements.max_cost_per_1k:
                return 1.0 - (model.cost_per_1k_tokens / requirements.max_cost_per_1k * 0.5)
            return 0.0
        return 0.8

    @staticmethod
    def _latency_score(model: ModelRecord, requirements: TaskRequirements) -> float:
        if requirements.max_latency_ms and model.latency_avg_ms > 0:
            if model.latency_avg_ms <= requirements.max_latency_ms:
                return 1.0 - (model.latency_avg_ms / requirements.max_latency_ms * 0.5)
            return 0.0
        return 0.8

    @staticmethod
    def _privacy_score(model: ModelRecord, requirements: TaskRequirements) -> float:
        required = DATA_CLASS_TO_PRIVACY.get(requirements.data_classification, ModelPrivacyLevel.PRIVATE)
        if model.privacy_level == required:
            return 1.0
        if model.privacy_level == ModelPrivacyLevel.HYBRID:
            return 0.7
        if model.privacy_level == ModelPrivacyLevel.PRIVATE:
            return 0.9
        return 0.3

    @staticmethod
    def _explain_selection(model: ModelRecord, requirements: TaskRequirements, score: float) -> str:
        reasons = []
        if requirements.required_capabilities:
            reasons.append(f"capabilities={model.capabilities}")
        if requirements.data_classification in ("confidential", "restricted"):
            reasons.append(f"privacy={model.privacy_level.value}")
        if requirements.max_cost_per_1k:
            reasons.append(f"cost={model.cost_per_1k_tokens}/1k")
        reasons.append(f"quality={model.quality_score}")
        return f"Selected {model.provider}/{model.model_name} (score={score:.3f}): {', '.join(reasons)}"


__all__ = ["ModelRouter", "RoutingDecision", "TaskRequirements"]
