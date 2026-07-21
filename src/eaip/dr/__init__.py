"""Disaster Recovery — DR plans, failover automation, RTO/RPO tracking, and recovery testing."""

from __future__ import annotations

from eaip.dr.events import (
    DrPlanActivated,
    DrPlanCreated,
    DrPlanTested,
    DrPlanTestFailed,
    FailoverCompleted,
    FailoverFailed,
    FailoverRolledBack,
    FailoverStarted,
    RtoRpoViolation,
)
from eaip.dr.exceptions import (
    DrError,
    DrTestError,
    FailoverError,
    PlanNotFoundError,
    RtoViolationError,
    StepExecutionError,
)
from eaip.dr.failover import FailoverManager
from eaip.dr.health import DrHealthCheck
from eaip.dr.integration import DrRuntimeModule
from eaip.dr.models import (
    DrComponent,
    DrConfig,
    DrPlan,
    DrStep,
    DrTestResult,
    FailoverEvent,
)
from eaip.dr.plans import DrPlanManager
from eaip.dr.testing import DrTestService

__all__ = [
    "DrComponent",
    "DrConfig",
    "DrError",
    "DrHealthCheck",
    "DrPlan",
    "DrPlanActivated",
    "DrPlanCreated",
    "DrPlanManager",
    "DrPlanTestFailed",
    "DrPlanTested",
    "DrRuntimeModule",
    "DrStep",
    "DrTestError",
    "DrTestResult",
    "DrTestService",
    "FailoverCompleted",
    "FailoverError",
    "FailoverEvent",
    "FailoverFailed",
    "FailoverManager",
    "FailoverRolledBack",
    "FailoverStarted",
    "PlanNotFoundError",
    "RtoRpoViolation",
    "RtoViolationError",
    "StepExecutionError",
]
