"""Tests for integration models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.integration.models import (
    ConnectorDefinition,
    IntegrationConfig,
    IntegrationMessage,
    MessageRoute,
    Transformation,
    WebhookRegistration,
)


class TestConnectorDefinition:
    def test_minimal(self) -> None:
        c = ConnectorDefinition(
            id="c1", name="HTTP Out", type="http", endpoint_url="https://api.example.com"
        )
        assert c.id == "c1"
        assert c.type == "http"
        assert c.enabled is True
        assert c.max_retries == 3
        assert c.timeout_seconds == 30

    def test_frozen(self) -> None:
        c = ConnectorDefinition(id="c1", name="C1", type="http", endpoint_url="https://ex.com")
        with pytest.raises(ValidationError):
            c.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ConnectorDefinition(
                id="c1", name="C1", type="http", endpoint_url="https://ex.com", unknown=True
            )

    def test_all_types(self) -> None:
        for t in ("http", "webhook", "mq", "grpc", "custom"):
            c = ConnectorDefinition(id=f"c_{t}", name=t, type=t, endpoint_url="https://ex.com")
            assert c.type == t

    def test_custom_fields(self) -> None:
        c = ConnectorDefinition(
            id="c1",
            name="C1",
            type="http",
            endpoint_url="https://ex.com",
            auth_config={"api_key": "xxx"},
            config={"retry_delay": 5},
            enabled=False,
            tags=("prod", "critical"),
            metadata={"owner": "team-a"},
            max_retries=5,
            timeout_seconds=60,
        )
        assert c.auth_config == {"api_key": "xxx"}
        assert c.config == {"retry_delay": 5}
        assert c.enabled is False
        assert c.tags == ("prod", "critical")
        assert c.metadata == {"owner": "team-a"}
        assert c.max_retries == 5
        assert c.timeout_seconds == 60


class TestIntegrationMessage:
    def test_minimal(self) -> None:
        m = IntegrationMessage(id="m1", source="sys-a", destination="sys-b")
        assert m.content_type == "application/json"
        assert m.headers == {}
        assert m.payload == {}
        assert m.correlation_id == ""

    def test_frozen(self) -> None:
        m = IntegrationMessage(id="m1", source="a", destination="b")
        with pytest.raises(ValidationError):
            m.source = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            IntegrationMessage(id="m1", source="a", destination="b", bad=True)

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        m = IntegrationMessage(
            id="m1",
            source="sys-a",
            destination="sys-b",
            headers={"trace": "abc"},
            payload={"order_id": "123"},
            content_type="application/xml",
            correlation_id="corr-1",
            timestamp=ts,
            metadata={"env": "prod"},
        )
        assert m.headers == {"trace": "abc"}
        assert m.payload == {"order_id": "123"}
        assert m.content_type == "application/xml"
        assert m.correlation_id == "corr-1"
        assert m.timestamp == ts
        assert m.metadata == {"env": "prod"}


class TestMessageRoute:
    def test_minimal(self) -> None:
        r = MessageRoute(
            id="r1", name="Route1", source_pattern="sys-a", destination_pattern="sys-b"
        )
        assert r.transformation_ids == ()
        assert r.enabled is True
        assert r.priority == 0
        assert r.error_handling == "discard"

    def test_frozen(self) -> None:
        r = MessageRoute(id="r1", name="R1", source_pattern="a", destination_pattern="b")
        with pytest.raises(ValidationError):
            r.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            MessageRoute(id="r1", name="R1", source_pattern="a", destination_pattern="b", bad=True)

    def test_full(self) -> None:
        r = MessageRoute(
            id="r1",
            name="Full Route",
            source_pattern="orders.*",
            destination_pattern="warehouse",
            transformation_ids=("t1", "t2"),
            enabled=False,
            priority=10,
            error_handling="dead_letter",
            filter_expression="status == 'active'",
        )
        assert r.transformation_ids == ("t1", "t2")
        assert r.enabled is False
        assert r.priority == 10
        assert r.error_handling == "dead_letter"
        assert r.filter_expression == "status == 'active'"

    def test_all_error_handlings(self) -> None:
        for eh in ("discard", "retry", "dead_letter"):
            r = MessageRoute(
                id="r1", name="R1", source_pattern="a", destination_pattern="b", error_handling=eh
            )
            assert r.error_handling == eh


class TestTransformation:
    def test_minimal(self) -> None:
        t = Transformation(id="t1", name="MapFields", type="mapping")
        assert t.config == {}
        assert t.input_schema == {}
        assert t.output_schema == {}
        assert t.enabled is True

    def test_frozen(self) -> None:
        t = Transformation(id="t1", name="T1", type="mapping")
        with pytest.raises(ValidationError):
            t.type = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            Transformation(id="t1", name="T1", type="mapping", bad=True)

    def test_all_types(self) -> None:
        for typ in ("mapping", "filter", "enrich", "script"):
            t = Transformation(id=f"t_{typ}", name=typ, type=typ)
            assert t.type == typ

    def test_full(self) -> None:
        t = Transformation(
            id="t1",
            name="Full",
            type="enrich",
            config={"data": {"source": "external"}},
            input_schema={"field": "string"},
            output_schema={"field": "string"},
            enabled=False,
        )
        assert t.config == {"data": {"source": "external"}}
        assert t.input_schema == {"field": "string"}
        assert t.enabled is False


class TestWebhookRegistration:
    def test_minimal(self) -> None:
        w = WebhookRegistration(id="w1", name="Webhook1", url="https://hooks.example.com")
        assert w.secret == ""
        assert w.events == ()
        assert w.enabled is True
        assert w.call_count == 0

    def test_frozen(self) -> None:
        w = WebhookRegistration(id="w1", name="W1", url="https://ex.com")
        with pytest.raises(ValidationError):
            w.url = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            WebhookRegistration(id="w1", name="W1", url="https://ex.com", bad=True)

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        w = WebhookRegistration(
            id="w1",
            name="Webhook1",
            url="https://hooks.example.com",
            secret="s3cret",
            events=("order.created", "order.updated"),
            enabled=False,
            created_at=ts,
            last_called_at=ts,
            call_count=42,
            metadata={"env": "prod"},
        )
        assert w.secret == "s3cret"
        assert w.events == ("order.created", "order.updated")
        assert w.enabled is False
        assert w.created_at == ts
        assert w.last_called_at == ts
        assert w.call_count == 42
        assert w.metadata == {"env": "prod"}


class TestIntegrationConfig:
    def test_defaults(self) -> None:
        c = IntegrationConfig()
        assert c.max_message_size_bytes == 1_048_576
        assert c.default_timeout_seconds == 30
        assert c.max_retries == 3
        assert c.enable_dead_letter is True
        assert c.dead_letter_retention_days == 7
        assert c.enable_audit_logging is True

    def test_custom(self) -> None:
        c = IntegrationConfig(
            max_message_size_bytes=2_097_152,
            default_timeout_seconds=60,
            max_retries=5,
            enable_dead_letter=False,
            dead_letter_retention_days=14,
            enable_audit_logging=False,
        )
        assert c.max_message_size_bytes == 2_097_152
        assert c.default_timeout_seconds == 60
        assert c.max_retries == 5
        assert c.enable_dead_letter is False
        assert c.dead_letter_retention_days == 14
        assert c.enable_audit_logging is False

    def test_frozen(self) -> None:
        c = IntegrationConfig()
        with pytest.raises(ValidationError):
            c.max_retries = 10

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            IntegrationConfig(unknown=True)
