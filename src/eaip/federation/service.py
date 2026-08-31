from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from eaip.federation.models import FederatedOrg


class FederationService:
    def __init__(self) -> None:
        self._orgs: dict[str, FederatedOrg] = {}
        self._trust: dict[str, dict[str, Any]] = {}  # trust_id -> {from_org, to_org, tenant_id, scopes}
        self._delegations: dict[str, dict[str, Any]] = {}  # delegation_id -> {who, what, purpose, expires_at}
        self._audit: list[dict[str, Any]] = []

    def create_org(self, org_id: str, tenant_id: str, name: str, parent_org_id: str = "", metadata: dict[str, Any] | None = None) -> FederatedOrg:
        if parent_org_id and parent_org_id not in self._orgs:
            raise ValueError(f"parent {parent_org_id!r} not found")
        org = FederatedOrg(org_id=org_id, parent_org_id=parent_org_id, name=name, tenant_id=tenant_id, metadata=metadata or {})
        self._orgs[org_id] = org
        return org

    def get(self, org_id: str) -> FederatedOrg | None:
        return self._orgs.get(org_id)

    def children_of(self, parent_org_id: str) -> list[FederatedOrg]:
        return [v for v in self._orgs.values() if v.parent_org_id == parent_org_id]

    def list_for_tenant(self, tenant_id: str) -> list[FederatedOrg]:
        return [v for v in self._orgs.values() if v.tenant_id == tenant_id]

    def create_trust(self, from_org: str, to_org: str, tenant_id: str, scopes: list[str] | None = None) -> dict[str, Any]:
        tid = f"trust-{uuid.uuid4().hex[:8]}"
        rec = {"trust_id": tid, "from_org": from_org, "to_org": to_org, "tenant_id": tenant_id, "scopes": scopes or ["read"], "created_at": datetime.now(UTC).isoformat()}
        self._trust[tid] = rec
        self._audit.append({"type": "trust_created", "trust_id": tid, "tenant_id": tenant_id})
        return rec

    def list_trusts(self, tenant_id: str) -> list[dict[str, Any]]:
        return [v for v in self._trust.values() if v["tenant_id"] == tenant_id]

    def create_delegation(self, who: str, what: str, purpose: str, tenant_id: str, ttl_seconds: int = 3600) -> dict[str, Any]:
        did = f"del-{uuid.uuid4().hex[:8]}"
        expires = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        rec = {"delegation_id": did, "who": who, "what": what, "purpose": purpose, "tenant_id": tenant_id, "expires_at": expires.isoformat(), "created_at": datetime.now(UTC).isoformat()}
        self._delegations[did] = rec
        self._audit.append({"type": "delegation_created", "delegation_id": did, "tenant_id": tenant_id})
        return rec

    def check_delegation(self, delegation_id: str) -> dict[str, Any]:
        rec = self._delegations.get(delegation_id)
        if not rec:
            return {"valid": False, "reason": "not found"}
        try:
            exp = datetime.fromisoformat(rec["expires_at"])
            if datetime.now(UTC) > exp:
                return {"valid": False, "reason": "expired"}
        except Exception:
            pass
        return {"valid": True, "delegation": rec}

    def list_delegations(self, tenant_id: str) -> list[dict[str, Any]]:
        return [v for v in self._delegations.values() if v["tenant_id"] == tenant_id]

    def audit_log(self, tenant_id: str) -> list[dict[str, Any]]:
        return [e for e in self._audit if e.get("tenant_id") == tenant_id]

    def can_access(self, requester_org_id: str, target_org_id: str) -> bool:
        if requester_org_id == target_org_id:
            return True
        # explicit trust grants access
        for t in self._trust.values():
            if t["from_org"] == requester_org_id and t["to_org"] == target_org_id:
                return True
        target = self._orgs.get(target_org_id)
        if not target:
            return False
        if target.parent_org_id == requester_org_id:
            return True
        cur = target
        while cur and cur.parent_org_id:
            if cur.parent_org_id == requester_org_id:
                return True
            cur = self._orgs.get(cur.parent_org_id)
        return False

    def check_access(self, requester_org_id: str, target_org_id: str, tenant_id: str) -> dict[str, Any]:
        allowed = self.can_access(requester_org_id, target_org_id)
        self._audit.append({"type": "access_denied" if not allowed else "access_granted", "requester": requester_org_id, "target": target_org_id, "tenant_id": tenant_id, "allowed": allowed})
        return {"allowed": allowed, "requester": requester_org_id, "target": target_org_id}
