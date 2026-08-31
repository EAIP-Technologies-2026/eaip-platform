"""VerificationEngine — artifact and proof verification, tamper detection."""

from __future__ import annotations

import hashlib
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.audit_chain.proof import ProofEngine
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class VerificationReport(BaseModel):
    """Aggregated verification report for a tenant."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str
    total_proofs: int
    verified: int
    tampered: int
    chain_valid: bool
    details: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: str = ""


class VerificationEngine:
    """Verifies artifact integrity, decision/approval/connector proofs, and detects tampering."""

    def __init__(self, proof_engine: ProofEngine) -> None:
        self._proof_engine = proof_engine
        self._log = get_logger("eaip.audit_chain.verification")

    def verify_artifact_integrity(
        self,
        artifact_id: str,
        expected_hash: str,
        actual_content: bytes | str,
    ) -> dict[str, Any]:
        """Verify an artifact matches its expected hash."""
        if isinstance(actual_content, str):
            actual_content = actual_content.encode()
        actual_hash = hashlib.sha256(actual_content).hexdigest()
        valid = actual_hash == expected_hash
        return {"artifact_id": artifact_id, "valid": valid, "expected_hash": expected_hash, "actual_hash": actual_hash}

    def verify_decision_proof(self, tenant_id: str, decision_id: str) -> dict[str, Any]:
        """Verify proofs associated with a decision execution."""
        proofs = self._proof_engine.get_execution_proofs(tenant_id, decision_id)
        if not proofs:
            return {"decision_id": decision_id, "verified": False, "reason": "no proofs found"}
        results = [self._proof_engine.verify_proof(tenant_id, p.proof_id) for p in proofs]
        all_valid = all(r.valid for r in results)
        return {
            "decision_id": decision_id,
            "verified": all_valid,
            "proof_count": len(proofs),
            "results": [{"proof_id": r.proof_id, "valid": r.valid} for r in results],
        }

    def verify_approval_proof(self, tenant_id: str, approval_id: str) -> dict[str, Any]:
        """Verify proofs associated with an approval."""
        proofs = self._proof_engine.get_execution_proofs(tenant_id, approval_id)
        if not proofs:
            return {"approval_id": approval_id, "verified": False, "reason": "no proofs found"}
        results = [self._proof_engine.verify_proof(tenant_id, p.proof_id) for p in proofs]
        all_valid = all(r.valid for r in results)
        return {
            "approval_id": approval_id,
            "verified": all_valid,
            "proof_count": len(proofs),
            "results": [{"proof_id": r.proof_id, "valid": r.valid} for r in results],
        }

    def verify_connector_action_proof(self, tenant_id: str, connector_action_id: str) -> dict[str, Any]:
        """Verify proofs associated with a connector action."""
        proofs = self._proof_engine.get_execution_proofs(tenant_id, connector_action_id)
        if not proofs:
            return {"connector_action_id": connector_action_id, "verified": False, "reason": "no proofs found"}
        results = [self._proof_engine.verify_proof(tenant_id, p.proof_id) for p in proofs]
        all_valid = all(r.valid for r in results)
        return {
            "connector_action_id": connector_action_id,
            "verified": all_valid,
            "proof_count": len(proofs),
        }

    def detect_tampering(self, tenant_id: str) -> list[dict[str, Any]]:
        """Detect any tampered proofs in the tenant's chain."""
        tampered: list[dict[str, Any]] = []
        chain_result = self._proof_engine.verify_chain(tenant_id)
        if chain_result.get("valid"):
            return tampered
        broken_at = chain_result.get("broken_at")
        tampered_at = chain_result.get("tampered_at")
        if broken_at:
            tampered.append({"proof_id": broken_at, "type": "chain_break"})
        if tampered_at:
            tampered.append({"proof_id": tampered_at, "type": "hash_mismatch"})
        return tampered

    def get_verification_report(self, tenant_id: str) -> VerificationReport:
        """Generate a full verification report for a tenant."""
        chain_result = self._proof_engine.verify_chain(tenant_id)
        proofs = self._proof_engine._by_tenant.get(tenant_id, [])
        verified = 0
        tampered_count = 0
        details: list[dict[str, Any]] = []
        for p in proofs:
            result = self._proof_engine.verify_proof(tenant_id, p.proof_id)
            if result.valid:
                verified += 1
            else:
                tampered_count += 1
            details.append({"proof_id": p.proof_id, "valid": result.valid})
        return VerificationReport(
            tenant_id=tenant_id,
            total_proofs=len(proofs),
            verified=verified,
            tampered=tampered_count,
            chain_valid=chain_result.get("valid", False),
            details=details,
            generated_at=utc_now().isoformat(),
        )


__all__ = ["VerificationEngine", "VerificationReport"]
