"""Governed business-function brains built on existing EAIP primitives."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from eaip.brain.enterprise_brain import EnterpriseBrain
from eaip.brain.models import BrainQuery
from eaip.events.store import EventStore
from eaip.memory.engine import MemoryEngine
from eaip.memory.models import MemoryItem, MemoryScope, MemoryType
from eaip.runtime.mission import Mission, MissionRegistry

if TYPE_CHECKING:
    from eaip.brain.persistence import SecondBrainRepository



@dataclass
class SecondBrain:
    brain_id: str
    name: str
    description: str
    business_function: str
    owner_id: str
    organization_id: str = ""
    objectives: list[str] = field(default_factory=list)
    instructions: str = ""
    knowledge_sources: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    approval_required: bool = True
    status: str = "draft"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    mission_ids: list[str] = field(default_factory=list)
    memory_ids: list[str] = field(default_factory=list)
    activity: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.brain_id,
            "name": self.name,
            "description": self.description,
            "businessFunction": self.business_function,
            "ownerId": self.owner_id,
            "organizationId": self.organization_id,
            "objectives": self.objectives,
            "instructions": self.instructions,
            "knowledgeSources": self.knowledge_sources,
            "rules": self.rules,
            "tools": self.tools,
            "approvalRequired": self.approval_required,
            "status": self.status,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
            "recommendations": self.recommendations,
            "missionIds": self.mission_ids,
            "memoryIds": self.memory_ids,
            "activity": self.activity,
        }

    @classmethod
    def from_row(cls, row: Any) -> "SecondBrain":
        def _as_list(value: Any) -> list[Any]:
            if value is None:
                return []
            if isinstance(value, str):
                import json

                return json.loads(value)
            return list(value)

        def _as_dicts(value: Any) -> list[dict[str, Any]]:
            items = _as_list(value)
            return [item for item in items if isinstance(item, dict)]

        return cls(
            brain_id=row["id"],
            name=row["name"],
            description=row["description"],
            business_function=row["business_function"],
            owner_id=row["owner_id"],
            organization_id=row["organization_id"] or "",
            objectives=_as_list(row["objectives"]),
            instructions=row["instructions"] or "",
            knowledge_sources=_as_list(row["knowledge_sources"]),
            rules=_as_list(row["rules"]),
            tools=_as_list(row["tools"]),
            approval_required=bool(row["approval_required"]),
            status=row["status"] or "active",
            recommendations=_as_dicts(row["recommendations"]),
            mission_ids=_as_list(row["mission_ids"]),
            memory_ids=_as_list(row["memory_ids"]),
            activity=_as_dicts(row["activity"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class SecondBrainService:
    """Owns Second Brain lifecycle state while reusing EAIP subsystems."""

    templates: dict[str, dict[str, Any]] = {
        "marketing": {
            "name": "Marketing Brain",
            "description": "Governed intelligence for qualified customer acquisition.",
            "businessFunction": "Marketing",
            "objectives": ["Improve qualified customer acquisition."],
            "instructions": "Prioritize evidence-backed growth opportunities and brand-safe actions.",
            "rules": ["Use available evidence before recommending action.", "Require approval before execution."],
            "tools": ["knowledge.search", "missions.create", "memory.write"],
        },
        "sales": {
            "name": "Sales Brain",
            "description": "Governed intelligence for pipeline quality and conversion.",
            "businessFunction": "Sales",
            "objectives": ["Improve pipeline conversion."],
            "instructions": "Surface high-confidence opportunities and risks in the pipeline.",
            "rules": ["Do not contact customers without approval."],
            "tools": ["knowledge.search", "missions.create", "memory.write"],
        },
        "operations": {
            "name": "Operations Brain",
            "description": "Governed intelligence for reliable business operations.",
            "businessFunction": "Operations",
            "objectives": ["Reduce operational friction."],
            "instructions": "Prioritize measurable process improvements and operational risk.",
            "rules": ["Cite the operating context for recommendations."],
            "tools": ["knowledge.search", "missions.create", "memory.write"],
        },
        "custom": {
            "name": "Business Brain",
            "description": "A configurable governed intelligence layer.",
            "businessFunction": "Custom",
            "objectives": [],
            "instructions": "",
            "rules": ["Require approval before execution."],
            "tools": ["knowledge.search", "missions.create", "memory.write"],
        },
    }

    def __init__(
        self,
        enterprise_brain: EnterpriseBrain | None = None,
        mission_registry: MissionRegistry | None = None,
        memory_engine: MemoryEngine | None = None,
        event_store: EventStore | None = None,
        repository: "SecondBrainRepository | None" = None,
    ) -> None:
        self._brains: dict[str, SecondBrain] = {}
        self._enterprise_brain = enterprise_brain
        self._missions = mission_registry
        self._memory = memory_engine
        self._events = event_store
        self._repository = repository
        self._execution_locks: dict[str, asyncio.Lock] = {}

    def _get_execution_lock(self, brain_id: str) -> asyncio.Lock:
        if brain_id not in self._execution_locks:
            self._execution_locks[brain_id] = asyncio.Lock()
        return self._execution_locks[brain_id]

    def templates_for(self) -> list[dict[str, Any]]:
        return [{"id": key, **value} for key, value in self.templates.items()]

    async def create(self, body: dict[str, Any], owner_id: str, organization_id: str = "") -> SecondBrain:
        template_id = str(body.get("template", "custom"))
        template = self.templates.get(template_id, self.templates["custom"])
        brain = SecondBrain(
            brain_id=f"brain-{uuid4().hex[:10]}",
            name=str(body.get("name") or template["name"]),
            description=str(body.get("description") or template["description"]),
            business_function=str(body.get("businessFunction") or template["businessFunction"]),
            owner_id=owner_id,
            organization_id=organization_id,
            objectives=list(body.get("objectives") or template["objectives"]),
            instructions=str(body.get("instructions") or template["instructions"]),
            knowledge_sources=list(body.get("knowledgeSources") or []),
            rules=list(body.get("rules") or template["rules"]),
            tools=list(body.get("tools") or template["tools"]),
            approval_required=bool(body.get("approvalRequired", True)),
            status="active",
        )
        self._brains[brain.brain_id] = brain
        await self._record(brain, "created", "Brain created")
        return brain

    async def list(self, owner_id: str) -> list[SecondBrain]:
        if self._repository is not None:
            return await self._repository.list_by_owner(owner_id)
        return sorted(
            (brain for brain in self._brains.values() if brain.owner_id == owner_id),
            key=lambda brain: brain.created_at,
            reverse=True,
        )

    async def get(self, brain_id: str, owner_id: str) -> SecondBrain | None:
        if self._repository is not None:
            brain = await self._repository.get(brain_id)
        else:
            brain = self._brains.get(brain_id)
        return brain if brain and brain.owner_id == owner_id else None

    async def configure(self, brain: SecondBrain, body: dict[str, Any]) -> SecondBrain:
        for key, field_name in {
            "name": "name",
            "description": "description",
            "businessFunction": "business_function",
            "instructions": "instructions",
            "objectives": "objectives",
            "knowledgeSources": "knowledge_sources",
            "rules": "rules",
            "tools": "tools",
        }.items():
            if key in body:
                setattr(brain, field_name, body[key])
        if "approvalRequired" in body:
            brain.approval_required = bool(body["approvalRequired"])
        brain.updated_at = datetime.now(UTC)
        await self._record(brain, "configured", "Brain configuration updated")
        return brain

    async def delete(self, brain_id: str, owner_id: str) -> bool:
        brain = await self.get(brain_id, owner_id)
        if brain is None:
            return False
        if self._repository is not None:
            await self._repository.delete(brain_id)
        self._brains.pop(brain_id, None)
        return True

    async def query(self, brain: SecondBrain, query: str) -> dict[str, Any]:
        result = None
        if self._enterprise_brain is not None:
            result = await self._enterprise_brain.query(
                BrainQuery(query=query, collection_names=tuple(brain.knowledge_sources))
            )
        sources = [source.model_dump() for source in result.sources] if result else []
        answer = result.answer if result else "No connected knowledge source returned evidence."
        recommendation = {
            "id": f"rec-{uuid4().hex[:10]}",
            "title": "Focus on evidence-backed acquisition opportunities",
            "rationale": answer or "Review the configured marketing objective and connected knowledge sources.",
            "evidence": sources,
            "confidence": result.confidence if result else 0.0,
            "status": "pending_approval" if brain.approval_required else "approved",
            "approvalRequired": brain.approval_required,
            "executionStatus": "ready_for_execution_integration",
        }
        brain.recommendations.insert(0, recommendation)
        await self._record(brain, "recommendation_generated", recommendation["title"])
        return {"answer": answer, "sources": sources, "recommendation": recommendation}

    async def create_mission(self, brain: SecondBrain, recommendation_id: str) -> dict[str, Any]:
        recommendation = next(
            (item for item in brain.recommendations if item["id"] == recommendation_id), None
        )
        if recommendation is None:
            raise ValueError("Recommendation not found")
        if recommendation["approvalRequired"] and recommendation["status"] != "approved":
            raise PermissionError("Recommendation requires approval")
        mission_id = f"mission-{uuid4().hex[:10]}"
        if self._missions is not None:
            mission = await self._missions.create(
                mission_id=mission_id,
                name=f"{brain.name}: {recommendation['title']}",
                knowledge_collections=tuple(brain.knowledge_sources),
                metadata={"brainId": brain.brain_id, "recommendationId": recommendation_id},
            )
            mission_data = mission.to_dict()
        else:
            mission_data = {"id": mission_id, "name": recommendation["title"], "status": "draft"}
        brain.mission_ids.insert(0, mission_id)
        recommendation["missionId"] = mission_id
        recommendation["status"] = "mission_created"
        await self._record(brain, "mission_created", mission_id)
        return mission_data

    async def approve(self, brain: SecondBrain, recommendation_id: str) -> dict[str, Any]:
        recommendation = next(
            (item for item in brain.recommendations if item["id"] == recommendation_id), None
        )
        if recommendation is None:
            raise ValueError("Recommendation not found")
        if recommendation["status"] != "pending_approval":
            raise PermissionError("Recommendation is not pending approval")
        recommendation["status"] = "approved"
        await self._record(brain, "approval_granted", recommendation_id)
        return recommendation

    async def reject_action(self, brain: SecondBrain, recommendation_id: str) -> dict[str, Any]:
        recommendation = next(
            (item for item in brain.recommendations if item["id"] == recommendation_id), None
        )
        if recommendation is None:
            raise ValueError("Recommendation not found")
        if recommendation["status"] != "pending_approval":
            raise PermissionError("Recommendation is not pending approval")
        recommendation["status"] = "rejected"
        recommendation["executionStatus"] = "rejected"
        await self._record(brain, "approval_rejected", recommendation_id)
        return recommendation

    async def execute_action(self, brain: SecondBrain, recommendation_id: str) -> dict[str, Any]:
        lock = self._get_execution_lock(brain.brain_id)
        async with lock:
            recommendation = next(
                (item for item in brain.recommendations if item["id"] == recommendation_id), None
            )
            if recommendation is None:
                raise ValueError("Recommendation not found")
            if recommendation["status"] == "rejected":
                raise PermissionError("Cannot execute a rejected recommendation")
            if recommendation.get("executionStatus") not in (
                None,
                "ready_for_execution_integration",
            ):
                raise PermissionError("Recommendation already executed")
            if recommendation["approvalRequired"] and recommendation["status"] != "approved":
                raise PermissionError("Recommendation requires approval before execution")

            mission_id = recommendation.get("missionId")
            if mission_id is None:
                mission_id = f"mission-{uuid4().hex[:10]}"
                if self._missions is not None:
                    mission = await self._missions.create(
                        mission_id=mission_id,
                        name=f"{brain.name}: {recommendation['title']}",
                        knowledge_collections=tuple(brain.knowledge_sources),
                        metadata={
                            "brainId": brain.brain_id,
                            "recommendationId": recommendation_id,
                            "source": "brain_action_center",
                        },
                    )
                    mission_data = mission.to_dict()
                else:
                    mission_data = {
                        "id": mission_id,
                        "name": recommendation["title"],
                        "status": "draft",
                    }
                brain.mission_ids.insert(0, mission_id)
                recommendation["missionId"] = mission_id
                await self._record(brain, "mission_created", mission_id)
            else:
                if self._missions is not None:
                    mission = await self._missions.get(mission_id)
                    mission_data = mission.to_dict() if mission is not None else {"id": mission_id}
                else:
                    mission_data = {"id": mission_id}

            execution_result: str = ""
            if self._missions is not None:
                mission = await self._missions.get(mission_id)
                if mission is not None:
                    try:
                        await mission.execute()
                        execution_result = mission.result or "Mission executed"
                        recommendation["executionStatus"] = "executed"
                        recommendation["executionResult"] = execution_result
                        recommendation["status"] = "executed"
                        await self._record(
                            brain,
                            "action_executed",
                            f"{recommendation['title']}: {execution_result}",
                        )
                    except Exception as exc:
                        execution_result = f"Execution failed: {exc}"
                        recommendation["executionStatus"] = "execution_failed"
                        recommendation["executionResult"] = execution_result
                        recommendation["status"] = "executed"
                        await self._record(brain, "action_execution_failed", str(exc))
                else:
                    recommendation["executionStatus"] = "ready_for_integration"
                    recommendation["status"] = "executed"
                    execution_result = "Mission created; execution integration pending."
                    recommendation["executionResult"] = execution_result
                    await self._record(brain, "action_ready_for_integration", recommendation["title"])
            else:
                recommendation["executionStatus"] = "ready_for_integration"
                recommendation["status"] = "executed"
                execution_result = "Mission created; execution integration pending."
                recommendation["executionResult"] = execution_result
                await self._record(brain, "action_ready_for_integration", recommendation["title"])

            await self._remember_outcome(brain, recommendation, execution_result)

            await self._persist(brain)
            return {
                "missionId": mission_id,
                "mission": mission_data,
                "executionStatus": recommendation["executionStatus"],
                "executionResult": execution_result,
            }

    async def _remember_outcome(
        self, brain: SecondBrain, recommendation: dict[str, Any], result: str
    ) -> None:
        content = (
            f"Action '{recommendation['title']}' executed. Result: {result}"
            if recommendation.get("executionStatus") == "executed"
            else f"Action '{recommendation['title']}' approved. {result}"
        )
        memory_id = f"brain-memory-{uuid4().hex[:10]}"
        if self._memory is not None:
            now = datetime.now(UTC)
            try:
                item = await self._memory.store.create(
                    MemoryItem(
                        memory_id=memory_id,
                        memory_type=MemoryType.SEMANTIC,
                        scope=MemoryScope(tenant_id=brain.owner_id),
                        content=content,
                        importance=0.9,
                        created_at=now,
                        updated_at=now,
                    )
                )
                brain.memory_ids.insert(0, item.memory_id)
            except Exception:
                brain.memory_ids.insert(0, memory_id)
        else:
            brain.memory_ids.insert(0, memory_id)
        await self._record(brain, "memory_recorded", content)

    async def remember(self, brain: SecondBrain, content: str) -> dict[str, Any]:
        memory_id = f"brain-memory-{uuid4().hex[:10]}"
        if self._memory is not None:
            now = datetime.now(UTC)
            item = await self._memory.store.create(
                MemoryItem(
                    memory_id=memory_id,
                    memory_type=MemoryType.SEMANTIC,
                    scope=MemoryScope(tenant_id=brain.owner_id),
                    content=content,
                    importance=0.8,
                    created_at=now,
                    updated_at=now,
                )
            )
            memory = {"id": item.memory_id, "content": item.content, "why": "Recorded from a governed Brain outcome."}
        else:
            memory = {"id": memory_id, "content": content, "why": "Recorded from a governed Brain outcome."}
        brain.memory_ids.insert(0, memory_id)
        await self._record(brain, "memory_recorded", content)
        return memory

    async def _record(self, brain: SecondBrain, action: str, message: str) -> None:
        entry = {
            "id": f"activity-{uuid4().hex[:10]}",
            "action": action,
            "message": message,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        brain.activity.insert(0, entry)
        if self._events is not None:
            self._events._events.append({**entry, "type": "brain"})
        await self._persist(brain)

    async def _persist(self, brain: SecondBrain) -> None:
        if self._repository is not None:
            await self._repository.save(brain)


__all__ = ["SecondBrain", "SecondBrainService"]
