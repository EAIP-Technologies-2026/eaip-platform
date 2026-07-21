"""Agent governance exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class AgentGovernanceError(EAIPError):
    """Base for agent governance failures."""

    default_code = ErrorCode.POLICY_VIOLATION


class AgentGovernancePolicyError(AgentGovernanceError):
    """Raised when a governance policy operation fails."""

    default_code = ErrorCode.POLICY_NOT_FOUND


class AgentGovernanceViolationError(AgentGovernanceError):
    """Raised when an agent violates a governance policy."""

    default_code = ErrorCode.POLICY_VIOLATION


class AgentPermissionError(AgentGovernanceError):
    """Raised when a permission operation fails."""

    default_code = ErrorCode.POLICY_NOT_FOUND


class AgentApprovalError(AgentGovernanceError):
    """Raised when an approval operation fails."""

    default_code = ErrorCode.POLICY_VIOLATION


class AgentRestrictionError(AgentGovernanceError):
    """Raised when a restriction operation fails."""

    default_code = ErrorCode.POLICY_VIOLATION


class AgentSopError(AgentGovernanceError):
    """Raised when an SOP operation fails."""

    default_code = ErrorCode.POLICY_NOT_FOUND


class AgentComplianceError(AgentGovernanceError):
    """Raised when a compliance operation fails."""

    default_code = ErrorCode.POLICY_VIOLATION


class AgentEscalationError(AgentGovernanceError):
    """Raised when an escalation operation fails."""

    default_code = ErrorCode.POLICY_VIOLATION


__all__ = [
    "AgentApprovalError",
    "AgentComplianceError",
    "AgentEscalationError",
    "AgentGovernanceError",
    "AgentGovernancePolicyError",
    "AgentGovernanceViolationError",
    "AgentPermissionError",
    "AgentRestrictionError",
    "AgentSopError",
]
