from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class FederatedOrg(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    org_id: str
    parent_org_id: str = ""
    name: str
    tenant_id: str
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)
