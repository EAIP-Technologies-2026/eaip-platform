"""KnowledgePermissionService — CRUD, access evaluation, roles, ACLs, and audit."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from eaip.knowledge_permissions.exceptions import (
    PermissionAssignmentError,
    PermissionAuditError,
    PermissionDeniedError,
    PermissionEvaluationError,
    PermissionNotFoundError,
    PermissionRoleError,
)
from eaip.knowledge_permissions.models import (
    AccessControlList,
    KnowledgeAccessAuditEntry,
    KnowledgeAccessRule,
    KnowledgePermission,
    KnowledgePermissionConfig,
    KnowledgePermissionEvaluation,
    KnowledgePermissionPolicy,
    KnowledgePermissionReport,
    KnowledgeResourceAccess,
    KnowledgeRole,
    KnowledgeRoleAssignment,
    PermissionLevel,
)
from eaip.logging.context import get_logger


class KnowledgePermissionService:
    """Service for managing knowledge permissions, roles, ACLs, and audit."""

    def __init__(self, config: KnowledgePermissionConfig | None = None) -> None:
        self._config = config or KnowledgePermissionConfig()
        self._permissions: dict[str, KnowledgePermission] = {}
        self._rules: dict[str, KnowledgeAccessRule] = {}
        self._roles: dict[str, KnowledgeRole] = {}
        self._assignments: dict[str, KnowledgeRoleAssignment] = {}
        self._acls: dict[str, AccessControlList] = {}
        self._audit_log: list[KnowledgeAccessAuditEntry] = []
        self._policies: dict[str, KnowledgePermissionPolicy] = {}
        self._log = get_logger("eaip.knowledge_permissions.service")

    # -- config -----------------------------------------------------------------

    @property
    def config(self) -> KnowledgePermissionConfig:
        return self._config

    def update_config(self, **updates: Any) -> KnowledgePermissionConfig:
        self._config = self._config.model_copy(update=updates)
        self._log.info("knowledge_permissions.config.updated", config=self._config)
        return self._config

    # -- permissions CRUD -------------------------------------------------------

    def create_permission(self, permission: KnowledgePermission) -> KnowledgePermission:
        self._permissions[permission.id] = permission
        self._log.info("knowledge_permissions.permission.created", permission_id=permission.id)
        return permission

    def get_permission(self, permission_id: str) -> KnowledgePermission:
        perm = self._permissions.get(permission_id)
        if perm is None:
            raise PermissionNotFoundError(f"Permission {permission_id!r} not found")
        return perm

    def update_permission(self, permission_id: str, **updates: Any) -> KnowledgePermission:
        existing = self.get_permission(permission_id)
        updated = existing.model_copy(update=updates)
        self._permissions[permission_id] = updated
        self._log.info("knowledge_permissions.permission.updated", permission_id=permission_id)
        return updated

    def delete_permission(self, permission_id: str) -> None:
        if permission_id not in self._permissions:
            raise PermissionNotFoundError(f"Permission {permission_id!r} not found")
        del self._permissions[permission_id]
        self._log.info("knowledge_permissions.permission.deleted", permission_id=permission_id)

    def list_permissions(self) -> list[KnowledgePermission]:
        return list(self._permissions.values())

    # -- access rules -----------------------------------------------------------

    def create_access_rule(self, rule: KnowledgeAccessRule) -> KnowledgeAccessRule:
        self._rules[rule.id] = rule
        self._log.info("knowledge_permissions.access_rule.created", rule_id=rule.id)
        return rule

    def get_access_rule(self, rule_id: str) -> KnowledgeAccessRule:
        rule = self._rules.get(rule_id)
        if rule is None:
            raise PermissionNotFoundError(f"Access rule {rule_id!r} not found")
        return rule

    def update_access_rule(self, rule_id: str, **updates: Any) -> KnowledgeAccessRule:
        existing = self.get_access_rule(rule_id)
        updated = existing.model_copy(update=updates)
        self._rules[rule_id] = updated
        self._log.info("knowledge_permissions.access_rule.updated", rule_id=rule_id)
        return updated

    def delete_access_rule(self, rule_id: str) -> None:
        if rule_id not in self._rules:
            raise PermissionNotFoundError(f"Access rule {rule_id!r} not found")
        del self._rules[rule_id]
        self._log.info("knowledge_permissions.access_rule.deleted", rule_id=rule_id)

    def list_access_rules(self) -> list[KnowledgeAccessRule]:
        return list(self._rules.values())

    # -- roles ------------------------------------------------------------------

    def create_role(self, role: KnowledgeRole) -> KnowledgeRole:
        self._roles[role.id] = role
        self._log.info("knowledge_permissions.role.created", role_id=role.id)
        return role

    def get_role(self, role_id: str) -> KnowledgeRole:
        role = self._roles.get(role_id)
        if role is None:
            raise PermissionRoleError(f"Role {role_id!r} not found")
        return role

    def update_role(self, role_id: str, **updates: Any) -> KnowledgeRole:
        existing = self.get_role(role_id)
        updated = existing.model_copy(update=updates)
        self._roles[role_id] = updated
        self._log.info("knowledge_permissions.role.updated", role_id=role_id)
        return updated

    def delete_role(self, role_id: str) -> None:
        if role_id not in self._roles:
            raise PermissionRoleError(f"Role {role_id!r} not found")
        del self._roles[role_id]
        self._log.info("knowledge_permissions.role.deleted", role_id=role_id)

    def list_roles(self) -> list[KnowledgeRole]:
        return list(self._roles.values())

    # -- role assignments -------------------------------------------------------

    def assign_role(self, assignment: KnowledgeRoleAssignment) -> KnowledgeRoleAssignment:
        if assignment.role_id not in self._roles:
            raise PermissionRoleError(f"Role {assignment.role_id!r} not found")
        self._assignments[assignment.id] = assignment
        self._log.info(
            "knowledge_permissions.role.assigned",
            assignment_id=assignment.id,
            role_id=assignment.role_id,
            subject_id=assignment.subject_id,
        )
        return assignment

    def get_assignment(self, assignment_id: str) -> KnowledgeRoleAssignment:
        assignment = self._assignments.get(assignment_id)
        if assignment is None:
            raise PermissionAssignmentError(f"Assignment {assignment_id!r} not found")
        return assignment

    def unassign_role(self, assignment_id: str) -> None:
        if assignment_id not in self._assignments:
            raise PermissionAssignmentError(f"Assignment {assignment_id!r} not found")
        del self._assignments[assignment_id]
        self._log.info("knowledge_permissions.role.unassigned", assignment_id=assignment_id)

    def list_assignments(self) -> list[KnowledgeRoleAssignment]:
        return list(self._assignments.values())

    def list_assignments_for_subject(self, subject_id: str) -> list[KnowledgeRoleAssignment]:
        return [a for a in self._assignments.values() if a.subject_id == subject_id]

    # -- ACLs -------------------------------------------------------------------

    def set_acl(self, acl: AccessControlList) -> AccessControlList:
        self._acls[acl.resource_id] = acl
        self._log.info("knowledge_permissions.acl.updated", resource_id=acl.resource_id)
        return acl

    def get_acl(self, resource_id: str) -> AccessControlList:
        acl = self._acls.get(resource_id)
        if acl is None:
            raise PermissionNotFoundError(f"ACL for resource {resource_id!r} not found")
        return acl

    def delete_acl(self, resource_id: str) -> None:
        if resource_id not in self._acls:
            raise PermissionNotFoundError(f"ACL for resource {resource_id!r} not found")
        del self._acls[resource_id]
        self._log.info("knowledge_permissions.acl.deleted", resource_id=resource_id)

    def list_acls(self) -> list[AccessControlList]:
        return list(self._acls.values())

    # -- policies ---------------------------------------------------------------

    def create_policy(self, policy: KnowledgePermissionPolicy) -> KnowledgePermissionPolicy:
        self._policies[policy.id] = policy
        self._log.info("knowledge_permissions.policy.created", policy_id=policy.id)
        return policy

    def get_policy(self, policy_id: str) -> KnowledgePermissionPolicy:
        policy = self._policies.get(policy_id)
        if policy is None:
            raise PermissionNotFoundError(f"Policy {policy_id!r} not found")
        return policy

    def update_policy(self, policy_id: str, **updates: Any) -> KnowledgePermissionPolicy:
        existing = self.get_policy(policy_id)
        updated = existing.model_copy(update=updates)
        self._policies[policy_id] = updated
        self._log.info("knowledge_permissions.policy.updated", policy_id=policy_id)
        return updated

    def delete_policy(self, policy_id: str) -> None:
        if policy_id not in self._policies:
            raise PermissionNotFoundError(f"Policy {policy_id!r} not found")
        del self._policies[policy_id]
        self._log.info("knowledge_permissions.policy.deleted", policy_id=policy_id)

    def list_policies(self) -> list[KnowledgePermissionPolicy]:
        return list(self._policies.values())

    # -- access evaluation ------------------------------------------------------

    def evaluate_access(
        self,
        subject_id: str,
        resource_id: str,
        requested_level: PermissionLevel,
    ) -> KnowledgePermissionEvaluation:
        if not self._config.enabled:
            raise PermissionEvaluationError("Knowledge permissions are disabled")

        effective_level = PermissionLevel.NONE
        matched_rules: list[str] = []
        matched_roles: list[str] = []

        effective_level, matched_rules = self._evaluate_rules(
            resource_id, requested_level, effective_level, matched_rules
        )

        if self._config.role_based_enabled:
            effective_level, matched_roles = self._evaluate_roles(
                subject_id, resource_id, requested_level, effective_level, matched_roles
            )

        if self._config.acl_enabled:
            effective_level = self._evaluate_acls(
                subject_id, resource_id, requested_level, effective_level
            )

        granted = self._level_satisfies(requested_level, effective_level)

        evaluation = KnowledgePermissionEvaluation(
            subject_id=subject_id,
            resource_id=resource_id,
            requested_level=requested_level,
            effective_level=effective_level,
            granted=granted,
            matched_rules=tuple(matched_rules),
            matched_roles=tuple(matched_roles),
            explanation=(
                f"Access {'granted' if granted else 'denied'} at level {effective_level.value}"
            ),
        )
        self._log.info("knowledge_permissions.access.evaluated", evaluation=evaluation)
        return evaluation

    def check_access(
        self,
        subject_id: str,
        resource_id: str,
        required_level: PermissionLevel,
    ) -> bool:
        evaluation = self.evaluate_access(subject_id, resource_id, required_level)
        if not evaluation.granted:
            raise PermissionDeniedError(
                f"Access denied for {subject_id!r} on {resource_id!r} "
                f"at level {required_level.value}"
            )
        return True

    def get_resource_access(
        self,
        subject_id: str,
        resource_id: str,
    ) -> KnowledgeResourceAccess:
        evaluation = self.evaluate_access(subject_id, resource_id, PermissionLevel.READ)
        return KnowledgeResourceAccess(
            subject_id=subject_id,
            resource_id=resource_id,
            effective_level=evaluation.effective_level,
            source_rules=evaluation.matched_rules,
            source_roles=evaluation.matched_roles,
        )

    def _evaluate_rules(
        self,
        resource_id: str,
        requested_level: PermissionLevel,
        effective_level: PermissionLevel,
        matched_rules: list[str],
    ) -> tuple[PermissionLevel, list[str]]:
        sorted_rules = sorted(self._rules.values(), key=lambda r: r.priority, reverse=True)
        for rule in sorted_rules:
            if not rule.enabled:
                continue
            if rule.resource_pattern != "*" and not resource_id.startswith(rule.resource_pattern):
                continue
            if requested_level in rule.allowed_levels:
                effective_level = max(
                    (effective_level, requested_level),
                    key=lambda lvl: list(PermissionLevel).index(lvl),
                )
                matched_rules.append(rule.id)
        return effective_level, matched_rules

    def _evaluate_roles(
        self,
        subject_id: str,
        resource_id: str,
        requested_level: PermissionLevel,
        effective_level: PermissionLevel,
        matched_roles: list[str],
    ) -> tuple[PermissionLevel, list[str]]:
        for assignment in self._assignments.values():
            if assignment.subject_id != subject_id:
                continue
            role = self._roles.get(assignment.role_id)
            if role is None:
                continue
            for perm in role.permissions:
                pattern = perm.resource_pattern
                if pattern != "*" and not resource_id.startswith(pattern):
                    continue
                if self._level_satisfies(requested_level, perm.level):
                    effective_level = max(
                        (effective_level, perm.level),
                        key=lambda lvl: list(PermissionLevel).index(lvl),
                    )
                    matched_roles.append(role.id)
        return effective_level, matched_roles

    def _evaluate_acls(
        self,
        subject_id: str,
        resource_id: str,
        requested_level: PermissionLevel,
        effective_level: PermissionLevel,
    ) -> PermissionLevel:
        acl = self._acls.get(resource_id)
        if acl is None:
            return effective_level
        for entry in acl.entries:
            if entry.subject_id != subject_id:
                continue
            if entry.expires_at and entry.expires_at < datetime.now(entry.expires_at.tzinfo):
                continue
            if self._level_satisfies(requested_level, entry.level):
                effective_level = max(
                    (effective_level, entry.level),
                    key=lambda lvl: list(PermissionLevel).index(lvl),
                )
        return effective_level

    @staticmethod
    def _level_satisfies(required: PermissionLevel, actual: PermissionLevel) -> bool:
        levels = list(PermissionLevel)
        return levels.index(actual) >= levels.index(required)

    # -- audit ------------------------------------------------------------------

    def log_audit_entry(self, entry: KnowledgeAccessAuditEntry) -> KnowledgeAccessAuditEntry:
        if not self._config.audit_enabled:
            raise PermissionAuditError("Audit is disabled")
        self._audit_log.append(entry)
        self._log.info("knowledge_permissions.audit.logged", entry_id=entry.id)
        return entry

    def list_audit_entries(self) -> list[KnowledgeAccessAuditEntry]:
        return list(self._audit_log)

    def query_audit_entries(
        self,
        subject_id: str | None = None,
        resource_id: str | None = None,
        action: str | None = None,
    ) -> list[KnowledgeAccessAuditEntry]:
        results = self._audit_log
        if subject_id is not None:
            results = [e for e in results if e.subject_id == subject_id]
        if resource_id is not None:
            results = [e for e in results if e.resource_id == resource_id]
        if action is not None:
            results = [e for e in results if e.action == action]
        return list(results)

    def clear_audit_log(self) -> None:
        self._audit_log.clear()
        self._log.info("knowledge_permissions.audit.cleared")

    # -- reports ----------------------------------------------------------------

    def generate_report(self) -> KnowledgePermissionReport:
        report = KnowledgePermissionReport(
            id=f"kp-report-{datetime.now().timestamp()}",
            total_permissions=len(self._permissions),
            total_rules=len(self._rules),
            total_roles=len(self._roles),
            total_assignments=len(self._assignments),
            summary={
                "permissions": len(self._permissions),
                "rules": len(self._rules),
                "roles": len(self._roles),
                "assignments": len(self._assignments),
                "acls": len(self._acls),
                "policies": len(self._policies),
                "audit_entries": len(self._audit_log),
            },
        )
        self._log.info("knowledge_permissions.report.generated", report_id=report.id)
        return report


__all__ = ["KnowledgePermissionService"]
