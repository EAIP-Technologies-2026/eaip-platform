"""Exception hierarchy for the AI Governance & Compliance subsystem."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class AiGovernanceError(EAIPError):
    """Base exception for AI governance failures."""

    default_code = ErrorCode.UNKNOWN


class AiGovernancePolicyError(AiGovernanceError):
    """Raised when a governance policy operation fails."""

    default_code = ErrorCode.POLICY_VIOLATION


class AiGovernanceViolationError(AiGovernanceError):
    """Raised when an AI governance policy is violated."""

    default_code = ErrorCode.POLICY_VIOLATION


class AiComplianceError(AiGovernanceError):
    """Base exception for AI compliance failures."""

    default_code = ErrorCode.UNKNOWN


class AiComplianceRequirementError(AiComplianceError):
    """Raised when a compliance requirement operation fails."""

    default_code = ErrorCode.VALIDATION_FAILED


class AiComplianceCheckError(AiComplianceError):
    """Raised when a compliance check fails."""

    default_code = ErrorCode.VALIDATION_FAILED


class AiBiasDetectionError(AiGovernanceError):
    """Raised when bias detection fails."""

    default_code = ErrorCode.UNKNOWN


class AiFairnessError(AiGovernanceError):
    """Raised when fairness metric computation fails."""

    default_code = ErrorCode.UNKNOWN


class AiExplainabilityError(AiGovernanceError):
    """Raised when explainability processing fails."""

    default_code = ErrorCode.UNKNOWN


class AiReviewError(AiGovernanceError):
    """Raised when a governance review operation fails."""

    default_code = ErrorCode.VALIDATION_FAILED


class AiRiskAssessmentError(AiGovernanceError):
    """Raised when a risk assessment operation fails."""

    default_code = ErrorCode.UNKNOWN


__all__ = [
    "AiBiasDetectionError",
    "AiComplianceCheckError",
    "AiComplianceError",
    "AiComplianceRequirementError",
    "AiExplainabilityError",
    "AiFairnessError",
    "AiGovernanceError",
    "AiGovernancePolicyError",
    "AiGovernanceViolationError",
    "AiReviewError",
    "AiRiskAssessmentError",
]
