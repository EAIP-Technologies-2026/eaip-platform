"""Enterprise Skill Marketplace Registry & Lifecycle Manager (Phase 5)."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from eaip.copilot.marketplace.dependencies import DependencyResolver
from eaip.copilot.marketplace.models import (
    PackageStatus,
    SkillPackageManifest,
    TrustLevel,
)
from eaip.copilot.marketplace.policy import MarketplacePolicy
from eaip.copilot.marketplace.validation import PackageValidator
from eaip.copilot.models import RiskTier
from eaip.copilot.skills.models import ConductorSkill
from eaip.copilot.skills.registry import SkillRegistry

logger = logging.getLogger("eaip.copilot.marketplace.registry")


class MarketplaceRegistry:
    """Enterprise Catalog & Lifecycle Manager for Conductor Skill Packages."""

    def __init__(self, skill_registry: SkillRegistry) -> None:
        """Initialize the marketplace registry with a skill registry."""
        self._skill_registry = skill_registry
        self._packages: dict[str, SkillPackageManifest] = {}
        self._bootstrap_default_catalog()

    def _bootstrap_default_catalog(self) -> None:
        """Bootstrap default initial marketplace catalog packages."""
        # Package 1: Operations Suite
        p1 = SkillPackageManifest(
            package_id="eaip.operations.v1",
            name="EAIP Core Operations Suite",
            version="1.0.0",
            publisher="EAIP Enterprise Core",
            description=(
                "Core system health, morning operational briefings, "
                "and status checks."
            ),
            trust_level=TrustLevel.BUILT_IN,
            status=PackageStatus.ENABLED,
            skills=[
                ConductorSkill(
                    id="system_health_briefing",
                    name="System Health Briefing",
                    description=(
                        "Summarize platform component statuses and "
                        "operational health."
                    ),
                    category="OPERATIONS",
                    allowed_tools=["system_health", "get_system_twin"],
                    required_permissions=["copilot:tools:system_health"],
                    risk_level=RiskTier.INFORMATIONAL,
                ),
                ConductorSkill(
                    id="morning_operations_briefing",
                    name="Morning Operations Briefing",
                    description=(
                        "Executive morning summary combining System Twin, "
                        "anomalies, and active agents."
                    ),
                    category="BRIEFING",
                    allowed_tools=["get_system_briefing", "get_system_twin"],
                    required_permissions=["copilot:tools:system_briefing"],
                    risk_level=RiskTier.INFORMATIONAL,
                ),
            ],
            tool_dependencies=[
                "system_health",
                "get_system_twin",
                "get_system_briefing",
            ],
            required_permissions=[
                "copilot:tools:system_health",
                "copilot:tools:system_briefing",
            ],
        )

        # Package 2: Incident & Diagnostics Pack
        p2 = SkillPackageManifest(
            package_id="eaip.diagnostics.v1",
            name="Agent & Workflow Diagnostic Pack",
            version="1.1.0",
            publisher="EAIP Enterprise Security & Ops",
            description=(
                "Diagnostic skills for inspecting agent rosters, failure traces, "
                "and workflow bottlenecks."
            ),
            trust_level=TrustLevel.VERIFIED,
            status=PackageStatus.AVAILABLE,
            skills=[
                ConductorSkill(
                    id="agent_health_investigation",
                    name="Agent Health Investigation",
                    description=(
                        "Inspect agent roster, identify failing agents, and "
                        "produce OBSERVED/INFERRED/RECOMMENDED diagnosis."
                    ),
                    category="DIAGNOSTICS",
                    allowed_tools=[
                        "list_agents",
                        "runtime_diagnostics",
                        "recent_failures",
                    ],
                    required_permissions=["copilot:tools:list_agents"],
                    risk_level=RiskTier.INFORMATIONAL,
                ),
                ConductorSkill(
                    id="workflow_investigation",
                    name="Workflow Diagnostics",
                    description=(
                        "Inspect workflow definitions and failure traces "
                        "to diagnose pipeline issues."
                    ),
                    category="WORKFLOW",
                    allowed_tools=["list_workflows", "recent_failures"],
                    required_permissions=["copilot:tools:list_workflows"],
                    risk_level=RiskTier.INFORMATIONAL,
                ),
            ],
            tool_dependencies=[
                "list_agents",
                "runtime_diagnostics",
                "recent_failures",
                "list_workflows",
            ],
            required_permissions=[
                "copilot:tools:list_agents",
                "copilot:tools:list_workflows",
            ],
        )

        self.register_manifest(p1)
        self.register_manifest(p2)

    def register_manifest(self, manifest: SkillPackageManifest) -> None:
        """Register a valid package manifest in the catalog."""
        valid, errors = PackageValidator.validate_manifest(manifest)
        if not valid:
            raise ValueError(
                f"Package validation failed for {manifest.package_id}: {', '.join(errors)}"
            )

        self._packages[manifest.package_id] = manifest

        # Register skills into SkillRegistry if package is enabled
        if manifest.status == PackageStatus.ENABLED:
            for skill in manifest.skills:
                self._skill_registry.register(skill)

    def list_catalog(self) -> Sequence[SkillPackageManifest]:
        """List all packages available in the enterprise catalog."""
        return list(self._packages.values())

    def get_package(self, package_id: str) -> SkillPackageManifest | None:
        """Inspect a specific marketplace package."""
        return self._packages.get(package_id)

    def install_package(
        self,
        package_id: str,
        user: dict[str, Any] | None = None,
        policy: MarketplacePolicy | None = None,
    ) -> SkillPackageManifest:
        """Install a package, validating enterprise policy and dependency chains."""
        manifest = self.get_package(package_id)
        if not manifest:
            raise ValueError(f"Package '{package_id}' not found in catalog.")

        # 1. Enforce Enterprise Policy
        if user and policy:
            allowed, reason = policy.validate_installation(manifest, user)
            if not allowed:
                raise PermissionError(f"Installation rejected by policy: {reason}")

        # 2. Enforce Dependency Chain Validation
        dep_valid, dep_errors = DependencyResolver.validate_dependencies(
            manifest, self.list_catalog()
        )
        if not dep_valid:
            raise ValueError(f"Dependency resolution failed: {', '.join(dep_errors)}")

        manifest.status = PackageStatus.INSTALLED
        logger.info(
            "Installed marketplace package %s v%s",
            manifest.package_id,
            manifest.version,
        )
        return manifest


    def enable_package(self, package_id: str) -> SkillPackageManifest:
        """Enable an installed package and register its skills into active Conductor discovery."""
        manifest = self.get_package(package_id)
        if not manifest:
            raise ValueError(f"Package '{package_id}' not found.")

        manifest.status = PackageStatus.ENABLED
        for skill in manifest.skills:
            self._skill_registry.register(skill)

        logger.info(
            "Enabled marketplace package %s v%s",
            manifest.package_id,
            manifest.version,
        )
        return manifest

    def disable_package(self, package_id: str) -> SkillPackageManifest:
        """Disable a package safely."""
        manifest = self.get_package(package_id)
        if not manifest:
            raise ValueError(f"Package '{package_id}' not found.")

        manifest.status = PackageStatus.DISABLED
        logger.info("Disabled marketplace package %s", manifest.package_id)
        return manifest

    def upgrade_package(self, package_id: str, new_version: str) -> SkillPackageManifest:
        """Upgrade an installed package to a new version cleanly."""
        manifest = self.get_package(package_id)
        if not manifest:
            raise ValueError(f"Package '{package_id}' not found.")

        old_version = manifest.version
        manifest.version = new_version
        logger.info(
            "Upgraded marketplace package %s from v%s to v%s",
            package_id,
            old_version,
            new_version,
        )
        return manifest

