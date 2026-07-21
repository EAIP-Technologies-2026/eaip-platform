"""KnowledgeGovernanceService — policies, quality, audit, retention, classification, validation."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from eaip.events.bus import EventBus
from eaip.knowledge_governance.events import (
    KnowledgeAuditTrailEntryCreated,
    KnowledgeClassificationUpdated,
    KnowledgeGovernanceConfigUpdated,
    KnowledgeGovernanceDashboardUpdated,
    KnowledgeGovernancePolicyCreated,
    KnowledgeGovernancePolicyEnforced,
    KnowledgeGovernancePolicyUpdated,
    KnowledgeGovernancePolicyViolated,
    KnowledgeGovernanceReportGenerated,
    KnowledgeQualityCheckCompleted,
    KnowledgeQualityCheckFailed,
    KnowledgeQualityCheckStarted,
    KnowledgeQualityScoreComputed,
    KnowledgeRetentionRuleApplied,
    KnowledgeSourceApproved,
    KnowledgeSourceRejected,
    KnowledgeSourceValidated,
    KnowledgeStewardshipAssigned,
    KnowledgeStewardshipUnassigned,
)
from eaip.knowledge_governance.exceptions import (
    KnowledgeClassificationError,
    KnowledgeGovernancePolicyError,
    KnowledgeGovernanceViolationError,
    KnowledgeQualityError,
    KnowledgeRetentionError,
    KnowledgeSourceValidationError,
    KnowledgeStewardshipError,
)
from eaip.knowledge_governance.models import (
    GovernanceScope,
    KnowledgeAuditTrail,
    KnowledgeClassificationLevel,
    KnowledgeClassificationPolicy,
    KnowledgeGovernanceConfig,
    KnowledgeGovernanceDashboard,
    KnowledgeGovernancePolicy,
    KnowledgeGovernanceReport,
    KnowledgeGovernanceRule,
    KnowledgeQualityCheck,
    KnowledgeQualityMetric,
    KnowledgeQualityResult,
    KnowledgeQualityScore,
    KnowledgeRetentionAction,
    KnowledgeRetentionRule,
    KnowledgeSourceStatus,
    KnowledgeSourceValidation,
    KnowledgeStewardshipAssignment,
    KnowledgeStewardshipRole,
)
from eaip.logging.context import get_logger


class KnowledgeGovernanceService:
    """Central service for Knowledge Governance operations."""

    def __init__(
        self,
        config: KnowledgeGovernanceConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the Knowledge Governance service.

        Args:
            config: Optional governance configuration.
            event_bus: Optional event bus for publishing domain events.
        """
        cfg = KnowledgeGovernanceConfig(id="default", name="Default Knowledge Governance Config")
        self._config = config or cfg
        self._event_bus = event_bus or EventBus()
        self._log = get_logger("eaip.knowledge_governance.service")
        self._policies: dict[str, KnowledgeGovernancePolicy] = {}
        self._quality_checks: dict[str, KnowledgeQualityCheck] = {}
        self._quality_results: dict[str, KnowledgeQualityResult] = {}
        self._quality_scores: dict[str, KnowledgeQualityScore] = {}
        self._audit_trails: dict[str, KnowledgeAuditTrail] = {}
        self._reports: dict[str, KnowledgeGovernanceReport] = {}
        self._retention_rules: dict[str, KnowledgeRetentionRule] = {}
        self._classification_policies: dict[str, KnowledgeClassificationPolicy] = {}
        self._source_validations: dict[str, KnowledgeSourceValidation] = {}
        self._stewardship_assignments: dict[str, KnowledgeStewardshipAssignment] = {}

    @property
    def config(self) -> KnowledgeGovernanceConfig:
        """Return the governance configuration."""
        return self._config

    # ── Policies ──────────────────────────────────────────────────────────────

    async def create_policy(
        self,
        name: str,
        scope: GovernanceScope = GovernanceScope.GLOBAL,
        description: str = "",
        rules: tuple[KnowledgeGovernanceRule, ...] = (),
    ) -> KnowledgeGovernancePolicy:
        """Create a new governance policy.

        Args:
            name: Policy name.
            scope: Governance scope.
            description: Optional description.
            rules: Optional tuple of governance rules.

        Returns:
            The created KnowledgeGovernancePolicy.

        Raises:
            KnowledgeGovernancePolicyError: If name is empty.
        """
        if not name:
            raise KnowledgeGovernancePolicyError("Policy name is required")
        policy = KnowledgeGovernancePolicy(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            scope=scope,
            rules=rules,
        )
        self._policies[policy.id] = policy
        await self._event_bus.publish(
            KnowledgeGovernancePolicyCreated(
                policy_id=policy.id,
                policy_name=policy.name,
                scope=policy.scope,
            ),
        )
        self._log.info("kg.policy.created", policy_id=policy.id, name=policy.name)
        return policy

    async def get_policy(self, policy_id: str) -> KnowledgeGovernancePolicy:
        """Get a governance policy by ID.

        Args:
            policy_id: The policy ID.

        Returns:
            The KnowledgeGovernancePolicy.

        Raises:
            KnowledgeGovernancePolicyError: If not found.
        """
        policy = self._policies.get(policy_id)
        if policy is None:
            raise KnowledgeGovernancePolicyError(
                f"Policy {policy_id!r} not found",
                context={"policy_id": policy_id},
            )
        return policy

    async def list_policies(
        self, scope: GovernanceScope | None = None
    ) -> list[KnowledgeGovernancePolicy]:
        """List all governance policies, optionally filtered by scope.

        Args:
            scope: Optional governance scope filter.

        Returns:
            List of KnowledgeGovernancePolicy instances.
        """
        result = list(self._policies.values())
        if scope is not None:
            result = [p for p in result if p.scope == scope]
        return result

    async def update_policy(
        self,
        policy_id: str,
        name: str | None = None,
        description: str | None = None,
        rules: tuple[KnowledgeGovernanceRule, ...] | None = None,
        enabled: bool | None = None,
    ) -> KnowledgeGovernancePolicy:
        """Update an existing governance policy.

        Args:
            policy_id: The policy ID.
            name: Optional new name.
            description: Optional new description.
            rules: Optional new rules.
            enabled: Optional enabled flag.

        Returns:
            The updated KnowledgeGovernancePolicy.

        Raises:
            KnowledgeGovernancePolicyError: If not found.
        """
        existing = await self.get_policy(policy_id)
        updates: dict[str, Any] = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if rules is not None:
            updates["rules"] = rules
        if enabled is not None:
            updates["enabled"] = enabled
        if not updates:
            return existing

        updated = existing.model_copy(update={**updates, "updated_at": datetime.now(UTC)})
        self._policies[policy_id] = updated
        await self._event_bus.publish(
            KnowledgeGovernancePolicyUpdated(
                policy_id=updated.id,
                policy_name=updated.name,
                changes=updates,
            ),
        )
        self._log.info("kg.policy.updated", policy_id=policy_id)
        return updated

    async def enforce_policy(
        self,
        policy_id: str,
        subject_id: str,
        action: str,
        resource: str,
    ) -> bool:
        """Enforce a governance policy for a given subject and action.

        Args:
            policy_id: The policy ID.
            subject_id: The subject identifier.
            action: The action being performed.
            resource: The resource being accessed.

        Returns:
            True if the policy allowed the action.

        Raises:
            KnowledgeGovernanceViolationError: If the policy is violated.
        """
        policy = await self.get_policy(policy_id)
        if not policy.enabled:
            return False

        for rule in policy.rules:
            if not rule.enabled:
                continue
            if action in rule.actions or not rule.actions:
                await self._event_bus.publish(
                    KnowledgeGovernancePolicyEnforced(
                        policy_id=policy.id,
                        policy_name=policy.name,
                        subject_id=subject_id,
                        action=action,
                        resource=resource,
                        matched_rules=(rule.id,),
                    ),
                )
                self._log.info(
                    "kg.policy.enforced",
                    policy_id=policy_id,
                    rule_id=rule.id,
                    subject=subject_id,
                )
                return True

        await self._event_bus.publish(
            KnowledgeGovernancePolicyViolated(
                policy_id=policy.id,
                policy_name=policy.name,
                subject_id=subject_id,
                action=action,
                resource=resource,
                explanation="No matching rule found",
            ),
        )
        raise KnowledgeGovernanceViolationError(
            f"Policy {policy_id!r} violated by {subject_id!r}",
            context={"policy_id": policy_id, "subject": subject_id, "action": action},
        )

    # ── Quality Checks ───────────────────────────────────────────────────────

    async def start_quality_check(
        self,
        resource_id: str,
        resource_type: str,
        name: str = "",
    ) -> KnowledgeQualityCheck:
        """Start a quality check on a knowledge resource.

        Args:
            resource_id: The resource identifier.
            resource_type: The resource type.
            name: Optional check name.

        Returns:
            The created KnowledgeQualityCheck.
        """
        check = KnowledgeQualityCheck(
            id=str(uuid.uuid4()),
            name=name or f"Quality Check - {resource_id}",
            resource_id=resource_id,
            resource_type=resource_type,
        )
        self._quality_checks[check.id] = check
        await self._event_bus.publish(
            KnowledgeQualityCheckStarted(
                check_id=check.id,
                resource_id=resource_id,
                resource_type=resource_type,
            ),
        )
        self._log.info("kg.quality_check.started", check_id=check.id)
        return check

    async def complete_quality_check(
        self,
        check_id: str,
        metrics: tuple[KnowledgeQualityMetric, ...] = (),
        overall_score: float = 0.0,
        summary: str = "",
        details: dict[str, Any] | None = None,
    ) -> KnowledgeQualityResult:
        """Complete a quality check with results.

        Args:
            check_id: The check ID.
            metrics: Optional tuple of quality metrics.
            overall_score: Overall quality score.
            summary: Optional summary message.
            details: Optional details dictionary.

        Returns:
            The KnowledgeQualityResult.

        Raises:
            KnowledgeQualityError: If check not found.
        """
        check = self._quality_checks.get(check_id)
        if check is None:
            raise KnowledgeQualityError(
                f"Quality check {check_id!r} not found",
                context={"check_id": check_id},
            )

        passed = all(m.passed for m in metrics) if metrics else True

        result = KnowledgeQualityResult(
            check_id=check_id,
            resource_id=check.resource_id,
            resource_type=check.resource_type,
            metrics=metrics,
            overall_score=overall_score,
            passed=passed,
            summary=summary,
            details=details or {},
        )
        self._quality_results[result.check_id] = result
        self._log.info("kg.quality_check.completed", check_id=check_id, passed=passed)
        return result

    async def complete_check(
        self,
        check_id: str,
        metrics: tuple[KnowledgeQualityMetric, ...] = (),
        overall_score: float = 0.0,
        passed: bool = True,
    ) -> KnowledgeQualityResult:
        """Complete a quality check and publish events.

        Args:
            check_id: The check ID.
            metrics: Quality metrics.
            overall_score: Overall score.
            passed: Whether the check passed.

        Returns:
            The KnowledgeQualityResult.

        Raises:
            KnowledgeQualityError: If check not found.
        """
        result = await self.complete_quality_check(
            check_id=check_id,
            metrics=metrics,
            overall_score=overall_score,
            summary="Check completed" if passed else "Check failed",
        )

        check = self._quality_checks[check_id]
        completed = check.model_copy(
            update={"completed_at": datetime.now(UTC), "status": "completed"},
        )
        self._quality_checks[check_id] = completed

        if passed:
            await self._event_bus.publish(
                KnowledgeQualityCheckCompleted(
                    check_id=check_id,
                    resource_id=check.resource_id,
                    resource_type=check.resource_type,
                    overall_score=overall_score,
                    passed=True,
                ),
            )
        else:
            await self._event_bus.publish(
                KnowledgeQualityCheckFailed(
                    check_id=check_id,
                    resource_id=check.resource_id,
                    resource_type=check.resource_type,
                    error="Quality check failed",
                ),
            )

        score_id = str(uuid.uuid4())
        score = KnowledgeQualityScore(
            id=score_id,
            resource_id=check.resource_id,
            resource_type=check.resource_type,
            score=overall_score,
            metric_count=len(metrics),
            passed_count=sum(1 for m in metrics if m.passed) if metrics else 0,
        )
        self._quality_scores[score_id] = score
        await self._event_bus.publish(
            KnowledgeQualityScoreComputed(
                score_id=score_id,
                resource_id=check.resource_id,
                resource_type=check.resource_type,
                score=overall_score,
            ),
        )

        self._log.info("kg.check.completed", check_id=check_id, passed=passed)
        return result

    async def get_quality_result(self, check_id: str) -> KnowledgeQualityResult:
        """Get a quality result by check ID.

        Args:
            check_id: The check ID.

        Returns:
            The KnowledgeQualityResult.

        Raises:
            KnowledgeQualityError: If not found.
        """
        result = self._quality_results.get(check_id)
        if result is None:
            raise KnowledgeQualityError(
                f"Quality result {check_id!r} not found",
                context={"check_id": check_id},
            )
        return result

    async def list_quality_results(self) -> list[KnowledgeQualityResult]:
        """List all quality results.

        Returns:
            List of KnowledgeQualityResult instances.
        """
        return list(self._quality_results.values())

    # ── Audit Trails ─────────────────────────────────────────────────────────

    async def create_audit_entry(
        self,
        action: str,
        actor: str = "",
        resource_id: str = "",
        resource_type: str = "",
        details: dict[str, Any] | None = None,
    ) -> KnowledgeAuditTrail:
        """Create a new audit trail entry.

        Args:
            action: The action description.
            actor: Optional actor identifier.
            resource_id: Optional resource identifier.
            resource_type: Optional resource type.
            details: Optional details dictionary.

        Returns:
            The created KnowledgeAuditTrail entry.
        """
        entry = KnowledgeAuditTrail(
            id=str(uuid.uuid4()),
            action=action,
            actor=actor,
            resource_id=resource_id,
            resource_type=resource_type,
            details=details or {},
        )
        self._audit_trails[entry.id] = entry
        await self._event_bus.publish(
            KnowledgeAuditTrailEntryCreated(
                entry_id=entry.id,
                action=entry.action,
                actor=entry.actor,
                resource_id=entry.resource_id,
            ),
        )
        self._log.info("kg.audit.entry.created", entry_id=entry.id, action=action)
        return entry

    async def list_audit_entries(
        self,
        actor: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list[KnowledgeAuditTrail]:
        """List audit trail entries, optionally filtered.

        Args:
            actor: Optional actor filter.
            action: Optional action filter.
            limit: Maximum number of entries to return.

        Returns:
            List of KnowledgeAuditTrail entries.
        """
        result = list(self._audit_trails.values())
        if actor is not None:
            result = [e for e in result if e.actor == actor]
        if action is not None:
            result = [e for e in result if e.action == action]
        result.sort(key=lambda e: e.timestamp, reverse=True)
        return result[:limit]

    # ── Reports ──────────────────────────────────────────────────────────────

    async def generate_report(
        self,
        report_type: str,
        name: str = "",
        data: dict[str, Any] | None = None,
    ) -> KnowledgeGovernanceReport:
        """Generate a governance report.

        Args:
            report_type: The report type.
            name: Optional report name.
            data: Optional report data.

        Returns:
            The generated KnowledgeGovernanceReport.
        """
        report = KnowledgeGovernanceReport(
            id=str(uuid.uuid4()),
            name=name or f"Report - {report_type}",
            report_type=report_type,
            data=data or {},
        )
        self._reports[report.id] = report
        await self._event_bus.publish(
            KnowledgeGovernanceReportGenerated(
                report_id=report.id,
                report_type=report_type,
            ),
        )
        self._log.info("kg.report.generated", report_id=report.id, report_type=report_type)
        return report

    async def list_reports(self, report_type: str | None = None) -> list[KnowledgeGovernanceReport]:
        """List governance reports, optionally filtered by type.

        Args:
            report_type: Optional report type filter.

        Returns:
            List of KnowledgeGovernanceReport instances.
        """
        result = list(self._reports.values())
        if report_type is not None:
            result = [r for r in result if r.report_type == report_type]
        return result

    # ── Retention Rules ──────────────────────────────────────────────────────

    async def create_retention_rule(
        self,
        name: str,
        resource_type: str = "",
        max_age_days: int = 365,
        action: KnowledgeRetentionAction = KnowledgeRetentionAction.ARCHIVE,
        description: str = "",
    ) -> KnowledgeRetentionRule:
        """Create a new retention rule.

        Args:
            name: Rule name.
            resource_type: Optional resource type filter.
            max_age_days: Maximum age in days.
            action: Action to take when rule triggers.
            description: Optional description.

        Returns:
            The created KnowledgeRetentionRule.

        Raises:
            KnowledgeRetentionError: If name is empty.
        """
        if not name:
            raise KnowledgeRetentionError("Retention rule name is required")
        rule = KnowledgeRetentionRule(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            resource_type=resource_type,
            max_age_days=max_age_days,
            action=action,
        )
        self._retention_rules[rule.id] = rule
        self._log.info("kg.retention_rule.created", rule_id=rule.id)
        return rule

    async def apply_retention_rule(
        self,
        rule_id: str,
        resource_ids: tuple[str, ...] = (),
    ) -> None:
        """Apply a retention rule to specified resources.

        Args:
            rule_id: The retention rule ID.
            resource_ids: The resource IDs to apply the rule to.

        Raises:
            KnowledgeRetentionError: If rule not found.
        """
        rule = self._retention_rules.get(rule_id)
        if rule is None:
            raise KnowledgeRetentionError(
                f"Retention rule {rule_id!r} not found",
                context={"rule_id": rule_id},
            )
        if not rule.enabled:
            raise KnowledgeRetentionError(
                f"Retention rule {rule_id!r} is disabled",
                context={"rule_id": rule_id},
            )
        count = len(resource_ids)
        await self._event_bus.publish(
            KnowledgeRetentionRuleApplied(
                rule_id=rule_id,
                rule_name=rule.name,
                resource_count=count,
                action=rule.action,
            ),
        )
        self._log.info("kg.retention_rule.applied", rule_id=rule_id, count=count)

    async def list_retention_rules(self) -> list[KnowledgeRetentionRule]:
        """List all retention rules.

        Returns:
            List of KnowledgeRetentionRule instances.
        """
        return list(self._retention_rules.values())

    # ── Classification ───────────────────────────────────────────────────────

    async def create_classification_policy(
        self,
        name: str,
        default_level: KnowledgeClassificationLevel = KnowledgeClassificationLevel.INTERNAL,
        description: str = "",
    ) -> KnowledgeClassificationPolicy:
        """Create a new classification policy.

        Args:
            name: Policy name.
            default_level: Default classification level.
            description: Optional description.

        Returns:
            The created KnowledgeClassificationPolicy.

        Raises:
            KnowledgeClassificationError: If name is empty.
        """
        if not name:
            raise KnowledgeClassificationError("Classification policy name is required")
        policy = KnowledgeClassificationPolicy(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            default_level=default_level,
        )
        self._classification_policies[policy.id] = policy
        self._log.info("kg.classification_policy.created", policy_id=policy.id)
        return policy

    async def update_classification(
        self,
        resource_id: str,
        resource_type: str,
        new_level: KnowledgeClassificationLevel,
        previous_level: KnowledgeClassificationLevel = KnowledgeClassificationLevel.INTERNAL,
    ) -> None:
        """Update the classification of a resource.

        Args:
            resource_id: The resource identifier.
            resource_type: The resource type.
            new_level: The new classification level.
            previous_level: The previous classification level.
        """
        await self._event_bus.publish(
            KnowledgeClassificationUpdated(
                resource_id=resource_id,
                resource_type=resource_type,
                previous_level=previous_level,
                new_level=new_level,
            ),
        )
        self._log.info(
            "kg.classification.updated",
            resource_id=resource_id,
            old=previous_level,
            new=new_level,
        )

    # ── Source Validation ────────────────────────────────────────────────────

    async def validate_source(
        self,
        source_id: str,
        source_type: str = "",
        validated_by: str = "",
    ) -> KnowledgeSourceValidation:
        """Validate a knowledge source.

        Args:
            source_id: The source identifier.
            source_type: Optional source type.
            validated_by: Optional validator identifier.

        Returns:
            The KnowledgeSourceValidation record.
        """
        validation = KnowledgeSourceValidation(
            id=str(uuid.uuid4()),
            source_id=source_id,
            source_type=source_type,
            status=KnowledgeSourceStatus.VALIDATED,
            validated_by=validated_by,
            validated_at=datetime.now(UTC),
        )
        self._source_validations[validation.id] = validation
        await self._event_bus.publish(
            KnowledgeSourceValidated(
                validation_id=validation.id,
                source_id=source_id,
                source_type=source_type,
            ),
        )
        self._log.info("kg.source.validated", validation_id=validation.id, source_id=source_id)
        return validation

    async def approve_source(self, validation_id: str) -> KnowledgeSourceValidation:
        """Approve a validated source.

        Args:
            validation_id: The validation record ID.

        Returns:
            The updated KnowledgeSourceValidation.

        Raises:
            KnowledgeSourceValidationError: If not found.
        """
        validation = self._source_validations.get(validation_id)
        if validation is None:
            raise KnowledgeSourceValidationError(
                f"Source validation {validation_id!r} not found",
                context={"validation_id": validation_id},
            )
        updated = validation.model_copy(update={"status": KnowledgeSourceStatus.APPROVED})
        self._source_validations[validation_id] = updated
        await self._event_bus.publish(
            KnowledgeSourceApproved(
                validation_id=validation_id,
                source_id=validation.source_id,
                source_type=validation.source_type,
            ),
        )
        self._log.info("kg.source.approved", validation_id=validation_id)
        return updated

    async def reject_source(
        self,
        validation_id: str,
        reason: str = "",
    ) -> KnowledgeSourceValidation:
        """Reject a validated source.

        Args:
            validation_id: The validation record ID.
            reason: Optional rejection reason.

        Returns:
            The updated KnowledgeSourceValidation.

        Raises:
            KnowledgeSourceValidationError: If not found.
        """
        validation = self._source_validations.get(validation_id)
        if validation is None:
            raise KnowledgeSourceValidationError(
                f"Source validation {validation_id!r} not found",
                context={"validation_id": validation_id},
            )
        updated = validation.model_copy(
            update={
                "status": KnowledgeSourceStatus.REJECTED,
                "validation_notes": reason,
            },
        )
        self._source_validations[validation_id] = updated
        await self._event_bus.publish(
            KnowledgeSourceRejected(
                validation_id=validation_id,
                source_id=validation.source_id,
                source_type=validation.source_type,
                reason=reason,
            ),
        )
        self._log.info("kg.source.rejected", validation_id=validation_id, reason=reason)
        return updated

    async def list_source_validations(
        self,
        status: KnowledgeSourceStatus | None = None,
    ) -> list[KnowledgeSourceValidation]:
        """List source validations, optionally filtered by status.

        Args:
            status: Optional status filter.

        Returns:
            List of KnowledgeSourceValidation instances.
        """
        result = list(self._source_validations.values())
        if status is not None:
            result = [v for v in result if v.status == status]
        return result

    # ── Stewardship ──────────────────────────────────────────────────────────

    async def assign_steward(
        self,
        resource_id: str,
        user_id: str,
        role: KnowledgeStewardshipRole = KnowledgeStewardshipRole.STEWARD,
        resource_type: str = "",
    ) -> KnowledgeStewardshipAssignment:
        """Assign a stewardship role to a user for a resource.

        Args:
            resource_id: The resource identifier.
            user_id: The user identifier.
            role: The stewardship role.
            resource_type: Optional resource type.

        Returns:
            The KnowledgeStewardshipAssignment.
        """
        assignment = KnowledgeStewardshipAssignment(
            id=str(uuid.uuid4()),
            resource_id=resource_id,
            resource_type=resource_type,
            user_id=user_id,
            role=role,
        )
        self._stewardship_assignments[assignment.id] = assignment
        await self._event_bus.publish(
            KnowledgeStewardshipAssigned(
                assignment_id=assignment.id,
                resource_id=resource_id,
                user_id=user_id,
                role=role,
            ),
        )
        self._log.info("kg.stewardship.assigned", assignment_id=assignment.id)
        return assignment

    async def unassign_steward(self, assignment_id: str) -> None:
        """Unassign a stewardship role.

        Args:
            assignment_id: The assignment ID.

        Raises:
            KnowledgeStewardshipError: If not found.
        """
        assignment = self._stewardship_assignments.get(assignment_id)
        if assignment is None:
            raise KnowledgeStewardshipError(
                f"Stewardship assignment {assignment_id!r} not found",
                context={"assignment_id": assignment_id},
            )
        del self._stewardship_assignments[assignment_id]
        await self._event_bus.publish(
            KnowledgeStewardshipUnassigned(
                assignment_id=assignment_id,
                resource_id=assignment.resource_id,
                user_id=assignment.user_id,
                role=assignment.role,
            ),
        )
        self._log.info("kg.stewardship.unassigned", assignment_id=assignment_id)

    async def list_stewardship_assignments(
        self,
        resource_id: str | None = None,
        user_id: str | None = None,
    ) -> list[KnowledgeStewardshipAssignment]:
        """List stewardship assignments, optionally filtered.

        Args:
            resource_id: Optional resource ID filter.
            user_id: Optional user ID filter.

        Returns:
            List of KnowledgeStewardshipAssignment instances.
        """
        result = list(self._stewardship_assignments.values())
        if resource_id is not None:
            result = [a for a in result if a.resource_id == resource_id]
        if user_id is not None:
            result = [a for a in result if a.user_id == user_id]
        return result

    # ── Dashboard ────────────────────────────────────────────────────────────

    async def get_dashboard(self) -> KnowledgeGovernanceDashboard:
        """Get the governance dashboard snapshot.

        Returns:
            The KnowledgeGovernanceDashboard with current metrics.
        """
        total = len(self._policies)
        active = sum(1 for p in self._policies.values() if p.enabled)
        total_checks = len(self._quality_checks)
        completed_checks = [c for c in self._quality_checks.values() if c.completed_at is not None]
        passed = sum(
            1
            for c in completed_checks
            if c.status == "completed"
            and any(r.passed for r in self._quality_results.values() if r.check_id == c.id)
        )
        failed = sum(1 for c in completed_checks if c.status == "failed")
        scores = list(self._quality_scores.values())
        avg_score = sum(s.score for s in scores) / len(scores) if scores else 0.0

        dashboard = KnowledgeGovernanceDashboard(
            id="knowledge_governance_dashboard",
            total_policies=total,
            active_policies=active,
            total_quality_checks=total_checks,
            passed_checks=passed,
            failed_checks=failed,
            audit_entries=len(self._audit_trails),
            retention_rules=len(self._retention_rules),
            classification_policies=len(self._classification_policies),
            source_validations=len(self._source_validations),
            stewardship_assignments=len(self._stewardship_assignments),
            overall_quality_score=avg_score,
        )

        await self._event_bus.publish(
            KnowledgeGovernanceDashboardUpdated(
                dashboard_id=dashboard.id,
                overall_quality_score=avg_score,
                total_policies=total,
            ),
        )
        return dashboard

    # ── Config ───────────────────────────────────────────────────────────────

    async def update_config(self, **updates: Any) -> KnowledgeGovernanceConfig:
        """Update the governance configuration.

        Args:
            updates: Configuration fields to update.

        Returns:
            The updated KnowledgeGovernanceConfig.
        """
        self._config = self._config.model_copy(update=updates)
        await self._event_bus.publish(
            KnowledgeGovernanceConfigUpdated(
                config_id=self._config.id,
                config_name=self._config.name,
            ),
        )
        self._log.info("kg.config.updated")
        return self._config


__all__ = ["KnowledgeGovernanceService"]
