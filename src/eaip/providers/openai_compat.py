"""Generic OpenAI-compatible provider.

Supports any API that follows the OpenAI chat completions format
(https://platform.openai.com/docs/api-reference/chat). Examples include
NVIDIA AI Foundry, Together AI, Anyscale, Fireworks AI, and local proxies.
"""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack

import httpx
from opentelemetry import trace
from opentelemetry.trace import SpanKind, StatusCode

from eaip.logging.context import get_logger
from eaip.providers.models import (
    ChatRequest,
    ChatResponse,
    ModelCapability,
    ModelFeature,
    ToolCall,
)


class OpenAICompatProvider:
    """Generic provider for OpenAI-compatible chat completion APIs.

    Args:
        name: Unique provider name.
        endpoint: Base URL for the API (e.g. ``https://api.openai.com/v1``).
        api_key: API key for authentication.
        default_model: Default model to use when not specified in requests.
        timeout_seconds: HTTP request timeout.
    """

    name: str

    def __init__(
        self,
        name: str,
        endpoint: str,
        api_key: str = "",
        default_model: str = "",
        timeout_seconds: float = 30.0,
    ) -> None:
        """Initialize the OpenAICompatProvider.

        Args:
            name: Unique provider name.
            endpoint: Base URL for the API.
            api_key: API key for authentication.
            default_model: Default model to use.
            timeout_seconds: HTTP request timeout.
        """
        self.name = name
        self._endpoint = endpoint.rstrip("/")
        self._api_key = api_key
        self._default_model = default_model
        self._timeout = timeout_seconds
        self._client: httpx.AsyncClient | None = None
        self._log = get_logger(f"eaip.providers.{name}")

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Send a chat request to the OpenAI-compatible API."""
        model = request.model or self._default_model
        payload: dict[str, object] = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "stream": False,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.response_format is not None:
            payload["response_format"] = request.response_format
        if request.tools:

            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in request.tools
            ]

        t0 = time.monotonic()
        tracer = trace.get_tracer("eaip.providers")
        with tracer.start_as_current_span(
            "provider.chat",
            kind=SpanKind.CLIENT,
            attributes={
                "provider.name": self.name,
                "provider.endpoint": self._endpoint,
                "model": model,
            },
        ) as span:
            async with AsyncExitStack() as stack:
                if self._client is not None:
                    client = self._client
                else:
                    client = await stack.enter_async_context(
                        httpx.AsyncClient(timeout=self._timeout)
                    )
                resp = await client.post(
                    f"{self._endpoint}/chat/completions",
                    json=payload,
                    headers=self._headers(),
                )
                try:
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as exc:
                    span.set_status(StatusCode.ERROR, str(exc))
                    span.record_exception(exc)
                    raise

        duration = (time.monotonic() - t0) * 1000
        choice = data["choices"][0]
        message = choice.get("message", {})
        raw_tool_calls = message.get("tool_calls")
        tool_calls: tuple[ToolCall, ...] | None = None
        if raw_tool_calls:
            calls: list[ToolCall] = []
            for tc in raw_tool_calls:
                raw_args = tc.get("function", {}).get("arguments", "{}")
                try:
                    parsed_args: dict[str, object] = json.loads(raw_args)
                except json.JSONDecodeError:
                    parsed_args = {"_raw": raw_args}
                calls.append(
                    ToolCall(
                        id=tc.get("id", ""),
                        name=tc.get("function", {}).get("name", ""),
                        arguments=parsed_args,
                    )
                )
            tool_calls = tuple(calls)
        return ChatResponse(
            model=data.get("model", model),
            provider=self.name,
            content=message.get("content") or "",
            finish_reason=choice.get("finish_reason", "stop"),
            tool_calls=tool_calls,
            usage=data.get("usage", {}),
            duration_ms=round(duration, 1),
        )

    async def chat_stream(
        self,
        request: ChatRequest,
    ) -> AsyncIterator[str]:
        """Send a chat request and stream response tokens via SSE."""
        model = request.model or self._default_model
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "stream": True,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        async with AsyncExitStack() as stack:
            if self._client is not None:
                client = self._client
            else:
                client = await stack.enter_async_context(httpx.AsyncClient(timeout=self._timeout))
            resp = await stack.enter_async_context(
                client.stream(
                    "POST",
                    f"{self._endpoint}/chat/completions",
                    json=payload,
                    headers=self._headers(),
                )
            )
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    chunk = line[6:]
                    if chunk.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(chunk)
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    async def list_models(self) -> list[ModelCapability]:
        """Return model capabilities.

        Attempts to fetch from the API's model list endpoint.
        Falls back to the default model if the endpoint is unavailable.
        """
        models: list[ModelCapability] = []
        tracer = trace.get_tracer("eaip.providers")
        try:
            with tracer.start_as_current_span(
                "provider.list_models",
                kind=SpanKind.CLIENT,
                attributes={"provider.name": self.name, "provider.endpoint": self._endpoint},
            ):
                async with AsyncExitStack() as stack:
                    if self._client is not None:
                        client = self._client
                    else:
                        client = await stack.enter_async_context(httpx.AsyncClient(timeout=10.0))
                    resp = await client.get(
                        f"{self._endpoint}/models",
                        headers=self._headers(),
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    models.extend(
                        ModelCapability(
                            model_id=entry["id"],
                            provider=self.name,
                            features=(ModelFeature.CHAT, ModelFeature.STREAMING),
                        )
                        for entry in data.get("data", [])
                    )
        except Exception:
            self._log.warning("provider.models.list_failed", endpoint=self._endpoint)
            if self._default_model:
                models.append(
                    ModelCapability(
                        model_id=self._default_model,
                        provider=self.name,
                        features=(ModelFeature.CHAT, ModelFeature.STREAMING),
                    )
                )
        return models

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._api_key:
            h["Authorization"] = f"Bearer {self._api_key}"
        return h


__all__ = ["OpenAICompatProvider"]
