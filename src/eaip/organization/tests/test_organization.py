"""Tests for the organization package — models, events, exceptions, service, integration, health."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from eaip.organization.events import (
    OrganizationActivated,
    OrganizationArchived,
    OrganizationAuditLogged,
    OrganizationCreated,
    OrganizationDeactivated,
    OrganizationDeleted,
    OrganizationDomainsVerified,
    OrganizationMemberAdded,
    OrganizationMemberRemoved,
    OrganizationMemberRoleChanged,
    OrganizationPolicyCreated,
    OrganizationPolicyUpdated,
    OrganizationReportGenerated,
    OrganizationSettingsUpdated,
    OrganizationSubscriptionsUpdated,
    OrganizationUnitAdded,
    OrganizationUnitMoved,
    OrganizationUnitRemoved,
    OrganizationUpdated,
)
from eaip.organization.exceptions import (
    OrganizationConfigError,
    OrganizationDomainError,
    OrganizationError,
    OrganizationMemberError,
    OrganizationNotFoundError,
    OrganizationPolicyError,
    OrganizationSubscriptionError,
    OrganizationUnitError,
)
from eaip.organization.health import OrganizationHealthCheck
from eaip.organization.integration import OrganizationRuntimeModule
from eaip.organization.models import (
    Organization,
    OrganizationAuditEntry,
    OrganizationConfig,
    OrganizationContact,
    OrganizationDomain,
    OrganizationFeature,
    OrganizationHierarchy,
    OrganizationMember,
    OrganizationPolicy,
    OrganizationReport,
    OrganizationRole,
    OrganizationSettings,
    OrganizationStatus,
    OrganizationSubscription,
    OrganizationType,
    OrganizationUnit,
    OrganizationUnitType,
)
from eaip.organization.service import OrganizationService

# =========================================================================
# Models
# =========================================================================


class TestOrganizationModel:
    def test_create_organization(self) -> None:
        org = Organization(id="org-1", name="Test Org", slug="test-org")
        assert org.id == "org-1"
        assert org.name == "Test Org"
        assert org.status is OrganizationStatus.ACTIVE
        assert org.org_type is OrganizationType.OTHER

    def test_organization_is_frozen(self) -> None:
        org = Organization(id="org-1", name="Test", slug="test")
        with pytest.raises(ValueError, match="Instance is frozen"):
            org.name = "changed"

    def test_organization_forbids_extra(self) -> None:
        with pytest.raises(ValueError, match="Extra inputs are not permitted"):
            Organization.model_validate({"id": "o1", "name": "N", "slug": "n", "unknown": "x"})


class TestOrganizationUnitModel:
    def test_create_unit(self) -> None:
        unit = OrganizationUnit(id="unit-1", org_id="org-1", name="Engineering")
        assert unit.unit_type is OrganizationUnitType.OTHER

    def test_unit_is_frozen(self) -> None:
        unit = OrganizationUnit(id="u1", org_id="o1", name="N")
        with pytest.raises(ValueError, match="Instance is frozen"):
            unit.name = "changed"


class TestOrganizationMemberModel:
    def test_create_member(self) -> None:
        member = OrganizationMember(id="mem-1", org_id="org-1", user_id="user-1", email="a@b.com")
        assert member.role is OrganizationRole.MEMBER

    def test_member_is_frozen(self) -> None:
        member = OrganizationMember(id="m1", org_id="o1", user_id="u1", email="a@b.com")
        with pytest.raises(ValueError, match="Instance is frozen"):
            member.email = "c@d.com"


class TestOrganizationSettingsModel:
    def test_defaults(self) -> None:
        settings = OrganizationSettings(org_id="org-1")
        assert settings.max_members == 100
        assert settings.require_2fa is False


class TestOrganizationPolicyModel:
    def test_create_policy(self) -> None:
        policy = OrganizationPolicy(
            id="pol-1", org_id="org-1", name="Data Policy", policy_type="data"
        )
        assert policy.enabled is True


class TestOrganizationAuditEntryModel:
    def test_create_audit_entry(self) -> None:
        entry = OrganizationAuditEntry(
            id="audit-1",
            org_id="org-1",
            actor_id="user-1",
            action="member.added",
            resource_type="member",
            resource_id="mem-1",
        )
        assert entry.action == "member.added"


class TestOrganizationReportModel:
    def test_create_report(self) -> None:
        now = datetime.now(UTC)
        report = OrganizationReport(
            id="rpt-1",
            org_id="org-1",
            report_type="monthly",
            period_start=now,
            period_end=now,
        )
        assert report.total_members == 0


class TestOrganizationConfigModel:
    def test_create_config(self) -> None:
        config = OrganizationConfig(id="cfg-1", org_id="org-1", key="theme", value="dark")
        assert config.value == "dark"


class TestOrganizationSubscriptionModel:
    def test_create_subscription(self) -> None:
        now = datetime.now(UTC)
        sub = OrganizationSubscription(
            id="sub-1", org_id="org-1", plan="enterprise", start_date=now
        )
        assert sub.status == "active"
        assert sub.auto_renew is True


class TestOrganizationFeatureModel:
    def test_create_feature(self) -> None:
        feat = OrganizationFeature(id="feat-1", org_id="org-1", feature_key="audit_log")
        assert feat.enabled is True


class TestOrganizationDomainModel:
    def test_create_domain(self) -> None:
        domain = OrganizationDomain(id="dom-1", org_id="org-1", domain="example.com")
        assert domain.verified is False


class TestOrganizationContactModel:
    def test_create_contact(self) -> None:
        contact = OrganizationContact(id="cnt-1", org_id="org-1", email="admin@example.com")
        assert contact.is_primary is False


class TestOrganizationHierarchyModel:
    def test_create_hierarchy(self) -> None:
        hierarchy = OrganizationHierarchy(org_id="org-1")
        assert hierarchy.depth == 0
        assert hierarchy.ancestor_ids == ()


class TestStrEnums:
    def test_organization_status_values(self) -> None:
        assert OrganizationStatus.ACTIVE.value == "active"
        assert OrganizationStatus.ARCHIVED.value == "archived"

    def test_organization_type_values(self) -> None:
        assert OrganizationType.CORPORATION.value == "corporation"

    def test_organization_role_values(self) -> None:
        assert OrganizationRole.OWNER.value == "owner"

    def test_organization_unit_type_values(self) -> None:
        assert OrganizationUnitType.DEPARTMENT.value == "department"


# =========================================================================
# Events
# =========================================================================


class TestOrganizationEvents:
    def test_organization_created_event_type(self) -> None:
        event = OrganizationCreated(org_id="org-1", name="Test", slug="test")
        assert event.event_type == "eaip.organization.created"

    def test_organization_updated_event_type(self) -> None:
        event = OrganizationUpdated(org_id="org-1", changes={"name": "New"})
        assert event.event_type == "eaip.organization.updated"

    def test_organization_deleted_event_type(self) -> None:
        event = OrganizationDeleted(org_id="org-1")
        assert event.event_type == "eaip.organization.deleted"

    def test_organization_activated_event(self) -> None:
        event = OrganizationActivated(org_id="org-1")
        assert event.event_type == "eaip.organization.activated"

    def test_organization_deactivated_event(self) -> None:
        event = OrganizationDeactivated(org_id="org-1")
        assert event.event_type == "eaip.organization.deactivated"

    def test_organization_archived_event(self) -> None:
        event = OrganizationArchived(org_id="org-1")
        assert event.event_type == "eaip.organization.archived"

    def test_unit_added_event(self) -> None:
        event = OrganizationUnitAdded(org_id="org-1", unit_id="unit-1", name="Eng")
        assert event.event_type == "eaip.organization.unit_added"

    def test_unit_moved_event(self) -> None:
        event = OrganizationUnitMoved(org_id="org-1", unit_id="unit-1")
        assert event.event_type == "eaip.organization.unit_moved"

    def test_unit_removed_event(self) -> None:
        event = OrganizationUnitRemoved(org_id="org-1", unit_id="unit-1")
        assert event.event_type == "eaip.organization.unit_removed"

    def test_member_added_event(self) -> None:
        event = OrganizationMemberAdded(
            org_id="org-1", member_id="mem-1", user_id="u1", email="a@b.com"
        )
        assert event.event_type == "eaip.organization.member_added"

    def test_member_removed_event(self) -> None:
        event = OrganizationMemberRemoved(org_id="org-1", member_id="mem-1", user_id="u1")
        assert event.event_type == "eaip.organization.member_removed"

    def test_member_role_changed_event(self) -> None:
        event = OrganizationMemberRoleChanged(
            org_id="org-1",
            member_id="mem-1",
            user_id="u1",
            previous_role="member",
            new_role="admin",
        )
        assert event.event_type == "eaip.organization.member_role_changed"

    def test_settings_updated_event(self) -> None:
        event = OrganizationSettingsUpdated(org_id="org-1")
        assert event.event_type == "eaip.organization.settings_updated"

    def test_policy_created_event(self) -> None:
        event = OrganizationPolicyCreated(
            org_id="org-1", policy_id="pol-1", name="Policy", policy_type="data"
        )
        assert event.event_type == "eaip.organization.policy_created"

    def test_policy_updated_event(self) -> None:
        event = OrganizationPolicyUpdated(org_id="org-1", policy_id="pol-1")
        assert event.event_type == "eaip.organization.policy_updated"

    def test_domains_verified_event(self) -> None:
        event = OrganizationDomainsVerified(org_id="org-1")
        assert event.event_type == "eaip.organization.domains_verified"

    def test_subscriptions_updated_event(self) -> None:
        event = OrganizationSubscriptionsUpdated(
            org_id="org-1", subscription_id="sub-1", plan="enterprise", status="active"
        )
        assert event.event_type == "eaip.organization.subscriptions_updated"

    def test_report_generated_event(self) -> None:
        now = datetime.now(UTC)
        event = OrganizationReportGenerated(
            org_id="org-1",
            report_id="rpt-1",
            report_type="monthly",
            period_start=now,
            period_end=now,
        )
        assert event.event_type == "eaip.organization.report_generated"

    def test_audit_logged_event(self) -> None:
        event = OrganizationAuditLogged(
            org_id="org-1",
            entry_id="audit-1",
            actor_id="user-1",
            action="member.added",
            resource_type="member",
            resource_id="mem-1",
        )
        assert event.event_type == "eaip.organization.audit_logged"


# =========================================================================
# Exceptions
# =========================================================================


class TestOrganizationExceptions:
    def test_organization_error(self) -> None:
        err = OrganizationError("test")
        assert "test" in str(err)

    def test_not_found_error(self) -> None:
        err = OrganizationNotFoundError("not found")
        assert isinstance(err, OrganizationError)

    def test_config_error(self) -> None:
        err = OrganizationConfigError("bad config")
        assert isinstance(err, OrganizationError)

    def test_member_error(self) -> None:
        err = OrganizationMemberError("member issue")
        assert isinstance(err, OrganizationError)

    def test_unit_error(self) -> None:
        err = OrganizationUnitError("unit issue")
        assert isinstance(err, OrganizationError)

    def test_policy_error(self) -> None:
        err = OrganizationPolicyError("policy issue")
        assert isinstance(err, OrganizationError)

    def test_domain_error(self) -> None:
        err = OrganizationDomainError("domain issue")
        assert isinstance(err, OrganizationError)

    def test_subscription_error(self) -> None:
        err = OrganizationSubscriptionError("sub issue")
        assert isinstance(err, OrganizationError)


# =========================================================================
# Service
# =========================================================================


class TestOrganizationServiceCRUD:
    @pytest.fixture
    def service(self) -> OrganizationService:
        return OrganizationService()

    async def test_create_organization(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="Test Org", slug="test-org")
        assert org.name == "Test Org"
        assert org.slug == "test-org"
        assert org.status is OrganizationStatus.ACTIVE

    async def test_get_organization(self, service: OrganizationService) -> None:
        created = await service.create_organization(name="Test", slug="test")
        fetched = await service.get_organization(created.id)
        assert fetched == created

    async def test_get_organization_not_found(self, service: OrganizationService) -> None:
        with pytest.raises(OrganizationNotFoundError):
            await service.get_organization("nonexistent")

    async def test_update_organization(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="Old", slug="old")
        updated = await service.update_organization(org.id, name="New")
        assert updated.name == "New"

    async def test_delete_organization(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="Del", slug="del")
        await service.delete_organization(org.id)
        with pytest.raises(OrganizationNotFoundError):
            await service.get_organization(org.id)

    async def test_list_organizations(self, service: OrganizationService) -> None:
        await service.create_organization(name="A", slug="a")
        await service.create_organization(name="B", slug="b")
        orgs = await service.list_organizations()
        assert len(orgs) == 2

    async def test_activate_deactivate_archive(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="X", slug="x")
        await service.deactivate_organization(org.id)
        assert (await service.get_organization(org.id)).status is OrganizationStatus.INACTIVE
        await service.activate_organization(org.id)
        assert (await service.get_organization(org.id)).status is OrganizationStatus.ACTIVE
        await service.archive_organization(org.id)
        assert (await service.get_organization(org.id)).status is OrganizationStatus.ARCHIVED


class TestOrganizationServiceUnits:
    @pytest.fixture
    def service(self) -> OrganizationService:
        return OrganizationService()

    async def test_add_and_get_unit(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        unit = await service.add_unit(org.id, "Engineering")
        fetched = await service.get_unit(unit.id)
        assert fetched.name == "Engineering"

    async def test_move_unit(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        parent = await service.add_unit(org.id, "Parent")
        child = await service.add_unit(org.id, "Child")
        moved = await service.move_unit(child.id, parent.id)
        assert moved.parent_unit_id == parent.id

    async def test_remove_unit(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        unit = await service.add_unit(org.id, "ToRemove")
        await service.remove_unit(unit.id)
        with pytest.raises(OrganizationUnitError):
            await service.get_unit(unit.id)

    async def test_list_units(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        await service.add_unit(org.id, "Eng")
        await service.add_unit(org.id, "HR")
        units = await service.list_units(org.id)
        assert len(units) == 2


class TestOrganizationServiceMembers:
    @pytest.fixture
    def service(self) -> OrganizationService:
        return OrganizationService()

    async def test_add_and_get_member(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        member = await service.add_member(org.id, "user-1", "a@b.com", "Alice")
        assert member.email == "a@b.com"

    async def test_add_duplicate_member_raises(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        await service.add_member(org.id, "user-1", "a@b.com")
        with pytest.raises(OrganizationMemberError):
            await service.add_member(org.id, "user-1", "a@b.com")

    async def test_remove_member(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        member = await service.add_member(org.id, "u1", "e@m.com")
        await service.remove_member(member.id)
        with pytest.raises(OrganizationMemberError):
            await service.get_member(member.id)

    async def test_change_member_role(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        member = await service.add_member(org.id, "u1", "e@m.com")
        updated = await service.change_member_role(member.id, OrganizationRole.ADMIN)
        assert updated.role is OrganizationRole.ADMIN

    async def test_list_members(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        await service.add_member(org.id, "u1", "a@b.com")
        await service.add_member(org.id, "u2", "c@d.com")
        members = await service.list_members(org.id)
        assert len(members) == 2


class TestOrganizationServiceSettings:
    @pytest.fixture
    def service(self) -> OrganizationService:
        return OrganizationService()

    async def test_get_settings_defaults(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        settings = await service.get_settings(org.id)
        assert settings.max_members == 100

    async def test_update_settings(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        updated = await service.update_settings(org.id, max_members=500, require_2fa=True)
        assert updated.max_members == 500
        assert updated.require_2fa is True


class TestOrganizationServicePolicies:
    @pytest.fixture
    def service(self) -> OrganizationService:
        return OrganizationService()

    async def test_create_and_get_policy(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        policy = await service.create_policy(org.id, "Data Policy", "data")
        fetched = await service.get_policy(policy.id)
        assert fetched.name == "Data Policy"

    async def test_update_policy(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        policy = await service.create_policy(org.id, "Old", "data")
        updated = await service.update_policy(policy.id, name="New")
        assert updated.name == "New"

    async def test_list_policies(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        await service.create_policy(org.id, "P1", "data")
        await service.create_policy(org.id, "P2", "security")
        policies = await service.list_policies(org.id)
        assert len(policies) == 2


class TestOrganizationServiceDomains:
    @pytest.fixture
    def service(self) -> OrganizationService:
        return OrganizationService()

    async def test_add_and_verify_domain(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        domain = await service.add_domain(org.id, "example.com")
        assert domain.verified is False
        verified = await service.verify_domain(domain.id)
        assert verified.verified is True

    async def test_duplicate_domain_raises(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        await service.add_domain(org.id, "example.com")
        with pytest.raises(OrganizationDomainError):
            await service.add_domain(org.id, "example.com")


class TestOrganizationServiceSubscriptions:
    @pytest.fixture
    def service(self) -> OrganizationService:
        return OrganizationService()

    async def test_create_and_get_subscription(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        now = datetime.now(UTC)
        sub = await service.create_subscription(org.id, "enterprise", now)
        fetched = await service.get_subscription(sub.id)
        assert fetched.plan == "enterprise"


class TestOrganizationServiceReports:
    @pytest.fixture
    def service(self) -> OrganizationService:
        return OrganizationService()

    async def test_generate_report(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        now = datetime.now(UTC)
        report = await service.generate_report(org.id, "monthly", now, now)
        assert report.report_type == "monthly"

    async def test_get_report(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        now = datetime.now(UTC)
        report = await service.generate_report(org.id, "monthly", now, now)
        fetched = await service.get_report(report.id)
        assert fetched.id == report.id


class TestOrganizationServiceAudit:
    @pytest.fixture
    def service(self) -> OrganizationService:
        return OrganizationService()

    async def test_log_audit_entry(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        entry = await service.log_audit_entry(org.id, "user-1", "member.added", "member", "mem-1")
        assert entry.action == "member.added"

    async def test_list_audit_entries(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="O", slug="o")
        await service.log_audit_entry(org.id, "u1", "member.added", "member", "m1")
        await service.log_audit_entry(org.id, "u1", "member.removed", "member", "m2")
        entries = await service.list_audit_entries(org.id)
        assert len(entries) == 2
        filtered = await service.list_audit_entries(org.id, action="member.added")
        assert len(filtered) == 1


class TestOrganizationServiceEvents:
    @pytest.fixture
    def service(self) -> OrganizationService:
        bus = MagicMock()
        bus.publish = AsyncMock()
        return OrganizationService(event_bus=bus)

    async def test_create_publishes_event(self, service: OrganizationService) -> None:
        await service.create_organization(name="T", slug="t")
        bus = cast(Any, service._event_bus)
        assert bus.publish.called
        call_args = bus.publish.call_args[0][0]
        assert isinstance(call_args, OrganizationCreated)

    async def test_delete_publishes_event(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="T", slug="t")
        bus = cast(Any, service._event_bus)
        bus.publish.reset_mock()
        await service.delete_organization(org.id)
        call_args = bus.publish.call_args[0][0]
        assert isinstance(call_args, OrganizationDeleted)

    async def test_activate_publishes_event(self, service: OrganizationService) -> None:
        org = await service.create_organization(name="T", slug="t")
        bus = cast(Any, service._event_bus)
        bus.publish.reset_mock()
        await service.activate_organization(org.id)
        call_args = bus.publish.call_args[0][0]
        assert isinstance(call_args, OrganizationActivated)


# =========================================================================
# Integration
# =========================================================================


class TestOrganizationRuntimeModule:
    @pytest.fixture
    def kernel(self) -> MagicMock:
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        return kernel

    async def test_start_registers_health_check(self, kernel: MagicMock) -> None:
        module = OrganizationRuntimeModule()
        await module.start(kernel)
        assert module.started is True
        kernel.platform.health.register.assert_called_once()

    async def test_stop(self, kernel: MagicMock) -> None:
        module = OrganizationRuntimeModule()
        await module.start(kernel)
        await module.stop(kernel)
        assert module.started is False

    async def test_name(self) -> None:
        module = OrganizationRuntimeModule()
        assert module.name == "organization"


# =========================================================================
# Health
# =========================================================================


class TestOrganizationHealthCheck:
    @pytest.fixture
    def health(self) -> OrganizationHealthCheck:
        return OrganizationHealthCheck()

    async def test_check_healthy_by_default(self, health: OrganizationHealthCheck) -> None:
        report = await health.check()
        assert report.component == "organization"
        assert report.status.value == "healthy"

    async def test_set_degraded(self, health: OrganizationHealthCheck) -> None:
        health.set_degraded("database unavailable")
        report = await health.check()
        assert report.status.value == "degraded"

    async def test_name(self, health: OrganizationHealthCheck) -> None:
        assert health.name == "organization"
