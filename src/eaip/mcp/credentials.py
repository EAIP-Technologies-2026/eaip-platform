from __future__ import annotations

import os
from typing import Any

from eaip.mcp.models import MCPCredentialRef
from eaip.shared.time import utc_now

SECRET_KEYS = {"password", "secret", "token", "api_key", "apikey", "credential", "auth", "bearer"}


class CredentialStore:
    def __init__(self) -> None:
        self._store: dict[str, MCPCredentialRef] = {}

    def _key(self, tenant_id: str, credential_id: str) -> str:
        return f"{tenant_id}:{credential_id}"

    def store(self, credential_id: str, tenant_id: str, credential_type: str = "api_key", provider: str = "", reference: str = "") -> MCPCredentialRef:
        ref = MCPCredentialRef(
            credential_id=credential_id,
            tenant_id=tenant_id,
            credential_type=credential_type,
            provider=provider,
            reference=reference or f"vault://{tenant_id}/{credential_id}",
            created_at=utc_now(),
        )
        self._store[self._key(tenant_id, credential_id)] = ref
        return ref

    def get(self, credential_id: str, tenant_id: str) -> MCPCredentialRef | None:
        return self._store.get(self._key(tenant_id, credential_id))

    def list_for_tenant(self, tenant_id: str) -> list[MCPCredentialRef]:
        return [v for k, v in self._store.items() if k.startswith(f"{tenant_id}:")]

    def delete(self, credential_id: str, tenant_id: str) -> bool:
        return self._store.pop(self._key(tenant_id, credential_id), None) is not None

    @staticmethod
    def validate_not_in_payload(payload: dict[str, Any]) -> bool:
        for k in payload:
            if k.lower() in SECRET_KEYS:
                return False
        return True


def get_secret_resolver(credential_store: CredentialStore | None = None):
    async def resolve(credential_id: str, tenant_id: str) -> str:
        if credential_store:
            ref = credential_store.get(credential_id, tenant_id)
            if ref:
                env_val = os.environ.get(f"EAIP_SECRET_{credential_id.upper()}")
                if env_val:
                    return env_val
                return "***"
        return "***"

    return resolve
