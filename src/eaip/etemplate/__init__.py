"""Enterprise Template Engine — register, render, and manage templates."""

from __future__ import annotations

from eaip.etemplate.engine import TemplateEngine
from eaip.etemplate.events import (
    TemplateRegistered,
    TemplateRendered,
    TemplateUpdated,
)
from eaip.etemplate.exceptions import (
    TemplateEngineError,
    TemplateNotFoundError,
    TemplateRenderError,
)
from eaip.etemplate.health import TemplateEngineHealthCheck
from eaip.etemplate.integration import TemplateEngineRuntimeModule
from eaip.etemplate.models import (
    RenderResult,
    TemplateDefinition,
    TemplateEngineConfig,
    TemplateFormat,
    TemplateVariable,
)

__all__ = [
    "RenderResult",
    "TemplateDefinition",
    "TemplateEngine",
    "TemplateEngineConfig",
    "TemplateEngineError",
    "TemplateEngineHealthCheck",
    "TemplateEngineRuntimeModule",
    "TemplateFormat",
    "TemplateNotFoundError",
    "TemplateRegistered",
    "TemplateRenderError",
    "TemplateRendered",
    "TemplateUpdated",
    "TemplateVariable",
]
