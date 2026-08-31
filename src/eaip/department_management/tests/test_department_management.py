"""Tests for the department management package."""

from __future__ import annotations

import pydantic
import pytest

from eaip.department_management.events import (
    DepartmentAuditLogged,
    DepartmentBudgetUpdated,
    DepartmentCreated,
    DepartmentDeleted,
    DepartmentHierarchyChanged,
    DepartmentMemberAdded,
    DepartmentMerged,
    DepartmentReportGenerated,
    DepartmentResourceAllocated,
    DepartmentSplit,
)
from eaip.department_management.exceptions import (
    DepartmentBudgetError,
    DepartmentHierarchyError,
    DepartmentMemberError,
    DepartmentNotFoundError,
    DepartmentResourceError,
)
from eaip.department_management.models import (
    Department,
    DepartmentAuditEntry,
    DepartmentBudget,
    DepartmentCategory,
    DepartmentConfig,
    DepartmentContact,
    DepartmentHierarchy,
    DepartmentMember,
    DepartmentPolicy,
    DepartmentReport,
    DepartmentResource,
    DepartmentResourceType,
    DepartmentRole,
    DepartmentSettings,
    DepartmentStatus,
)
from eaip.department_management.service import DepartmentManagementService


class TestDepartmentModels:
    """Tests for department domain models."""

    def test_department_frozen(self) -> None:
        dept = Department(id="d1", name="Engineering")
        with pytest.raises(pydantic.ValidationError):
            dept.name = "Changed"  # type: ignore[misc]

    def test_department_defaults(self) -> None:
        dept = Department(id="d1", name="Engineering")
        assert dept.status is DepartmentStatus.ACTIVE
        assert dept.description == ""

    def test_department_budget_remaining(self) -> None:
        budget = DepartmentBudget(
            id="b1",
            department_id="d1",
            fiscal_year="2025",
            total_amount=1000.0,
            spent_amount=300.0,
        )
        assert budget.remaining == 700.0

    def test_department_resource_defaults(self) -> None:
        res = DepartmentResource(
            id="r1",
            department_id="d1",
            resource_type=DepartmentResourceType.EQUIPMENT,
            name="Laptops",
        )
        assert res.quantity == 1
        assert res.released_at is None

    def test_department_member_default_role(self) -> None:
        member = DepartmentMember(department_id="d1", user_id="u1")
        assert member.role is DepartmentRole.MEMBER
        assert member.is_active is True

    def test_department_status_enum(self) -> None:
        expected = [
            DepartmentStatus.ACTIVE,
            DepartmentStatus.INACTIVE,
            DepartmentStatus.SUSPENDED,
            DepartmentStatus.ARCHIVED,
        ]
        assert list(DepartmentStatus) == expected

    def test_department_config_defaults(self) -> None:
        config = DepartmentConfig()
        assert config.max_depth == 10
        assert config.allow_nested_departments is True
        assert config.default_role is DepartmentRole.MEMBER

    def test_department_category(self) -> None:
        cat = DepartmentCategory(id="c1", name="Engineering")
        assert cat.description == ""

    def test_department_contact_defaults(self) -> None:
        contact = DepartmentContact(department_id="d1")
        assert contact.email == ""
        assert contact.primary_contact_id is None

    def test_department_settings_defaults(self) -> None:
        settings = DepartmentSettings(department_id="d1")
        assert settings.max_members == 100
        assert settings.allow_external_collaboration is False

    def test_department_policy_defaults(self) -> None:
        policy = DepartmentPolicy(id="p1", department_id="d1", name="Test Policy")
        assert policy.enabled is True
        assert policy.rules == {}

    def test_department_hierarchy_frozen(self) -> None:
        h = DepartmentHierarchy(department_id="d1", ancestor_id="d0", depth=1)
        with pytest.raises(pydantic.ValidationError):
            h.depth = 2  # type: ignore[misc]

    def test_department_report_defaults(self) -> None:
        rpt = DepartmentReport(
            id="r1",
            department_id="d1",
            report_type="quarterly",
            title="Q1 Report",
        )
        assert rpt.generated_by == "system"
        assert rpt.data == {}

    def test_department_audit_entry_defaults(self) -> None:
        entry = DepartmentAuditEntry(id="a1", department_id="d1", action="created", actor_id="u1")
        assert entry.details == {}


class TestDepartmentManagementService:
    """Tests for DepartmentManagementService."""

    def test_create_department(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        assert dept.name == "Engineering"
        assert dept.status is DepartmentStatus.ACTIVE
        assert dept.id.startswith("dept_")
        events = svc.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], DepartmentCreated)
        assert events[0].department_id == dept.id

    def test_get_department_not_found(self) -> None:
        svc = DepartmentManagementService()
        with pytest.raises(DepartmentNotFoundError):
            svc.get_department("nonexistent")

    def test_get_department_found(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        fetched = svc.get_department(dept.id)
        assert fetched.id == dept.id

    def test_update_department(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        updated = svc.update_department(dept.id, {"name": "Engineering Updated"})
        assert updated.name == "Engineering Updated"

    def test_delete_department(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        svc.delete_department(dept.id)
        with pytest.raises(DepartmentNotFoundError):
            svc.get_department(dept.id)

    def test_delete_department_with_children_raises(self) -> None:
        svc = DepartmentManagementService()
        parent = svc.create_department(name="Parent")
        svc.create_department(name="Child", parent_id=parent.id)
        with pytest.raises(DepartmentHierarchyError):
            svc.delete_department(parent.id)

    def test_list_departments(self) -> None:
        svc = DepartmentManagementService()
        svc.create_department(name="Engineering")
        svc.create_department(name="Sales")
        assert len(svc.list_departments()) == 2

    def test_activate_department(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        svc.deactivate_department(dept.id)
        activated = svc.activate_department(dept.id)
        assert activated.status is DepartmentStatus.ACTIVE

    def test_deactivate_department(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        deactivated = svc.deactivate_department(dept.id)
        assert deactivated.status is DepartmentStatus.INACTIVE

    def test_merge_departments(self) -> None:
        svc = DepartmentManagementService()
        source = svc.create_department(name="Source")
        target = svc.create_department(name="Target")
        svc.add_member(source.id, "user1")
        result = svc.merge_departments(source.id, target.id)
        assert result.id == target.id
        assert len(svc.list_members(target.id)) == 1

    def test_split_department(self) -> None:
        svc = DepartmentManagementService()
        source = svc.create_department(name="Source")
        source_result, new_dept = svc.split_department(source.id, "New Dept")
        assert source_result.id == source.id
        assert new_dept.name == "New Dept"

    def test_change_parent(self) -> None:
        svc = DepartmentManagementService()
        parent1 = svc.create_department(name="Parent1")
        parent2 = svc.create_department(name="Parent2")
        child = svc.create_department(name="Child", parent_id=parent1.id)
        svc.change_parent(child.id, parent2.id)
        assert child.parent_id == parent1.id  # original not mutated
        fetched = svc.get_department(child.id)
        assert fetched.parent_id == parent2.id

    def test_change_parent_self_raises(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Dept")
        with pytest.raises(DepartmentHierarchyError):
            svc.change_parent(dept.id, dept.id)

    def test_get_ancestors(self) -> None:
        svc = DepartmentManagementService()
        parent = svc.create_department(name="Parent")
        child = svc.create_department(name="Child", parent_id=parent.id)
        grandchild = svc.create_department(name="Grandchild", parent_id=child.id)
        ancestors = svc.get_ancestors(grandchild.id)
        assert len(ancestors) == 2

    def test_get_descendants(self) -> None:
        svc = DepartmentManagementService()
        parent = svc.create_department(name="Parent")
        child = svc.create_department(name="Child", parent_id=parent.id)
        svc.create_department(name="Grandchild", parent_id=child.id)
        descendants = svc.get_descendants(parent.id)
        assert len(descendants) == 2

    def test_add_member(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        member = svc.add_member(dept.id, "user1", DepartmentRole.MANAGER)
        assert member.user_id == "user1"
        assert member.role is DepartmentRole.MANAGER

    def test_add_member_duplicate_raises(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        svc.add_member(dept.id, "user1")
        with pytest.raises(DepartmentMemberError):
            svc.add_member(dept.id, "user1")

    def test_remove_member(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        svc.add_member(dept.id, "user1")
        svc.remove_member(dept.id, "user1")
        assert len(svc.list_members(dept.id)) == 0

    def test_remove_member_not_found_raises(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        with pytest.raises(DepartmentMemberError):
            svc.remove_member(dept.id, "nonexistent")

    def test_change_member_role(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        svc.add_member(dept.id, "user1", DepartmentRole.MEMBER)
        updated = svc.change_member_role(dept.id, "user1", DepartmentRole.HEAD)
        assert updated.role is DepartmentRole.HEAD

    def test_create_budget(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        budget = svc.create_budget(dept.id, "2025", 50000.0)
        assert budget.fiscal_year == "2025"
        assert budget.total_amount == 50000.0

    def test_update_budget(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        budget = svc.create_budget(dept.id, "2025", 50000.0)
        updated = svc.update_budget(budget.id, total_amount=60000.0)
        assert updated.total_amount == 60000.0

    def test_get_budget_not_found(self) -> None:
        svc = DepartmentManagementService()
        with pytest.raises(DepartmentBudgetError):
            svc.get_budget("nonexistent")

    def test_allocate_resource(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        res = svc.allocate_resource(
            dept.id,
            DepartmentResourceType.EQUIPMENT,
            "Laptops",
            quantity=10,
        )
        assert res.name == "Laptops"
        assert res.quantity == 10

    def test_release_resource(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        res = svc.allocate_resource(dept.id, DepartmentResourceType.EQUIPMENT, "Laptops")
        released = svc.release_resource(res.id)
        assert released.released_at is not None

    def test_release_resource_not_found(self) -> None:
        svc = DepartmentManagementService()
        with pytest.raises(DepartmentResourceError):
            svc.release_resource("nonexistent")

    def test_generate_report(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        rpt = svc.generate_report(dept.id, "quarterly", "Q1 Report", {"revenue": 1000})
        assert rpt.title == "Q1 Report"
        assert rpt.data["revenue"] == 1000

    def test_log_audit_entry(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        entry = svc.log_audit_entry(dept.id, "member.added", "admin")
        assert entry.action == "member.added"
        events = svc.collect_events()
        assert any(isinstance(e, DepartmentAuditLogged) for e in events)

    def test_update_settings(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        settings = svc.update_settings(dept.id, {"max_members": 200})
        assert settings.max_members == 200

    def test_get_config_defaults(self) -> None:
        svc = DepartmentManagementService()
        config = svc.get_config()
        assert config.max_depth == 10

    def test_update_config(self) -> None:
        svc = DepartmentManagementService()
        config = svc.update_config({"max_depth": 5})
        assert config.max_depth == 5

    def test_create_policy(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        policy = svc.create_policy(dept.id, "Budget Policy", rules={"max_budget": 100000})
        assert policy.name == "Budget Policy"

    def test_create_category(self) -> None:
        svc = DepartmentManagementService()
        cat = svc.create_category("Engineering", "Engineering departments")
        assert cat.name == "Engineering"

    def test_set_contact(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        contact = svc.set_contact(dept.id, email="eng@example.com", phone="123-4567")
        assert contact.email == "eng@example.com"

    def test_get_contact(self) -> None:
        svc = DepartmentManagementService()
        dept = svc.create_department(name="Engineering")
        svc.set_contact(dept.id, email="eng@example.com")
        contact = svc.get_contact(dept.id)
        assert contact is not None
        assert contact.email == "eng@example.com"

    def test_events_cleared_after_collect(self) -> None:
        svc = DepartmentManagementService()
        svc.create_department(name="Engineering")
        svc.collect_events()
        assert svc.collect_events() == []

    def test_event_type_strings(self) -> None:
        prefix = "eaip.department_management"
        assert DepartmentCreated.event_type == f"{prefix}.department_created"
        assert DepartmentDeleted.event_type == f"{prefix}.department_deleted"
        assert DepartmentMerged.event_type == f"{prefix}.department_merged"
        assert DepartmentSplit.event_type == f"{prefix}.department_split"
        assert DepartmentHierarchyChanged.event_type == f"{prefix}.department_hierarchy_changed"
        assert DepartmentMemberAdded.event_type == f"{prefix}.department_member_added"
        assert DepartmentBudgetUpdated.event_type == f"{prefix}.department_budget_updated"
        assert DepartmentResourceAllocated.event_type == f"{prefix}.department_resource_allocated"
        assert DepartmentReportGenerated.event_type == f"{prefix}.department_report_generated"
        assert DepartmentAuditLogged.event_type == f"{prefix}.department_audit_logged"
