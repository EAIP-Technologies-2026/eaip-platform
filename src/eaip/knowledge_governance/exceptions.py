"""Knowledge Governance exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class KnowledgeGovernanceError(EAIPError):
    """Base exception for Knowledge Governance errors."""

    default_code = ErrorCode.UNKNOWN


class KnowledgeGovernancePolicyError(KnowledgeGovernanceError):
    """Raised when a governance policy operation fails."""

    default_code = ErrorCode.UNKNOWN


class KnowledgeGovernanceViolationError(KnowledgeGovernanceError):
    """Raised when a governance policy is violated."""

    default_code = ErrorCode.POLICY_VIOLATION


class KnowledgeQualityError(KnowledgeGovernanceError):
    """Raised when a quality check operation fails."""

    default_code = ErrorCode.UNKNOWN


class KnowledgeClassificationError(KnowledgeGovernanceError):
    """Raised when classification fails."""

    default_code = ErrorCode.UNKNOWN


class KnowledgeRetentionError(KnowledgeGovernanceError):
    """Raised when a retention operation fails."""

    default_code = ErrorCode.UNKNOWN


class KnowledgeSourceValidationError(KnowledgeGovernanceError):
    """Raised when source validation fails."""

    default_code = ErrorCode.VALIDATION_FAILED


class KnowledgeStewardshipError(KnowledgeGovernanceError):
    """Raised when a stewardship operation fails."""

    default_code = ErrorCode.UNKNOWN


class KnowledgeGovernanceConfigError(KnowledgeGovernanceError):
    """Raised when governance configuration is invalid."""

    default_code = ErrorCode.CONFIGURATION_INVALID


__all__ = [
    "KnowledgeClassificationError",
    "KnowledgeGovernanceConfigError",
    "KnowledgeGovernanceError",
    "KnowledgeGovernancePolicyError",
    "KnowledgeGovernanceViolationError",
    "KnowledgeQualityError",
    "KnowledgeRetentionError",
    "KnowledgeSourceValidationError",
    "KnowledgeStewardshipError",
]
