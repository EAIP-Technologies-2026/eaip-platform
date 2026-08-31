"""Department management service — CRUD, hierarchy, members, budgets, resources, reports."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from eaip.department_management.events import (
    DepartmentActivated,
    DepartmentAuditLogged,
    DepartmentBudgetUpdated,
    DepartmentCreated,
    DepartmentDeactivated,
    DepartmentDeleted,
    DepartmentHierarchyChanged,
    DepartmentMemberAdded,
    DepartmentMemberRemoved,
    DepartmentMemberRoleChanged,
    DepartmentMerged,
    DepartmentReportGenerated,
    DepartmentResourceAllocated,
    DepartmentResourceReleased,
    DepartmentSettingsUpdated,
    DepartmentSplit,
    DepartmentUpdated,
)
from eaip.department_management.exceptions import (
    DepartmentBudgetError,
    DepartmentConfigError,
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
from eaip.logging.context import get_logger


class DepartmentManagementService:
    """Service layer for department management operations."""

    def __init__(self) -> None:
        """Initialize DepartmentManagementService."""
        self._departments: dict[str, Department] = {}
        self._hierarchy: list[DepartmentHierarchy] = []
        self._members: list[DepartmentMember] = []
        self._budgets: dict[str, DepartmentBudget] = {}
        self._resources: dict[str, DepartmentResource] = {}
        self._reports: dict[str, DepartmentReport] = {}
        self._audit_log: list[DepartmentAuditEntry] = []
        self._policies: list[DepartmentPolicy] = []
        self._categories: dict[str, DepartmentCategory] = {}
        self._contacts: dict[str, DepartmentContact] = {}
        self._settings: dict[str, DepartmentSettings] = {}
        self._config: DepartmentConfig = DepartmentConfig()
        self._events: list[Any] = []
        self._log = get_logger("eaip.department_management.service")

    # ---- events ----

    def collect_events(self) -> list[Any]:
        """Return and clear accumulated domain events."""
        events = list(self._events)
        self._events.clear()
        return events

    # ---- departments (CRUD) ----

    def create_department(
        self,
        name: str,
        description: str = "",
        parent_id: str | None = None,
        category_id: str | None = None,
        created_by: str = "system",
    ) -> Department:
        """Create a new department."""
        depth = 0
        if parent_id:
            if parent_id not in self._departments:
                raise DepartmentNotFoundError(f"Parent department {parent_id} not found")
            depth = self._get_depth(parent_id) + 1
            if depth > self._config.max_depth:
                raise DepartmentHierarchyError(
                    f"Maximum nesting depth {self._config.max_depth} exceeded"
                )

        dept = Department(
            id=self._next_id("dept"),
            name=name,
            description=description,
            parent_id=parent_id,
            category_id=category_id,
        )
        self._departments[dept.id] = dept

        if parent_id:
            self._hierarchy.append(
                DepartmentHierarchy(
                    department_id=dept.id,
                    ancestor_id=parent_id,
                    depth=1,
                    path=[parent_id, dept.id],
                )
            )

        self._events.append(
            DepartmentCreated(
                department_id=dept.id,
                name=name,
                parent_id=parent_id,
                created_by=created_by,
            )
        )
        return dept

    def get_department(self, department_id: str) -> Department:
        """Get a department by ID."""
        dept = self._departments.get(department_id)
        if dept is None:
            raise DepartmentNotFoundError(f"Department {department_id} not found")
        return dept

    def update_department(
        self,
        department_id: str,
        changes: dict[str, Any],
        updated_by: str = "system",
    ) -> Department:
        """Update a department's attributes."""
        dept = self.get_department(department_id)
        allowed = {"name", "description", "category_id", "metadata"}
        filtered = {k: v for k, v in changes.items() if k in allowed}
        if not filtered:
            raise DepartmentConfigError("No valid fields to update")
        updated = dept.model_copy(update={**filtered, "updated_at": datetime.now()})
        self._departments[department_id] = updated
        self._events.append(
            DepartmentUpdated(
                department_id=department_id,
                changes=filtered,
                updated_by=updated_by,
            )
        )
        return updated

    def delete_department(self, department_id: str, deleted_by: str = "system") -> None:
        """Delete a department."""
        self.get_department(department_id)
        for d in self._departments.values():
            if d.parent_id == department_id:
                raise DepartmentHierarchyError(
                    f"Cannot delete department {department_id}: it has child departments"
                )
        del self._departments[department_id]
        self._hierarchy = [h for h in self._hierarchy if h.department_id != department_id]
        self._members = [m for m in self._members if m.department_id != department_id]
        self._events.append(DepartmentDeleted(department_id=department_id, deleted_by=deleted_by))

    def list_departments(self) -> list[Department]:
        """Return all departments."""
        return list(self._departments.values())

    # ---- lifecycle ----

    def activate_department(self, department_id: str, activated_by: str = "system") -> Department:
        """Activate a department."""
        dept = self.get_department(department_id)
        updated = dept.model_copy(
            update={
                "status": DepartmentStatus.ACTIVE,
                "updated_at": datetime.now(),
            }
        )
        self._departments[department_id] = updated
        self._events.append(
            DepartmentActivated(department_id=department_id, activated_by=activated_by)
        )
        return updated

    def deactivate_department(
        self, department_id: str, deactivated_by: str = "system"
    ) -> Department:
        """Deactivate a department."""
        dept = self.get_department(department_id)
        updated = dept.model_copy(
            update={
                "status": DepartmentStatus.INACTIVE,
                "updated_at": datetime.now(),
            }
        )
        self._departments[department_id] = updated
        self._events.append(
            DepartmentDeactivated(
                department_id=department_id,
                deactivated_by=deactivated_by,
            )
        )
        return updated

    def merge_departments(
        self,
        source_id: str,
        target_id: str,
        merged_by: str = "system",
    ) -> Department:
        """Merge source department into target department."""
        self.get_department(source_id)
        target = self.get_department(target_id)
        for member in [m for m in self._members if m.department_id == source_id]:
            self._members.append(
                DepartmentMember(
                    department_id=target_id,
                    user_id=member.user_id,
                    role=member.role,
                )
            )
        self._members = [m for m in self._members if m.department_id != source_id]
        del self._departments[source_id]
        self._events.append(
            DepartmentMerged(
                source_department_id=source_id,
                target_department_id=target_id,
                merged_by=merged_by,
            )
        )
        return target

    def split_department(
        self,
        source_id: str,
        new_name: str,
        split_by: str = "system",
    ) -> tuple[Department, Department]:
        """Split a department into two."""
        source = self.get_department(source_id)
        new_dept = self.create_department(
            name=new_name,
            parent_id=source.parent_id,
            created_by=split_by,
        )
        self._events.append(
            DepartmentSplit(
                source_department_id=source_id,
                new_department_id=new_dept.id,
                split_by=split_by,
            )
        )
        return source, new_dept

    # ---- hierarchy ----

    def change_parent(
        self,
        department_id: str,
        new_parent_id: str | None,
        changed_by: str = "system",
    ) -> Department:
        """Change the parent of a department."""
        dept = self.get_department(department_id)
        if new_parent_id and new_parent_id not in self._departments:
            raise DepartmentNotFoundError(f"Parent department {new_parent_id} not found")
        if department_id == new_parent_id:
            raise DepartmentHierarchyError("A department cannot be its own parent")
        old_parent_id = dept.parent_id
        updated = dept.model_copy(
            update={
                "parent_id": new_parent_id,
                "updated_at": datetime.now(),
            }
        )
        self._departments[department_id] = updated
        self._hierarchy = [h for h in self._hierarchy if h.department_id != department_id]
        if new_parent_id:
            self._hierarchy.append(
                DepartmentHierarchy(
                    department_id=department_id,
                    ancestor_id=new_parent_id,
                    depth=1,
                    path=[new_parent_id, department_id],
                )
            )
        self._events.append(
            DepartmentHierarchyChanged(
                department_id=department_id,
                old_parent_id=old_parent_id,
                new_parent_id=new_parent_id,
                changed_by=changed_by,
            )
        )
        return updated

    def get_ancestors(self, department_id: str) -> list[str]:
        """Return ancestor IDs for a department."""
        result: list[str] = []
        current = self._departments.get(department_id)
        while current and current.parent_id:
            parent = self._departments.get(current.parent_id)
            if parent:
                result.append(parent.id)
                current = parent
            else:
                break
        return result

    def get_descendants(self, department_id: str) -> list[Department]:
        """Return all descendants of a department."""
        return [
            d
            for d in self._departments.values()
            if d.parent_id == department_id or department_id in self.get_ancestors(d.id)
        ]

    def _get_depth(self, department_id: str) -> int:
        depth = 0
        current = self._departments.get(department_id)
        while current and current.parent_id:
            depth += 1
            current = self._departments.get(current.parent_id)
        return depth

    # ---- members ----

    def add_member(
        self,
        department_id: str,
        user_id: str,
        role: DepartmentRole = DepartmentRole.MEMBER,
        added_by: str = "system",
    ) -> DepartmentMember:
        """Add a member to a department."""
        self.get_department(department_id)
        existing = [
            m for m in self._members if m.department_id == department_id and m.user_id == user_id
        ]
        if existing:
            raise DepartmentMemberError(
                f"User {user_id} is already a member of department {department_id}"
            )
        member = DepartmentMember(department_id=department_id, user_id=user_id, role=role)
        self._members.append(member)
        self._events.append(
            DepartmentMemberAdded(
                department_id=department_id,
                user_id=user_id,
                role=role.value,
                added_by=added_by,
            )
        )
        return member

    def remove_member(
        self,
        department_id: str,
        user_id: str,
        removed_by: str = "system",
    ) -> None:
        """Remove a member from a department."""
        self.get_department(department_id)
        before = len(self._members)
        self._members = [
            m
            for m in self._members
            if not (m.department_id == department_id and m.user_id == user_id)
        ]
        if len(self._members) == before:
            raise DepartmentMemberError(
                f"User {user_id} is not a member of department {department_id}"
            )
        self._events.append(
            DepartmentMemberRemoved(
                department_id=department_id,
                user_id=user_id,
                removed_by=removed_by,
            )
        )

    def change_member_role(
        self,
        department_id: str,
        user_id: str,
        new_role: DepartmentRole,
        changed_by: str = "system",
    ) -> DepartmentMember:
        """Change a member's role."""
        for i, member in enumerate(self._members):
            if member.department_id == department_id and member.user_id == user_id:
                old_role = member.role
                updated = member.model_copy(update={"role": new_role})
                self._members[i] = updated
                self._events.append(
                    DepartmentMemberRoleChanged(
                        department_id=department_id,
                        user_id=user_id,
                        old_role=old_role.value,
                        new_role=new_role.value,
                        changed_by=changed_by,
                    )
                )
                return updated
        raise DepartmentMemberError(f"User {user_id} is not a member of department {department_id}")

    def list_members(self, department_id: str) -> list[DepartmentMember]:
        """List all members of a department."""
        return [m for m in self._members if m.department_id == department_id]

    # ---- budgets ----

    def create_budget(
        self,
        department_id: str,
        fiscal_year: str,
        total_amount: float = 0.0,
        currency: str = "USD",
        updated_by: str = "system",
    ) -> DepartmentBudget:
        """Create a budget for a department."""
        self.get_department(department_id)
        budget = DepartmentBudget(
            id=self._next_id("budget"),
            department_id=department_id,
            fiscal_year=fiscal_year,
            total_amount=total_amount,
            currency=currency,
        )
        self._budgets[budget.id] = budget
        self._events.append(
            DepartmentBudgetUpdated(
                budget_id=budget.id,
                department_id=department_id,
                fiscal_year=fiscal_year,
                new_total=total_amount,
                updated_by=updated_by,
            )
        )
        return budget

    def update_budget(
        self,
        budget_id: str,
        total_amount: float | None = None,
        spent_amount: float | None = None,
        updated_by: str = "system",
    ) -> DepartmentBudget:
        """Update a budget."""
        budget = self._budgets.get(budget_id)
        if budget is None:
            raise DepartmentBudgetError(f"Budget {budget_id} not found")
        updates: dict[str, Any] = {"updated_at": datetime.now()}
        if total_amount is not None:
            updates["total_amount"] = total_amount
        if spent_amount is not None:
            updates["spent_amount"] = spent_amount
        old_total = budget.total_amount
        new_total = updates.get("total_amount", budget.total_amount)
        updated = budget.model_copy(update=updates)
        self._budgets[budget_id] = updated
        self._events.append(
            DepartmentBudgetUpdated(
                budget_id=budget_id,
                department_id=budget.department_id,
                fiscal_year=budget.fiscal_year,
                old_total=old_total,
                new_total=new_total,
                updated_by=updated_by,
            )
        )
        return updated

    def get_budget(self, budget_id: str) -> DepartmentBudget:
        """Get a budget by ID."""
        budget = self._budgets.get(budget_id)
        if budget is None:
            raise DepartmentBudgetError(f"Budget {budget_id} not found")
        return budget

    def list_budgets(self, department_id: str) -> list[DepartmentBudget]:
        """List budgets for a department."""
        return [b for b in self._budgets.values() if b.department_id == department_id]

    # ---- resources ----

    def allocate_resource(
        self,
        department_id: str,
        resource_type: DepartmentResourceType,
        name: str,
        description: str = "",
        quantity: int = 1,
        allocated_by: str = "system",
    ) -> DepartmentResource:
        """Allocate a resource to a department."""
        self.get_department(department_id)
        resource = DepartmentResource(
            id=self._next_id("res"),
            department_id=department_id,
            resource_type=resource_type,
            name=name,
            description=description,
            quantity=quantity,
        )
        self._resources[resource.id] = resource
        self._events.append(
            DepartmentResourceAllocated(
                resource_id=resource.id,
                department_id=department_id,
                resource_type=resource_type.value,
                name=name,
                allocated_by=allocated_by,
            )
        )
        return resource

    def release_resource(self, resource_id: str, released_by: str = "system") -> DepartmentResource:
        """Release a resource from a department."""
        resource = self._resources.get(resource_id)
        if resource is None:
            raise DepartmentResourceError(f"Resource {resource_id} not found")
        updated = resource.model_copy(update={"released_at": datetime.now()})
        self._resources[resource_id] = updated
        self._events.append(
            DepartmentResourceReleased(
                resource_id=resource_id,
                department_id=resource.department_id,
                released_by=released_by,
            )
        )
        return updated

    def list_resources(self, department_id: str) -> list[DepartmentResource]:
        """List resources for a department."""
        return [r for r in self._resources.values() if r.department_id == department_id]

    # ---- reports ----

    def generate_report(
        self,
        department_id: str,
        report_type: str,
        title: str,
        data: dict[str, Any] | None = None,
        generated_by: str = "system",
    ) -> DepartmentReport:
        """Generate a report for a department."""
        self.get_department(department_id)
        report = DepartmentReport(
            id=self._next_id("rpt"),
            department_id=department_id,
            report_type=report_type,
            title=title,
            data=data or {},
            generated_by=generated_by,
        )
        self._reports[report.id] = report
        self._events.append(
            DepartmentReportGenerated(
                report_id=report.id,
                department_id=department_id,
                report_type=report_type,
                generated_by=generated_by,
            )
        )
        return report

    def list_reports(self, department_id: str) -> list[DepartmentReport]:
        """List reports for a department."""
        return [r for r in self._reports.values() if r.department_id == department_id]

    # ---- audit ----

    def log_audit_entry(
        self,
        department_id: str,
        action: str,
        actor_id: str,
        details: dict[str, Any] | None = None,
    ) -> DepartmentAuditEntry:
        """Log an audit entry for a department."""
        entry = DepartmentAuditEntry(
            id=self._next_id("audit"),
            department_id=department_id,
            action=action,
            actor_id=actor_id,
            details=details or {},
        )
        self._audit_log.append(entry)
        self._events.append(
            DepartmentAuditLogged(
                entry_id=entry.id,
                department_id=department_id,
                action=action,
                actor_id=actor_id,
            )
        )
        return entry

    def list_audit_entries(self, department_id: str) -> list[DepartmentAuditEntry]:
        """List audit entries for a department."""
        return [e for e in self._audit_log if e.department_id == department_id]

    # ---- settings ----

    def update_settings(
        self,
        department_id: str,
        changes: dict[str, Any],
        updated_by: str = "system",
    ) -> DepartmentSettings:
        """Update settings for a department."""
        self.get_department(department_id)
        current = self._settings.get(department_id, DepartmentSettings(department_id=department_id))
        updated = current.model_copy(update=changes)
        self._settings[department_id] = updated
        self._events.append(
            DepartmentSettingsUpdated(
                department_id=department_id,
                changes=changes,
                updated_by=updated_by,
            )
        )
        return updated

    def get_settings(self, department_id: str) -> DepartmentSettings:
        """Get settings for a department."""
        return self._settings.get(department_id, DepartmentSettings(department_id=department_id))

    # ---- config ----

    def get_config(self) -> DepartmentConfig:
        """Get the global department management config."""
        return self._config

    def update_config(self, changes: dict[str, Any]) -> DepartmentConfig:
        """Update the global department management config."""
        allowed = {
            "max_depth",
            "allow_nested_departments",
            "default_role",
            "audit_enabled",
        }
        filtered = {k: v for k, v in changes.items() if k in allowed}
        if not filtered:
            raise DepartmentConfigError("No valid config fields to update")
        self._config = self._config.model_copy(update=filtered)
        return self._config

    # ---- policies ----

    def create_policy(
        self,
        department_id: str,
        name: str,
        description: str = "",
        rules: dict[str, Any] | None = None,
    ) -> DepartmentPolicy:
        """Create a policy for a department."""
        self.get_department(department_id)
        policy = DepartmentPolicy(
            id=self._next_id("pol"),
            department_id=department_id,
            name=name,
            description=description,
            rules=rules or {},
        )
        self._policies.append(policy)
        return policy

    def list_policies(self, department_id: str) -> list[DepartmentPolicy]:
        """List policies for a department."""
        return [p for p in self._policies if p.department_id == department_id]

    # ---- categories ----

    def create_category(self, name: str, description: str = "") -> DepartmentCategory:
        """Create a department category."""
        cat = DepartmentCategory(id=self._next_id("cat"), name=name, description=description)
        self._categories[cat.id] = cat
        return cat

    def list_categories(self) -> list[DepartmentCategory]:
        """List all categories."""
        return list(self._categories.values())

    # ---- contacts ----

    def set_contact(self, department_id: str, **kwargs: Any) -> DepartmentContact:
        """Set contact info for a department."""
        self.get_department(department_id)
        contact = DepartmentContact(department_id=department_id, **kwargs)
        self._contacts[department_id] = contact
        return contact

    def get_contact(self, department_id: str) -> DepartmentContact | None:
        """Get contact info for a department."""
        return self._contacts.get(department_id)

    # ---- helpers ----

    _next_counter: int = 0

    def _next_id(self, prefix: str) -> str:
        type(self)._next_counter += 1
        return f"{prefix}_{type(self)._next_counter}"
