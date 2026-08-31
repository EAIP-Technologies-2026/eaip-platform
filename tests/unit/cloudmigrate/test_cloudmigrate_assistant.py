"""Tests for CloudMigrationAssistant."""

from __future__ import annotations

import pytest

from eaip.cloudmigrate.assistant import CloudMigrationAssistant
from eaip.cloudmigrate.models import (
    MigrationAssessment,
    MigrationConfig,
    MigrationPlan,
    MigrationTask,
)


class TestCloudMigrationAssistant:
    @pytest.mark.asyncio
    async def test_create_assessment(self) -> None:
        assistant = CloudMigrationAssistant()
        assessment = MigrationAssessment(id="a1", source="aws", target="azure")
        result = await assistant.create_assessment(assessment)
        assert result.id == "a1"

    @pytest.mark.asyncio
    async def test_get_assessment_found(self) -> None:
        assistant = CloudMigrationAssistant()
        assessment = MigrationAssessment(id="a1", source="aws", target="azure")
        await assistant.create_assessment(assessment)
        result = await assistant.get_assessment("a1")
        assert result is not None
        assert result.id == "a1"

    @pytest.mark.asyncio
    async def test_get_assessment_not_found(self) -> None:
        assistant = CloudMigrationAssistant()
        result = await assistant.get_assessment("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_create_and_get_plan(self) -> None:
        assistant = CloudMigrationAssistant()
        plan = MigrationPlan(id="p1", assessment_id="a1", steps=("step1", "step2"))
        await assistant.create_plan(plan)
        result = await assistant.get_plan("p1")
        assert result is not None
        assert result.steps == ("step1", "step2")

    @pytest.mark.asyncio
    async def test_add_and_list_tasks(self) -> None:
        assistant = CloudMigrationAssistant()
        plan = MigrationPlan(id="p1", assessment_id="a1")
        await assistant.create_plan(plan)
        t1 = MigrationTask(id="t1", plan_id="p1", name="setup", order=1)
        t2 = MigrationTask(id="t2", plan_id="p1", name="migrate", order=2)
        await assistant.add_task(t1)
        await assistant.add_task(t2)
        tasks = await assistant.get_tasks_for_plan("p1")
        assert len(tasks) == 2
        assert tasks[0].name == "setup"
        assert tasks[1].name == "migrate"

    @pytest.mark.asyncio
    async def test_config(self) -> None:
        cfg = MigrationConfig(max_concurrent_tasks=10)
        assistant = CloudMigrationAssistant(config=cfg)
        assert assistant.config.max_concurrent_tasks == 10
