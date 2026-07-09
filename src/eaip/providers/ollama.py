"""Ollama provider — local LLM inference via the Ollama API.

See https://github.com/ollama/ollama/blob/main/docs/api.md
"""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack
from typing import Any

import httpx

from eaip.logging.context import get_logger
from eaip.providers.models import (
    ChatRequest,
    ChatResponse,
    ModelCapability,
    ModelFeature,
)


class OllamaProvider:
    """Provider that communicates with a local Ollama instance.

    Args:
        name: Unique provider name (default: ``"ollama"``).
        endpoint: Ollama server URL (default: ``http://localhost:11434``).
        default_model: Default model tag (e.g. ``"llama3.2"``).
        timeout_seconds: HTTP request timeout.
    """

    name: str

    def __init__(
        self,
        name: str = "ollama",
        endpoint: str = "http://localhost:11434",
        default_model: str = "",
        timeout_seconds: float = 60.0,
    ) -> None:
        """Initialize the OllamaProvider.

        Args:
            name: Unique provider name.
            endpoint: Ollama server URL.
            default_model: Default model tag.
            timeout_seconds: HTTP request timeout.
        """
        self.name = name
        self._endpoint = endpoint.rstrip("/")
        self._default_model = default_model
        self._timeout = timeout_seconds
        self._client: httpx.AsyncClient | None = None
        self._log = get_logger("eaip.providers.ollama")

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Send a chat request to Ollama's chat API."""
        model = request.model or self._default_model
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": False,
        }
        if request.temperature != 0.7:  # noqa: PLR2004
            payload["options"] = {"temperature": request.temperature}

        t0 = time.monotonic()
        async with AsyncExitStack() as stack:
            if self._client is not None:
                client = self._client
            else:
                client = await stack.enter_async_context(httpx.AsyncClient(timeout=self._timeout))
            resp = await client.post(
                f"{self._endpoint}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        duration = (time.monotonic() - t0) * 1000
        return ChatResponse(
            model=data.get("model", model),
            provider=self.name,
            content=data["message"]["content"],
            finish_reason=data.get("done_reason", "stop"),
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
            duration_ms=round(duration, 1),
        )

    async def chat_stream(
        self,
        request: ChatRequest,
    ) -> AsyncIterator[str]:
        """Send a chat request and stream response tokens."""
        model = request.model or self._default_model
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": True,
        }
        if request.temperature != 0.7:  # noqa: PLR2004
            payload["options"] = {"temperature": request.temperature}

        async with AsyncExitStack() as stack:
            if self._client is not None:
                client = self._client
            else:
                client = await stack.enter_async_context(httpx.AsyncClient(timeout=self._timeout))
            resp = await stack.enter_async_context(
                client.stream(
                    "POST",
                    f"{self._endpoint}/api/chat",
                    json=payload,
                )
            )
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue

    async def list_models(self) -> list[ModelCapability]:
        """Fetch the list of available models from Ollama."""
        models: list[ModelCapability] = []
        try:
            async with AsyncExitStack() as stack:
                if self._client is not None:
                    client = self._client
                else:
                    client = await stack.enter_async_context(httpx.AsyncClient(timeout=10.0))
                resp = await client.get(f"{self._endpoint}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                models.extend(
                    ModelCapability(
                        model_id=entry["name"],
                        provider=self.name,
                        features=(ModelFeature.CHAT, ModelFeature.STREAMING),
                    )
                    for entry in data.get("models", [])
                )
        except Exception:
            self._log.warning("provider.ollama.list_failed", endpoint=self._endpoint)
            if self._default_model:
                models.append(
                    ModelCapability(
                        model_id=self._default_model,
                        provider=self.name,
                        features=(ModelFeature.CHAT, ModelFeature.STREAMING),
                    )
                )
        return models


__all__ = ["OllamaProvider"]
