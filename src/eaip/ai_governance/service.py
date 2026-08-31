"""AiGovernanceService for AI Governance & Compliance."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from eaip.ai_governance.events import (
    AiAuditTrailEntryCreated,
    AiBiasCheckCompleted,
    AiComplianceCheckCompleted,
    AiComplianceCheckFailed,
    AiComplianceCheckStarted,
    AiComplianceReportGenerated,
    AiComplianceRequirementUpdated,
    AiFairnessMetricComputed,
    AiGovernanceDashboardUpdated,
    AiGovernancePolicyCreated,
    AiGovernancePolicyEnforced,
    AiGovernancePolicyUpdated,
    AiGovernancePolicyViolated,
    AiGovernanceReviewApproved,
    AiGovernanceReviewCompleted,
    AiGovernanceReviewRejected,
    AiGovernanceReviewStarted,
    AiModelRiskAssessed,
)
from eaip.ai_governance.exceptions import (
    AiComplianceCheckError,
    AiComplianceRequirementError,
    AiGovernancePolicyError,
    AiGovernanceViolationError,
    AiReviewError,
    AiRiskAssessmentError,
)
from eaip.ai_governance.models import (
    AiAuditTrail,
    AiBiasCheckResult,
    AiComplianceCheck,
    AiComplianceReport,
    AiComplianceRequirement,
    AiComplianceResult,
    AiExplainabilityRecord,
    AiFairnessMetric,
    AiGovernanceConfig,
    AiGovernanceDashboard,
    AiGovernancePolicy,
    AiGovernanceReview,
    AiGovernanceRule,
    AiModelRiskAssessment,
    ComplianceStandard,
    ComplianceStatus as AiComplianceStatus,
    PolicyType,
    ReviewStatus,
    RiskLevel,
)
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger


class AiGovernanceService:
    """Central service for AI Governance & Compliance operations."""

    def __init__(
        self,
        config: AiGovernanceConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the AI Governance service.

        Args:
            config: Optional governance configuration.
            event_bus: Optional event bus for publishing domain events.
        """
        self._config = config or AiGovernanceConfig()
        self._event_bus = event_bus or EventBus()
        self._log = get_logger("eaip.ai_governance.service")
        self._policies: dict[str, AiGovernancePolicy] = {}
        self._requirements: dict[str, AiComplianceRequirement] = {}
        self._checks: dict[str, AiComplianceCheck] = {}
        self._audit_trails: dict[str, AiAuditTrail] = {}
        self._reviews: dict[str, AiGovernanceReview] = {}
        self._risk_assessments: dict[str, AiModelRiskAssessment] = {}
        self._bias_checks: dict[str, AiBiasCheckResult] = {}
        self._fairness_metrics: dict[str, AiFairnessMetric] = {}
        self._explainability_records: dict[str, AiExplainabilityRecord] = {}

    @property
    def config(self) -> AiGovernanceConfig:
        """Return the governance configuration."""
        return self._config

    # ── Governance Policies ──────────────────────────────────────────

    async def create_policy(
        self,
        name: str,
        policy_type: PolicyType,
        description: str = "",
        rules: tuple[AiGovernanceRule, ...] = (),
    ) -> AiGovernancePolicy:
        """Create a new AI governance policy.

        Args:
            name: Policy name.
            policy_type: Type of policy.
            description: Optional description.
            rules: Optional tuple of governance rules.

        Returns:
            The created AiGovernancePolicy.

        Raises:
            AiGovernancePolicyError: If name is empty.
        """
        if not name:
            raise AiGovernancePolicyError("Policy name is required")
        policy = AiGovernancePolicy(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            policy_type=policy_type,
            rules=rules,
        )
        self._policies[policy.id] = policy
        await self._event_bus.publish(
            AiGovernancePolicyCreated(
                policy_id=policy.id,
                policy_name=policy.name,
                policy_type=policy.policy_type,
            ),
        )
        self._log.info("policy.created", policy_id=policy.id, name=policy.name)
        return policy

    async def get_policy(self, policy_id: str) -> AiGovernancePolicy:
        """Get a governance policy by ID.

        Args:
            policy_id: The policy ID.

        Returns:
            The AiGovernancePolicy.

        Raises:
            AiGovernancePolicyError: If not found.
        """
        policy = self._policies.get(policy_id)
        if policy is None:
            raise AiGovernancePolicyError(
                f"Policy {policy_id!r} not found",
                context={"policy_id": policy_id},
            )
        return policy

    async def list_policies(
        self, policy_type: PolicyType | None = None
    ) -> list[AiGovernancePolicy]:
        """List all governance policies, optionally filtered by type.

        Args:
            policy_type: Optional policy type filter.

        Returns:
            List of AiGovernancePolicy instances.
        """
        result = list(self._policies.values())
        if policy_type is not None:
            result = [p for p in result if p.policy_type == policy_type]
        return result

    async def update_policy(
        self,
        policy_id: str,
        name: str | None = None,
        description: str | None = None,
        rules: tuple[AiGovernanceRule, ...] | None = None,
        enabled: bool | None = None,
    ) -> AiGovernancePolicy:
        """Update an existing governance policy.

        Args:
            policy_id: The policy ID.
            name: Optional new name.
            description: Optional new description.
            rules: Optional new rules.
            enabled: Optional enabled flag.

        Returns:
            The updated AiGovernancePolicy.

        Raises:
            AiGovernancePolicyError: If not found.
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
            AiGovernancePolicyUpdated(
                policy_id=updated.id,
                policy_name=updated.name,
                changes=updates,
            ),
        )
        self._log.info("policy.updated", policy_id=policy_id)
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
            AiGovernanceViolationError: If the policy is violated.
        """
        policy = await self.get_policy(policy_id)
        if not policy.enabled:
            return False

        for rule in policy.rules:
            if not rule.enabled:
                continue
            if action in rule.actions or not rule.actions:
                await self._event_bus.publish(
                    AiGovernancePolicyEnforced(
                        policy_id=policy.id,
                        policy_name=policy.name,
                        subject_id=subject_id,
                        action=action,
                        resource=resource,
                        matched_rules=(rule.id,),
                    ),
                )
                self._log.info(
                    "policy.enforced",
                    policy_id=policy_id,
                    rule_id=rule.id,
                    subject=subject_id,
                )
                return True

        await self._event_bus.publish(
            AiGovernancePolicyViolated(
                policy_id=policy.id,
                policy_name=policy.name,
                subject_id=subject_id,
                action=action,
                resource=resource,
                explanation="No matching rule found",
            ),
        )
        raise AiGovernanceViolationError(
            f"Policy {policy_id!r} violated by {subject_id!r}",
            context={"policy_id": policy_id, "subject": subject_id, "action": action},
        )

    # ── Compliance ───────────────────────────────────────────────────

    async def create_requirement(
        self,
        name: str,
        standard: ComplianceStandard,
        description: str = "",
        control_id: str = "",
        category: str = "",
        severity: str = "medium",
    ) -> AiComplianceRequirement:
        """Create a new compliance requirement.

        Args:
            name: Requirement name.
            standard: Compliance standard.
            description: Optional description.
            control_id: Optional control identifier.
            category: Optional category.
            severity: Optional severity level.

        Returns:
            The created AiComplianceRequirement.

        Raises:
            AiComplianceRequirementError: If name is empty.
        """
        if not name:
            raise AiComplianceRequirementError("Requirement name is required")
        requirement = AiComplianceRequirement(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            standard=standard,
            control_id=control_id,
            category=category,
            severity=severity,
        )
        self._requirements[requirement.id] = requirement
        self._log.info("requirement.created", requirement_id=requirement.id)
        return requirement

    async def get_requirement(self, requirement_id: str) -> AiComplianceRequirement:
        """Get a compliance requirement by ID.

        Args:
            requirement_id: The requirement ID.

        Returns:
            The AiComplianceRequirement.

        Raises:
            AiComplianceRequirementError: If not found.
        """
        req = self._requirements.get(requirement_id)
        if req is None:
            raise AiComplianceRequirementError(
                f"Requirement {requirement_id!r} not found",
                context={"requirement_id": requirement_id},
            )
        return req

    async def list_requirements(
        self, standard: ComplianceStandard | None = None
    ) -> list[AiComplianceRequirement]:
        """List compliance requirements, optionally filtered by standard.

        Args:
            standard: Optional compliance standard filter.

        Returns:
            List of AiComplianceRequirement instances.
        """
        result = list(self._requirements.values())
        if standard is not None:
            result = [r for r in result if r.standard == standard]
        return result

    async def run_compliance_check(self, requirement_id: str) -> AiComplianceCheck:
        """Run a compliance check for a requirement.

        Args:
            requirement_id: The requirement ID.

        Returns:
            The created AiComplianceCheck.

        Raises:
            AiComplianceRequirementError: If requirement not found.
        """
        requirement = await self.get_requirement(requirement_id)
        check = AiComplianceCheck(
            id=str(uuid.uuid4()),
            requirement_id=requirement_id,
            name=f"Check {requirement.name}",
            started_at=datetime.now(UTC),
        )
        self._checks[check.id] = check
        await self._event_bus.publish(
            AiComplianceCheckStarted(
                check_id=check.id,
                requirement_id=requirement_id,
                standard=requirement.standard,
            ),
        )
        self._log.info("compliance.check.started", check_id=check.id)
        return check

    async def complete_compliance_check(
        self,
        check_id: str,
        status: AiComplianceStatus,
        score: float = 0.0,
        summary: str = "",
        details: dict[str, Any] | None = None,
    ) -> AiComplianceResult:
        """Complete a compliance check with a given status.

        Args:
            check_id: The check ID.
            status: The compliance status.
            score: Optional compliance score.
            summary: Optional summary message.
            details: Optional details dictionary.

        Returns:
            The AiComplianceResult.

        Raises:
            AiComplianceCheckError: If check not found.
        """
        check = self._checks.get(check_id)
        if check is None:
            raise AiComplianceCheckError(
                f"Check {check_id!r} not found",
                context={"check_id": check_id},
            )

        completed = check.model_copy(
            update={
                "status": status,
                "completed_at": datetime.now(UTC),
                "details": details or {},
            },
        )
        self._checks[check_id] = completed

        result = AiComplianceResult(
            check_id=check_id,
            requirement_id=check.requirement_id,
            status=status,
            score=score,
            summary=summary,
            details=details or {},
        )

        if status == AiComplianceStatus.COMPLIANT:
            await self._event_bus.publish(
                AiComplianceCheckCompleted(
                    check_id=check_id,
                    requirement_id=check.requirement_id,
                    status=status,
                    score=score,
                ),
            )
        else:
            await self._event_bus.publish(
                AiComplianceCheckFailed(
                    check_id=check_id,
                    requirement_id=check.requirement_id,
                    error=summary,
                ),
            )

        requirement = self._requirements.get(check.requirement_id)
        if requirement is not None:
            updated = requirement.model_copy(update={"status": status})
            self._requirements[requirement.id] = updated
            await self._event_bus.publish(
                AiComplianceRequirementUpdated(
                    requirement_id=requirement.id,
                    name=requirement.name,
                    old_status=requirement.status,
                    new_status=status,
                ),
            )

        self._log.info("compliance.check.completed", check_id=check_id, status=status)
        return result

    async def generate_compliance_report(self, standard: ComplianceStandard) -> AiComplianceReport:
        """Generate a compliance report for a given standard.

        Args:
            standard: The compliance standard.

        Returns:
            The generated AiComplianceReport.
        """
        results: list[AiComplianceResult] = []
        for check in self._checks.values():
            req = self._requirements.get(check.requirement_id)
            if req is not None and req.standard == standard and check.completed_at is not None:
                results.append(
                    AiComplianceResult(
                        check_id=check.id,
                        requirement_id=check.requirement_id,
                        status=check.status,
                    ),
                )

        total = len(results)
        passed = sum(1 for r in results if r.status == AiComplianceStatus.COMPLIANT)
        failed = total - passed
        score = (passed / total * 100.0) if total > 0 else 0.0
        overall = (
            AiComplianceStatus.COMPLIANT
            if failed == 0 and total > 0
            else AiComplianceStatus.NON_COMPLIANT
            if failed > 0
            else AiComplianceStatus.PENDING
        )

        report = AiComplianceReport(
            id=str(uuid.uuid4()),
            name=f"Compliance Report - {standard}",
            standard=standard,
            results=tuple(results),
            overall_status=overall,
            total_checks=total,
            passed_checks=passed,
            failed_checks=failed,
            score=score,
        )

        await self._event_bus.publish(
            AiComplianceReportGenerated(
                report_id=report.id,
                standard=standard,
                overall_status=overall,
                score=score,
            ),
        )
        self._log.info(
            "compliance.report.generated",
            report_id=report.id,
            standard=standard,
            score=score,
        )
        return report

    # ── Audit Trails ─────────────────────────────────────────────────

    async def create_audit_entry(
        self,
        action: str,
        actor: str = "",
        resource_id: str = "",
        resource_type: str = "",
        details: dict[str, Any] | None = None,
    ) -> AiAuditTrail:
        """Create a new audit trail entry.

        Args:
            action: The action description.
            actor: Optional actor identifier.
            resource_id: Optional resource identifier.
            resource_type: Optional resource type.
            details: Optional details dictionary.

        Returns:
            The created AiAuditTrail entry.
        """
        entry = AiAuditTrail(
            id=str(uuid.uuid4()),
            action=action,
            actor=actor,
            resource_id=resource_id,
            resource_type=resource_type,
            details=details or {},
        )
        self._audit_trails[entry.id] = entry
        await self._event_bus.publish(
            AiAuditTrailEntryCreated(
                entry_id=entry.id,
                action=entry.action,
                actor=entry.actor,
                resource_id=entry.resource_id,
                resource_type=entry.resource_type,
            ),
        )
        self._log.info("audit.entry.created", entry_id=entry.id, action=action)
        return entry

    async def list_audit_entries(
        self,
        actor: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list[AiAuditTrail]:
        """List audit trail entries, optionally filtered.

        Args:
            actor: Optional actor filter.
            action: Optional action filter.
            limit: Maximum number of entries to return.

        Returns:
            List of AiAuditTrail entries.
        """
        result = list(self._audit_trails.values())
        if actor is not None:
            result = [e for e in result if e.actor == actor]
        if action is not None:
            result = [e for e in result if e.action == action]
        result.sort(key=lambda e: e.timestamp, reverse=True)
        return result[:limit]

    # ── Reviews ──────────────────────────────────────────────────────

    async def start_review(
        self,
        resource_id: str,
        resource_type: str,
        reviewer: str = "",
    ) -> AiGovernanceReview:
        """Start a new governance review.

        Args:
            resource_id: The resource under review.
            resource_type: The resource type.
            reviewer: Optional reviewer identifier.

        Returns:
            The created AiGovernanceReview.
        """
        review = AiGovernanceReview(
            id=str(uuid.uuid4()),
            resource_id=resource_id,
            resource_type=resource_type,
            reviewer=reviewer,
        )
        self._reviews[review.id] = review
        await self._event_bus.publish(
            AiGovernanceReviewStarted(
                review_id=review.id,
                resource_id=resource_id,
                resource_type=resource_type,
                reviewer=reviewer,
            ),
        )
        self._log.info("review.started", review_id=review.id)
        return review

    async def approve_review(
        self,
        review_id: str,
        comments: str = "",
    ) -> AiGovernanceReview:
        """Approve a governance review.

        Args:
            review_id: The review ID.
            comments: Optional approval comments.

        Returns:
            The updated AiGovernanceReview.

        Raises:
            AiReviewError: If review not found.
        """
        review = self._reviews.get(review_id)
        if review is None:
            raise AiReviewError(
                f"Review {review_id!r} not found",
                context={"review_id": review_id},
            )

        updated = review.model_copy(
            update={
                "status": ReviewStatus.APPROVED,
                "decision": "approved",
                "comments": comments,
                "completed_at": datetime.now(UTC),
            },
        )
        self._reviews[review_id] = updated
        await self._event_bus.publish(
            AiGovernanceReviewApproved(
                review_id=review_id,
                resource_id=review.resource_id,
                reviewer=review.reviewer,
                comments=comments,
            ),
        )
        await self._event_bus.publish(
            AiGovernanceReviewCompleted(
                review_id=review_id,
                resource_id=review.resource_id,
                decision="approved",
                status=ReviewStatus.APPROVED,
            ),
        )
        self._log.info("review.approved", review_id=review_id)
        return updated

    async def reject_review(
        self,
        review_id: str,
        comments: str = "",
    ) -> AiGovernanceReview:
        """Reject a governance review.

        Args:
            review_id: The review ID.
            comments: Optional rejection comments.

        Returns:
            The updated AiGovernanceReview.

        Raises:
            AiReviewError: If review not found.
        """
        review = self._reviews.get(review_id)
        if review is None:
            raise AiReviewError(
                f"Review {review_id!r} not found",
                context={"review_id": review_id},
            )

        updated = review.model_copy(
            update={
                "status": ReviewStatus.REJECTED,
                "decision": "rejected",
                "comments": comments,
                "completed_at": datetime.now(UTC),
            },
        )
        self._reviews[review_id] = updated
        await self._event_bus.publish(
            AiGovernanceReviewRejected(
                review_id=review_id,
                resource_id=review.resource_id,
                reviewer=review.reviewer,
                comments=comments,
            ),
        )
        await self._event_bus.publish(
            AiGovernanceReviewCompleted(
                review_id=review_id,
                resource_id=review.resource_id,
                decision="rejected",
                status=ReviewStatus.REJECTED,
            ),
        )
        self._log.info("review.rejected", review_id=review_id)
        return updated

    async def get_review(self, review_id: str) -> AiGovernanceReview:
        """Get a governance review by ID.

        Args:
            review_id: The review ID.

        Returns:
            The AiGovernanceReview.

        Raises:
            AiReviewError: If not found.
        """
        review = self._reviews.get(review_id)
        if review is None:
            raise AiReviewError(
                f"Review {review_id!r} not found",
                context={"review_id": review_id},
            )
        return review

    async def list_reviews(self, status: ReviewStatus | None = None) -> list[AiGovernanceReview]:
        """List governance reviews, optionally filtered by status.

        Args:
            status: Optional review status filter.

        Returns:
            List of AiGovernanceReview instances.
        """
        result = list(self._reviews.values())
        if status is not None:
            result = [r for r in result if r.status == status]
        return result

    # ── Risk Assessment ──────────────────────────────────────────────

    async def assess_model_risk(
        self,
        model_id: str,
        model_name: str = "",
        dimensions: dict[str, float] | None = None,
    ) -> AiModelRiskAssessment:
        """Assess risk for an AI model.

        Args:
            model_id: The model identifier.
            model_name: Optional model name.
            dimensions: Optional risk dimension scores.

        Returns:
            The AiModelRiskAssessment.
        """
        critical_threshold = 0.8
        high_threshold = 0.6
        medium_threshold = 0.3
        recommend_threshold = 0.5

        dims = dimensions or {}
        risk_score = sum(dims.values()) / max(len(dims), 1)
        if risk_score >= critical_threshold:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= high_threshold:
            risk_level = RiskLevel.HIGH
        elif risk_score >= medium_threshold:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        recommendations: list[str] = []
        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            recommendations.append("Implement additional safeguards")
            recommendations.append("Schedule human review")
        if risk_score > recommend_threshold:
            recommendations.append("Monitor model outputs regularly")

        assessment = AiModelRiskAssessment(
            id=str(uuid.uuid4()),
            model_id=model_id,
            model_name=model_name,
            risk_level=risk_level,
            risk_score=risk_score,
            dimensions=dims,
            recommendations=tuple(recommendations),
        )
        self._risk_assessments[assessment.id] = assessment
        await self._event_bus.publish(
            AiModelRiskAssessed(
                assessment_id=assessment.id,
                model_id=model_id,
                model_name=model_name,
                risk_level=risk_level,
                risk_score=risk_score,
            ),
        )
        self._log.info(
            "risk.assessed",
            assessment_id=assessment.id,
            model_id=model_id,
            risk_level=risk_level,
        )
        return assessment

    async def get_risk_assessment(self, assessment_id: str) -> AiModelRiskAssessment:
        """Get a risk assessment by ID.

        Args:
            assessment_id: The assessment ID.

        Returns:
            The AiModelRiskAssessment.

        Raises:
            AiRiskAssessmentError: If not found.
        """
        assessment = self._risk_assessments.get(assessment_id)
        if assessment is None:
            raise AiRiskAssessmentError(
                f"Risk assessment {assessment_id!r} not found",
                context={"assessment_id": assessment_id},
            )
        return assessment

    async def list_risk_assessments(
        self, risk_level: RiskLevel | None = None
    ) -> list[AiModelRiskAssessment]:
        """List risk assessments, optionally filtered by level.

        Args:
            risk_level: Optional risk level filter.

        Returns:
            List of AiModelRiskAssessment instances.
        """
        result = list(self._risk_assessments.values())
        if risk_level is not None:
            result = [a for a in result if a.risk_level == risk_level]
        return result

    # ── Bias Detection ───────────────────────────────────────────────

    async def run_bias_check(
        self,
        model_id: str,
        dataset_id: str = "",
        dimensions: dict[str, float] | None = None,
        threshold: float = 0.1,
    ) -> AiBiasCheckResult:
        """Run a bias detection check on a model.

        Args:
            model_id: The model identifier.
            dataset_id: Optional dataset identifier.
            dimensions: Optional dimension bias scores.
            threshold: Bias threshold.

        Returns:
            The AiBiasCheckResult.
        """
        dims = dimensions or {}
        bias_score = sum(dims.values()) / max(len(dims), 1)
        biased = bias_score > threshold

        recommendations: list[str] = []
        if biased:
            recommendations.append("Review training data for representation bias")
            recommendations.append("Apply debiasing techniques")
            recommendations.append("Re-evaluate model fairness")

        result = AiBiasCheckResult(
            id=str(uuid.uuid4()),
            model_id=model_id,
            dataset_id=dataset_id,
            bias_score=bias_score,
            threshold=threshold,
            biased=biased,
            dimensions=dims,
            recommendations=tuple(recommendations),
        )
        self._bias_checks[result.id] = result
        await self._event_bus.publish(
            AiBiasCheckCompleted(
                check_id=result.id,
                model_id=model_id,
                bias_score=bias_score,
                biased=biased,
            ),
        )
        self._log.info(
            "bias.check.completed",
            check_id=result.id,
            model_id=model_id,
            biased=biased,
        )
        return result

    async def get_bias_check(self, check_id: str) -> AiBiasCheckResult:
        """Get a bias check result by ID.

        Args:
            check_id: The check ID.

        Returns:
            The AiBiasCheckResult.

        Raises:
            AiGovernancePolicyError: If not found.
        """
        result = self._bias_checks.get(check_id)
        if result is None:
            raise AiGovernancePolicyError(
                f"Bias check {check_id!r} not found",
                context={"check_id": check_id},
            )
        return result

    # ── Fairness Metrics ─────────────────────────────────────────────

    async def compute_fairness_metric(
        self,
        model_id: str,
        metric_name: str,
        value: float,
        threshold: float = 0.0,
    ) -> AiFairnessMetric:
        """Compute a fairness metric for a model.

        Args:
            model_id: The model identifier.
            metric_name: The metric name.
            value: The computed value.
            threshold: Optional pass/fail threshold.

        Returns:
            The AiFairnessMetric.
        """
        metric = AiFairnessMetric(
            id=str(uuid.uuid4()),
            model_id=model_id,
            metric_name=metric_name,
            value=value,
            threshold=threshold,
            passed=value <= threshold if threshold > 0 else True,
        )
        self._fairness_metrics[metric.id] = metric
        await self._event_bus.publish(
            AiFairnessMetricComputed(
                metric_id=metric.id,
                model_id=model_id,
                metric_name=metric_name,
                value=value,
                passed=metric.passed,
            ),
        )
        self._log.info(
            "fairness.metric.computed",
            metric_id=metric.id,
            metric_name=metric_name,
            passed=metric.passed,
        )
        return metric

    async def get_fairness_metric(self, metric_id: str) -> AiFairnessMetric:
        """Get a fairness metric by ID.

        Args:
            metric_id: The metric ID.

        Returns:
            The AiFairnessMetric.

        Raises:
            AiGovernancePolicyError: If not found.
        """
        metric = self._fairness_metrics.get(metric_id)
        if metric is None:
            raise AiGovernancePolicyError(
                f"Fairness metric {metric_id!r} not found",
                context={"metric_id": metric_id},
            )
        return metric

    # ── Dashboard ────────────────────────────────────────────────────

    async def get_dashboard(self) -> AiGovernanceDashboard:
        """Get the AI Governance dashboard snapshot.

        Returns:
            The AiGovernanceDashboard with current metrics.
        """
        total = len(self._policies)
        active = sum(1 for p in self._policies.values() if p.enabled)
        total_checks = len(self._checks)
        completed_checks = [c for c in self._checks.values() if c.completed_at is not None]
        passed = sum(1 for c in completed_checks if c.status == AiComplianceStatus.COMPLIANT)
        failed = sum(1 for c in completed_checks if c.status == AiComplianceStatus.NON_COMPLIANT)
        open_reviews = sum(1 for r in self._reviews.values() if r.status == ReviewStatus.PENDING)
        compliance_score = (
            (passed / max(len(completed_checks), 1)) * 100.0 if completed_checks else 0.0
        )

        dashboard = AiGovernanceDashboard(
            id="ai_governance_dashboard",
            name="AI Governance Dashboard",
            total_policies=total,
            active_policies=active,
            total_compliance_checks=total_checks,
            passed_checks=passed,
            failed_checks=failed,
            open_reviews=open_reviews,
            risk_assessments=len(self._risk_assessments),
            overall_compliance_score=compliance_score,
        )

        await self._event_bus.publish(
            AiGovernanceDashboardUpdated(
                dashboard_id=dashboard.id,
                overall_compliance_score=compliance_score,
                total_policies=total,
            ),
        )
        return dashboard


__all__ = ["AiGovernanceService"]
