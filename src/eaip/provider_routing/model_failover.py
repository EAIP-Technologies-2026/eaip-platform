"""Model failover — health-checked fallback with policy enforcement."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.logging.context import get_logger
from eaip.provider_routing.model_registry import ModelRegistry, ModelStatus


class FailoverResult(BaseModel):
    """Result of a failover attempt."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    original_model_id: str
    fallback_model_id: str = ""
    success: bool = False
    reason: str = ""
    chain_position: int = 0


class ModelFailover:
    """Model failover manager.

    primary -> health check -> fallback -> policy check -> route.
    Never fallback to a policy-forbidden model.
    """

    def __init__(self, registry: ModelRegistry) -> None:
        self._registry = registry
        self._failover_chains: dict[str, list[str]] = {}
        self._forbidden_pairs: set[tuple[str, str]] = set()
        self._log = get_logger("eaip.provider_routing.model_failover")

    def set_failover_chain(self, model_id: str, tenant_id: str, chain: list[str]) -> None:
        """Set the failover chain for a model."""
        key = f"{tenant_id}:{model_id}"
        self._failover_chains[key] = chain

    def get_failover_chain(self, model_id: str, tenant_id: str) -> list[str]:
        """Get the failover chain for a model."""
        return self._failover_chains.get(f"{tenant_id}:{model_id}", [])

    def forbid_fallback(self, from_model: str, to_model: str) -> None:
        """Mark a model pair as forbidden for failover."""
        self._forbidden_pairs.add((from_model, to_model))

    def check_failover_allowed(self, from_model: str, to_model: str, tenant_id: str) -> bool:
        """Check if failover from one model to another is allowed by policy."""
        if (from_model, to_model) in self._forbidden_pairs:
            return False
        target = self._registry.get_model(to_model, tenant_id)
        if target is None:
            return False
        if target.status == ModelStatus.UNAVAILABLE:
            return False
        return True

    async def failover(
        self, model_id: str, tenant_id: str, error: str = ""
    ) -> FailoverResult:
        """Attempt failover to next available model in chain."""
        chain = self.get_failover_chain(model_id, tenant_id)
        if not chain:
            self._log.warning("failover.no_chain", model_id=model_id)
            return FailoverResult(
                original_model_id=model_id,
                reason="No failover chain defined",
            )

        for i, candidate_id in enumerate(chain):
            if not self.check_failover_allowed(model_id, candidate_id, tenant_id):
                self._log.info(
                    "failover.forbidden",
                    from_model=model_id,
                    to_model=candidate_id,
                )
                continue

            candidate = self._registry.get_model(candidate_id, tenant_id)
            if candidate is None:
                continue
            if candidate.status in (ModelStatus.UNAVAILABLE, ModelStatus.DEPRECATED):
                continue

            self._log.info(
                "failover.success",
                from_model=model_id,
                to_model=candidate_id,
                position=i,
            )
            return FailoverResult(
                original_model_id=model_id,
                fallback_model_id=candidate_id,
                success=True,
                reason=f"Failover to {candidate_id} after {error}",
                chain_position=i,
            )

        return FailoverResult(
            original_model_id=model_id,
            reason="All fallback models exhausted or forbidden",
        )


__all__ = ["FailoverResult", "ModelFailover"]
