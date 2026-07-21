"""Tests for :mod:`eaip.devplatform.models`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.devplatform.models import (
    ApiEndpoint,
    ApiParameter,
    ApiVersion,
    DeveloperKey,
    DeveloperProfile,
    DeveloperProfileStatus,
    ParameterLocation,
    PlaygroundSession,
    SdkConfig,
    UsageRecord,
    VersionStatus,
)


class TestApiVersion:
    def test_minimal(self) -> None:
        v = ApiVersion(id="v1", version_string="1.0.0")
        assert v.id == "v1"
        assert v.version_string == "1.0.0"
        assert v.status is VersionStatus.ACTIVE
        assert isinstance(v.released_at, datetime)

    def test_frozen(self) -> None:
        v = ApiVersion(id="v1", version_string="1.0.0")
        with pytest.raises(ValueError):
            v.id = "changed"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValueError):
            ApiVersion(id="v1", version_string="1.0.0", bad="x")  # type: ignore[call-arg]

    def test_deprecated_status(self) -> None:
        v = ApiVersion(id="v2", version_string="2.0.0", status=VersionStatus.DEPRECATED)
        assert v.status is VersionStatus.DEPRECATED

    def test_with_sunset_at(self) -> None:
        dt = datetime(2026, 1, 1, tzinfo=UTC)
        v = ApiVersion(id="v3", version_string="3.0.0", sunset_at=dt)
        assert v.sunset_at == dt

    def test_with_metadata(self) -> None:
        v = ApiVersion(id="v4", version_string="4.0.0", metadata={"author": "team"})
        assert v.metadata["author"] == "team"


class TestApiParameter:
    def test_minimal(self) -> None:
        p = ApiParameter(name="id", type="string", location=ParameterLocation.PATH)
        assert p.name == "id"
        assert p.location is ParameterLocation.PATH
        assert p.required is False

    def test_required_param(self) -> None:
        p = ApiParameter(name="q", type="string", location=ParameterLocation.QUERY, required=True)
        assert p.required is True

    def test_with_default(self) -> None:
        p = ApiParameter(name="page", type="integer", location=ParameterLocation.QUERY, default=1)
        assert p.default == 1

    def test_frozen(self) -> None:
        p = ApiParameter(name="id", type="string", location=ParameterLocation.PATH)
        with pytest.raises(ValueError):
            p.name = "other"  # type: ignore[misc]


class TestApiEndpoint:
    def test_minimal(self) -> None:
        e = ApiEndpoint(id="e1", path="/v1/users", method="GET", version="1.0.0")
        assert e.id == "e1"
        assert e.auth_required is True
        assert e.rate_limit == 100

    def test_with_parameters(self) -> None:
        p = ApiParameter(name="id", type="string", location=ParameterLocation.PATH, required=True)
        e = ApiEndpoint(
            id="e2", path="/v1/users/{id}", method="GET", version="1.0.0", parameters=(p,)
        )
        assert len(e.parameters) == 1
        assert e.parameters[0].name == "id"

    def test_frozen(self) -> None:
        e = ApiEndpoint(id="e1", path="/test", method="GET", version="1.0.0")
        with pytest.raises(ValueError):
            e.path = "/other"  # type: ignore[misc]


class TestDeveloperKey:
    def test_minimal(self) -> None:
        k = DeveloperKey(
            id="k1", name="My Key", key_prefix="abc123", key_hash="hash", developer_id="d1"
        )
        assert k.enabled is True
        assert isinstance(k.created_at, datetime)

    def test_frozen(self) -> None:
        k = DeveloperKey(id="k1", name="K", key_prefix="pre", key_hash="h", developer_id="d1")
        with pytest.raises(ValueError):
            k.name = "Other"  # type: ignore[misc]

    def test_with_permissions(self) -> None:
        k = DeveloperKey(
            id="k2",
            name="Admin Key",
            key_prefix="xyz",
            key_hash="h2",
            developer_id="d2",
            permissions=("read", "write"),
        )
        assert "read" in k.permissions

    def test_with_expiry(self) -> None:
        dt = datetime(2025, 12, 31, tzinfo=UTC)
        k = DeveloperKey(
            id="k3", name="Temp", key_prefix="tmp", key_hash="h3", developer_id="d3", expires_at=dt
        )
        assert k.expires_at == dt

    def test_disabled(self) -> None:
        k = DeveloperKey(
            id="k4", name="Off", key_prefix="off", key_hash="h4", developer_id="d4", enabled=False
        )
        assert k.enabled is False


class TestUsageRecord:
    def test_minimal(self) -> None:
        r = UsageRecord(id="r1", developer_id="d1", api_version="1.0.0", endpoint="/users")
        assert r.status_code == 200
        assert r.response_time_ms == 0.0

    def test_frozen(self) -> None:
        r = UsageRecord(id="r1", developer_id="d1", api_version="1.0.0", endpoint="/users")
        with pytest.raises(ValueError):
            r.id = "other"  # type: ignore[misc]

    def test_with_full_data(self) -> None:
        r = UsageRecord(
            id="r2",
            developer_id="d2",
            api_version="2.0.0",
            endpoint="/items",
            response_time_ms=150.5,
            status_code=200,
            bytes_sent=100,
            bytes_received=300,
        )
        assert r.response_time_ms == 150.5
        assert r.bytes_received == 300

    def test_error_status(self) -> None:
        r = UsageRecord(
            id="r3", developer_id="d1", api_version="1.0.0", endpoint="/users", status_code=500
        )
        assert r.status_code == 500


class TestDeveloperProfile:
    def test_minimal(self) -> None:
        p = DeveloperProfile(id="d1", name="Alice", email="alice@example.com")
        assert p.status is DeveloperProfileStatus.ACTIVE
        assert p.keys == ()

    def test_frozen(self) -> None:
        p = DeveloperProfile(id="d1", name="Alice", email="a@b.com")
        with pytest.raises(ValueError):
            p.name = "Bob"  # type: ignore[misc]

    def test_suspended(self) -> None:
        p = DeveloperProfile(
            id="d2", name="Bob", email="bob@c.com", status=DeveloperProfileStatus.SUSPENDED
        )
        assert p.status is DeveloperProfileStatus.SUSPENDED

    def test_with_applications(self) -> None:
        p = DeveloperProfile(
            id="d3",
            name="Charlie",
            email="c@d.com",
            applications=("app1", "app2"),
        )
        assert len(p.applications) == 2


class TestPlaygroundSession:
    def test_minimal(self) -> None:
        s = PlaygroundSession(id="s1", developer_id="d1", endpoint_id="e1")
        assert isinstance(s.created_at, datetime)
        assert s.request_preview == {}

    def test_frozen(self) -> None:
        s = PlaygroundSession(id="s1", developer_id="d1", endpoint_id="e1")
        with pytest.raises(ValueError):
            s.id = "other"  # type: ignore[misc]

    def test_with_previews(self) -> None:
        s = PlaygroundSession(
            id="s2",
            developer_id="d1",
            endpoint_id="e2",
            request_preview={"query": "test"},
            response_preview={"data": "ok"},
        )
        assert s.request_preview["query"] == "test"
        assert s.response_preview["data"] == "ok"

    def test_last_activity_defaults(self) -> None:
        s = PlaygroundSession(id="s3", developer_id="d1", endpoint_id="e1")
        assert isinstance(s.last_activity, datetime)


class TestSdkConfig:
    def test_defaults(self) -> None:
        c = SdkConfig()
        assert c.default_rate_limit == 100
        assert c.max_keys_per_developer == 10
        assert c.key_expiry_days == 365
        assert c.enable_playground is True
        assert c.enable_analytics is True

    def test_custom(self) -> None:
        c = SdkConfig(
            default_rate_limit=50,
            max_keys_per_developer=5,
            key_expiry_days=180,
            enable_playground=False,
            playground_timeout_minutes=15,
            usage_retention_days=30,
            enable_analytics=False,
        )
        assert c.default_rate_limit == 50
        assert c.enable_playground is False
        assert c.usage_retention_days == 30

    def test_frozen(self) -> None:
        c = SdkConfig()
        with pytest.raises(ValueError):
            c.default_rate_limit = 200  # type: ignore[misc]
