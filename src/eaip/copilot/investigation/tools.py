"""Governed investigation tools for EAIP Conductor Phase 9.

These tools compose existing platform infrastructure (system health, agents,
workflows, knowledge, memory) to gather evidence for an active investigation.
They do NOT bypass governance — every tool access goes through the normal
permission and approval pipeline.
"""

from __future__ import annotations

import contextlib
import json

from pydantic.json_schema import JsonSchemaValue

from eaip.agents.registry import AgentRegistry
from eaip.copilot.investigation.models import (
    CreateInvestigationRequest,
    EvidenceSource,
    EvidenceType,
    InvestigationPriority,
    InvestigationStatus,
)
from eaip.copilot.investigation.service import InvestigationService
from eaip.copilot.models import RiskTier
from eaip.health.reporter import HealthReporter
from eaip.knowledge.engine import KnowledgeEngine
from eaip.tools.base import Tool
from eaip.workflow.registry import WorkflowRegistry


class CreateInvestigationTool:
    """Create a new persistent enterprise investigation."""

    name = "create_investigation"
    description = (
        "Create a new investigation to analyze an enterprise "
        "operational question."
    )
    risk = RiskTier.INFORMATIONAL
    permission = "copilot:investigations:write"

    def __init__(self, service: InvestigationService) -> None:
        """Initialize with the investigation service."""
        self._service = service

    @property
    def parameters(self) -> JsonSchemaValue:
        """JSON Schema for creation arguments."""
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Investigation title.",
                },
                "objective": {
                    "type": "string",
                    "description": "What the investigation aims to determine.",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "default": "medium",
                },
            },
            "required": ["title", "objective"],
        }

    async def execute(self, **kwargs: object) -> str:
        """Create an investigation and return its details."""
        user = kwargs.get("user")
        if not isinstance(user, dict):
            return json.dumps(
                {"error": "authenticated user context is required"}
            )
        title = str(kwargs.get("title", "")).strip()
        objective = str(kwargs.get("objective", "")).strip()
        if not title or not objective:
            return json.dumps(
                {"error": "title and objective are required"}
            )
        priority_str = str(
            kwargs.get("priority", "medium")
        ).lower()
        try:
            priority = InvestigationPriority(priority_str)
        except ValueError:
            priority = InvestigationPriority.MEDIUM

        request = CreateInvestigationRequest(
            title=title,
            objective=objective,
            priority=priority,
        )
        inv = await self._service.create(user, request)
        return json.dumps(self._service.serialize(inv), default=str)


class ListInvestigationsTool:
    """List active investigations for the current user."""

    name = "list_investigations"
    description = "List the user's active and recent investigations."
    risk = RiskTier.INFORMATIONAL
    permission = "copilot:investigations:read"

    def __init__(self, service: InvestigationService) -> None:
        """Initialize with the investigation service."""
        self._service = service

    @property
    def parameters(self) -> JsonSchemaValue:
        """JSON Schema for list arguments."""
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by status.",
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                },
            },
        }

    async def execute(self, **kwargs: object) -> str:
        """List investigations visible to the user."""
        user = kwargs.get("user")
        if not isinstance(user, dict):
            return json.dumps(
                {"error": "authenticated user context is required"}
            )
        limit = int(str(kwargs.get("limit", 10)))
        status_str = str(kwargs.get("status", "")).strip()
        status = None
        if status_str:
            with contextlib.suppress(ValueError):
                status = InvestigationStatus(status_str)
        investigations = await self._service.list_investigations(
            user, status=status, limit=limit
        )
        return json.dumps(
            [self._service.serialize(i) for i in investigations],
            default=str,
        )


class GetInvestigationTool:
    """Get detailed information about a specific investigation."""

    name = "get_investigation"
    description = "Get details for a specific investigation by ID."
    risk = RiskTier.INFORMATIONAL
    permission = "copilot:investigations:read"

    def __init__(self, service: InvestigationService) -> None:
        """Initialize with the investigation service."""
        self._service = service

    @property
    def parameters(self) -> JsonSchemaValue:
        """JSON Schema for get arguments."""
        return {
            "type": "object",
            "properties": {
                "investigation_id": {
                    "type": "string",
                    "description": "The investigation ID.",
                },
            },
            "required": ["investigation_id"],
        }

    async def execute(self, **kwargs: object) -> str:
        """Get an investigation by ID."""
        user = kwargs.get("user")
        if not isinstance(user, dict):
            return json.dumps(
                {"error": "authenticated user context is required"}
            )
        inv_id = str(kwargs.get("investigation_id", "")).strip()
        if not inv_id:
            return json.dumps(
                {"error": "investigation_id is required"}
            )
        inv = await self._service.get(user, inv_id)
        if inv is None:
            return json.dumps(
                {"error": "Investigation not found"}
            )
        return json.dumps(self._service.serialize(inv), default=str)


class AddInvestigationEvidenceTool:
    """Add classified evidence to an active investigation."""

    name = "add_investigation_evidence"
    description = (
        "Add OBSERVED, INFERRED, or RECOMMENDED evidence "
        "to an investigation."
    )
    risk = RiskTier.INFORMATIONAL
    permission = "copilot:investigations:write"

    def __init__(self, service: InvestigationService) -> None:
        """Initialize with the investigation service."""
        self._service = service

    @property
    def parameters(self) -> JsonSchemaValue:
        """JSON Schema for evidence arguments."""
        return {
            "type": "object",
            "properties": {
                "investigation_id": {
                    "type": "string",
                    "description": "The investigation ID.",
                },
                "evidence_type": {
                    "type": "string",
                    "enum": ["observed", "inferred", "recommended"],
                    "description": "Classification of evidence.",
                },
                "source": {
                    "type": "string",
                    "enum": [
                        "tool", "knowledge", "memory",
                        "event", "user", "system",
                    ],
                    "description": "Evidence source.",
                },
                "content": {
                    "type": "string",
                    "description": "Evidence content.",
                },
                "source_tool": {
                    "type": "string",
                    "default": "",
                },
                "confidence": {
                    "type": "number",
                    "default": 1.0,
                },
            },
            "required": [
                "investigation_id",
                "evidence_type",
                "source",
                "content",
            ],
        }

    async def execute(self, **kwargs: object) -> str:
        """Add evidence to an investigation."""
        user = kwargs.get("user")
        if not isinstance(user, dict):
            return json.dumps(
                {"error": "authenticated user context is required"}
            )
        inv_id = str(
            kwargs.get("investigation_id", "")
        ).strip()
        etype_str = str(
            kwargs.get("evidence_type", "observed")
        ).lower()
        source_str = str(
            kwargs.get("source", "tool")
        ).lower()
        content = str(kwargs.get("content", "")).strip()
        source_tool = str(kwargs.get("source_tool", ""))
        confidence = float(str(kwargs.get("confidence", 1.0)))

        try:
            etype = EvidenceType(etype_str)
        except ValueError:
            etype = EvidenceType.OBSERVED
        try:
            source = EvidenceSource(source_str)
        except ValueError:
            source = EvidenceSource.TOOL

        try:
            evidence = await self._service.add_evidence(
                user,
                inv_id,
                evidence_type=etype,
                source=source,
                content=content,
                source_tool=source_tool,
                confidence=confidence,
            )
        except (ValueError, PermissionError) as exc:
            return json.dumps({"error": str(exc)})
        return json.dumps(
            self._service.serialize_evidence(evidence),
            default=str,
        )


class CollectEvidenceTool:
    """Gather evidence from existing EAIP tools for an investigation.

    This tool composes existing platform tools to gather live system
    evidence.  It does NOT bypass governance — tool execution goes
    through the normal permission pipeline.
    """

    name = "collect_investigation_evidence"
    description = (
        "Gather live evidence from platform tools "
        "(health, agents, workflows, knowledge) for an investigation."
    )
    risk = RiskTier.INFORMATIONAL
    permission = "copilot:investigations:write"

    def __init__(
        self,
        service: InvestigationService,
        health_reporter: HealthReporter,
        agent_registry: AgentRegistry,
        workflow_registry: WorkflowRegistry,
        knowledge_engine: KnowledgeEngine,
    ) -> None:
        """Initialize with service and platform registries."""
        self._service = service
        self._health_reporter = health_reporter
        self._agent_registry = agent_registry
        self._workflow_registry = workflow_registry
        self._knowledge_engine = knowledge_engine

    @property
    def parameters(self) -> JsonSchemaValue:
        """JSON Schema for evidence collection arguments."""
        return {
            "type": "object",
            "properties": {
                "investigation_id": {
                    "type": "string",
                    "description": "The investigation ID.",
                },
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Evidence sources to collect from: "
                        "health, agents, workflows, knowledge."
                    ),
                    "default": ["health", "agents", "workflows"],
                },
                "query": {
                    "type": "string",
                    "default": "",
                    "description": "Optional knowledge search query.",
                },
            },
            "required": ["investigation_id"],
        }

    async def execute(self, **kwargs: object) -> str:
        """Collect evidence from multiple sources."""
        user = kwargs.get("user")
        if not isinstance(user, dict):
            return json.dumps(
                {"error": "authenticated user context is required"}
            )
        inv_id = str(
            kwargs.get("investigation_id", "")
        ).strip()
        sources_raw = kwargs.get("sources", [])
        sources = (
            list(sources_raw)
            if isinstance(sources_raw, list)
            else ["health", "agents", "workflows"]
        )
        query = str(kwargs.get("query", "")).strip()

        collected: list[dict[str, object]] = []

        if "health" in sources:
            try:
                report = await self._health_reporter.report()
                content = (
                    f"System health: {report.status.value} — "
                    f"{report.message}"
                )
                ev = await self._service.add_evidence(
                    user,
                    inv_id,
                    evidence_type=EvidenceType.OBSERVED,
                    source=EvidenceSource.TOOL,
                    content=content,
                    source_tool="system_health",
                    confidence=1.0,
                )
                collected.append(self._service.serialize_evidence(ev))
            except Exception as exc:
                collected.append(
                    {"error": f"health: {exc!s}"}
                )

        if "agents" in sources:
            try:
                agents = (
                    await self._agent_registry.list_agents()
                )
                count = len(agents)
                names = [a.name for a in agents[:5]]
                content = (
                    f"Registered agents: {count} total. "
                    f"First 5: {', '.join(names)}"
                )
                ev = await self._service.add_evidence(
                    user,
                    inv_id,
                    evidence_type=EvidenceType.OBSERVED,
                    source=EvidenceSource.TOOL,
                    content=content,
                    source_tool="list_agents",
                    confidence=1.0,
                )
                collected.append(self._service.serialize_evidence(ev))
            except Exception as exc:
                collected.append(
                    {"error": f"agents: {exc!s}"}
                )

        if "workflows" in sources:
            try:
                defs = (
                    await self._workflow_registry.list_definitions()
                )
                count = len(defs)
                names = [d.name for d in defs[:5]]
                content = (
                    f"Registered workflows: {count} total. "
                    f"First 5: {', '.join(names)}"
                )
                ev = await self._service.add_evidence(
                    user,
                    inv_id,
                    evidence_type=EvidenceType.OBSERVED,
                    source=EvidenceSource.TOOL,
                    content=content,
                    source_tool="list_workflows",
                    confidence=1.0,
                )
                collected.append(self._service.serialize_evidence(ev))
            except Exception as exc:
                collected.append(
                    {"error": f"workflows: {exc!s}"}
                )

        if "knowledge" in sources and query:
            try:
                result = await self._knowledge_engine.search(
                    query, top_k=3
                )
                chunk_count = result.total_results
                content = (
                    f"Knowledge search for '{query}': "
                    f"{chunk_count} results found."
                )
                if result.chunks:
                    top = result.chunks[0]
                    content += f" Top result score: {top.score:.2f}"
                ev = await self._service.add_evidence(
                    user,
                    inv_id,
                    evidence_type=EvidenceType.OBSERVED,
                    source=EvidenceSource.KNOWLEDGE,
                    content=content,
                    source_tool="knowledge_search",
                    confidence=0.9,
                )
                collected.append(self._service.serialize_evidence(ev))
            except Exception as exc:
                collected.append(
                    {"error": f"knowledge: {exc!s}"}
                )

        return json.dumps(
            {"collected": len(collected), "evidence": collected},
            default=str,
        )


def build_investigation_tools(
    *,
    investigation_service: InvestigationService,
    health_reporter: HealthReporter,
    agent_registry: AgentRegistry,
    workflow_registry: WorkflowRegistry,
    knowledge_engine: KnowledgeEngine,
) -> dict[str, Tool]:
    """Build the investigation tool set for Conductor."""
    tools: list[Tool] = [
        CreateInvestigationTool(investigation_service),
        ListInvestigationsTool(investigation_service),
        GetInvestigationTool(investigation_service),
        AddInvestigationEvidenceTool(investigation_service),
        CollectEvidenceTool(
            investigation_service,
            health_reporter,
            agent_registry,
            workflow_registry,
            knowledge_engine,
        ),
    ]
    return {tool.name: tool for tool in tools}


__all__ = [
    "AddInvestigationEvidenceTool",
    "CollectEvidenceTool",
    "CreateInvestigationTool",
    "GetInvestigationTool",
    "ListInvestigationsTool",
    "build_investigation_tools",
]
