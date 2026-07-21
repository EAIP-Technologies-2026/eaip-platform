"""WorkflowDesigner — create, manage, and publish workflow blueprints."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from eaip.shared.time import utc_now
from eaip.wfdesigner.events import (
    BlueprintCreated,
    BlueprintPublished,
    BlueprintVersioned,
    NodeConfigured,
)
from eaip.wfdesigner.exceptions import BlueprintNotFoundError
from eaip.wfdesigner.models import (
    DesignerConfig,
    NodeType,
    WorkflowBlueprint,
    WorkflowEdge,
    WorkflowNode,
    WorkflowStatus,
)

EventCallback = Callable[[Any], Any]


class WorkflowDesigner:
    def __init__(
        self,
        config: DesignerConfig | None = None,
        event_callback: EventCallback | None = None,
    ) -> None:
        self._config = config or DesignerConfig()
        self._blueprints: dict[str, WorkflowBlueprint] = {}
        self._event_callback = event_callback

    def set_event_callback(self, callback: EventCallback | None) -> None:
        self._event_callback = callback

    def _emit(self, event: Any) -> None:
        if self._event_callback:
            self._event_callback(event)

    async def create_blueprint(
        self,
        name: str,
        *,
        description: str = "",
        nodes: tuple[WorkflowNode, ...] | None = None,
        edges: tuple[WorkflowEdge, ...] | None = None,
        properties: dict[str, object] | None = None,
    ) -> WorkflowBlueprint:
        now = utc_now()
        blueprint = WorkflowBlueprint(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            nodes=nodes or (),
            edges=edges or (),
            properties=properties or {},
            status=WorkflowStatus.DRAFT,
            version=1,
            created_at=now,
            updated_at=now,
        )
        self._blueprints[blueprint.id] = blueprint
        self._emit(BlueprintCreated(blueprint_id=blueprint.id, name=name))
        return blueprint

    async def get_blueprint(self, blueprint_id: str) -> WorkflowBlueprint:
        if blueprint_id not in self._blueprints:
            raise BlueprintNotFoundError(blueprint_id)
        return self._blueprints[blueprint_id]

    async def list_blueprints(
        self,
        status: WorkflowStatus | None = None,
    ) -> list[WorkflowBlueprint]:
        all_bps = list(self._blueprints.values())
        if status:
            all_bps = [b for b in all_bps if b.status == status]
        return all_bps

    async def publish_blueprint(self, blueprint_id: str) -> WorkflowBlueprint:
        blueprint = await self.get_blueprint(blueprint_id)
        if blueprint.status == WorkflowStatus.PUBLISHED:
            new_version = blueprint.version + 1
            self._emit(
                BlueprintVersioned(
                    blueprint_id=blueprint_id,
                    old_version=blueprint.version,
                    new_version=new_version,
                )
            )
        else:
            new_version = blueprint.version

        updated = WorkflowBlueprint(
            id=blueprint.id,
            name=blueprint.name,
            description=blueprint.description,
            nodes=blueprint.nodes,
            edges=blueprint.edges,
            properties=blueprint.properties,
            status=WorkflowStatus.PUBLISHED,
            version=new_version,
            created_at=blueprint.created_at,
            updated_at=utc_now(),
        )
        self._blueprints[blueprint_id] = updated
        self._emit(
            BlueprintPublished(
                blueprint_id=blueprint_id,
                name=blueprint.name,
                version=new_version,
            )
        )
        return updated

    async def archive_blueprint(self, blueprint_id: str) -> WorkflowBlueprint:
        blueprint = await self.get_blueprint(blueprint_id)
        updated = WorkflowBlueprint(
            id=blueprint.id,
            name=blueprint.name,
            description=blueprint.description,
            nodes=blueprint.nodes,
            edges=blueprint.edges,
            properties=blueprint.properties,
            status=WorkflowStatus.ARCHIVED,
            version=blueprint.version,
            created_at=blueprint.created_at,
            updated_at=utc_now(),
        )
        self._blueprints[blueprint_id] = updated
        return updated

    async def add_node(
        self,
        blueprint_id: str,
        node_type: NodeType,
        *,
        label: str = "",
        config: dict[str, object] | None = None,
        position_x: float = 0.0,
        position_y: float = 0.0,
    ) -> WorkflowBlueprint:
        blueprint = await self.get_blueprint(blueprint_id)
        node = WorkflowNode(
            id=str(uuid.uuid4()),
            type=node_type,
            label=label or node_type.value,
            config=config or {},
            position_x=position_x,
            position_y=position_y,
        )
        updated = WorkflowBlueprint(
            id=blueprint.id,
            name=blueprint.name,
            description=blueprint.description,
            nodes=(*blueprint.nodes, node),
            edges=blueprint.edges,
            properties=blueprint.properties,
            status=blueprint.status,
            version=blueprint.version,
            created_at=blueprint.created_at,
            updated_at=utc_now(),
        )
        self._blueprints[blueprint_id] = updated
        self._emit(
            NodeConfigured(
                blueprint_id=blueprint_id,
                node_id=node.id,
                node_type=node_type.value,
            )
        )
        return updated

    async def add_edge(
        self,
        blueprint_id: str,
        source_node_id: str,
        target_node_id: str,
        *,
        label: str = "",
        condition: str | None = None,
    ) -> WorkflowBlueprint:
        blueprint = await self.get_blueprint(blueprint_id)
        edge = WorkflowEdge(
            id=str(uuid.uuid4()),
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            label=label,
            condition=condition,
        )
        updated = WorkflowBlueprint(
            id=blueprint.id,
            name=blueprint.name,
            description=blueprint.description,
            nodes=blueprint.nodes,
            edges=(*blueprint.edges, edge),
            properties=blueprint.properties,
            status=blueprint.status,
            version=blueprint.version,
            created_at=blueprint.created_at,
            updated_at=utc_now(),
        )
        self._blueprints[blueprint_id] = updated
        return updated


__all__ = ["WorkflowDesigner"]
