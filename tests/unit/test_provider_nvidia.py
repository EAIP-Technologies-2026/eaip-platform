from __future__ import annotations

import httpx
import pytest

from eaip.providers.models import ChatMessage, ChatRequest
from eaip.providers.nvidia import NVIDIAProvider


class _MockTransport(httpx.AsyncBaseTransport):
    def __init__(self, content: bytes, status: int = 200) -> None:
        self._content = content
        self._status = status

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=self._status,
            content=self._content,
            headers={"Content-Type": "application/json"},
            request=request,
        )


_CHAT_RESP = b"""
{
    "model": "meta/llama3-70b-instruct",
    "choices": [{"message": {"content": "Hello from NVIDIA"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5}
}
"""


class TestNVIDIAProvider:
    @pytest.mark.asyncio
    async def test_chat(self) -> None:
        provider = NVIDIAProvider(endpoint="http://test-nvidia/v1", api_key="test-key")
        transport = _MockTransport(_CHAT_RESP)
        provider._inner._client = httpx.AsyncClient(transport=transport)

        msg = ChatMessage(role="user", content="hello")
        req = ChatRequest(model="meta/llama3-70b-instruct", messages=(msg,))
        resp = await provider.chat(req)
        assert "NVIDIA" in resp.content
        assert resp.model == "meta/llama3-70b-instruct"

    @pytest.mark.asyncio
    async def test_list_models(self) -> None:
        models_resp = b'{"data": [{"id": "meta/llama3-70b-instruct"}, {"id": "mistralai/mixtral"}]}'
        provider = NVIDIAProvider(endpoint="http://test-nvidia/v1")
        transport = _MockTransport(models_resp)
        provider._inner._client = httpx.AsyncClient(transport=transport)

        models = await provider.list_models()
        assert len(models) >= 2
