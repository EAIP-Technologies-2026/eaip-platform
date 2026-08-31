"""ReplayEngine — safe, idempotent replay of past executions."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.audit_chain.proof import ProofEngine
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class ReplayStep(BaseModel):
    """A single step in a replay log."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    step_id: str
    step_type: str
    description: str
    proof_id: str = ""
    simulated: bool = True
    timestamp: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class ReplayResult(BaseModel):
    """Result of a replay operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    replay_id: str
    execution_id: str
    steps: tuple[ReplayStep, ...] = ()
    success: bool = True
    mode: str = "simulated"
    idempotency_key: str = ""


class ReplayEngine:
    """Replays executions in safe/simulated mode.

    Never duplicates irreversible production actions.
    Uses idempotency keys to prevent re-execution.
    """

    def __init__(self, proof_engine: ProofEngine) -> None:
        self._proof_engine = proof_engine
        self._replay_logs: dict[str, ReplayResult] = {}
        self._idempotency_keys: set[str] = set()
        self._log = get_logger("eaip.audit_chain.replay")

    def replay_execution(
        self,
        tenant_id: str,
        execution_id: str,
    ) -> ReplayResult:
        """Replay an execution step-by-step in simulated mode.

        Never duplicates irreversible production actions.
        """
        idempotency_key = f"replay:{tenant_id}:{execution_id}"
        if idempotency_key in self._idempotency_keys:
            existing = self._find_existing_replay(tenant_id, execution_id)
            if existing:
                return existing

        proofs = self._proof_engine.get_execution_proofs(tenant_id, execution_id)
        replay_id = f"replay-{uuid.uuid4().hex[:10]}"
        steps: list[ReplayStep] = []

        for i, proof in enumerate(proofs):
            step = ReplayStep(
                step_id=f"step-{i}",
                step_type="proof_verification",
                description=f"Verifying proof {proof.proof_id} for execution {execution_id}",
                proof_id=proof.proof_id,
                simulated=True,
                timestamp=utc_now().isoformat(),
                details={
                    "intent_hash": proof.intent_hash,
                    "context_hash": proof.context_hash,
                    "policy_hash": proof.policy_hash,
                    "model_hash": proof.model_hash,
                    "tool_hash": proof.tool_hash,
                    "input_hash": proof.input_hash,
                    "output_hash": proof.output_hash,
                    "chain_index": proof.chain_index,
                },
            )
            steps.append(step)

        verification = self._proof_engine.verify_chain(tenant_id)
        summary_step = ReplayStep(
            step_id=f"step-{len(steps)}",
            step_type="chain_verification",
            description="Full chain integrity verification",
            simulated=True,
            timestamp=utc_now().isoformat(),
            details={"chain_valid": verification.get("valid", False), "proof_count": verification.get("count", 0)},
        )
        steps.append(summary_step)

        result = ReplayResult(
            replay_id=replay_id,
            execution_id=execution_id,
            steps=tuple(steps),
            success=verification.get("valid", False),
            mode="simulated",
            idempotency_key=idempotency_key,
        )
        self._replay_logs[replay_id] = result
        self._idempotency_keys.add(idempotency_key)
        self._log.info("replay.execution", replay_id=replay_id, execution_id=execution_id, steps=len(steps))
        return result

    def replay_decision(
        self,
        tenant_id: str,
        decision_id: str,
    ) -> ReplayResult:
        """Reconstruct the context of a past decision."""
        return self.replay_execution(tenant_id, decision_id)

    def get_replay_log(self, replay_id: str) -> ReplayResult | None:
        return self._replay_logs.get(replay_id)

    def _find_existing_replay(self, tenant_id: str, execution_id: str) -> ReplayResult | None:
        for r in self._replay_logs.values():
            if r.execution_id == execution_id and r.idempotency_key == f"replay:{tenant_id}:{execution_id}":
                return r
        return None


__all__ = ["ReplayEngine", "ReplayResult", "ReplayStep"]
