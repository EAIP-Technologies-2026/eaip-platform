from __future__ import annotations

import uuid
from typing import Any

from eaip.solution_packs.catalog import get_pack
from eaip.solution_packs.models import SolutionPackInstallation


class SolutionPackRegistry:
    def __init__(self) -> None:
        self._installations: dict[str, SolutionPackInstallation] = {}

    def _key(self, tenant_id: str, pack_id: str) -> str:
        return f"{tenant_id}:{pack_id}"

    def install(self, pack_id: str, tenant_id: str, config: dict[str, Any] | None = None) -> SolutionPackInstallation:
        pack = get_pack(pack_id)
        if not pack:
            raise ValueError(f"unknown pack {pack_id!r}")
        key = self._key(tenant_id, pack_id)
        if key in self._installations:
            return self._installations[key]
        inst = SolutionPackInstallation(installation_id=f"sp-{uuid.uuid4().hex[:8]}", pack_id=pack_id, tenant_id=tenant_id, industry=pack.industry, config=config or {})
        self._installations[key] = inst
        return inst

    def get(self, pack_id: str, tenant_id: str) -> SolutionPackInstallation | None:
        return self._installations.get(self._key(tenant_id, pack_id))

    def list_for_tenant(self, tenant_id: str) -> list[SolutionPackInstallation]:
        return [v for k, v in self._installations.items() if k.startswith(f"{tenant_id}:")]

    def uninstall(self, pack_id: str, tenant_id: str) -> bool:
        return self._installations.pop(self._key(tenant_id, pack_id), None) is not None
