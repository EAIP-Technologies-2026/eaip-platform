"""AI Provider Framework — model serving, routing, and failover.

Provides the abstractions for connecting AI model providers (Ollama, NVIDIA,
OpenAI-compatible) to the platform, including discovery, registration,
health monitoring, and capability-aware request routing.
"""

from __future__ import annotations

from eaip.providers.base import Provider
from eaip.providers.discovery import ProviderDiscovery
from eaip.providers.events import (
    ProviderModelDiscovered,
    ProviderRegistered,
    ProviderRequestCompleted,
    ProviderRequestFailed,
    ProviderRequestStarted,
    ProviderStatusChanged,
    ProviderUnregistered,
)
from eaip.providers.exceptions import (
    ModelNotFoundError,
    ProviderError,
    ProviderNotFoundError,
    ProviderTimeoutError,
)
from eaip.providers.health import ProviderHealthCheck, ProviderHealthMonitor
from eaip.providers.integration import ProviderRuntimeModule
from eaip.providers.models import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ModelCapability,
    ModelFeature,
    ProviderInstance,
    ProviderStatus,
    ToolCall,
    ToolDefinition,
    ToolResult,
)
from eaip.providers.nvidia import NVIDIAProvider
from eaip.providers.ollama import OllamaProvider
from eaip.providers.openai_compat import OpenAICompatProvider
from eaip.providers.registry import ProviderRegistry
from eaip.providers.selector import ProviderSelector

__all__ = [
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "ModelCapability",
    "ModelFeature",
    "ModelNotFoundError",
    "NVIDIAProvider",
    "OllamaProvider",
    "OpenAICompatProvider",
    "Provider",
    "ProviderDiscovery",
    "ProviderError",
    "ProviderHealthCheck",
    "ProviderHealthMonitor",
    "ProviderInstance",
    "ProviderModelDiscovered",
    "ProviderNotFoundError",
    "ProviderRegistered",
    "ProviderRegistry",
    "ProviderRequestCompleted",
    "ProviderRequestFailed",
    "ProviderRequestStarted",
    "ProviderRuntimeModule",
    "ProviderSelector",
    "ProviderStatus",
    "ProviderStatusChanged",
    "ProviderTimeoutError",
    "ProviderUnregistered",
    "ToolCall",
    "ToolDefinition",
    "ToolResult",
]
