"""Extended marketplace models — richer categories and tenant-scoped packages."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from eaip.marketplace.models import MarketplacePackage


class ExtendedPackageCategory(StrEnum):
    """Extended package categories for the marketplace."""

    AGENT = "agent"
    WORKFLOW = "workflow"
    MISSION = "mission"
    SKILL = "skill"
    INTEGRATION = "integration"
    INDUSTRY_PACK = "industry_pack"
    TEMPLATE = "template"
    KNOWLEDGE_PACK = "knowledge_pack"
    AUTOMATION_PACK = "automation_pack"


class Visibility(StrEnum):
    """Package visibility scope."""

    PUBLIC = "public"
    PRIVATE = "private"


class ExtendedMarketplacePackage(MarketplacePackage):
    """Marketplace package with tenant isolation and extended metadata.

    Extends :class:`MarketplacePackage` so existing code handling the base
    type continues to work. The base fields (package_id, name, type,
    version, description, author, dependencies, tags, status, etc.) are
    inherited unchanged.
    """

    tenant_id: str = Field(default="default", description="Owning tenant")
    visibility: Visibility = Field(default=Visibility.PUBLIC)
    capabilities: tuple[str, ...] = Field(default=())
    requirements: tuple[str, ...] = Field(default=())
    compatibility: tuple[str, ...] = Field(default=())
    industry: str = Field(default="")


__all__ = ["ExtendedMarketplacePackage", "ExtendedPackageCategory", "Visibility"]
