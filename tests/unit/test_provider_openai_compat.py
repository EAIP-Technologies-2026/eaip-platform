from __future__ import annotations

import json

import httpx
import pytest


from eaip.providers.models import ChatMessage, ChatRequest
from eaip.providers.openai_compat import OpenAICompatProvider


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
    "model": "gpt-4",
    "choices": [{"message": {"content": "Hello from OpenAI-compat"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 5, "completion_tokens": 3}
}
"""


class TestOpenAICompatProvider:
    @pytest.mark.asyncio
    async def test_chat(self) -> None:
        provider = OpenAICompatProvider(
            name="test-openai", endpoint="http://test-api/v1", api_key="sk-test"
        )
        transport = _MockTransport(_CHAT_RESP)
        provider._client = httpx.AsyncClient(transport=transport)

        msg = ChatMessage(role="user", content="hello")
        req = ChatRequest(model="gpt-4", messages=(msg,))
        resp = await provider.chat(req)
        assert "OpenAI-compat" in resp.content
        assert resp.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_chat_headers(self) -> None:
        """Verify Authorization header is sent with API key."""
        request_sent: list[httpx.Request] = []

        class _CaptureTransport(httpx.AsyncBaseTransport):
            async def handle_async_request(self, r: httpx.Request) -> httpx.Response:
                request_sent.append(r)
                return httpx.Response(200, content=_CHAT_RESP, request=r)

        provider = OpenAICompatProvider(
            name="test", endpoint="http://test-api/v1", api_key="sk-secret"
        )
        provider._client = httpx.AsyncClient(transport=_CaptureTransport())

        msg = ChatMessage(role="user", content="hi")
        req = ChatRequest(model="gpt-4", messages=(msg,))
        await provider.chat(req)

        assert len(request_sent) == 1
        assert request_sent[0].headers.get("Authorization") == "Bearer sk-secret"

    @pytest.mark.asyncio
    async def test_list_models(self) -> None:
        models_resp = b'{"data": [{"id": "gpt-4"}, {"id": "gpt-3.5-turbo"}]}'
        provider = OpenAICompatProvider(name="test", endpoint="http://test-api/v1")
        transport = _MockTransport(models_resp)
        provider._client = httpx.AsyncClient(transport=transport)

        models = await provider.list_models()
        assert len(models) == 2
        assert models[0].model_id == "gpt-4"

    @pytest.mark.asyncio
    async def test_list_models_fallback(self) -> None:
        provider = OpenAICompatProvider(
            name="test", endpoint="http://bad-url/v1", default_model="gpt-4"
        )
        models = await provider.list_models()
        assert len(models) == 1
        assert models[0].model_id == "gpt-4"

    @pytest.mark.asyncio
    async def test_chat_structured_output(self) -> None:
        request_sent: list[httpx.Request] = []

        class _CaptureTransport(httpx.AsyncBaseTransport):
            async def handle_async_request(self, r: httpx.Request) -> httpx.Response:
                request_sent.append(r)
                return httpx.Response(200, content=_CHAT_RESP, request=r)

        provider = OpenAICompatProvider(
            name="test", endpoint="http://test-api/v1", api_key="sk-secret"
        )
        provider._client = httpx.AsyncClient(transport=_CaptureTransport())

        msg = ChatMessage(role="user", content="hi")
        req = ChatRequest(
            model="gpt-4",
            messages=(msg,),
            response_format={"type": "json_object"},
        )
        await provider.chat(req)

        assert len(request_sent) == 1
        body = json.loads(request_sent[0].content)
        assert body.get("response_format") == {"type": "json_object"}

