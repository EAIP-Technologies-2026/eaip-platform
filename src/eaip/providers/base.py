"""Provider protocol — the abstract interface for AI providers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from eaip.providers.models import ChatRequest, ChatResponse, ModelCapability


@runtime_checkable
class Provider(Protocol):
    """Protocol for AI providers.

    Implementations must provide:
    - name: A unique provider name.
    - chat(): Send a chat request and receive a response.
    - chat_stream(): Send a chat request and receive a streaming response.
    - list_models(): Return the models this provider supports.
    """

    name: str

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Send a chat request to the provider.

        Args:
            request: The chat request.

        Returns:
            A chat response.
        """
        ...

    async def chat_stream(
        self,
        _request: ChatRequest,
    ) -> AsyncIterator[str]:
        """Send a chat request and stream the response tokens.

        Args:
            _request: The chat request (stream flag is forced True).

        Yields:
            Response tokens as they arrive.
        """
        ...
        return
        yield  # type: ignore[unreachable]  # pragma: no cover

    async def list_models(self) -> list[ModelCapability]:
        """Return the list of models this provider supports.

        Returns:
            A list of model capabilities.
        """
        ...


__all__ = ["Provider"]
