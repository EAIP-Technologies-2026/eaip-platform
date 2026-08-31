"""ProviderSelector — routes requests to the best provider for a model.

Supports:
- Model-based routing (which provider serves this model?)
- Status-aware selection (skip unavailable providers)
- Failover (try alternatives on failure)
- Priority-based ordering
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.providers.exceptions import ModelNotFoundError
from eaip.providers.models import (
    ChatRequest,
    ChatResponse,
    ProviderStatus,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from eaip.providers.base import Provider
    from eaip.providers.registry import ProviderRegistry


class ProviderSelector:
    """Selects and invokes the best provider for a given model request.

    Args:
        registry: The provider registry to select from.
        providers: A dict mapping provider names to Provider instances.
    """

    def __init__(
        self,
        registry: ProviderRegistry,
        providers: dict[str, Provider],
    ) -> None:
        """Initialize the ProviderSelector.

        Args:
            registry: The provider registry to select from.
            providers: A dict mapping provider names to Provider instances.
        """
        self._registry = registry
        self._providers = providers
        self._log = get_logger("eaip.providers.selector")

    def select_provider(self, model: str) -> Provider:
        """Select the best provider for the requested model.

        Iterates registered providers in priority order, checking each
        for model availability and status.

        Args:
            model: The model identifier string.

        Returns:
            A Provider instance capable of serving the model.

        Raises:
            ModelNotFoundError: If no available provider serves this model.
        """
        instances = sorted(
            self._registry.all(),
            key=lambda i: i.priority,
            reverse=True,
        )
        for inst in instances:
            if inst.status is not ProviderStatus.AVAILABLE:
                continue
            for mc in inst.models:
                if mc.model_id == model:
                    provider = self._providers.get(inst.name)
                    if provider is not None:
                        return provider

        available = [i.name for i in self._registry.all() if i.status is ProviderStatus.AVAILABLE]
        raise ModelNotFoundError(
            f"No available provider serves model {model!r}",
            context={"model": model, "available_providers": available},
        )

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Route a chat request to the appropriate provider.

        Attempts failover to the next best provider on failure.

        Args:
            request: The chat request.

        Returns:
            A chat response.

        Raises:
            ModelNotFoundError: If no provider can serve the model.
        """
        return await self._route_with_failover(request, stream=False)

    async def chat_stream(
        self,
        request: ChatRequest,
    ) -> AsyncIterator[str]:
        """Route a streaming chat request to the appropriate provider.

        Args:
            request: The chat request.

        Yields:
            Response tokens.
        """
        provider = self.select_provider(request.model)
        async for token in provider.chat_stream(request):
            yield token

    async def _route_with_failover(
        self,
        request: ChatRequest,
        stream: bool = False,
    ) -> ChatResponse:
        """Attempt to route the request, trying alternatives on failure."""
        instances = sorted(
            self._registry.all(),
            key=lambda i: i.priority,
            reverse=True,
        )
        last_error: Exception | None = None

        for inst in instances:
            if inst.status is not ProviderStatus.AVAILABLE:
                continue
            has_model = any(mc.model_id == request.model for mc in inst.models)
            if not has_model:
                continue
            provider = self._providers.get(inst.name)
            if provider is None:
                continue
            try:
                if stream:
                    raise NotImplementedError("stream failover not implemented")
                return await provider.chat(request)
            except Exception as exc:
                self._log.warning(
                    "provider.failover",
                    provider=inst.name,
                    model=request.model,
                    error=repr(exc),
                )
                last_error = exc

        available = [i.name for i in self._registry.all() if i.status is ProviderStatus.AVAILABLE]
        raise ModelNotFoundError(
            f"No available provider serves model {request.model!r}",
            context={"model": request.model, "available_providers": available},
        ) from last_error


__all__ = ["ProviderSelector"]
