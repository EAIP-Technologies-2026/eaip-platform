"""Tests for :mod:`eaip.sdk.generation`."""

from __future__ import annotations

import pytest

from eaip.sdk.exceptions import LanguageNotSupportedError
from eaip.sdk.generation import SdkGenerator
from eaip.sdk.models import EndpointModel, SdkConfig, SdkDefinition, SdkEndpoint


@pytest.fixture
def generator() -> SdkGenerator:
    return SdkGenerator()


@pytest.fixture
def sample_sdk() -> SdkDefinition:
    return SdkDefinition(
        id="sdk-1",
        name="UserAPI",
        language="python",
        version="1.0.0",
        description="API for managing users",
    )


@pytest.fixture
def sample_endpoints() -> list[SdkEndpoint]:
    return [
        SdkEndpoint(
            id="list-users",
            path="/v1/users",
            method="GET",
            description="List all users",
            parameters=("page", "limit"),
        ),
        SdkEndpoint(
            id="create-user",
            path="/v1/users",
            method="POST",
            description="Create a new user",
            request_schema={"type": "object", "properties": {"name": {"type": "string"}}},
        ),
    ]


class TestSdkGenerator:
    async def test_generate_python_client(
        self,
        generator: SdkGenerator,
        sample_sdk: SdkDefinition,
        sample_endpoints: list[SdkEndpoint],
    ) -> None:
        code = await generator.generate_client(sample_sdk, "python", endpoints=sample_endpoints)
        assert "class UserAPIClient" in code
        assert "def list_users" in code
        assert "def create_user" in code
        assert "def close" in code
        assert "httpx" in code

    async def test_generate_javascript_client(
        self,
        generator: SdkGenerator,
        sample_sdk: SdkDefinition,
        sample_endpoints: list[SdkEndpoint],
    ) -> None:
        code = await generator.generate_client(sample_sdk, "javascript", endpoints=sample_endpoints)
        assert "class UserAPIClient" in code
        assert "listUsers" in code
        assert "createUser" in code

    async def test_generate_java_client(
        self,
        generator: SdkGenerator,
        sample_sdk: SdkDefinition,
        sample_endpoints: list[SdkEndpoint],
    ) -> None:
        code = await generator.generate_client(sample_sdk, "java", endpoints=sample_endpoints)
        assert "class UserAPIClient" in code
        assert "listUsers" in code or "list-users" in code

    async def test_generate_go_client(
        self,
        generator: SdkGenerator,
        sample_sdk: SdkDefinition,
        sample_endpoints: list[SdkEndpoint],
    ) -> None:
        code = await generator.generate_client(sample_sdk, "go", endpoints=sample_endpoints)
        assert "type UserAPIClient struct" in code

    async def test_generate_dotnet_client(
        self,
        generator: SdkGenerator,
        sample_sdk: SdkDefinition,
        sample_endpoints: list[SdkEndpoint],
    ) -> None:
        code = await generator.generate_client(sample_sdk, "dotnet", endpoints=sample_endpoints)
        assert "class UserAPIClient" in code
        assert "namespace" in code

    async def test_unsupported_language(
        self, generator: SdkGenerator, sample_sdk: SdkDefinition
    ) -> None:
        with pytest.raises(LanguageNotSupportedError):
            await generator.generate_client(sample_sdk, "rust")

    async def test_language_not_in_config(
        self, generator: SdkGenerator, sample_sdk: SdkDefinition
    ) -> None:
        restricted_gen = SdkGenerator(config=SdkConfig(supported_languages=("python",)))
        with pytest.raises(LanguageNotSupportedError):
            await restricted_gen.generate_client(sample_sdk, "javascript")

    def test_generate_endpoint_code(
        self, generator: SdkGenerator, sample_endpoints: list[SdkEndpoint]
    ) -> None:
        code = generator.generate_endpoint_code(sample_endpoints[0], "python")
        assert "def list_users" in code
        assert "/v1/users" in code

    def test_generate_endpoint_code_javascript(self, generator: SdkGenerator) -> None:
        ep = SdkEndpoint(id="get-item", path="/v1/items/{id}", method="GET")
        code = generator.generate_endpoint_code(ep, "javascript")
        assert "getItem" in code

    def test_generate_model_code_python(self, generator: SdkGenerator) -> None:
        model = EndpointModel(id="mod-1", name="User", fields={"name": "str", "email": "str"})
        code = generator.generate_model_code(model, "python")
        assert "class User" in code
        assert "name: str" in code

    def test_generate_config_code_from_dict(self, generator: SdkGenerator) -> None:
        code = generator.generate_config_code({"timeout": 30, "retries": 3}, "python")
        assert "SDK_CONFIG" in code
        assert "timeout" in code

    def test_generate_config_code_from_config(self, generator: SdkGenerator) -> None:
        config = SdkConfig(max_clients_per_sdk=50)
        code = generator.generate_config_code(config, "python")
        assert "SDK_CONFIG" in code or "{" in code
