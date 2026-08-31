"""Tests for MessageTransformationService."""

from __future__ import annotations

import pytest

from eaip.integration.exceptions import TransformationError
from eaip.integration.models import IntegrationMessage, Transformation
from eaip.integration.transform import MessageTransformationService


class TestMessageTransformationService:
    @pytest.fixture
    def service(self) -> MessageTransformationService:
        return MessageTransformationService()

    @pytest.fixture
    def sample_message(self) -> IntegrationMessage:
        return IntegrationMessage(
            id="m1",
            source="sys-a",
            destination="sys-b",
            payload={"name": "Alice", "role": "admin", "age": 30},
        )


class TestTransform(TestMessageTransformationService):
    @pytest.mark.asyncio
    async def test_transform_missing_transformation(
        self, service: MessageTransformationService
    ) -> None:
        m = IntegrationMessage(id="m1", source="a", destination="b")
        with pytest.raises(TransformationError):
            await service.transform(m, ("nonexistent",))

    @pytest.mark.asyncio
    async def test_transform_unknown_type(self, service: MessageTransformationService) -> None:
        t = Transformation(id="t1", name="Bad", type="unknown_type")
        service.register_transformation(t)
        m = IntegrationMessage(id="m1", source="a", destination="b")
        with pytest.raises(TransformationError):
            await service.transform(m, ("t1",))

    @pytest.mark.asyncio
    async def test_transform_disabled_skipped(self, service: MessageTransformationService) -> None:
        t = Transformation(
            id="t1",
            name="Disabled",
            type="mapping",
            config={"field_mapping": {"x": "y"}},
            enabled=False,
        )
        service.register_transformation(t)
        m = IntegrationMessage(id="m1", source="a", destination="b", payload={"x": 1})
        result = await service.transform(m, ("t1",))
        assert result.payload == {"x": 1}

    @pytest.mark.asyncio
    async def test_transform_multiple_chain(self, service: MessageTransformationService) -> None:
        t1 = Transformation(
            id="t1", name="Map", type="mapping", config={"field_mapping": {"name": "full_name"}}
        )
        t2 = Transformation(
            id="t2", name="Enrich", type="enrich", config={"data": {"source": "transformed"}}
        )
        service.register_transformation(t1)
        service.register_transformation(t2)
        m = IntegrationMessage(id="m1", source="a", destination="b", payload={"name": "Alice"})
        result = await service.transform(m, ("t1", "t2"))
        assert "full_name" in result.payload
        assert result.payload["source"] == "transformed"


class TestApplyMapping(TestMessageTransformationService):
    @pytest.mark.asyncio
    async def test_mapping_basic(
        self, service: MessageTransformationService, sample_message: IntegrationMessage
    ) -> None:
        result = await service.apply_mapping(
            sample_message, {"field_mapping": {"name": "full_name"}}
        )
        assert "full_name" in result.payload
        assert "name" not in result.payload

    @pytest.mark.asyncio
    async def test_mapping_empty(
        self, service: MessageTransformationService, sample_message: IntegrationMessage
    ) -> None:
        result = await service.apply_mapping(sample_message, {})
        assert result.payload == sample_message.payload

    @pytest.mark.asyncio
    async def test_mapping_preserves_unmapped(
        self, service: MessageTransformationService, sample_message: IntegrationMessage
    ) -> None:
        result = await service.apply_mapping(
            sample_message, {"field_mapping": {"name": "full_name"}}
        )
        assert result.payload["role"] == "admin"
        assert result.payload["age"] == 30


class TestApplyFilter(TestMessageTransformationService):
    @pytest.mark.asyncio
    async def test_filter_eq_pass(
        self, service: MessageTransformationService, sample_message: IntegrationMessage
    ) -> None:
        result = await service.apply_filter(
            sample_message, {"field": "role", "operator": "eq", "value": "admin"}
        )
        assert "_filtered" not in result.payload

    @pytest.mark.asyncio
    async def test_filter_eq_fail(
        self, service: MessageTransformationService, sample_message: IntegrationMessage
    ) -> None:
        result = await service.apply_filter(
            sample_message, {"field": "role", "operator": "eq", "value": "user"}
        )
        assert result.payload.get("_filtered") is True

    @pytest.mark.asyncio
    async def test_filter_exists_pass(
        self, service: MessageTransformationService, sample_message: IntegrationMessage
    ) -> None:
        result = await service.apply_filter(sample_message, {"field": "name", "operator": "exists"})
        assert "_filtered" not in result.payload

    @pytest.mark.asyncio
    async def test_filter_exists_fail(
        self, service: MessageTransformationService, sample_message: IntegrationMessage
    ) -> None:
        result = await service.apply_filter(
            sample_message, {"field": "missing_field", "operator": "exists"}
        )
        assert result.payload.get("_filtered") is True

    @pytest.mark.asyncio
    async def test_filter_gt_pass(
        self, service: MessageTransformationService, sample_message: IntegrationMessage
    ) -> None:
        result = await service.apply_filter(
            sample_message, {"field": "age", "operator": "gt", "value": 25}
        )
        assert "_filtered" not in result.payload

    @pytest.mark.asyncio
    async def test_filter_gt_fail(
        self, service: MessageTransformationService, sample_message: IntegrationMessage
    ) -> None:
        result = await service.apply_filter(
            sample_message, {"field": "age", "operator": "gt", "value": 35}
        )
        assert result.payload.get("_filtered") is True


class TestApplyEnrichment(TestMessageTransformationService):
    @pytest.mark.asyncio
    async def test_enrich_adds_data(
        self, service: MessageTransformationService, sample_message: IntegrationMessage
    ) -> None:
        result = await service.apply_enrichment(
            sample_message, {"data": {"country": "US", "timezone": "EST"}}
        )
        assert result.payload["country"] == "US"
        assert result.payload["timezone"] == "EST"

    @pytest.mark.asyncio
    async def test_enrich_overwrites(
        self, service: MessageTransformationService, sample_message: IntegrationMessage
    ) -> None:
        result = await service.apply_enrichment(sample_message, {"data": {"name": "Overwritten"}})
        assert result.payload["name"] == "Overwritten"

    @pytest.mark.asyncio
    async def test_enrich_empty(
        self, service: MessageTransformationService, sample_message: IntegrationMessage
    ) -> None:
        result = await service.apply_enrichment(sample_message, {})
        assert result.payload == sample_message.payload


class TestApplyScript(TestMessageTransformationService):
    @pytest.mark.asyncio
    async def test_script_transform(self, service: MessageTransformationService) -> None:
        m = IntegrationMessage(id="m1", source="a", destination="b", payload={"x": 1, "y": 2})
        result = await service.apply_script_transform(
            m,
            {
                "script": "result = {'sum': payload['x'] + payload['y'], 'product': payload['x'] * payload['y']}"
            },
        )
        assert result.payload["sum"] == 3
        assert result.payload["product"] == 2

    @pytest.mark.asyncio
    async def test_script_empty(
        self, service: MessageTransformationService, sample_message: IntegrationMessage
    ) -> None:
        result = await service.apply_script_transform(sample_message, {})
        assert result.payload == sample_message.payload

    @pytest.mark.asyncio
    async def test_script_error(self, service: MessageTransformationService) -> None:
        m = IntegrationMessage(id="m1", source="a", destination="b", payload={})
        with pytest.raises(TransformationError):
            await service.apply_script_transform(m, {"script": "invalid python code !!!"})
