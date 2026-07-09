from __future__ import annotations

import httpx
import pytest

from eaip.providers.models import ChatMessage, ChatRequest, ChatResponse
from eaip.providers.ollama import OllamaProvider


class _MockTransport(httpx.AsyncBaseTransport):
    def __init__(self, response_data: bytes, status: int = 200) -> None:
        self._response_data = response_data
        self._status = status

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=self._status,
            content=self._response_data,
            headers={"Content-Type": "application/json"},
            request=request,
        )


_CHAT_RESPONSE = b"""
{
    "model": "llama3",
    "message": {"role": "assistant", "content": "Hello! How can I help?"},
    "done_reason": "stop",
    "prompt_eval_count": 10,
    "eval_count": 5
}
"""


class TestOllamaProvider:
    @pytest.mark.asyncio
    async def test_chat(self) -> None:
        provider = OllamaProvider(endpoint="http://test:11434")
        transport = _MockTransport(_CHAT_RESPONSE)
        provider._client = httpx.AsyncClient(transport=transport)

        msg = ChatMessage(role="user", content="hi")
        req = ChatRequest(model="llama3", messages=(msg,))
        resp = await provider.chat(req)

        assert resp.model == "llama3"
        assert "Hello" in resp.content
        assert resp.finish_reason == "stop"
        assert resp.provider == "ollama"

    @pytest.mark.asyncio
    async def test_list_models(self) -> None:
        tags_response = b'{"models": [{"name": "llama3"}, {"name": "mistral"}]}'
        provider = OllamaProvider(endpoint="http://test:11434")
        transport = _MockTransport(tags_response)
        provider._client = httpx.AsyncClient(transport=transport)

        models = await provider.list_models()
        assert len(models) == 2
        assert models[0].model_id == "llama3"

    @pytest.mark.asyncio
    async def test_list_models_fallback(self) -> None:
        provider = OllamaProvider(endpoint="http://nonexistent:11434", default_model="llama3")
        models = await provider.list_models()
        assert len(models) == 1
        assert models[0].model_id == "llama3"

    @pytest.mark.asyncio
    async def test_chat_stream(self) -> None:
        stream_data = (
            b'{"message": {"content": "Hello"}}\n'
            b'{"message": {"content": " world"}}\n'
            b'{"message": {"content": ""}, "done": true}\n'
        )
        provider = OllamaProvider(endpoint="http://test:11434")
        transport = _MockTransport(stream_data)
        provider._client = httpx.AsyncClient(transport=transport)

        msg = ChatMessage(role="user", content="hi")
        req = ChatRequest(model="llama3", messages=(msg,), stream=True)
        tokens = [t async for t in provider.chat_stream(req)]
        assert tokens == ["Hello", " world"]
