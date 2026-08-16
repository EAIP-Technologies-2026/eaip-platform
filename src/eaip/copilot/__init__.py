"""EAIP Conductor — a governed assistant embedded in the enterprise console.

Conductor reuses the platform's registries and services (tool registry, agent
registry, workflow registry, knowledge engine, health reporter, audit logger)
to inspect and act on the platform through permission- and risk-gated tools.
"""

from __future__ import annotations

from eaip.copilot.approvals import ApprovalService
from eaip.copilot.governance import GovernancePolicy
from eaip.copilot.investigation import InvestigationService
from eaip.copilot.models import (
    ApprovalRequest,
    ApprovalStatus,
    ConductorChatRequest,
    CopilotTurn,
    RiskTier,
    ToolEvent,
)
from eaip.copilot.planner import ConductorPlanner
from eaip.copilot.service import ConductorService
from eaip.copilot.tools import (
    BaseOperationalTool,
    OperationalTool,
    OperationalToolMetadata,
    OperationalToolRegistry,
    build_copilot_tools,
    create_canonical_operational_registry,
)

__all__ = [
    "ApprovalRequest",
    "ApprovalService",
    "ApprovalStatus",
    "BaseOperationalTool",
    "ConductorChatRequest",
    "ConductorPlanner",
    "ConductorService",
    "CopilotTurn",
    "GovernancePolicy",
    "OperationalTool",
    "OperationalToolMetadata",
    "OperationalToolRegistry",
    "RiskTier",
    "ToolEvent",
    "build_copilot_tools",
    "create_canonical_operational_registry",
]
