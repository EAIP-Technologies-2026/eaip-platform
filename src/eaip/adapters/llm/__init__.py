"""LLM Adapter — high-level LLM orchestration (EP-0003)."""

from eaip.adapters.llm.anthropic_adapter import AnthropicAdapter
from eaip.adapters.llm.base import LLMAdapter
from eaip.adapters.llm.exceptions import LLMAdapterError, MaxToolRoundsError, ToolExecutionError
from eaip.adapters.llm.models import LLMRequest, LLMResponse, RunContext
from eaip.adapters.llm.openai_adapter import OpenAIAdapter
from eaip.adapters.llm.orchestration import ToolCallOrchestrator
from eaip.adapters.llm.stub import StubLLMAdapter

__all__ = [
    "AnthropicAdapter",
    "LLMAdapter",
    "LLMAdapterError",
    "LLMRequest",
    "LLMResponse",
    "MaxToolRoundsError",
    "OpenAIAdapter",
    "RunContext",
    "StubLLMAdapter",
    "ToolCallOrchestrator",
    "ToolExecutionError",
]
