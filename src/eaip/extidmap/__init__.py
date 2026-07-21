"""External Identity Mapper — EP-0162."""

from __future__ import annotations

from eaip.extidmap.events import (
    IdentityMapped,
    IdentityUnlinked,
    MappingUpdated,
)
from eaip.extidmap.exceptions import (
    MappingError,
    MappingNotFoundError,
)
from eaip.extidmap.health import ExternalIdentityHealthCheck
from eaip.extidmap.integration import ExternalIdentityRuntimeModule
from eaip.extidmap.mapper import ExternalIdentityMapper
from eaip.extidmap.models import (
    IdentityMapping,
    MapperConfig,
    MappingRule,
)

__all__ = [
    "ExternalIdentityHealthCheck",
    "ExternalIdentityMapper",
    "ExternalIdentityRuntimeModule",
    "IdentityMapped",
    "IdentityMapping",
    "IdentityUnlinked",
    "MapperConfig",
    "MappingError",
    "MappingNotFoundError",
    "MappingRule",
    "MappingUpdated",
]
