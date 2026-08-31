"""Platform Bootstrap & Init — project scaffolding, quickstart templates, configuration generator."""

from eaip.bootstrap.events import (
    ProjectScaffolded,
    TemplateCreated,
    TemplateDeleted,
    TemplateUpdated,
)
from eaip.bootstrap.exceptions import (
    BootstrapError,
    FileGenerationError,
    ScaffoldError,
    TemplateNotFoundError,
)
from eaip.bootstrap.health import BootstrapHealthCheck
from eaip.bootstrap.integration import BootstrapRuntimeModule
from eaip.bootstrap.models import BootstrapConfig, ProjectTemplate, ScaffoldConfig, ScaffoldResult
from eaip.bootstrap.scaffold import ScaffoldService

__all__ = [
    "BootstrapConfig",
    "BootstrapError",
    "BootstrapHealthCheck",
    "BootstrapRuntimeModule",
    "FileGenerationError",
    "ProjectScaffolded",
    "ProjectTemplate",
    "ScaffoldConfig",
    "ScaffoldError",
    "ScaffoldResult",
    "ScaffoldService",
    "TemplateCreated",
    "TemplateDeleted",
    "TemplateNotFoundError",
    "TemplateUpdated",
]
