"""Tests for the knowledge permissions subsystem."""

from __future__ import annotations

import pytest

from eaip.knowledge_permissions.events import (
    KnowledgeAccessDenied,
    KnowledgeAccessGranted,
    KnowledgeAccessRuleCreated,
    KnowledgeAccessRuleEvaluated,
    KnowledgePermissionAuditLogged,
    KnowledgePermissionCreated,
    KnowledgePermissionDeleted,
    KnowledgePermissionGranted,
    KnowledgePermissionPolicyUpdated,
    KnowledgePermissionReportGenerated,
    KnowledgePermissionRevoked,
    KnowledgePermissionUpdated,
    KnowledgeRoleAssigned,
    KnowledgeRoleCreated,
    KnowledgeRoleDeleted,
    KnowledgeRoleUnassigned,
    KnowledgeRoleUpdated,
)
from eaip.knowledge_permissions.exceptions import (
    KnowledgePermissionError,
    PermissionAssignmentError,
    PermissionAuditError,
    PermissionConfigError,
    PermissionDeniedError,
    PermissionEvaluationError,
    PermissionNotFoundError,
    PermissionRoleError,
)
from eaip.knowledge_permissions.health import KnowledgePermissionHealthCheck
from eaip.knowledge_permissions.models import (
    AccessControlList,
    KnowledgeAccessAuditEntry,
    KnowledgeAccessRule,
    KnowledgeAccessScope,
    KnowledgePermission,
    KnowledgePermissionConditionOperator,
    KnowledgePermissionConfig,
    KnowledgePermissionEvaluation,
    KnowledgePermissionPolicy,
    KnowledgePermissionReport,
    KnowledgeResourceAccess,
    KnowledgeResourcePermission,
    KnowledgeRole,
    KnowledgeRoleAssignment,
    PermissionLevel,
)
from eaip.knowledge_permissions.service import KnowledgePermissionService


class TestModels:
    def test_permission_level_values(self) -> None:
        assert PermissionLevel.NONE.value == "none"
        assert PermissionLevel.READ.value == "read"
        assert PermissionLevel.WRITE.value == "write"
        assert PermissionLevel.ADMIN.value == "admin"
        assert PermissionLevel.OWNER.value == "owner"

    def test_knowledge_access_scope_values(self) -> None:
        assert KnowledgeAccessScope.COLLECTION.value == "collection"
        assert KnowledgeAccessScope.DOCUMENT.value == "document"
        assert KnowledgeAccessScope.CATEGORY.value == "category"
        assert KnowledgeAccessScope.GLOBAL.value == "global"

    def test_permission_frozen(self) -> None:
        perm = KnowledgePermission(
            id="p1", subject_id="user1", resource_id="doc1", level=PermissionLevel.READ
        )
        with pytest.raises(AttributeError):
            perm.level = PermissionLevel.WRITE

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            KnowledgePermission(
                id="p1",
                subject_id="user1",
                resource_id="doc1",
                level=PermissionLevel.READ,
                unknown_field="x",  # type: ignore[call-arg]
            )

    def test_knowledge_permission_config_defaults(self) -> None:
        config = KnowledgePermissionConfig()
        assert config.enabled is True
        assert config.default_level == PermissionLevel.NONE
        assert config.audit_enabled is True
        assert config.role_based_enabled is True
        assert config.acl_enabled is True
        assert config.max_cache_seconds == 300
        assert config.max_rules_per_policy == 100

    def test_knowledge_permission_evaluation_defaults(self) -> None:
        eval_result = KnowledgePermissionEvaluation(
            subject_id="user1",
            resource_id="doc1",
            requested_level=PermissionLevel.READ,
            effective_level=PermissionLevel.READ,
            granted=True,
        )
        assert eval_result.matched_rules == ()
        assert eval_result.matched_roles == ()
        assert eval_result.explanation == ""

    def test_knowledge_permission_report_defaults(self) -> None:
        report = KnowledgePermissionReport(id="rpt1")
        assert report.total_permissions == 0
        assert report.total_rules == 0
        assert report.total_roles == 0
        assert report.total_assignments == 0

    def test_knowledge_role_defaults(self) -> None:
        role = KnowledgeRole(id="r1", name="viewer")
        assert role.description == ""
        assert role.permissions == ()
        assert role.metadata == {}

    def test_knowledge_role_assignment_defaults(self) -> None:
        assignment = KnowledgeRoleAssignment(
            id="a1", role_id="r1", subject_id="user1", scope=KnowledgeAccessScope.COLLECTION
        )
        assert assignment.scope_id == ""
        assert assignment.assigned_by == ""
        assert assignment.expires_at is None

    def test_knowledge_access_rule_defaults(self) -> None:
        rule = KnowledgeAccessRule(
            id="rule1",
            name="test-rule",
            scope=KnowledgeAccessScope.COLLECTION,
        )
        assert rule.resource_pattern == "*"
        assert rule.allowed_levels == ()
        assert rule.conditions == ()
        assert rule.priority == 0
        assert rule.enabled is True
        assert rule.description == ""

    def test_knowledge_permission_condition_operator_values(self) -> None:
        assert KnowledgePermissionConditionOperator.EQ.value == "eq"
        assert KnowledgePermissionConditionOperator.IN.value == "in"
        assert KnowledgePermissionConditionOperator.MATCHES.value == "matches"

    def test_access_control_list_defaults(self) -> None:
        acl = AccessControlList(resource_id="doc1")
        assert acl.entries == ()
        assert acl.version == 1

    def test_knowledge_resource_permission_defaults(self) -> None:
        rp = KnowledgeResourcePermission(resource_pattern="*", level=PermissionLevel.READ)
        assert rp.scope == KnowledgeAccessScope.COLLECTION

    def test_knowledge_resource_access_defaults(self) -> None:
        ra = KnowledgeResourceAccess(
            subject_id="user1", resource_id="doc1", effective_level=PermissionLevel.READ
        )
        assert ra.source_rules == ()
        assert ra.source_roles == ()
        assert ra.expires_at is None


class TestEvents:
    def test_permission_created_event_type(self) -> None:
        perm = KnowledgePermission(
            id="p1", subject_id="user1", resource_id="doc1", level=PermissionLevel.READ
        )
        event = KnowledgePermissionCreated(permission=perm)
        assert event.event_type == "eaip.knowledge_permissions.permission.created"

    def test_permission_updated_event(self) -> None:
        event = KnowledgePermissionUpdated(
            permission_id="p1", changes={"level": PermissionLevel.WRITE}
        )
        assert event.event_type == "eaip.knowledge_permissions.permission.updated"

    def test_permission_deleted_event(self) -> None:
        event = KnowledgePermissionDeleted(permission_id="p1")
        assert event.event_type == "eaip.knowledge_permissions.permission.deleted"

    def test_permission_granted_event(self) -> None:
        access = KnowledgeResourceAccess(
            subject_id="user1", resource_id="doc1", effective_level=PermissionLevel.READ
        )
        event = KnowledgePermissionGranted(
            subject_id="user1", resource_id="doc1", level="read", access=access
        )
        assert event.event_type == "eaip.knowledge_permissions.permission.granted"

    def test_permission_revoked_event(self) -> None:
        event = KnowledgePermissionRevoked(
            subject_id="user1", resource_id="doc1", permission_id="p1"
        )
        assert event.event_type == "eaip.knowledge_permissions.permission.revoked"

    def test_role_created_event(self) -> None:
        role = KnowledgeRole(id="r1", name="viewer")
        event = KnowledgeRoleCreated(role=role)
        assert event.event_type == "eaip.knowledge_permissions.role.created"

    def test_role_updated_event(self) -> None:
        event = KnowledgeRoleUpdated(role_id="r1", changes={"name": "editor"})
        assert event.event_type == "eaip.knowledge_permissions.role.updated"

    def test_role_deleted_event(self) -> None:
        event = KnowledgeRoleDeleted(role_id="r1")
        assert event.event_type == "eaip.knowledge_permissions.role.deleted"

    def test_role_assigned_event(self) -> None:
        assignment = KnowledgeRoleAssignment(
            id="a1", role_id="r1", subject_id="user1", scope=KnowledgeAccessScope.COLLECTION
        )
        event = KnowledgeRoleAssigned(assignment=assignment)
        assert event.event_type == "eaip.knowledge_permissions.role.assigned"

    def test_role_unassigned_event(self) -> None:
        event = KnowledgeRoleUnassigned(assignment_id="a1", role_id="r1", subject_id="user1")
        assert event.event_type == "eaip.knowledge_permissions.role.unassigned"

    def test_access_rule_created_event(self) -> None:
        rule = KnowledgeAccessRule(
            id="rule1",
            name="test",
            scope=KnowledgeAccessScope.COLLECTION,
        )
        event = KnowledgeAccessRuleCreated(rule=rule)
        assert event.event_type == "eaip.knowledge_permissions.access_rule.created"

    def test_access_rule_evaluated_event(self) -> None:
        event = KnowledgeAccessRuleEvaluated(
            rule_id="rule1", subject_id="user1", resource_id="doc1", matched=True
        )
        assert event.event_type == "eaip.knowledge_permissions.access_rule.evaluated"

    def test_access_granted_event(self) -> None:
        eval_result = KnowledgePermissionEvaluation(
            subject_id="user1",
            resource_id="doc1",
            requested_level=PermissionLevel.READ,
            effective_level=PermissionLevel.READ,
            granted=True,
        )
        event = KnowledgeAccessGranted(
            subject_id="user1", resource_id="doc1", level="read", evaluation=eval_result
        )
        assert event.event_type == "eaip.knowledge_permissions.access.granted"

    def test_access_denied_event(self) -> None:
        eval_result = KnowledgePermissionEvaluation(
            subject_id="user1",
            resource_id="doc1",
            requested_level=PermissionLevel.WRITE,
            effective_level=PermissionLevel.READ,
            granted=False,
        )
        event = KnowledgeAccessDenied(
            subject_id="user1",
            resource_id="doc1",
            requested_level="write",
            evaluation=eval_result,
        )
        assert event.event_type == "eaip.knowledge_permissions.access.denied"

    def test_audit_logged_event(self) -> None:
        entry = KnowledgeAccessAuditEntry(
            id="e1",
            subject_id="user1",
            action="read",
            resource_id="doc1",
            granted=True,
            level=PermissionLevel.READ,
        )
        event = KnowledgePermissionAuditLogged(entry=entry)
        assert event.event_type == "eaip.knowledge_permissions.audit.logged"

    def test_policy_updated_event(self) -> None:
        policy = KnowledgePermissionPolicy(id="pol1", name="default")
        event = KnowledgePermissionPolicyUpdated(policy=policy)
        assert event.event_type == "eaip.knowledge_permissions.policy.updated"

    def test_report_generated_event(self) -> None:
        report = KnowledgePermissionReport(id="rpt1")
        event = KnowledgePermissionReportGenerated(report=report)
        assert event.event_type == "eaip.knowledge_permissions.report.generated"


class TestExceptions:
    def test_knowledge_permission_error(self) -> None:
        exc = KnowledgePermissionError("something went wrong")
        assert "something went wrong" in str(exc)

    def test_permission_not_found_error(self) -> None:
        exc = PermissionNotFoundError("permission not found")
        assert isinstance(exc, KnowledgePermissionError)

    def test_permission_denied_error(self) -> None:
        exc = PermissionDeniedError("access denied")
        assert isinstance(exc, KnowledgePermissionError)

    def test_permission_config_error(self) -> None:
        exc = PermissionConfigError("invalid config")
        assert isinstance(exc, KnowledgePermissionError)

    def test_permission_evaluation_error(self) -> None:
        exc = PermissionEvaluationError("evaluation failed")
        assert isinstance(exc, KnowledgePermissionError)

    def test_permission_role_error(self) -> None:
        exc = PermissionRoleError("role not found")
        assert isinstance(exc, KnowledgePermissionError)

    def test_permission_assignment_error(self) -> None:
        exc = PermissionAssignmentError("assignment failed")
        assert isinstance(exc, KnowledgePermissionError)

    def test_permission_audit_error(self) -> None:
        exc = PermissionAuditError("audit failed")
        assert isinstance(exc, KnowledgePermissionError)


class TestKnowledgePermissionService:
    def test_initial_config(self) -> None:
        service = KnowledgePermissionService()
        assert service.config.enabled is True

    def test_update_config(self) -> None:
        service = KnowledgePermissionService()
        updated = service.update_config(enabled=False)
        assert updated.enabled is False
        assert service.config.enabled is False

    def test_create_and_get_permission(self) -> None:
        service = KnowledgePermissionService()
        perm = KnowledgePermission(
            id="p1", subject_id="user1", resource_id="doc1", level=PermissionLevel.READ
        )
        service.create_permission(perm)
        assert service.get_permission("p1").level == PermissionLevel.READ

    def test_get_permission_not_found(self) -> None:
        service = KnowledgePermissionService()
        with pytest.raises(PermissionNotFoundError):
            service.get_permission("nonexistent")

    def test_update_permission(self) -> None:
        service = KnowledgePermissionService()
        perm = KnowledgePermission(
            id="p1", subject_id="user1", resource_id="doc1", level=PermissionLevel.READ
        )
        service.create_permission(perm)
        updated = service.update_permission("p1", level=PermissionLevel.WRITE)
        assert updated.level == PermissionLevel.WRITE

    def test_delete_permission(self) -> None:
        service = KnowledgePermissionService()
        perm = KnowledgePermission(
            id="p1", subject_id="user1", resource_id="doc1", level=PermissionLevel.READ
        )
        service.create_permission(perm)
        service.delete_permission("p1")
        assert len(service.list_permissions()) == 0

    def test_delete_permission_not_found(self) -> None:
        service = KnowledgePermissionService()
        with pytest.raises(PermissionNotFoundError):
            service.delete_permission("nonexistent")

    def test_create_and_get_access_rule(self) -> None:
        service = KnowledgePermissionService()
        rule = KnowledgeAccessRule(
            id="rule1",
            name="test-rule",
            scope=KnowledgeAccessScope.COLLECTION,
        )
        service.create_access_rule(rule)
        assert service.get_access_rule("rule1").name == "test-rule"

    def test_access_rule_lifecycle(self) -> None:
        service = KnowledgePermissionService()
        rule = KnowledgeAccessRule(
            id="rule1",
            name="test",
            scope=KnowledgeAccessScope.COLLECTION,
        )
        service.create_access_rule(rule)
        service.update_access_rule("rule1", name="updated")
        assert service.get_access_rule("rule1").name == "updated"
        service.delete_access_rule("rule1")
        assert len(service.list_access_rules()) == 0

    def test_create_and_get_role(self) -> None:
        service = KnowledgePermissionService()
        role = KnowledgeRole(id="r1", name="viewer")
        service.create_role(role)
        assert service.get_role("r1").name == "viewer"

    def test_get_role_not_found(self) -> None:
        service = KnowledgePermissionService()
        with pytest.raises(PermissionRoleError):
            service.get_role("nonexistent")

    def test_role_lifecycle(self) -> None:
        service = KnowledgePermissionService()
        role = KnowledgeRole(id="r1", name="viewer")
        service.create_role(role)
        service.update_role("r1", name="editor")
        assert service.get_role("r1").name == "editor"
        service.delete_role("r1")
        assert len(service.list_roles()) == 0

    def test_assign_and_unassign_role(self) -> None:
        service = KnowledgePermissionService()
        role = KnowledgeRole(id="r1", name="viewer")
        service.create_role(role)
        assignment = KnowledgeRoleAssignment(
            id="a1", role_id="r1", subject_id="user1", scope=KnowledgeAccessScope.COLLECTION
        )
        service.assign_role(assignment)
        assert len(service.list_assignments()) == 1
        service.unassign_role("a1")
        assert len(service.list_assignments()) == 0

    def test_assign_role_without_role_raises(self) -> None:
        service = KnowledgePermissionService()
        assignment = KnowledgeRoleAssignment(
            id="a1",
            role_id="nonexistent",
            subject_id="user1",
            scope=KnowledgeAccessScope.COLLECTION,
        )
        with pytest.raises(PermissionRoleError):
            service.assign_role(assignment)

    def test_get_assignment_not_found(self) -> None:
        service = KnowledgePermissionService()
        with pytest.raises(PermissionAssignmentError):
            service.get_assignment("nonexistent")

    def test_list_assignments_for_subject(self) -> None:
        service = KnowledgePermissionService()
        role = KnowledgeRole(id="r1", name="viewer")
        service.create_role(role)
        a1 = KnowledgeRoleAssignment(
            id="a1", role_id="r1", subject_id="user1", scope=KnowledgeAccessScope.COLLECTION
        )
        a2 = KnowledgeRoleAssignment(
            id="a2", role_id="r1", subject_id="user2", scope=KnowledgeAccessScope.COLLECTION
        )
        service.assign_role(a1)
        service.assign_role(a2)
        assert len(service.list_assignments_for_subject("user1")) == 1

    def test_acl_set_and_get(self) -> None:
        service = KnowledgePermissionService()
        acl = AccessControlList(resource_id="doc1")
        service.set_acl(acl)
        assert service.get_acl("doc1").resource_id == "doc1"

    def test_acl_not_found(self) -> None:
        service = KnowledgePermissionService()
        with pytest.raises(PermissionNotFoundError):
            service.get_acl("nonexistent")

    def test_delete_acl(self) -> None:
        service = KnowledgePermissionService()
        acl = AccessControlList(resource_id="doc1")
        service.set_acl(acl)
        service.delete_acl("doc1")
        assert len(service.list_acls()) == 0

    def test_policy_lifecycle(self) -> None:
        service = KnowledgePermissionService()
        policy = KnowledgePermissionPolicy(id="pol1", name="default")
        service.create_policy(policy)
        assert service.get_policy("pol1").name == "default"
        service.update_policy("pol1", name="strict")
        assert service.get_policy("pol1").name == "strict"
        service.delete_policy("pol1")
        assert len(service.list_policies()) == 0

    def test_evaluate_access_granted(self) -> None:
        service = KnowledgePermissionService()
        rule = KnowledgeAccessRule(
            id="rule1",
            name="allow-read",
            scope=KnowledgeAccessScope.COLLECTION,
            resource_pattern="doc1",
            allowed_levels=(PermissionLevel.READ,),
        )
        service.create_access_rule(rule)
        eval_result = service.evaluate_access("user1", "doc1", PermissionLevel.READ)
        assert eval_result.granted is True
        assert eval_result.effective_level == PermissionLevel.READ

    def test_evaluate_access_denied(self) -> None:
        service = KnowledgePermissionService()
        eval_result = service.evaluate_access("user1", "doc1", PermissionLevel.WRITE)
        assert eval_result.granted is False
        assert eval_result.effective_level == PermissionLevel.NONE

    def test_check_access_denied_raises(self) -> None:
        service = KnowledgePermissionService()
        with pytest.raises(PermissionDeniedError):
            service.check_access("user1", "doc1", PermissionLevel.WRITE)

    def test_get_resource_access(self) -> None:
        service = KnowledgePermissionService()
        rule = KnowledgeAccessRule(
            id="rule1",
            name="allow-read",
            scope=KnowledgeAccessScope.COLLECTION,
            resource_pattern="doc1",
            allowed_levels=(PermissionLevel.READ,),
        )
        service.create_access_rule(rule)
        access = service.get_resource_access("user1", "doc1")
        assert access.effective_level == PermissionLevel.READ
        assert "rule1" in access.source_rules

    def test_evaluate_with_disabled_config_raises(self) -> None:
        service = KnowledgePermissionService()
        service.update_config(enabled=False)
        with pytest.raises(PermissionEvaluationError):
            service.evaluate_access("user1", "doc1", PermissionLevel.READ)

    def test_audit_log_lifecycle(self) -> None:
        service = KnowledgePermissionService()
        entry = KnowledgeAccessAuditEntry(
            id="e1",
            subject_id="user1",
            action="read",
            resource_id="doc1",
            granted=True,
            level=PermissionLevel.READ,
        )
        service.log_audit_entry(entry)
        assert len(service.list_audit_entries()) == 1

    def test_audit_disabled_raises(self) -> None:
        service = KnowledgePermissionService()
        service.update_config(audit_enabled=False)
        entry = KnowledgeAccessAuditEntry(
            id="e1",
            subject_id="user1",
            action="read",
            resource_id="doc1",
            granted=True,
            level=PermissionLevel.READ,
        )
        with pytest.raises(PermissionAuditError):
            service.log_audit_entry(entry)

    def test_query_audit_entries(self) -> None:
        service = KnowledgePermissionService()
        e1 = KnowledgeAccessAuditEntry(
            id="e1",
            subject_id="user1",
            action="read",
            resource_id="doc1",
            granted=True,
            level=PermissionLevel.READ,
        )
        e2 = KnowledgeAccessAuditEntry(
            id="e2",
            subject_id="user2",
            action="write",
            resource_id="doc2",
            granted=False,
            level=PermissionLevel.WRITE,
        )
        service.log_audit_entry(e1)
        service.log_audit_entry(e2)
        results = service.query_audit_entries(subject_id="user1")
        assert len(results) == 1
        assert results[0].id == "e1"

    def test_clear_audit_log(self) -> None:
        service = KnowledgePermissionService()
        entry = KnowledgeAccessAuditEntry(
            id="e1",
            subject_id="user1",
            action="read",
            resource_id="doc1",
            granted=True,
            level=PermissionLevel.READ,
        )
        service.log_audit_entry(entry)
        service.clear_audit_log()
        assert len(service.list_audit_entries()) == 0

    def test_generate_report(self) -> None:
        service = KnowledgePermissionService()
        report = service.generate_report()
        assert report.total_permissions == 0
        assert report.total_rules == 0
        assert report.total_roles == 0
        assert report.total_assignments == 0
        assert isinstance(report.id, str)


class TestHealthCheck:
    async def test_healthy(self) -> None:
        service = KnowledgePermissionService()
        check = KnowledgePermissionHealthCheck(service)
        report = await check.check()
        assert report.component == "knowledge_permissions"
        assert report.details["enabled"] is True

    async def test_degraded_when_disabled(self) -> None:
        service = KnowledgePermissionService()
        service.update_config(enabled=False)
        check = KnowledgePermissionHealthCheck(service)
        report = await check.check()
        assert report.status.value == "degraded"
        assert report.details["enabled"] is False
