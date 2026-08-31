"""Tests for API Documentation models."""

from __future__ import annotations

import pytest

from eaip.apidocs.models import ApiDocConfig, DocChangelog, DocFormat, EndpointDoc, GeneratedDoc


class TestApiDocConfig:
    def test_required_fields(self) -> None:
        cfg = ApiDocConfig(title="My API", version="1.0.0")
        assert cfg.title == "My API"
        assert cfg.version == "1.0.0"
        assert cfg.servers == ()
        assert cfg.tags == ()

    def test_with_all_fields(self) -> None:
        cfg = ApiDocConfig(
            title="My API",
            version="2.0.0",
            description="An API",
            contact={"name": "Test", "email": "test@example.com"},
            license={"name": "MIT"},
            servers=({"url": "https://api.example.com"},),
            tags=("users", "admin"),
        )
        assert cfg.contact["name"] == "Test"
        assert len(cfg.servers) == 1

    def test_frozen(self) -> None:
        cfg = ApiDocConfig(title="T", version="1")
        with pytest.raises(ValueError):
            cfg.title = "changed"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            ApiDocConfig(title="T", version="1", unknown=True)  # type: ignore[call-arg]


class TestGeneratedDoc:
    def test_required_fields(self) -> None:
        doc = GeneratedDoc(id="doc_1", source_version="1.0.0", format=DocFormat.OPENAPI_JSON)
        assert doc.id == "doc_1"
        assert doc.source_version == "1.0.0"
        assert doc.format is DocFormat.OPENAPI_JSON

    def test_frozen(self) -> None:
        doc = GeneratedDoc(id="d1", source_version="1", format=DocFormat.MARKDOWN)
        with pytest.raises(ValueError):
            doc.format = DocFormat.HTML


class TestEndpointDoc:
    def test_required_fields(self) -> None:
        ep = EndpointDoc(id="ep_1", endpoint_path="/users", method="GET")
        assert ep.endpoint_path == "/users"
        assert ep.method == "GET"
        assert ep.deprecated is False

    def test_with_all_fields(self) -> None:
        ep = EndpointDoc(
            id="ep_1",
            endpoint_path="/users/{id}",
            method="GET",
            summary="Get user by ID",
            description="Returns a single user",
            parameters=({"name": "id", "in": "path"},),
            request_body={},
            responses={"200": {"description": "OK"}},
            tags=("users",),
            deprecated=True,
            metadata={"since": "v1"},
        )
        assert ep.deprecated is True
        assert len(ep.responses) == 1

    def test_frozen(self) -> None:
        ep = EndpointDoc(id="e1", endpoint_path="/test", method="GET")
        with pytest.raises(ValueError):
            ep.method = "POST"


class TestDocChangelog:
    def test_required_fields(self) -> None:
        cl = DocChangelog(id="cl_1", version="1.1.0")
        assert cl.version == "1.1.0"
        assert cl.changes == ()

    def test_with_changes(self) -> None:
        cl = DocChangelog(id="cl_1", version="2.0.0", changes=("Added new endpoint", "Fixed bug"))
        assert len(cl.changes) == 2

    def test_frozen(self) -> None:
        cl = DocChangelog(id="c1", version="1")
        with pytest.raises(ValueError):
            cl.version = "2"
