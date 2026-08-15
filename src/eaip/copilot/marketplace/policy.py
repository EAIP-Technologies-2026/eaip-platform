"""Enterprise Administration & Trust Policy Engine for EAIP Conductor Marketplace (Phase 6)."""

from __future__ import annotations

from typing import Any

from eaip.copilot.marketplace.models import SkillPackageManifest, TrustLevel
from eaip.copilot.models import RiskTier


class MarketplacePolicy:
    """Enforces enterprise administration policies for skill package installation and execution."""

    def __init__(
        self,
        *,
        allowed_trust_levels: set[TrustLevel] | None = None,
        blocked_publishers: set[str] | None = None,
        max_allowed_risk_level: RiskTier = RiskTier.DESTRUCTIVE,
        require_admin_approval: bool = True,
    ) -> None:
        """Initialize marketplace policy with enterprise constraints."""
        self.allowed_trust_levels = allowed_trust_levels or {
            TrustLevel.BUILT_IN,
            TrustLevel.FIRST_PARTY,
            TrustLevel.VERIFIED,
            TrustLevel.THIRD_PARTY,
        }
        self.blocked_publishers = blocked_publishers or set()
        self.max_allowed_risk_level = max_allowed_risk_level
        self.require_admin_approval = require_admin_approval

    def validate_installation(
        self, manifest: SkillPackageManifest, user: dict[str, Any]
    ) -> tuple[bool, str]:
        """Evaluate package against enterprise policy and user authorization claims."""
        # Rule 1: Trust Level Constraint
        if manifest.trust_level not in self.allowed_trust_levels:
            return (
                False,
                f"Trust level '{manifest.trust_level.value}' is not allowed by enterprise policy.",
            )

        # Rule 2: Blocked Publisher Constraint
        if manifest.publisher in self.blocked_publishers:
            return False, f"Publisher '{manifest.publisher}' is blocked by enterprise policy."

        # Rule 3: Risk Tier Constraint
        risk_order = {
            RiskTier.INFORMATIONAL: 0,
            RiskTier.ACTION: 1,
            RiskTier.DESTRUCTIVE: 2,
        }
        if risk_order.get(manifest.risk_level, 0) > risk_order.get(
            self.max_allowed_risk_level, 2
        ):
            return (
                False,
                f"Package risk level '{manifest.risk_level.value}' "
                "exceeds maximum allowed threshold.",
            )

        # Rule 4: Admin Role Requirement
        roles = user.get("roles", [])
        if self.require_admin_approval and "admin" not in roles:
            return False, "Package installation requires Enterprise Admin authorization."

        return True, "Installation allowed by policy."
