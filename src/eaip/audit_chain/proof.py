"""ExecutionProof model and ProofEngine — verifiable execution audit."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.audit_chain.chain import AuditChain
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class ExecutionProof(BaseModel):
    """Cryptographic proof of an execution step."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    proof_id: str
    tenant_id: str
    execution_id: str
    intent_hash: str = ""
    context_hash: str = ""
    policy_hash: str = ""
    model_hash: str = ""
    tool_hash: str = ""
    connector_hash: str = ""
    input_hash: str = ""
    output_hash: str = ""
    timestamp: str = ""
    previous_hash: str = ""
    current_hash: str = ""
    chain_index: int = 0


class VerificationResult(BaseModel):
    """Result of verifying a proof."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    proof_id: str
    valid: bool
    details: dict[str, Any] = Field(default_factory=dict)


def _hash_payload(payload: str) -> str:
    return hashlib.sha256(payload.encode()).hexdigest()


def _sanitize_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Remove secrets from data before hashing."""
    secret_keys = {"secret", "password", "token", "api_key", "credential", "authorization"}
    return {k: v for k, v in data.items() if not any(s in k.lower() for s in secret_keys)}


class ProofEngine:
    """Generates and verifies execution proofs using SHA-256 hash chains.

    Never includes secrets in hashed payloads.
    """

    def __init__(self, audit_chain: AuditChain | None = None) -> None:
        self._chain = audit_chain or AuditChain()
        self._proofs: dict[str, ExecutionProof] = {}
        self._by_execution: dict[str, list[ExecutionProof]] = {}
        self._by_tenant: dict[str, list[ExecutionProof]] = {}
        self._log = get_logger("eaip.audit_chain.proof")

    def generate_proof(
        self,
        tenant_id: str,
        execution_id: str,
        intent: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        policy: dict[str, Any] | None = None,
        model: dict[str, Any] | None = None,
        tool: dict[str, Any] | None = None,
        connector: dict[str, Any] | None = None,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
    ) -> ExecutionProof:
        """Generate a cryptographic proof for an execution."""
        proof_id = f"proof-{uuid.uuid4().hex[:12]}"
        ts = utc_now().isoformat()

        intent_hash = _hash_payload(json.dumps(_sanitize_payload(intent or {}), sort_keys=True))
        context_hash = _hash_payload(json.dumps(_sanitize_payload(context or {}), sort_keys=True))
        policy_hash = _hash_payload(json.dumps(_sanitize_payload(policy or {}), sort_keys=True))
        model_hash = _hash_payload(json.dumps(_sanitize_payload(model or {}), sort_keys=True))
        tool_hash = _hash_payload(json.dumps(_sanitize_payload(tool or {}), sort_keys=True))
        connector_hash = _hash_payload(json.dumps(_sanitize_payload(connector or {}), sort_keys=True))
        input_hash = _hash_payload(json.dumps(_sanitize_payload(inputs or {}), sort_keys=True))
        output_hash = _hash_payload(json.dumps(_sanitize_payload(outputs or {}), sort_keys=True))

        existing = self._by_tenant.get(tenant_id, [])
        previous_hash = existing[-1].current_hash if existing else ""
        chain_index = len(existing)

        current_hash = _hash_payload(
            f"{proof_id}|{tenant_id}|{execution_id}|{intent_hash}|{context_hash}|"
            f"{policy_hash}|{model_hash}|{tool_hash}|{connector_hash}|"
            f"{input_hash}|{output_hash}|{ts}|{previous_hash}|{chain_index}"
        )

        proof = ExecutionProof(
            proof_id=proof_id,
            tenant_id=tenant_id,
            execution_id=execution_id,
            intent_hash=intent_hash,
            context_hash=context_hash,
            policy_hash=policy_hash,
            model_hash=model_hash,
            tool_hash=tool_hash,
            connector_hash=connector_hash,
            input_hash=input_hash,
            output_hash=output_hash,
            timestamp=ts,
            previous_hash=previous_hash,
            current_hash=current_hash,
            chain_index=chain_index,
        )

        self._proofs[proof_id] = proof
        self._by_execution.setdefault(tenant_id, {}).setdefault(execution_id, []).append(proof)
        self._by_tenant.setdefault(tenant_id, []).append(proof)

        self._chain.append(
            tenant_id=tenant_id,
            actor="proof_engine",
            action=f"proof:{proof_id}",
            metadata={"execution_id": execution_id, "proof_id": proof_id, "current_hash": current_hash},
        )

        self._log.info("proof.generated", proof_id=proof_id, execution_id=execution_id)
        return proof

    def verify_proof(self, tenant_id: str, proof_id: str) -> VerificationResult:
        """Verify a single proof's integrity."""
        proof = self._proofs.get(proof_id)
        if proof is None or proof.tenant_id != tenant_id:
            return VerificationResult(proof_id=proof_id, valid=False, details={"reason": "not found"})

        expected_hash = _hash_payload(
            f"{proof.proof_id}|{proof.tenant_id}|{proof.execution_id}|{proof.intent_hash}|"
            f"{proof.context_hash}|{proof.policy_hash}|{proof.model_hash}|{proof.tool_hash}|"
            f"{proof.connector_hash}|{proof.input_hash}|{proof.output_hash}|"
            f"{proof.timestamp}|{proof.previous_hash}|{proof.chain_index}"
        )
        valid = proof.current_hash == expected_hash
        return VerificationResult(
            proof_id=proof_id,
            valid=valid,
            details={"expected_hash": expected_hash, "actual_hash": proof.current_hash},
        )

    def verify_chain(self, tenant_id: str) -> dict[str, Any]:
        """Verify the full proof chain integrity for a tenant."""
        proofs = self._by_tenant.get(tenant_id, [])
        if not proofs:
            return {"valid": True, "count": 0}
        for i, proof in enumerate(proofs):
            expected_prev = proofs[i - 1].current_hash if i > 0 else ""
            if proof.previous_hash != expected_prev:
                return {"valid": False, "count": len(proofs), "broken_at": proof.proof_id}
            result = self.verify_proof(tenant_id, proof.proof_id)
            if not result.valid:
                return {"valid": False, "count": len(proofs), "tampered_at": proof.proof_id}
        return {"valid": True, "count": len(proofs)}

    def get_proof(self, proof_id: str) -> ExecutionProof | None:
        return self._proofs.get(proof_id)

    def get_execution_proofs(self, tenant_id: str, execution_id: str) -> list[ExecutionProof]:
        return self._by_execution.get(tenant_id, {}).get(execution_id, [])

    def inspect_execution(self, tenant_id: str, execution_id: str) -> dict[str, Any]:
        """Human-readable breakdown of execution proofs."""
        proofs = self.get_execution_proofs(tenant_id, execution_id)
        if not proofs:
            return {"execution_id": execution_id, "proofs": [], "count": 0}
        return {
            "execution_id": execution_id,
            "count": len(proofs),
            "proofs": [
                {
                    "proof_id": p.proof_id,
                    "intent_hash": p.intent_hash,
                    "context_hash": p.context_hash,
                    "policy_hash": p.policy_hash,
                    "model_hash": p.model_hash,
                    "tool_hash": p.tool_hash,
                    "input_hash": p.input_hash,
                    "output_hash": p.output_hash,
                    "timestamp": p.timestamp,
                    "chain_index": p.chain_index,
                }
                for p in proofs
            ],
        }


__all__ = ["ExecutionProof", "ProofEngine", "VerificationResult"]
