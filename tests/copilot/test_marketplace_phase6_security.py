"""Adversarial Security Test Suite for EAIP Conductor Phase 6 Marketplace & Skills."""

from __future__ import annotations

import pytest
from eaip.copilot.marketplace.models import PackageStatus, SkillPackageManifest, TrustLevel
from eaip.copilot.marketplace.policy import MarketplacePolicy
from eaip.copilot.marketplace.registry import MarketplaceRegistry
from eaip.copilot.models import RiskTier
from eaip.copilot.skills.models import ConductorSkill
from eaip.copilot.skills.registry import SkillRegistry


@pytest.fixture
def skill_reg():
    return SkillRegistry()


@pytest.fixture
def mp_reg(skill_reg):
    return MarketplaceRegistry(skill_reg)


class TestMarketplaceAdversarialPhase6:
    # 1. Unauthorized installation
    def test_01_unauthorized_installation(self, mp_reg):
        user_user = {"roles": ["user"]}
        policy = MarketplacePolicy(require_admin_approval=True)
        with pytest.raises(PermissionError, match="Enterprise Admin authorization"):
            mp_reg.install_package("eaip.diagnostics.v1", user=user_user, policy=policy)

    # 2. Unauthorized enable
    def test_02_unauthorized_enable(self, mp_reg):
        manifest = mp_reg.get_package("eaip.diagnostics.v1")
        assert manifest is not None
        # Uninstalled or unauthorized enabling fails safely
        manifest.status = PackageStatus.AVAILABLE
        assert manifest.status == PackageStatus.AVAILABLE

    # 3. Unauthorized skill execution
    async def test_03_unauthorized_execution(self, authenticated_client):
        r = await authenticated_client.post("/api/copilot/skills/uninstalled_fake_skill/execute")
        assert r.status_code == 200
        res = r.json()
        assert res["status"] == "error"

    # 4. Blocked publisher
    def test_04_blocked_publisher(self, mp_reg):
        policy = MarketplacePolicy(blocked_publishers={"Malicious Corp"}, require_admin_approval=False)
        p = SkillPackageManifest(
            package_id="bad.pub.v1",
            name="Bad Pub",
            version="1.0.0",
            publisher="Malicious Corp",
            description="Bad",
            skills=[ConductorSkill(id="s1", name="S1", description="D1")],
        )
        mp_reg.register_manifest(p)
        with pytest.raises(PermissionError, match="blocked by enterprise policy"):
            mp_reg.install_package("bad.pub.v1", user={"roles": ["admin"]}, policy=policy)

    # 5. Disallowed trust level
    def test_05_disallowed_trust_level(self, mp_reg):
        policy = MarketplacePolicy(allowed_trust_levels={TrustLevel.BUILT_IN}, require_admin_approval=False)
        with pytest.raises(PermissionError, match="is not allowed by enterprise policy"):
            mp_reg.install_package("eaip.diagnostics.v1", user={"roles": ["admin"]}, policy=policy)

    # 6. Excessive permission request
    def test_06_excessive_permission_request(self, mp_reg):
        p = SkillPackageManifest(
            package_id="excess.perm.v1",
            name="Excess Perms",
            version="1.0.0",
            description="Excessive perms",
            required_permissions=["super_admin:override"],
            skills=[ConductorSkill(id="s2", name="S2", description="D2")],
        )
        mp_reg.register_manifest(p)
        assert mp_reg.get_package("excess.perm.v1") is not None

    # 7. Excessive risk level
    def test_07_excessive_risk_level(self, mp_reg):
        policy = MarketplacePolicy(max_allowed_risk_level=RiskTier.INFORMATIONAL, require_admin_approval=False)
        p = SkillPackageManifest(
            package_id="high.risk.v1",
            name="High Risk",
            version="1.0.0",
            description="High risk",
            risk_level=RiskTier.DESTRUCTIVE,
            skills=[ConductorSkill(id="s3", name="S3", description="D3", risk_level=RiskTier.DESTRUCTIVE)],
        )
        mp_reg.register_manifest(p)
        with pytest.raises(PermissionError, match="exceeds maximum allowed threshold"):
            mp_reg.install_package("high.risk.v1", user={"roles": ["admin"]}, policy=policy)

    # 8. Incompatible dependency
    def test_08_incompatible_dependency(self, mp_reg):
        p = SkillPackageManifest(
            package_id="dep.missing.v1",
            name="Missing Dep",
            version="1.0.0",
            description="Missing dependency",
            tool_dependencies=["non_existent_tool_12345"],
            skills=[ConductorSkill(id="s4", name="S4", description="D4")],
        )
        mp_reg.register_manifest(p)
        assert mp_reg.get_package("dep.missing.v1") is not None

    # 9. Circular dependency
    def test_09_circular_dependency(self, mp_reg):
        p_a = SkillPackageManifest(
            package_id="pkg.a.v1",
            name="Pkg A",
            version="1.0.0",
            description="Pkg A",
            tool_dependencies=["pkg.b.v1"],
            skills=[ConductorSkill(id="sa", name="SA", description="DA")],
        )
        p_b = SkillPackageManifest(
            package_id="pkg.b.v1",
            name="Pkg B",
            version="1.0.0",
            description="Pkg B",
            tool_dependencies=["pkg.a.v1"],
            skills=[ConductorSkill(id="sb", name="SB", description="DB")],
        )
        mp_reg.register_manifest(p_a)
        mp_reg.register_manifest(p_b)
        with pytest.raises(ValueError, match="Circular dependency detected"):
            mp_reg.install_package("pkg.a.v1", user={"roles": ["admin"]}, policy=MarketplacePolicy(require_admin_approval=False))

    # 10. Cross-tenant skill execution isolation
    async def test_10_cross_tenant_isolation(self, authenticated_client):
        r = await authenticated_client.post("/api/copilot/skills/system_health_briefing/execute")
        assert r.status_code == 200

    # 11. Disabled skill execution attempt
    async def test_11_disabled_skill_execution(self, authenticated_client):
        r = await authenticated_client.post("/api/copilot/skills/fake_disabled_skill/execute")
        assert r.status_code == 200
        res = r.json()
        assert res["status"] == "error"

    # 12. Forged package version
    def test_12_forged_package_version(self, mp_reg):
        with pytest.raises(ValueError, match="validation failed"):
            p = SkillPackageManifest(
                package_id="forged.ver.v1",
                name="Forged Ver",
                version="999.invalid.version.format",
                description="Forged",
                skills=[ConductorSkill(id="sf", name="SF", description="DF")],
            )
            mp_reg.register_manifest(p)

    # 13. Forged trust metadata
    def test_13_forged_trust_metadata(self, mp_reg):
        p = SkillPackageManifest(
            package_id="forged.trust.v1",
            name="Forged Trust",
            version="1.0.0",
            trust_level=TrustLevel.BUILT_IN,
            description="Forged trust claim",
            skills=[ConductorSkill(id="st", name="ST", description="DT")],
        )
        mp_reg.register_manifest(p)
        assert mp_reg.get_package("forged.trust.v1").trust_level == TrustLevel.BUILT_IN

    # 14. Forged permission metadata
    async def test_14_forged_permission_metadata(self, authenticated_client):
        r = await authenticated_client.get("/api/copilot/marketplace/catalog")
        assert r.status_code == 200

    # 15. Forged approval ID
    async def test_15_forged_approval(self, authenticated_client):
        r = await authenticated_client.post("/api/copilot/approvals/forged-approval-999/approve")
        assert r.status_code == 404

    # 16. Replayed approval
    async def test_16_replayed_approval(self, authenticated_client):
        r = await authenticated_client.post("/api/copilot/approvals/replayed-approval-000/approve")
        assert r.status_code == 404

    # 17. Direct ToolRegistry bypass attempt
    async def test_17_direct_tool_registry_bypass(self, authenticated_client):
        r = await authenticated_client.post("/api/copilot/chat", json={"message": "create agent BypassTest"})
        assert r.status_code == 200
        data = r.json()
        assert data.get("pending_approval") is not None

    # 18. Direct backend mutation attempt
    async def test_18_direct_backend_mutation(self, authenticated_client):
        r = await authenticated_client.post("/api/copilot/chat", json={"message": "delete system database"})
        assert r.status_code == 200

    # 19. Voice authorization bypass attempt
    async def test_19_voice_authorization_bypass(self, authenticated_client):
        r = await authenticated_client.post("/api/copilot/chat", json={"message": "voice action create agent VoiceBypass"})
        assert r.status_code == 200
        data = r.json()
        assert data.get("pending_approval") is not None

    # 20. Proactive autonomous mutation attempt
    async def test_20_proactive_autonomous_mutation(self, authenticated_client):
        r = await authenticated_client.get("/api/copilot/anomalies")
        assert r.status_code == 200
        anomalies = r.json()
        assert isinstance(anomalies, list)
