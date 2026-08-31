"""Permission Context Resolver.

Resolves an authenticated identity's permission-aware context against
the platform's existing AuthorizationManager, PolicyEngine, and CapabilityRegistry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import CapabilityStatus, OperationType
from eaip.context.permission_context import (
    CapabilityAccessLevel,
    CapabilityPermissionContext,
    IdentityScope,
    PermissionAwareContext,
)
from eaip.logging.context import get_logger
from eaip.policy.context import PolicyEvaluationContext
from eaip.policy.models import PolicyDecision, PolicyEffect

if TYPE_CHECKING:
    from eaip.capabilities.registry import CapabilityRegistry
    from eaip.policy.authorization import AuthorizationManager


ADMIN_ROLES = {"admin", "system_admin", "platform_admin", "super_admin"}
OPERATOR_ROLES = {"operator", "sre", "engineer", "lead", "developer"}
AUDITOR_ROLES = {"auditor", "compliance_officer", "security_auditor"}


class PermissionContextResolver:
    """Resolves effective capability access for an authenticated identity."""

    def __init__(
        self,
        authz_manager: AuthorizationManager,
        capability_registry: CapabilityRegistry,
    ) -> None:
        """Initialize the permission context resolver.

        Args:
            authz_manager: Authoritative platform AuthorizationManager.
            capability_registry: Authoritative platform CapabilityRegistry.
        """
        self._authz = authz_manager
        self._registry = capability_registry
        self._log = get_logger("eaip.context.permission_resolver")

    def resolve_context(
        self,
        identity: IdentityScope,
        target_tenant_id: str | None = None,
    ) -> PermissionAwareContext:
        """Resolve a full PermissionAwareContext for an identity.

        Args:
            identity: Authenticated identity scope.
            target_tenant_id: Optional target tenant (defaults to identity.tenant_id).

        Returns:
            Resolved PermissionAwareContext describing accessible capabilities.
        """
        effective_tenant = target_tenant_id or identity.tenant_id
        is_same_tenant = identity.tenant_id == effective_tenant
        is_system_admin = bool(set(identity.roles) & ADMIN_ROLES)

        # Enforce strict tenant isolation: foreign tenant access rejected unless system admin
        if not is_same_tenant and not is_system_admin:
            self._log.warn(
                "tenant.isolation.blocked",
                subject_id=identity.user_id,
                subject_tenant=identity.tenant_id,
                target_tenant=effective_tenant,
            )
            return PermissionAwareContext(
                identity=identity,
                capabilities={},
                visible_capability_ids=(),
                executable_capability_ids=(),
                restricted_capability_ids=tuple(c.name for c in self._registry.all()),
            )

        capabilities_map: dict[str, CapabilityPermissionContext] = {}
        visible_ids: list[str] = []
        executable_ids: list[str] = []
        restricted_ids: list[str] = []

        all_caps = self._registry.all()

        for cap in all_caps:
            # Skip disabled or deprecated if not admin
            if (
                cap.status in (CapabilityStatus.DISABLED, CapabilityStatus.DEPRECATED)
                and not is_system_admin
            ):
                restricted_ids.append(cap.name)
                capabilities_map[cap.name] = CapabilityPermissionContext(
                    capability_id=cap.id_or_name(),
                    capability_name=cap.name,
                    access=CapabilityAccessLevel(restricted=True),
                    applicable_roles=identity.roles,
                    tenant_id=effective_tenant,
                )
                continue

            access_level = self._evaluate_capability_access(
                identity, cap.name, effective_tenant, is_system_admin
            )

            cap_ctx = CapabilityPermissionContext(
                capability_id=cap.id_or_name(),
                capability_name=cap.name,
                access=access_level,
                applicable_roles=identity.roles,
                tenant_id=effective_tenant,
            )
            capabilities_map[cap.name] = cap_ctx

            if access_level.visible and not access_level.restricted:
                visible_ids.append(cap.name)
            if access_level.executable and not access_level.restricted:
                executable_ids.append(cap.name)
            if access_level.restricted:
                restricted_ids.append(cap.name)

        return PermissionAwareContext(
            identity=identity,
            capabilities=capabilities_map,
            visible_capability_ids=tuple(visible_ids),
            executable_capability_ids=tuple(executable_ids),
            restricted_capability_ids=tuple(restricted_ids),
        )

    def _evaluate_capability_access(
        self,
        identity: IdentityScope,
        capability_name: str,
        tenant_id: str,
        is_system_admin: bool,
    ) -> CapabilityAccessLevel:
        """Evaluate access level for a single capability against existing policy rules and RBAC."""
        roles_set = set(identity.roles)

        # Build standard evaluation contexts
        eval_ctx_read = PolicyEvaluationContext(
            subject_id=identity.user_id,
            subject_roles=identity.roles,
            action="capability:read",
            resource=capability_name,
            attributes={"tenant_id": tenant_id, **identity.attributes},
        )
        eval_ctx_exec = PolicyEvaluationContext(
            subject_id=identity.user_id,
            subject_roles=identity.roles,
            action="capability:invoke",
            resource=capability_name,
            attributes={"tenant_id": tenant_id, **identity.attributes},
        )
        eval_ctx_write = PolicyEvaluationContext(
            subject_id=identity.user_id,
            subject_roles=identity.roles,
            action="capability:write",
            resource=capability_name,
            attributes={"tenant_id": tenant_id, **identity.attributes},
        )

        read_decision: PolicyDecision = self._authz.check_permission(eval_ctx_read)
        exec_decision: PolicyDecision = self._authz.check_permission(eval_ctx_exec)
        write_decision: PolicyDecision = self._authz.check_permission(eval_ctx_write)

        # Explicit policy DENY takes precedence
        has_explicit_read_deny = read_decision.effect is PolicyEffect.DENY and bool(
            read_decision.matched_rules
        )
        has_explicit_exec_deny = exec_decision.effect is PolicyEffect.DENY and bool(
            exec_decision.matched_rules
        )
        has_explicit_write_deny = write_decision.effect is PolicyEffect.DENY and bool(
            write_decision.matched_rules
        )

        if has_explicit_read_deny and not is_system_admin:
            return CapabilityAccessLevel(
                visible=False,
                discoverable=False,
                readable=False,
                executable=False,
                mutable=False,
                approval_required=False,
                restricted=True,
                effective_operations=(),
            )

        # Base role authorization boundaries
        is_admin = is_system_admin or bool(roles_set & ADMIN_ROLES)
        is_operator = bool(roles_set & OPERATOR_ROLES)
        is_auditor = bool(roles_set & AUDITOR_ROLES)
        is_user = bool(roles_set & {"user", "member", "developer", "engineer"})

        is_gov_cap = capability_name in ("eaip.administration", "eaip.security")

        # Determine visibility
        if is_admin:
            visible = True
        elif is_auditor:
            visible = not has_explicit_read_deny
        elif is_gov_cap:
            visible = read_decision.effect is PolicyEffect.ALLOW
        else:
            visible = (
                read_decision.effect is PolicyEffect.ALLOW
                or is_operator
                or is_user
                or ("guest" not in roles_set)
            ) and not has_explicit_read_deny
        readable = visible

        # Determine execution
        effective_ops: tuple[OperationType, ...]
        if is_admin:
            executable = True
            mutable = True
            approval_required = False
            effective_ops = (
                OperationType.READ,
                OperationType.QUERY,
                OperationType.CREATE,
                OperationType.UPDATE,
                OperationType.DELETE,
                OperationType.EXECUTE,
                OperationType.APPROVE,
            )
        elif is_operator:
            # Operators can execute operational/intelligence capabilities;
            # sensitive actions require approval
            executable = (not has_explicit_exec_deny) and not is_gov_cap
            mutable = (not has_explicit_write_deny) and not is_gov_cap
            approval_required = capability_name in (
                "eaip.operations",
                "eaip.orchestration",
                "eaip.missions",
            )
            effective_ops = (
                (
                    OperationType.READ,
                    OperationType.QUERY,
                    OperationType.EXECUTE,
                )
                if executable
                else (OperationType.READ, OperationType.QUERY)
            )
        elif is_auditor:
            # Auditors have read/query visibility across capabilities but no mutation/execution
            executable = False
            mutable = False
            approval_required = False
            effective_ops = (OperationType.READ, OperationType.QUERY) if visible else ()
        else:
            # Standard users have read visibility on standard capabilities;
            # execute only if policy explicitly allows
            executable = exec_decision.effect is PolicyEffect.ALLOW and not has_explicit_exec_deny
            mutable = write_decision.effect is PolicyEffect.ALLOW and not has_explicit_write_deny
            approval_required = False
            effective_ops = (OperationType.READ, OperationType.QUERY) if visible else ()

        return CapabilityAccessLevel(
            visible=visible,
            discoverable=visible,
            readable=readable,
            executable=executable,
            mutable=mutable,
            approval_required=approval_required,
            restricted=not visible,
            effective_operations=effective_ops,
        )


__all__ = ["PermissionContextResolver"]
