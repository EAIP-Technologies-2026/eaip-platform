"""Tests for DocGenerator."""

from __future__ import annotations

import pytest

from eaip.apidocs.generator import DocGenerator
from eaip.apidocs.models import ApiDocConfig, EndpointDoc


class TestDocGenerator:
    @pytest.fixture
    def generator(self) -> DocGenerator:
        return DocGenerator()

    def test_register_endpoint_doc(self) -> None:
        gen = DocGenerator()
        ep = EndpointDoc(id="ep_1", endpoint_path="/users", method="GET", summary="List users")
        result = gen.register_endpoint_doc(ep)
        assert result.id == "ep_1"

    def test_get_endpoint_docs(self) -> None:
        gen = DocGenerator()
        ep1 = EndpointDoc(id="ep_1", endpoint_path="/users", method="GET")
        ep2 = EndpointDoc(id="ep_2", endpoint_path="/items", method="POST")
        gen.register_endpoint_doc(ep1)
        gen.register_endpoint_doc(ep2)
        docs = gen.get_endpoint_docs()
        assert len(docs) == 2

    def test_get_endpoint_docs_empty(self) -> None:
        gen = DocGenerator()
        docs = gen.get_endpoint_docs()
        assert docs == []

    def test_remove_endpoint_doc(self) -> None:
        gen = DocGenerator()
        ep = EndpointDoc(id="ep_1", endpoint_path="/users", method="GET")
        gen.register_endpoint_doc(ep)
        gen.remove_endpoint_doc("ep_1")
        assert gen.get_endpoint_docs() == []

    @pytest.mark.asyncio
    async def test_generate_openapi(self) -> None:
        gen = DocGenerator()
        ep = EndpointDoc(
            id="ep_1",
            endpoint_path="/users",
            method="GET",
            summary="List users",
            description="Returns all users",
            parameters=({"name": "page", "in": "query"},),
            responses={"200": {"description": "OK"}},
            tags=("users",),
        )
        gen.register_endpoint_doc(ep)
        spec = await gen.generate_openapi()
        assert spec["openapi"] == "3.0.3"
        assert spec["info"]["title"] == "API"
        assert "/users" in spec["paths"]
        assert "get" in spec["paths"]["/users"]

    @pytest.mark.asyncio
    async def test_generate_openapi_no_endpoints(self) -> None:
        gen = DocGenerator()
        spec = await gen.generate_openapi()
        assert spec["paths"] == {}

    @pytest.mark.asyncio
    async def test_generate_openapi_with_config(self) -> None:
        cfg = ApiDocConfig(
            title="Custom API",
            version="2.0.0",
            description="Custom description",
            servers=({"url": "https://api.custom.com"},),
        )
        gen = DocGenerator(config=cfg)
        ep = EndpointDoc(id="ep_1", endpoint_path="/test", method="GET")
        gen.register_endpoint_doc(ep)
        spec = await gen.generate_openapi()
        assert spec["info"]["title"] == "Custom API"
        assert spec["info"]["version"] == "2.0.0"
        assert len(spec["servers"]) == 1

    @pytest.mark.asyncio
    async def test_generate_openapi_deprecated_endpoint(self) -> None:
        gen = DocGenerator()
        ep = EndpointDoc(id="ep_1", endpoint_path="/old", method="GET", deprecated=True)
        gen.register_endpoint_doc(ep)
        spec = await gen.generate_openapi()
        assert spec["paths"]["/old"]["get"]["deprecated"] is True

    @pytest.mark.asyncio
    async def test_generate_markdown(self) -> None:
        gen = DocGenerator()
        ep = EndpointDoc(
            id="ep_1",
            endpoint_path="/users",
            method="GET",
            summary="List users",
            description="Returns all users",
            parameters=({"name": "page", "in": "query"},),
        )
        gen.register_endpoint_doc(ep)
        md = await gen.generate_markdown()
        assert "# API" in md
        assert "GET" in md
        assert "/users" in md
        assert "List users" in md

    @pytest.mark.asyncio
    async def test_generate_markdown_no_endpoints(self) -> None:
        gen = DocGenerator()
        md = await gen.generate_markdown()
        assert "## Endpoints" in md

    @pytest.mark.asyncio
    async def test_generate_markdown_deprecated(self) -> None:
        gen = DocGenerator()
        ep = EndpointDoc(id="ep_1", endpoint_path="/old", method="DELETE", deprecated=True)
        gen.register_endpoint_doc(ep)
        md = await gen.generate_markdown()
        assert "deprecated" in md
