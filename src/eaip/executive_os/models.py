"""M9 Executive OS + Departmental Applications models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DepartmentId(str, Enum):
    executive = "executive"
    operations = "operations"
    finance = "finance"
    sales = "sales"
    marketing = "marketing"
    hr = "hr"
    it = "it"
    compliance = "compliance"
    support = "support"


class IndustryId(str, Enum):
    healthcare = "healthcare"
    financial_services = "financial_services"
    consultancy = "consultancy"
    manufacturing = "manufacturing"
    d2c_retail = "d2c_retail"


class ExecutiveBriefing(BaseModel):
    briefing_id: str = Field(default_factory=lambda: f"brief-{uuid.uuid4().hex[:8]}")
    tenant_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    what_changed: list[dict[str, Any]] = Field(default_factory=list)
    why: str = ""
    risks: list[dict[str, Any]] = Field(default_factory=list)
    opportunities: list[dict[str, Any]] = Field(default_factory=list)
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    forecast: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)


class DepartmentView(BaseModel):
    view_id: str = Field(default_factory=lambda: f"dept-{uuid.uuid4().hex[:8]}")
    department: DepartmentId
    tenant_id: str
    industry: IndustryId | None = None
    title: str = ""
    sections: list[dict[str, Any]] = Field(default_factory=list)
    kpis: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class KPIRecord(BaseModel):
    kpi_id: str = Field(default_factory=lambda: f"kpi-{uuid.uuid4().hex[:8]}")
    tenant_id: str
    name: str
    value: float = 0
    target: float = 0
    unit: str = ""
    trend: str = "stable"
    department: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
