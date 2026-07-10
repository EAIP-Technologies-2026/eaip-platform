"""Tests for :mod:`eaip.gateway.middleware`."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeAlias

import pytest

from eaip.gateway.auth import ApiKeyStore
from eaip.gateway.exceptions import AuthError, RateLimitExceededError
from eaip.gateway.middleware import (
    AuthMiddleware,
    CorsMiddleware,
    LoggingMiddleware,
    MetricsMiddleware,
    MiddlewarePipeline,
    RateLimitMiddleware,
)
from eaip.gateway.models import (
    ApiKeyCredentials,
    ApiRequest,
    ApiResponse,
    HttpMethod,
    RateLimitConfig,
)
from eaip.gateway.rate_limiter import RateLimiter

_Handler: TypeAlias = Callable[[ApiRequest], Awaitable[ApiResponse]]


@pytest.fixture
def ok_handler() -> _Handler:
    async def handler(req: ApiRequest) -> ApiResponse:
        return ApiResponse(request_id=req.id, status_code=200, body={"ok": True})

    return handler


class TestMiddlewarePipeline:
    async def test_empty_pipeline(self) -> None:
        pipeline = MiddlewarePipeline()

        async def handler(req: ApiRequest) -> ApiResponse:
            return ApiResponse(request_id=req.id, status_code=200)

        req = ApiRequest(id="r1", method=HttpMethod.GET, path="/")
        resp = await pipeline.run(req, handler)
        assert resp.status_code == 200

    async def test_middleware_order(self, ok_handler: _Handler) -> None:
        order: list[str] = []

        class _Mw1:
            async def handle(self, request: ApiRequest, next_call: _Handler) -> ApiResponse:
                order.append("mw1_before")
                resp = await next_call(request)
                order.append("mw1_after")
                return resp

        class _Mw2:
            async def handle(self, request: ApiRequest, next_call: _Handler) -> ApiResponse:
                order.append("mw2_before")
                resp = await next_call(request)
                order.append("mw2_after")
                return resp

        pipeline = MiddlewarePipeline()
        pipeline.add(_Mw1())
        pipeline.add(_Mw2())

        req = ApiRequest(id="r1", method=HttpMethod.GET, path="/")
        await pipeline.run(req, ok_handler)
        assert order == ["mw1_before", "mw2_before", "mw2_after", "mw1_after"]

    async def test_middleware_short_circuit(self) -> None:
        class _BlockMw:
            async def handle(self, request: ApiRequest, next_call: object) -> ApiResponse:
                return ApiResponse(request_id=request.id, status_code=403, body={"blocked": True})

        handler_called = False

        async def handler(req: ApiRequest) -> ApiResponse:
            nonlocal handler_called
            handler_called = True
            return ApiResponse(request_id=req.id, status_code=200)

        pipeline = MiddlewarePipeline()
        pipeline.add(_BlockMw())

        req = ApiRequest(id="r1", method=HttpMethod.GET, path="/")
        resp = await pipeline.run(req, handler)
        assert resp.status_code == 403
        assert handler_called is False

    async def test_add_remove(self) -> None:
        pipeline = MiddlewarePipeline()
        mw = LoggingMiddleware()
        pipeline.add(mw)
        assert len(pipeline.middlewares) == 1
        pipeline.remove(mw)
        assert len(pipeline.middlewares) == 0


class TestLoggingMiddleware:
    async def test_passthrough(self, ok_handler: object) -> None:
        mw = LoggingMiddleware()
        req = ApiRequest(id="r1", method=HttpMethod.GET, path="/test")
        resp = await mw.handle(req, ok_handler)  # type: ignore[arg-type]
        assert resp.status_code == 200


class TestMetricsMiddleware:
    async def test_records_metrics(self, ok_handler: object) -> None:
        mw = MetricsMiddleware()
        req = ApiRequest(id="r1", method=HttpMethod.GET, path="/test")

        await mw.handle(req, ok_handler)  # type: ignore[arg-type]
        assert mw.request_count == 1
        assert len(mw.durations) == 1

        await mw.handle(req, ok_handler)  # type: ignore[arg-type]
        assert mw.request_count == 2

    async def test_duration_positive(self, ok_handler: object) -> None:
        mw = MetricsMiddleware()
        req = ApiRequest(id="r1", method=HttpMethod.GET, path="/test")
        await mw.handle(req, ok_handler)  # type: ignore[arg-type]
        assert mw.durations[0] > 0


class TestAuthMiddleware:
    async def test_valid_auth(self) -> None:
        store = ApiKeyStore()
        creds = ApiKeyCredentials(key_id="k1", name="TestKey")
        raw_key = store.register_key(creds)

        mw = AuthMiddleware(store)

        async def handler(req: ApiRequest) -> ApiResponse:
            assert req.subject_id == "TestKey"
            return ApiResponse(request_id=req.id, status_code=200)

        req = ApiRequest(
            id="r1",
            method=HttpMethod.GET,
            path="/secure",
            headers={"Authorization": f"Bearer k1:{raw_key}"},
        )
        resp = await mw.handle(req, handler)
        assert resp.status_code == 200

    async def test_missing_header(self) -> None:
        store = ApiKeyStore()
        mw = AuthMiddleware(store)
        req = ApiRequest(id="r1", method=HttpMethod.GET, path="/secure")
        with pytest.raises(AuthError, match="Missing or malformed"):
            await mw.handle(req, lambda r: None)  # type: ignore[arg-type,return-value]

    async def test_invalid_key(self) -> None:
        store = ApiKeyStore()
        creds = ApiKeyCredentials(key_id="k1", name="TestKey")
        store.register_key(creds, raw_key="correct-key")

        mw = AuthMiddleware(store)
        req = ApiRequest(
            id="r1",
            method=HttpMethod.GET,
            path="/secure",
            headers={"Authorization": "Bearer k1:wrong-key"},
        )
        with pytest.raises(AuthError, match="Invalid"):
            await mw.handle(req, lambda r: None)  # type: ignore[arg-type,return-value]

    async def test_disabled_key(self) -> None:
        store = ApiKeyStore()
        creds = ApiKeyCredentials(key_id="k1", name="Disabled", enabled=False)
        store.register_key(creds, raw_key="secret")

        mw = AuthMiddleware(store)
        req = ApiRequest(
            id="r1",
            method=HttpMethod.GET,
            path="/secure",
            headers={"Authorization": "Bearer k1:secret"},
        )
        with pytest.raises(AuthError, match="disabled"):
            await mw.handle(req, lambda r: None)  # type: ignore[arg-type,return-value]


class TestRateLimitMiddleware:
    async def test_allowed(self) -> None:
        limiter = RateLimiter()
        config = RateLimitConfig(max_requests=5, window_seconds=60.0)
        mw = RateLimitMiddleware(limiter, default_config=config)

        async def handler(req: ApiRequest) -> ApiResponse:
            return ApiResponse(request_id=req.id, status_code=200)

        req = ApiRequest(id="r1", method=HttpMethod.GET, path="/", subject_id="user1")
        resp = await mw.handle(req, handler)
        assert resp.status_code == 200

    async def test_blocked(self) -> None:
        limiter = RateLimiter()
        config = RateLimitConfig(max_requests=2, window_seconds=60.0)
        mw = RateLimitMiddleware(limiter, default_config=config)

        async def handler(req: ApiRequest) -> ApiResponse:
            return ApiResponse(request_id=req.id, status_code=200)

        req = ApiRequest(id="r1", method=HttpMethod.GET, path="/", subject_id="user1")
        assert (await mw.handle(req, handler)).status_code == 200
        assert (await mw.handle(req, handler)).status_code == 200
        with pytest.raises(RateLimitExceededError):
            await mw.handle(req, handler)

    async def test_no_config_allows_all(self) -> None:
        limiter = RateLimiter()
        mw = RateLimitMiddleware(limiter, default_config=None)

        async def handler(req: ApiRequest) -> ApiResponse:
            return ApiResponse(request_id=req.id, status_code=200)

        req = ApiRequest(id="r1", method=HttpMethod.GET, path="/")
        for _ in range(100):
            resp = await mw.handle(req, handler)
            assert resp.status_code == 200


class TestCorsMiddleware:
    async def test_adds_headers(self) -> None:
        mw = CorsMiddleware()

        async def handler(req: ApiRequest) -> ApiResponse:
            return ApiResponse(request_id=req.id, status_code=200)

        req = ApiRequest(id="r1", method=HttpMethod.GET, path="/", headers={"Origin": "http://example.com"})
        resp = await mw.handle(req, handler)
        assert resp.headers.get("Access-Control-Allow-Origin") == "http://example.com"

    async def test_options_preflight(self) -> None:
        mw = CorsMiddleware()
        req = ApiRequest(id="r1", method=HttpMethod.OPTIONS, path="/", headers={"Origin": "*"})
        resp = await mw.handle(req, lambda r: None)  # type: ignore[arg-type,return-value]
        assert resp.status_code == 204
        assert resp.headers.get("Access-Control-Allow-Origin") == "*"

    async def test_restricted_origin_blocked(self) -> None:
        mw = CorsMiddleware(allowed_origins=("https://trusted.com",))

        async def handler(req: ApiRequest) -> ApiResponse:
            return ApiResponse(request_id=req.id, status_code=200)

        req = ApiRequest(
            id="r1",
            method=HttpMethod.GET,
            path="/",
            headers={"Origin": "https://evil.com"},
        )
        resp = await mw.handle(req, handler)
        assert resp.headers.get("Access-Control-Allow-Origin") is None
