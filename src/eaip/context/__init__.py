"""Context & Prompt Intelligence — prompt templates, context assembly, compression.

Bundle-025 of the EAIP Platform Foundation Milestone.

Provides:
- Prompt template management with versioning (PromptManager, PromptRegistry)
- Context assembly from multiple sources (ContextBuilder)
- Context compression strategies (ContextCompressor)
- Domain models for prompts, versions, and assembled context
- Domain events for observability
- Health checks and runtime integration
"""

from __future__ import annotations

from eaip.context.builder import ContextBuilder
from eaip.context.compression import ContextCompressor
from eaip.context.events import (
    ContextAssembled,
    ContextCompressed,
    ContextEvent,
    PromptCreated,
    PromptVersioned,
)
from eaip.context.exceptions import (
    CompressionError,
    ContextAssemblyError,
    ContextError,
    PromptNotFoundError,
    TemplatePolicyError,
    TemplateRenderError,
)
from eaip.context.health import ContextHealthCheck
from eaip.context.integration import ContextRuntimeModule, create_context_integration
from eaip.context.models import (
    AssembledContext,
    CompressionConfig,
    CompressionStrategy,
    ContextBuilderConfig,
    ContextCacheConfig,
    ContextDocument,
    PromptRegistryEntry,
    PromptTemplate,
    PromptVersion,
)
from eaip.context.permission_context import (
    CapabilityAccessLevel,
    CapabilityPermissionContext,
    IdentityScope,
    PermissionAwareContext,
)
from eaip.context.permission_resolver import PermissionContextResolver
from eaip.context.registry import Observer, PromptRegistry
from eaip.context.templates import PromptManager

__all__ = [
    "AssembledContext",
    "CapabilityAccessLevel",
    "CapabilityPermissionContext",
    "CompressionConfig",
    "CompressionError",
    "CompressionStrategy",
    "ContextAssembled",
    "ContextAssemblyError",
    "ContextBuilder",
    "ContextBuilderConfig",
    "ContextCacheConfig",
    "ContextCompressed",
    "ContextCompressor",
    "ContextDocument",
    "ContextError",
    "ContextEvent",
    "ContextHealthCheck",
    "ContextRuntimeModule",
    "IdentityScope",
    "Observer",
    "PermissionAwareContext",
    "PermissionContextResolver",
    "PromptCreated",
    "PromptManager",
    "PromptNotFoundError",
    "PromptRegistry",
    "PromptRegistryEntry",
    "PromptTemplate",
    "PromptVersion",
    "PromptVersioned",
    "TemplatePolicyError",
    "TemplateRenderError",
    "create_context_integration",
]
