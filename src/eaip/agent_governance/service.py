"""AgentGovernanceService — policies, permissions, auditing, approvals, SOPs, compliance."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from eaip.agent_governance.events import (
    AgentActivityLogged,
    AgentApprovalRequestApproved,
    AgentApprovalRequestCreated,
    AgentApprovalRequestRejected,
    AgentComplianceCheckCompleted,
    AgentComplianceCheckFailed,
    AgentEscalationTriggered,
    AgentGovernanceConfigUpdated,
    AgentGovernancePolicyCreated,
    AgentGovernancePolicyEnforced,
    AgentGovernancePolicyUpdated,
    AgentGovernancePolicyViolated,
    AgentPermissionChanged,
    AgentRestrictionApplied,
    AgentSopActivated,
    AgentSopCreated,
    AgentSopUpdated,
    AgentUsagePolicyUpdated,
)
from eaip.agent_governance.exceptions import (
    AgentApprovalError,
    AgentComplianceError,
    AgentEscalationError,
    AgentGovernancePolicyError,
    AgentGovernanceViolationError,
    AgentPermissionError,
    AgentRestrictionError,
    AgentSopError,
)
from eaip.agent_governance.models import (
    AgentActivityLog,
    AgentApprovalConfig,
    AgentApprovalRequest,
    AgentApprovalStatus,
    AgentAuditEntry,
    AgentComplianceCheck,
    AgentComplianceResult,
    AgentEscalationRule,
    AgentGovernanceConfig,
    AgentGovernancePolicy,
    AgentPermission,
    AgentRestriction,
    AgentSop,
    AgentSopStatus,
    AgentUsagePolicy,
)
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger


class AgentGovernanceService:
    """Central service for agent governance operations."""

    def __init__(
        self, config: AgentGovernanceConfig | None = None, event_bus: EventBus | None = None
    ) -> None:
        self._config = config or AgentGovernanceConfig(
            id="default", name="Default Governance Config"
        )
        self._policies: dict[str, AgentGovernancePolicy] = {}
        self._permissions: dict[str, AgentPermission] = {}
        self._activity_logs: dict[str, AgentActivityLog] = {}
        self._audit_entries: dict[str, AgentAuditEntry] = {}
        self._approval_configs: dict[str, AgentApprovalConfig] = {}
        self._approval_requests: dict[str, AgentApprovalRequest] = {}
        self._restrictions: dict[str, AgentRestriction] = {}
        self._usage_policies: dict[str, AgentUsagePolicy] = {}
        self._sops: dict[str, AgentSop] = {}
        self._compliance_checks: dict[str, AgentComplianceCheck] = {}
        self._compliance_results: dict[str, AgentComplianceResult] = {}
        self._escalation_rules: dict[str, AgentEscalationRule] = {}
        self._event_listeners: list[Any] = []
        self._log = get_logger("eaip.agent_governance.service")
        self._event_bus = event_bus

    # ── event dispatching ───────────────────────────────────────────────────

    def subscribe(self, listener: Any) -> None:
        self._event_listeners.append(listener)

    def _emit(self, event: Any) -> None:
        for listener in self._event_listeners:
            try:
                listener(event)
            except Exception:
                self._log.exception("agent_governance.event_dispatch.failed")
        if self._event_bus is not None:
            import asyncio

            asyncio.ensure_future(self._event_bus.publish(event))

    # ── config ──────────────────────────────────────────────────────────────

    @property
    def config(self) -> AgentGovernanceConfig:
        return self._config

    def update_config(self, **updates: Any) -> AgentGovernanceConfig:
        self._config = self._config.model_copy(update=updates)
        event = AgentGovernanceConfigUpdated(
            config_id=self._config.id,
            config_name=self._config.name,
        )
        self._emit(event)
        self._log.info("agent_governance.config.updated", config=self._config)
        return self._config

    # ── policies ────────────────────────────────────────────────────────────

    def create_policy(self, policy: AgentGovernancePolicy) -> AgentGovernancePolicy:
        if policy.id in self._policies:
            raise AgentGovernancePolicyError(f"Policy {policy.id!r} already exists")
        self._policies[policy.id] = policy
        event = AgentGovernancePolicyCreated(policy_id=policy.id, policy_name=policy.name)
        self._emit(event)
        self._log.info("agent_governance.policy.created", policy_id=policy.id)
        return policy

    def get_policy(self, policy_id: str) -> AgentGovernancePolicy:
        policy = self._policies.get(policy_id)
        if policy is None:
            raise AgentGovernancePolicyError(f"Policy {policy_id!r} not found")
        return policy

    def update_policy(self, policy_id: str, **updates: Any) -> AgentGovernancePolicy:
        existing = self.get_policy(policy_id)
        updated = existing.model_copy(update={**updates, "updated_at": datetime.now(UTC)})
        self._policies[policy_id] = updated
        event = AgentGovernancePolicyUpdated(policy_id=policy_id, policy_name=updated.name)
        self._emit(event)
        self._log.info("agent_governance.policy.updated", policy_id=policy_id)
        return updated

    def delete_policy(self, policy_id: str) -> None:
        if policy_id not in self._policies:
            raise AgentGovernancePolicyError(f"Policy {policy_id!r} not found")
        del self._policies[policy_id]
        self._log.info("agent_governance.policy.deleted", policy_id=policy_id)

    def list_policies(self) -> list[AgentGovernancePolicy]:
        return list(self._policies.values())

    def enforce_policy(self, policy_id: str, agent_id: str, action: str) -> bool:
        policy = self.get_policy(policy_id)
        if not policy.enabled:
            return True
        for rule in policy.rules:
            if rule.effect == "deny" and action in rule.actions:
                self._emit(
                    AgentGovernancePolicyViolated(
                        policy_id=policy_id,
                        agent_id=agent_id,
                        action=action,
                        detail=f"Denied by rule {rule.id!r}",
                    )
                )
                raise AgentGovernanceViolationError(f"Action {action!r} denied by rule {rule.id!r}")
        self._emit(
            AgentGovernancePolicyEnforced(policy_id=policy_id, agent_id=agent_id, action=action)
        )
        return True

    # ── permissions ─────────────────────────────────────────────────────────

    def grant_permission(self, permission: AgentPermission) -> AgentPermission:
        self._permissions[permission.id] = permission
        event = AgentPermissionChanged(
            agent_id=permission.agent_id,
            permission_id=permission.id,
            change="granted",
        )
        self._emit(event)
        self._log.info("agent_governance.permission.granted", permission_id=permission.id)
        return permission

    def revoke_permission(self, permission_id: str) -> AgentPermission:
        perm = self._permissions.get(permission_id)
        if perm is None:
            raise AgentPermissionError(f"Permission {permission_id!r} not found")
        revoked = perm.model_copy(update={"revoked": True})
        self._permissions[permission_id] = revoked
        event = AgentPermissionChanged(
            agent_id=revoked.agent_id,
            permission_id=permission_id,
            change="revoked",
        )
        self._emit(event)
        self._log.info("agent_governance.permission.revoked", permission_id=permission_id)
        return revoked

    def get_permission(self, permission_id: str) -> AgentPermission:
        perm = self._permissions.get(permission_id)
        if perm is None:
            raise AgentPermissionError(f"Permission {permission_id!r} not found")
        return perm

    def list_permissions(self, agent_id: str | None = None) -> list[AgentPermission]:
        if agent_id is None:
            return list(self._permissions.values())
        return [p for p in self._permissions.values() if p.agent_id == agent_id]

    # ── activity logging ────────────────────────────────────────────────────

    def log_activity(self, log: AgentActivityLog) -> AgentActivityLog:
        self._activity_logs[log.id] = log
        event = AgentActivityLogged(log_id=log.id, agent_id=log.agent_id, action=log.action)
        self._emit(event)
        return log

    def get_activity_log(self, log_id: str) -> AgentActivityLog:
        log = self._activity_logs.get(log_id)
        if log is None:
            raise AgentGovernancePolicyError(f"Activity log {log_id!r} not found")
        return log

    def list_activity_logs(self, agent_id: str | None = None) -> list[AgentActivityLog]:
        if agent_id is None:
            return list(self._activity_logs.values())
        return [log for log in self._activity_logs.values() if log.agent_id == agent_id]

    # ── audit ───────────────────────────────────────────────────────────────

    def create_audit_entry(self, entry: AgentAuditEntry) -> AgentAuditEntry:
        self._audit_entries[entry.id] = entry
        return entry

    def list_audit_entries(self, agent_id: str | None = None) -> list[AgentAuditEntry]:
        if agent_id is None:
            return list(self._audit_entries.values())
        return [e for e in self._audit_entries.values() if e.agent_id == agent_id]

    # ── approvals ───────────────────────────────────────────────────────────

    def create_approval_config(self, config: AgentApprovalConfig) -> AgentApprovalConfig:
        self._approval_configs[config.id] = config
        self._log.info("agent_governance.approval_config.created", config_id=config.id)
        return config

    def get_approval_config(self, config_id: str) -> AgentApprovalConfig:
        config = self._approval_configs.get(config_id)
        if config is None:
            raise AgentApprovalError(f"Approval config {config_id!r} not found")
        return config

    def create_approval_request(self, request: AgentApprovalRequest) -> AgentApprovalRequest:
        if not self._config.approvals_enabled:
            raise AgentApprovalError("Approvals are disabled")
        self._approval_requests[request.id] = request
        event = AgentApprovalRequestCreated(
            request_id=request.id,
            agent_id=request.agent_id,
            action=request.action,
        )
        self._emit(event)
        self._log.info("agent_governance.approval_request.created", request_id=request.id)
        return request

    def approve_request(self, request_id: str, approved_by: str) -> AgentApprovalRequest:
        req = self._approval_requests.get(request_id)
        if req is None:
            raise AgentApprovalError(f"Approval request {request_id!r} not found")
        if req.status is not AgentApprovalStatus.PENDING:
            raise AgentApprovalError(f"Approval request {request_id!r} is {req.status.value}")
        updated = req.model_copy(
            update={
                "status": AgentApprovalStatus.APPROVED,
                "approved_by": approved_by,
                "resolved_at": datetime.now(UTC),
            }
        )
        self._approval_requests[request_id] = updated
        event = AgentApprovalRequestApproved(
            request_id=request_id,
            agent_id=updated.agent_id,
            approved_by=approved_by,
        )
        self._emit(event)
        self._log.info("agent_governance.approval_request.approved", request_id=request_id)
        return updated

    def reject_request(
        self, request_id: str, rejected_by: str, reason: str = ""
    ) -> AgentApprovalRequest:
        req = self._approval_requests.get(request_id)
        if req is None:
            raise AgentApprovalError(f"Approval request {request_id!r} not found")
        if req.status is not AgentApprovalStatus.PENDING:
            raise AgentApprovalError(f"Approval request {request_id!r} is {req.status.value}")
        updated = req.model_copy(
            update={
                "status": AgentApprovalStatus.REJECTED,
                "rejected_by": rejected_by,
                "rejection_reason": reason,
                "resolved_at": datetime.now(UTC),
            }
        )
        self._approval_requests[request_id] = updated
        event = AgentApprovalRequestRejected(
            request_id=request_id,
            agent_id=updated.agent_id,
            rejected_by=rejected_by,
            reason=reason,
        )
        self._emit(event)
        self._log.info("agent_governance.approval_request.rejected", request_id=request_id)
        return updated

    def get_approval_request(self, request_id: str) -> AgentApprovalRequest:
        req = self._approval_requests.get(request_id)
        if req is None:
            raise AgentApprovalError(f"Approval request {request_id!r} not found")
        return req

    def list_approval_requests(self, agent_id: str | None = None) -> list[AgentApprovalRequest]:
        if agent_id is None:
            return list(self._approval_requests.values())
        return [r for r in self._approval_requests.values() if r.agent_id == agent_id]

    # ── restrictions ────────────────────────────────────────────────────────

    def apply_restriction(self, restriction: AgentRestriction) -> AgentRestriction:
        if not self._config.restrictions_enabled:
            raise AgentRestrictionError("Restrictions are disabled")
        self._restrictions[restriction.id] = restriction
        event = AgentRestrictionApplied(
            restriction_id=restriction.id,
            agent_id=restriction.agent_id,
            restriction_type=restriction.restriction_type,
        )
        self._emit(event)
        self._log.info("agent_governance.restriction.applied", restriction_id=restriction.id)
        return restriction

    def remove_restriction(self, restriction_id: str) -> None:
        if restriction_id not in self._restrictions:
            raise AgentRestrictionError(f"Restriction {restriction_id!r} not found")
        del self._restrictions[restriction_id]
        self._log.info("agent_governance.restriction.removed", restriction_id=restriction_id)

    def list_restrictions(self, agent_id: str | None = None) -> list[AgentRestriction]:
        if agent_id is None:
            return list(self._restrictions.values())
        return [r for r in self._restrictions.values() if r.agent_id == agent_id]

    # ── usage policies ──────────────────────────────────────────────────────

    def create_usage_policy(self, policy: AgentUsagePolicy) -> AgentUsagePolicy:
        self._usage_policies[policy.id] = policy
        self._log.info("agent_governance.usage_policy.created", policy_id=policy.id)
        return policy

    def get_usage_policy(self, policy_id: str) -> AgentUsagePolicy:
        policy = self._usage_policies.get(policy_id)
        if policy is None:
            raise AgentGovernancePolicyError(f"Usage policy {policy_id!r} not found")
        return policy

    def update_usage_policy(self, policy_id: str, **updates: Any) -> AgentUsagePolicy:
        existing = self.get_usage_policy(policy_id)
        updated = existing.model_copy(update=updates)
        self._usage_policies[policy_id] = updated
        event = AgentUsagePolicyUpdated(policy_id=policy_id, policy_name=updated.name)
        self._emit(event)
        self._log.info("agent_governance.usage_policy.updated", policy_id=policy_id)
        return updated

    def list_usage_policies(self) -> list[AgentUsagePolicy]:
        return list(self._usage_policies.values())

    # ── SOPs ────────────────────────────────────────────────────────────────

    def create_sop(self, sop: AgentSop) -> AgentSop:
        if not self._config.sop_enabled:
            raise AgentSopError("SOPs are disabled")
        self._sops[sop.id] = sop
        event = AgentSopCreated(sop_id=sop.id, sop_name=sop.name)
        self._emit(event)
        self._log.info("agent_governance.sop.created", sop_id=sop.id)
        return sop

    def get_sop(self, sop_id: str) -> AgentSop:
        sop = self._sops.get(sop_id)
        if sop is None:
            raise AgentSopError(f"SOP {sop_id!r} not found")
        return sop

    def update_sop(self, sop_id: str, **updates: Any) -> AgentSop:
        existing = self.get_sop(sop_id)
        updated = existing.model_copy(
            update={**updates, "version": existing.version + 1, "updated_at": datetime.now(UTC)}
        )
        self._sops[sop_id] = updated
        event = AgentSopUpdated(sop_id=sop_id, sop_name=updated.name, version=updated.version)
        self._emit(event)
        self._log.info("agent_governance.sop.updated", sop_id=sop_id)
        return updated

    def activate_sop(self, sop_id: str) -> AgentSop:
        existing = self.get_sop(sop_id)
        updated = existing.model_copy(update={"status": AgentSopStatus.ACTIVE})
        self._sops[sop_id] = updated
        event = AgentSopActivated(sop_id=sop_id, sop_name=updated.name)
        self._emit(event)
        self._log.info("agent_governance.sop.activated", sop_id=sop_id)
        return updated

    def archive_sop(self, sop_id: str) -> AgentSop:
        existing = self.get_sop(sop_id)
        updated = existing.model_copy(update={"status": AgentSopStatus.ARCHIVED})
        self._sops[sop_id] = updated
        self._log.info("agent_governance.sop.archived", sop_id=sop_id)
        return updated

    def list_sops(self) -> list[AgentSop]:
        return list(self._sops.values())

    # ── compliance ──────────────────────────────────────────────────────────

    def create_compliance_check(self, check: AgentComplianceCheck) -> AgentComplianceCheck:
        if not self._config.compliance_enabled:
            raise AgentComplianceError("Compliance is disabled")
        self._compliance_checks[check.id] = check
        self._log.info("agent_governance.compliance_check.created", check_id=check.id)
        return check

    def get_compliance_check(self, check_id: str) -> AgentComplianceCheck:
        check = self._compliance_checks.get(check_id)
        if check is None:
            raise AgentComplianceError(f"Compliance check {check_id!r} not found")
        return check

    def run_compliance_check(self, check_id: str, agent_id: str) -> AgentComplianceResult:
        check = self.get_compliance_check(check_id)
        passed = all(check.rules)
        result = AgentComplianceResult(
            id=f"{check_id}-{agent_id}",
            check_id=check_id,
            agent_id=agent_id,
            passed=passed,
            details={"rules_evaluated": len(check.rules)},
        )
        self._compliance_results[result.id] = result
        if passed:
            self._emit(
                AgentComplianceCheckCompleted(check_id=check_id, agent_id=agent_id, passed=True)
            )
        else:
            self._emit(
                AgentComplianceCheckFailed(
                    check_id=check_id, agent_id=agent_id, error="Rules not met"
                )
            )
        self._log.info(
            "agent_governance.compliance_check.completed",
            check_id=check_id,
            agent_id=agent_id,
            passed=passed,
        )
        return result

    def list_compliance_results(self, agent_id: str | None = None) -> list[AgentComplianceResult]:
        if agent_id is None:
            return list(self._compliance_results.values())
        return [r for r in self._compliance_results.values() if r.agent_id == agent_id]

    # ── escalation ──────────────────────────────────────────────────────────

    def create_escalation_rule(self, rule: AgentEscalationRule) -> AgentEscalationRule:
        self._escalation_rules[rule.id] = rule
        self._log.info("agent_governance.escalation_rule.created", rule_id=rule.id)
        return rule

    def get_escalation_rule(self, rule_id: str) -> AgentEscalationRule:
        rule = self._escalation_rules.get(rule_id)
        if rule is None:
            raise AgentEscalationError(f"Escalation rule {rule_id!r} not found")
        return rule

    def trigger_escalation(self, rule_id: str, agent_id: str, reason: str = "") -> dict[str, Any]:
        rule = self.get_escalation_rule(rule_id)
        if not rule.enabled:
            raise AgentEscalationError(f"Escalation rule {rule_id!r} is disabled")
        event = AgentEscalationTriggered(
            rule_id=rule_id,
            agent_id=agent_id,
            reason=reason,
        )
        self._emit(event)
        self._log.info(
            "agent_governance.escalation.triggered",
            rule_id=rule_id,
            agent_id=agent_id,
        )
        return {
            "rule_id": rule_id,
            "agent_id": agent_id,
            "reason": reason,
            "triggered_at": datetime.now(UTC),
        }

    def list_escalation_rules(self) -> list[AgentEscalationRule]:
        return list(self._escalation_rules.values())


__all__ = ["AgentGovernanceService"]
