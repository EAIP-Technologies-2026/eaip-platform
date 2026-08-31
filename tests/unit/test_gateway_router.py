"""Tests for :mod:`eaip.gateway.router`."""

from __future__ import annotations

import pytest

from eaip.gateway.exceptions import EndpointNotFoundError
from eaip.gateway.models import ApiRequest, ApiResponse, Endpoint, HttpMethod
from eaip.gateway.router import ApiRouter


@pytest.fixture
def router() -> ApiRouter:
    return ApiRouter()


@pytest.fixture
def sample_endpoint() -> Endpoint:
    async def handler(req: ApiRequest) -> ApiResponse:
        return ApiResponse(request_id=req.id, status_code=200, body={"echo": req.path})

    return Endpoint(path="/test", method=HttpMethod.GET, handler=handler)


class TestApiRouter:
    async def test_register_and_list(self, router: ApiRouter, sample_endpoint: Endpoint) -> None:
        router.register_endpoint(sample_endpoint)
        endpoints = router.list_endpoints()
        assert len(endpoints) == 1
        assert endpoints[0].path == "/test"

    async def test_get_endpoint_found(self, router: ApiRouter, sample_endpoint: Endpoint) -> None:
        router.register_endpoint(sample_endpoint)
        ep = router.get_endpoint("/test", HttpMethod.GET)
        assert ep is not None
        assert ep.path == "/test"
        assert ep.method is HttpMethod.GET

    async def test_get_endpoint_not_found(self, router: ApiRouter) -> None:
        ep = router.get_endpoint("/nonexistent", HttpMethod.GET)
        assert ep is None

    async def test_get_endpoint_wrong_method(
        self, router: ApiRouter, sample_endpoint: Endpoint
    ) -> None:
        router.register_endpoint(sample_endpoint)
        ep = router.get_endpoint("/test", HttpMethod.POST)
        assert ep is None

    async def test_unregister_endpoint(self, router: ApiRouter, sample_endpoint: Endpoint) -> None:
        router.register_endpoint(sample_endpoint)
        router.unregister_endpoint("/test", HttpMethod.GET)
        assert router.list_endpoints() == []

    async def test_unregister_nonexistent(self, router: ApiRouter) -> None:
        router.unregister_endpoint("/nope", HttpMethod.GET)
        assert router.list_endpoints() == []

    async def test_dispatch_success(self, router: ApiRouter) -> None:
        async def handler(req: ApiRequest) -> ApiResponse:
            return ApiResponse(request_id=req.id, status_code=200, body={"path": req.path})

        ep = Endpoint(path="/hello", method=HttpMethod.GET, auth_required=False, handler=handler)
        router.register_endpoint(ep)

        req = ApiRequest(id="req1", method=HttpMethod.GET, path="/hello")
        resp = await router.dispatch(req)
        assert resp.status_code == 200
        assert resp.body == {"path": "/hello"}

    async def test_dispatch_endpoint_not_found(self, router: ApiRouter) -> None:
        req = ApiRequest(id="req1", method=HttpMethod.GET, path="/unknown")
        with pytest.raises(EndpointNotFoundError):
            await router.dispatch(req)

    async def test_dispatch_handler_returns_raw(self, router: ApiRouter) -> None:
        async def handler(req: ApiRequest) -> dict[str, bool]:
            return {"raw": True}

        ep = Endpoint(path="/raw", method=HttpMethod.GET, auth_required=False, handler=handler)
        router.register_endpoint(ep)

        req = ApiRequest(id="req1", method=HttpMethod.GET, path="/raw")
        resp = await router.dispatch(req)
        assert resp.status_code == 200
        assert resp.body == {"raw": True}

    async def test_dispatch_response_has_request_id(self, router: ApiRouter) -> None:
        async def handler(req: ApiRequest) -> ApiResponse:
            return ApiResponse(request_id=req.id, status_code=200)

        ep = Endpoint(path="/echo", method=HttpMethod.POST, auth_required=False, handler=handler)
        router.register_endpoint(ep)

        req = ApiRequest(id="my-id", method=HttpMethod.POST, path="/echo")
        resp = await router.dispatch(req)
        assert resp.request_id == "my-id"
