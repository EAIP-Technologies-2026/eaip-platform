"""Tests for :mod:`eaip.gateway.models`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.gateway.models import (
    ApiKeyCredentials,
    ApiRequest,
    ApiResponse,
    Endpoint,
    HttpMethod,
    RateLimitConfig,
)
from eaip.shared.identifiers import CorrelationId


class TestHttpMethod:
    def test_values(self) -> None:
        assert HttpMethod.GET == "GET"
        assert HttpMethod.POST == "POST"
        assert HttpMethod.PUT == "PUT"
        assert HttpMethod.DELETE == "DELETE"
        assert HttpMethod.PATCH == "PATCH"

    def test_is_str_enum(self) -> None:
        assert issubclass(HttpMethod, str)


class TestRateLimitConfig:
    def test_valid(self) -> None:
        cfg = RateLimitConfig(max_requests=10, window_seconds=60.0)
        assert cfg.max_requests == 10
        assert cfg.window_seconds == 60.0

    def test_frozen(self) -> None:
        cfg = RateLimitConfig(max_requests=5, window_seconds=30.0)
        with pytest.raises(ValueError):
            cfg.max_requests = 10

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            RateLimitConfig(max_requests=5, window_seconds=30.0, extra_field="x")  # type: ignore[call-arg]

    def test_max_requests_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            RateLimitConfig(max_requests=0, window_seconds=60.0)

    def test_window_seconds_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            RateLimitConfig(max_requests=10, window_seconds=0.0)


class TestEndpoint:
    def test_minimal(self) -> None:
        async def handler(req: ApiRequest) -> ApiResponse:
            return ApiResponse(request_id=req.id, status_code=200)

        ep = Endpoint(path="/test", method=HttpMethod.GET, handler=handler)
        assert ep.path == "/test"
        assert ep.method is HttpMethod.GET
        assert ep.auth_required is True
        assert ep.rate_limit_config is None

    def test_frozen(self) -> None:
        async def handler(req: ApiRequest) -> ApiResponse:
            return ApiResponse(request_id=req.id, status_code=200)

        ep = Endpoint(path="/test", method=HttpMethod.GET, handler=handler)
        with pytest.raises(ValueError):
            ep.path = "/other"

    def test_extra_forbidden(self) -> None:
        async def handler(req: ApiRequest) -> ApiResponse:
            return ApiResponse(request_id=req.id, status_code=200)

        with pytest.raises(ValidationError):
            Endpoint(path="/test", method=HttpMethod.GET, handler=handler, unknown="x")  # type: ignore[call-arg]

    def test_handler_excluded_from_equality(self) -> None:
        async def handler(req: ApiRequest) -> ApiResponse:
            return ApiResponse(request_id=req.id, status_code=200)

        ep1 = Endpoint(path="/test", method=HttpMethod.GET, handler=handler)
        ep2 = Endpoint(path="/test", method=HttpMethod.GET, handler=handler)
        assert ep1 == ep2


class TestApiRequest:
    def test_minimal(self) -> None:
        req = ApiRequest(id="r1", method=HttpMethod.POST, path="/api/v1/data")
        assert req.id == "r1"
        assert req.method is HttpMethod.POST
        assert req.path == "/api/v1/data"
        assert req.headers == {}
        assert req.query_params == {}
        assert req.body is None

    def test_frozen(self) -> None:
        req = ApiRequest(id="r1", method=HttpMethod.GET, path="/test")
        with pytest.raises(ValueError):
            req.path = "/other"

    def test_with_correlation_id(self) -> None:
        cid = CorrelationId.new()
        req = ApiRequest(id="r1", method=HttpMethod.GET, path="/test", correlation_id=cid)
        assert req.correlation_id == cid

    def test_with_subject_id(self) -> None:
        req = ApiRequest(
            id="r1",
            method=HttpMethod.GET,
            path="/test",
            subject_id="user-1",
        )
        assert req.subject_id == "user-1"


class TestApiResponse:
    def test_minimal(self) -> None:
        resp = ApiResponse(request_id="r1", status_code=200)
        assert resp.request_id == "r1"
        assert resp.status_code == 200
        assert resp.body is None
        assert resp.duration_ms == 0.0

    def test_frozen(self) -> None:
        resp = ApiResponse(request_id="r1", status_code=200)
        with pytest.raises(ValueError):
            resp.status_code = 404

    def test_with_body(self) -> None:
        resp = ApiResponse(request_id="r1", status_code=200, body={"key": "value"})
        assert resp.body == {"key": "value"}

    def test_duration_ms(self) -> None:
        resp = ApiResponse(request_id="r1", status_code=200, duration_ms=12.5)
        assert resp.duration_ms == 12.5


class TestApiKeyCredentials:
    def test_valid(self) -> None:
        creds = ApiKeyCredentials(key_id="k1", name="Test Key")
        assert creds.key_id == "k1"
        assert creds.name == "Test Key"
        assert creds.roles == ()
        assert creds.enabled is True

    def test_with_roles(self) -> None:
        creds = ApiKeyCredentials(key_id="k1", name="Admin Key", roles=("admin", "write"))
        assert creds.roles == ("admin", "write")

    def test_disabled(self) -> None:
        creds = ApiKeyCredentials(key_id="k1", name="Disabled Key", enabled=False)
        assert creds.enabled is False

    def test_frozen(self) -> None:
        creds = ApiKeyCredentials(key_id="k1", name="Test")
        with pytest.raises(ValueError):
            creds.name = "Other"
