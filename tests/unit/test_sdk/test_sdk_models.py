"""Tests for :mod:`eaip.sdk.models`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.sdk.models import (
    ApiClient,
    BuildStatus,
    ClientStatus,
    EndpointModel,
    SdkBuild,
    SdkConfig,
    SdkDefinition,
    SdkEndpoint,
    SdkStatus,
)


class TestSdkDefinition:
    def test_minimal(self) -> None:
        sdk = SdkDefinition(id="sdk-1", name="MySDK", language="python", version="1.0.0")
        assert sdk.id == "sdk-1"
        assert sdk.name == "MySDK"
        assert sdk.status is SdkStatus.DRAFT
        assert isinstance(sdk.created_at, datetime)
        assert isinstance(sdk.updated_at, datetime)

    def test_frozen(self) -> None:
        sdk = SdkDefinition(id="sdk-1", name="MySDK", language="python", version="1.0.0")
        with pytest.raises(ValueError):
            sdk.name = "other"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValueError):
            SdkDefinition(  # type: ignore[call-arg]
                id="sdk-1",
                name="x",
                language="py",
                version="1",
                unknown="bad",
            )

    def test_with_all_fields(self) -> None:
        sdk = SdkDefinition(
            id="sdk-2",
            name="FullSDK",
            language="javascript",
            version="2.0.0",
            description="A full SDK",
            source_api_version="v2",
            endpoints=("ep-1",),
            models=("mod-1",),
            config={"timeout": 30},
            tags=("stable",),
            metadata={"author": "team"},
            status=SdkStatus.PUBLISHED,
        )
        assert sdk.source_api_version == "v2"
        assert sdk.endpoints == ("ep-1",)
        assert sdk.status is SdkStatus.PUBLISHED


class TestSdkEndpoint:
    def test_minimal(self) -> None:
        ep = SdkEndpoint(id="ep-1", path="/v1/items", method="GET")
        assert ep.auth_required is True
        assert ep.parameters == ()

    def test_frozen(self) -> None:
        ep = SdkEndpoint(id="ep-1", path="/test", method="POST")
        with pytest.raises(ValueError):
            ep.path = "/other"  # type: ignore[misc]

    def test_with_schema(self) -> None:
        ep = SdkEndpoint(
            id="ep-2",
            path="/v1/items",
            method="POST",
            request_schema={"type": "object"},
            response_schema={"type": "array"},
            auth_required=False,
        )
        assert ep.request_schema == {"type": "object"}
        assert ep.auth_required is False


class TestApiClient:
    def test_minimal(self) -> None:
        client = ApiClient(id="cli-1", name="MyApp", sdk_id="sdk-1")
        assert client.status is ClientStatus.ACTIVE
        assert client.client_version == "1.0.0"
        assert isinstance(client.created_at, datetime)

    def test_frozen(self) -> None:
        client = ApiClient(id="cli-1", name="MyApp", sdk_id="sdk-1")
        with pytest.raises(ValueError):
            client.name = "other"  # type: ignore[misc]

    def test_with_expiry(self) -> None:
        now = datetime.now(UTC)
        client = ApiClient(
            id="cli-2",
            name="ExpiringApp",
            sdk_id="sdk-1",
            expires_at=now,
            metadata={"env": "test"},
        )
        assert client.expires_at is not None
        assert client.metadata == {"env": "test"}

    def test_revoked_status(self) -> None:
        client = ApiClient(id="cli-3", name="BadApp", sdk_id="sdk-1", status=ClientStatus.REVOKED)
        assert client.status is ClientStatus.REVOKED


class TestSdkBuild:
    def test_minimal(self) -> None:
        build = SdkBuild(id="bld-1", sdk_id="sdk-1", version="1.0.0")
        assert build.status is BuildStatus.PENDING
        assert build.duration_ms == 0

    def test_completed(self) -> None:
        now = datetime.now(UTC)
        build = SdkBuild(
            id="bld-2",
            sdk_id="sdk-1",
            version="1.0.0",
            status=BuildStatus.COMPLETED,
            started_at=now,
            completed_at=now,
            duration_ms=1500,
            artifact_url="https://example.com/sdk.tar.gz",
            artifact_size_bytes=1024,
        )
        assert build.status is BuildStatus.COMPLETED
        assert build.artifact_size_bytes == 1024

    def test_failed(self) -> None:
        build = SdkBuild(
            id="bld-3",
            sdk_id="sdk-1",
            version="1.0.0",
            status=BuildStatus.FAILED,
            error="Build timeout",
        )
        assert build.error == "Build timeout"


class TestEndpointModel:
    def test_minimal(self) -> None:
        model = EndpointModel(id="mod-1", name="Item")
        assert model.fields == {}
        assert model.description == ""

    def test_with_fields(self) -> None:
        model = EndpointModel(
            id="mod-2",
            name="User",
            fields={"name": "str", "email": "str"},
            description="User model",
        )
        assert model.fields["name"] == "str"
        assert len(model.fields) == 2


class TestSdkConfig:
    def test_defaults(self) -> None:
        config = SdkConfig()
        assert config.max_clients_per_sdk == 100
        assert config.build_timeout_seconds == 300
        assert config.enable_auto_build is True
        assert config.artifact_retention_days == 90
        assert "python" in config.supported_languages
        assert config.default_language == "python"

    def test_custom(self) -> None:
        config = SdkConfig(
            max_clients_per_sdk=50,
            supported_languages=("python", "go"),
            default_language="go",
        )
        assert config.max_clients_per_sdk == 50
        assert config.default_language == "go"
        assert "javascript" not in config.supported_languages
