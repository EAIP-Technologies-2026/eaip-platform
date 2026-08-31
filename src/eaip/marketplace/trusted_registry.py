from __future__ import annotations

import os
import uuid
from typing import Any

from eaip.marketplace.models import MarketplacePackage, PackageStatus
from eaip.marketplace.signing import sign_artifact, verify_artifact

SECRET_ENV = "EAIP_MARKETPLACE_SIGNING_SECRET"
DEFAULT_SECRET = "dev-marketplace-secret-not-for-prod"


def _secret() -> str:
    return os.environ.get(SECRET_ENV, DEFAULT_SECRET)


class TrustedMarketplace:
    def __init__(self, secret: str | None = None) -> None:
        self._secret = secret or _secret()
        self._store: dict[str, dict[str, Any]] = {}  # package_id -> {package, signature, tenant_id}

    def publish(self, package: MarketplacePackage, tenant_id: str = "default") -> dict[str, Any]:
        payload = {"package_id": package.package_id, "version": package.version, "name": package.name, "tenant_id": tenant_id}
        sig = sign_artifact(payload, self._secret)
        record = {"package": package.model_dump(mode="json"), "signature": sig, "payload": payload, "tenant_id": tenant_id, "status": package.status.value}
        self._store[package.package_id] = record
        return record

    def verify(self, package_id: str) -> dict[str, Any]:
        rec = self._store.get(package_id)
        if not rec:
            return {"valid": False, "reason": "not found"}
        payload = rec["payload"]
        sig = rec["signature"]
        valid = verify_artifact(payload, sig, self._secret)
        return {"valid": valid, "package_id": package_id, "signature": sig[:12] + "..." if sig else ""}

    def revoke(self, package_id: str) -> bool:
        rec = self._store.get(package_id)
        if not rec:
            return False
        rec["status"] = PackageStatus.ARCHIVED.value
        rec["revoked"] = True
        return True

    def list_for_tenant(self, tenant_id: str) -> list[dict[str, Any]]:
        return [v for v in self._store.values() if v["tenant_id"] == tenant_id or v["tenant_id"] == "default"]

    def get(self, package_id: str) -> dict[str, Any] | None:
        return self._store.get(package_id)


__all__ = ["TrustedMarketplace"]
