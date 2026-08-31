"""Tests for :mod:`eaip.apiext.models`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from eaip.apiext.models import (
    ApiComposition,
    ApiCompositionConfig,
    CachedResponse,
    MergeStrategy,
    RateLimitPolicy,
    ResponseTransform,
)


class TestMergeStrategy:
    def test_values(self) -> None:
        assert MergeStrategy.CONCAT == "concat"
        assert MergeStrategy.MERGE == "merge"
        assert MergeStrategy.ZIP == "zip"
        assert MergeStrategy.CHAIN == "chain"

    def test_is_str_enum(self) -> None:
        assert issubclass(MergeStrategy, str)


class TestApiComposition:
    def test_minimal(self) -> None:
        comp = ApiComposition(
            id="comp-1",
            name="Test Composition",
            endpoint_path="/api/composed",
            method="GET",
            source_endpoints=("/api/a", "/api/b"),
        )
        assert comp.id == "comp-1"
        assert comp.name == "Test Composition"
        assert comp.endpoint_path == "/api/composed"
        assert comp.method == "GET"
        assert comp.source_endpoints == ("/api/a", "/api/b")
        assert comp.merge_strategy is MergeStrategy.CONCAT
        assert comp.enabled is True
        assert comp.timeout_seconds == 30.0

    def test_frozen(self) -> None:
        comp = ApiComposition(
            id="comp-1",
            name="Test",
            endpoint_path="/test",
            method="GET",
            source_endpoints=("/a",),
        )
        with pytest.raises(ValueError):
            comp.name = "Other"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ApiComposition(
                id="comp-1",
                name="Test",
                endpoint_path="/test",
                method="GET",
                source_endpoints=("/a",),
                unknown="x",
            )

    def test_with_merge_strategies(self) -> None:
        for strategy in MergeStrategy:
            comp = ApiComposition(
                id="comp-1",
                name="Test",
                endpoint_path="/test",
                method="POST",
                source_endpoints=("/a", "/b"),
                merge_strategy=strategy,
            )
            assert comp.merge_strategy is strategy

    def test_with_response_mapping(self) -> None:
        comp = ApiComposition(
            id="comp-1",
            name="Test",
            endpoint_path="/test",
            method="GET",
            source_endpoints=("/a",),
            response_mapping={"source_0": "result"},
        )
        assert comp.response_mapping == {"source_0": "result"}

    def test_with_cache_ttl(self) -> None:
        comp = ApiComposition(
            id="comp-1",
            name="Test",
            endpoint_path="/test",
            method="GET",
            source_endpoints=("/a",),
            cache_ttl_seconds=60.0,
        )
        assert comp.cache_ttl_seconds == 60.0

    def test_disabled(self) -> None:
        comp = ApiComposition(
            id="comp-1",
            name="Test",
            endpoint_path="/test",
            method="GET",
            source_endpoints=("/a",),
            enabled=False,
        )
        assert comp.enabled is False

    def test_timeout_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            ApiComposition(
                id="comp-1",
                name="Test",
                endpoint_path="/test",
                method="GET",
                source_endpoints=("/a",),
                timeout_seconds=0,
            )


class TestCachedResponse:
    def test_minimal(self) -> None:
        expires = datetime.now(UTC) + timedelta(hours=1)
        cached = CachedResponse(
            id="entry-1",
            cache_key="key:abc",
            expires_at=expires,
        )
        assert cached.id == "entry-1"
        assert cached.cache_key == "key:abc"
        assert cached.status_code == 200
        assert cached.hit_count == 0

    def test_frozen(self) -> None:
        expires = datetime.now(UTC) + timedelta(hours=1)
        cached = CachedResponse(id="e1", cache_key="k", expires_at=expires)
        with pytest.raises(ValueError):
            cached.hit_count = 5

    def test_with_body_and_headers(self) -> None:
        expires = datetime.now(UTC) + timedelta(hours=1)
        cached = CachedResponse(
            id="e1",
            cache_key="k",
            response_body={"data": "value"},
            status_code=201,
            headers={"content-type": "application/json"},
            expires_at=expires,
            hit_count=3,
        )
        assert cached.response_body == {"data": "value"}
        assert cached.status_code == 201
        assert cached.headers == {"content-type": "application/json"}
        assert cached.hit_count == 3

    def test_expires_at_required(self) -> None:
        with pytest.raises(ValidationError):
            CachedResponse(id="e1", cache_key="k")

    def test_hit_count_non_negative(self) -> None:
        expires = datetime.now(UTC) + timedelta(hours=1)
        with pytest.raises(ValidationError):
            CachedResponse(id="e1", cache_key="k", expires_at=expires, hit_count=-1)


class TestRateLimitPolicy:
    def test_minimal(self) -> None:
        policy = RateLimitPolicy(
            id="rl-1",
            name="Standard",
            key_pattern="{subject_id}",
            max_requests=100,
            window_seconds=60.0,
        )
        assert policy.id == "rl-1"
        assert policy.name == "Standard"
        assert policy.max_requests == 100
        assert policy.window_seconds == 60.0
        assert policy.burst_multiplier == 1.0

    def test_frozen(self) -> None:
        policy = RateLimitPolicy(
            id="rl-1",
            name="Standard",
            key_pattern="{subject_id}",
            max_requests=100,
            window_seconds=60.0,
        )
        with pytest.raises(ValueError):
            policy.max_requests = 200

    def test_with_burst(self) -> None:
        policy = RateLimitPolicy(
            id="rl-2",
            name="Bursty",
            key_pattern="{subject_id}",
            max_requests=100,
            window_seconds=60.0,
            burst_multiplier=2.0,
        )
        assert policy.burst_multiplier == 2.0

    def test_burst_must_be_ge_1(self) -> None:
        with pytest.raises(ValidationError):
            RateLimitPolicy(
                id="rl-3",
                name="Bad",
                key_pattern="{subject_id}",
                max_requests=100,
                window_seconds=60.0,
                burst_multiplier=0.5,
            )

    def test_custom_headers(self) -> None:
        policy = RateLimitPolicy(
            id="rl-4",
            name="Custom",
            key_pattern="{subject_id}",
            max_requests=50,
            window_seconds=30.0,
            response_headers=("X-Custom-Limit", "X-Custom-Remaining"),
        )
        assert policy.response_headers == ("X-Custom-Limit", "X-Custom-Remaining")

    def test_custom_status_and_message(self) -> None:
        policy = RateLimitPolicy(
            id="rl-5",
            name="Custom",
            key_pattern="{subject_id}",
            max_requests=10,
            window_seconds=10.0,
            status_code=429,
            error_message="Too many requests",
        )
        assert policy.status_code == 429
        assert policy.error_message == "Too many requests"


class TestResponseTransform:
    def test_minimal(self) -> None:
        transform = ResponseTransform(
            id="tf-1",
            name="Strip PII",
            endpoint_pattern="/api/**",
            transformations=("remove_field:ssn",),
        )
        assert transform.id == "tf-1"
        assert transform.endpoint_pattern == "/api/**"
        assert transform.enabled is True
        assert transform.priority == 0

    def test_frozen(self) -> None:
        transform = ResponseTransform(
            id="tf-1",
            name="Test",
            endpoint_pattern="/api/**",
            transformations=("remove_field:x",),
        )
        with pytest.raises(ValueError):
            transform.enabled = False

    def test_with_priority(self) -> None:
        transform = ResponseTransform(
            id="tf-2",
            name="High Priority",
            endpoint_pattern="/api/**",
            transformations=("rename_field:a:b",),
            priority=10,
        )
        assert transform.priority == 10

    def test_disabled(self) -> None:
        transform = ResponseTransform(
            id="tf-3",
            name="Disabled",
            endpoint_pattern="/api/**",
            transformations=(),
            enabled=False,
        )
        assert transform.enabled is False


class TestApiCompositionConfig:
    def test_defaults(self) -> None:
        config = ApiCompositionConfig()
        assert config.max_concurrent_requests == 10
        assert config.default_timeout == 30.0
        assert config.enable_caching is True
        assert config.cache_max_size == 1000
        assert config.enable_circuit_breaker is False

    def test_custom(self) -> None:
        config = ApiCompositionConfig(
            max_concurrent_requests=5,
            default_timeout=15.0,
            enable_caching=False,
            cache_max_size=500,
            enable_circuit_breaker=True,
        )
        assert config.max_concurrent_requests == 5
        assert config.default_timeout == 15.0
        assert config.enable_caching is False
        assert config.cache_max_size == 500
        assert config.enable_circuit_breaker is True

    def test_frozen(self) -> None:
        config = ApiCompositionConfig()
        with pytest.raises(ValueError):
            config.max_concurrent_requests = 20

    def test_positive_constraints(self) -> None:
        with pytest.raises(ValidationError):
            ApiCompositionConfig(max_concurrent_requests=0)
        with pytest.raises(ValidationError):
            ApiCompositionConfig(default_timeout=0)
        with pytest.raises(ValidationError):
            ApiCompositionConfig(cache_max_size=0)

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ApiCompositionConfig(unknown="x")
