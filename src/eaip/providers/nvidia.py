"""NVIDIA provider — NVIDIA AI Foundry / NGC API.

Uses the OpenAI-compatible chat completions format at
``https://integrate.api.nvidia.com/v1``.
Thin wrapper over OpenAICompatProvider with NVIDIA-specific defaults.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from eaip.providers.models import ChatRequest, ChatResponse, ModelCapability
from eaip.providers.openai_compat import OpenAICompatProvider


class NVIDIAProvider:
    """Provider for NVIDIA AI Foundry / NGC endpoints.

    Args:
        name: Unique provider name (default: ``"nvidia"``).
        endpoint: NVIDIA API base URL.
        api_key: NVIDIA API key.
        default_model: Default model ID (e.g. ``"meta/llama3-70b-instruct"``).
        timeout_seconds: HTTP request timeout.
    """

    name: str

    def __init__(
        self,
        name: str = "nvidia",
        endpoint: str = "https://integrate.api.nvidia.com/v1",
        api_key: str = "",
        default_model: str = "",
        timeout_seconds: float = 60.0,
    ) -> None:
        """Initialize the NVIDIAProvider.

        Args:
            name: Unique provider name.
            endpoint: NVIDIA API base URL.
            api_key: NVIDIA API key.
            default_model: Default model ID.
            timeout_seconds: HTTP request timeout.
        """
        self.name = name
        self._inner = OpenAICompatProvider(
            name=name,
            endpoint=endpoint,
            api_key=api_key,
            default_model=default_model,
            timeout_seconds=timeout_seconds,
        )

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Send a chat request to the NVIDIA API."""
        return await self._inner.chat(request)

    async def chat_stream(
        self,
        request: ChatRequest,
    ) -> AsyncIterator[str]:
        """Send a chat request and stream response tokens."""
        async for token in self._inner.chat_stream(request):
            yield token

    async def list_models(self) -> list[ModelCapability]:
        """Return the list of models available from NVIDIA."""
        return await self._inner.list_models()


__all__ = ["NVIDIAProvider"]
