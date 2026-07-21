"""Cloud migration assistant — assess, plan, and execute cloud migrations."""

from __future__ import annotations

from eaip.cloudmigrate.models import (
    MigrationAssessment,
    MigrationConfig,
    MigrationPlan,
    MigrationTask,
)
from eaip.logging.context import get_logger


class CloudMigrationAssistant:
    """Assistant for assessing, planning, and executing cloud migrations."""

    def __init__(self, config: MigrationConfig | None = None) -> None:
        self._config = config or MigrationConfig()
        self._assessments: dict[str, MigrationAssessment] = {}
        self._plans: dict[str, MigrationPlan] = {}
        self._tasks: dict[str, MigrationTask] = {}
        self._log = get_logger("eaip.cloudmigrate.assistant")

    @property
    def config(self) -> MigrationConfig:
        return self._config

    async def create_assessment(self, assessment: MigrationAssessment) -> MigrationAssessment:
        self._assessments[assessment.id] = assessment
        self._log.info("assessment.created", assessment_id=assessment.id)
        return assessment

    async def get_assessment(self, assessment_id: str) -> MigrationAssessment | None:
        return self._assessments.get(assessment_id)

    async def create_plan(self, plan: MigrationPlan) -> MigrationPlan:
        self._plans[plan.id] = plan
        self._log.info("plan.created", plan_id=plan.id)
        return plan

    async def get_plan(self, plan_id: str) -> MigrationPlan | None:
        return self._plans.get(plan_id)

    async def add_task(self, task: MigrationTask) -> MigrationTask:
        self._tasks[task.id] = task
        self._log.info("task.added", task_id=task.id, plan_id=task.plan_id)
        return task

    async def get_tasks_for_plan(self, plan_id: str) -> list[MigrationTask]:
        return sorted(
            [t for t in self._tasks.values() if t.plan_id == plan_id],
            key=lambda t: t.order,
        )
