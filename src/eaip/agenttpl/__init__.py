"""Agent Templates — predefined agent blueprints, categories, and parameterization."""

from __future__ import annotations

from eaip.agenttpl.events import (
    TemplateApplied,
    TemplateCreated,
    TemplateDeprecated,
    TemplateUpdated,
)
from eaip.agenttpl.exceptions import (
    TemplateError,
    TemplateNotFoundError,
    TemplateValidationError,
)
from eaip.agenttpl.health import AgentTemplateHealthCheck
from eaip.agenttpl.integration import AgentTemplateRuntimeModule
from eaip.agenttpl.models import (
    AgentTemplate,
    TemplateCategory,
    TemplateConfig,
    TemplateParameter,
)

__all__ = [
    "AgentTemplate",
    "AgentTemplateHealthCheck",
    "AgentTemplateRuntimeModule",
    "TemplateApplied",
    "TemplateCategory",
    "TemplateConfig",
    "TemplateCreated",
    "TemplateDeprecated",
    "TemplateError",
    "TemplateNotFoundError",
    "TemplateParameter",
    "TemplateUpdated",
    "TemplateValidationError",
]
