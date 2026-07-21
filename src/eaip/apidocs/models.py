"""API Documentation models — ApiDocConfig, GeneratedDoc, EndpointDoc, DocChangelog."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class DocFormat(StrEnum):
    OPENAPI_JSON = "openapi_json"
    OPENAPI_YAML = "openapi_yaml"
    MARKDOWN = "markdown"
    HTML = "html"


class ApiDocConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str
    version: str
    description: str = ""
    contact: dict[str, Any] = Field(default_factory=dict)
    license: dict[str, Any] = Field(default_factory=dict)
    servers: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    tags: tuple[str, ...] = Field(default_factory=tuple)


class GeneratedDoc(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    source_version: str
    format: DocFormat
    content: str = ""
    generated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EndpointDoc(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    endpoint_path: str
    method: str
    summary: str = ""
    description: str = ""
    parameters: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    request_body: dict[str, Any] = Field(default_factory=dict)
    responses: dict[str, Any] = Field(default_factory=dict)
    tags: tuple[str, ...] = Field(default_factory=tuple)
    deprecated: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocChangelog(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    version: str
    date: datetime = Field(default_factory=utc_now)
    changes: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "ApiDocConfig",
    "DocChangelog",
    "DocFormat",
    "EndpointDoc",
    "GeneratedDoc",
]
