"""API Documentation Generator — OpenAPI generation, markdown docs, changelog."""

from eaip.apidocs.changelog import DocChangelogService
from eaip.apidocs.events import (
    ChangelogCreated,
    DocGenerated,
    DocPublished,
    EndpointDocRegistered,
)
from eaip.apidocs.exceptions import (
    ApiDocsError,
    ChangelogError,
    DocGenerationError,
    DocNotFoundError,
)
from eaip.apidocs.generator import DocGenerator
from eaip.apidocs.health import ApiDocsHealthCheck
from eaip.apidocs.integration import ApiDocsRuntimeModule
from eaip.apidocs.models import ApiDocConfig, DocChangelog, EndpointDoc, GeneratedDoc
from eaip.apidocs.publisher import DocPublisher

__all__ = [
    "ApiDocConfig",
    "ApiDocsError",
    "ApiDocsHealthCheck",
    "ApiDocsRuntimeModule",
    "ChangelogCreated",
    "ChangelogError",
    "DocChangelog",
    "DocChangelogService",
    "DocGenerated",
    "DocGenerationError",
    "DocGenerator",
    "DocNotFoundError",
    "DocPublished",
    "DocPublisher",
    "EndpointDoc",
    "EndpointDocRegistered",
    "GeneratedDoc",
]
