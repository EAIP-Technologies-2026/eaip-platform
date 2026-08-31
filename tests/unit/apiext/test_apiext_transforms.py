"""Tests for :mod:`eaip.apiext.transforms`."""

from __future__ import annotations

import pytest

from eaip.apiext.exceptions import TransformError
from eaip.apiext.models import ResponseTransform
from eaip.apiext.transforms import ResponseTransformer


class TestResponseTransformer:
    @pytest.fixture
    def transformer(self) -> ResponseTransformer:
        return ResponseTransformer()

    @pytest.fixture
    def sample_transform(self) -> ResponseTransform:
        return ResponseTransform(
            id="tf-1",
            name="Remove SSN",
            endpoint_pattern="/api/**",
            transformations=("remove_field:ssn",),
        )

    def test_register_transform(
        self, transformer: ResponseTransformer, sample_transform: ResponseTransform
    ) -> None:
        transformer.register_transform(sample_transform)
        assert transformer.get_transform("tf-1") == sample_transform

    def test_register_duplicate_raises(
        self, transformer: ResponseTransformer, sample_transform: ResponseTransform
    ) -> None:
        transformer.register_transform(sample_transform)
        with pytest.raises(TransformError):
            transformer.register_transform(sample_transform)

    def test_unregister_transform(
        self, transformer: ResponseTransformer, sample_transform: ResponseTransform
    ) -> None:
        transformer.register_transform(sample_transform)
        transformer.unregister_transform("tf-1")
        assert transformer.get_transform("tf-1") is None

    def test_unregister_nonexistent_raises(self, transformer: ResponseTransformer) -> None:
        with pytest.raises(TransformError):
            transformer.unregister_transform("nonexistent")

    def test_list_transforms_empty(self, transformer: ResponseTransformer) -> None:
        assert transformer.list_transforms() == []

    def test_list_transforms(
        self, transformer: ResponseTransformer, sample_transform: ResponseTransform
    ) -> None:
        transformer.register_transform(sample_transform)
        transforms = transformer.list_transforms()
        assert len(transforms) == 1

    async def test_apply_rename_field(self, transformer: ResponseTransformer) -> None:
        tf = ResponseTransform(
            id="tf-rename",
            name="Rename",
            endpoint_pattern="/api/**",
            transformations=("rename_field:old_name:new_name",),
        )
        transformer.register_transform(tf)
        result = await transformer.apply_transforms(
            {"body": {"old_name": "value", "other": 42}, "headers": {}},
            "/api/v1/data",
        )
        assert "new_name" in result["body"]
        assert "old_name" not in result["body"]

    async def test_apply_remove_field(self, transformer: ResponseTransformer) -> None:
        tf = ResponseTransform(
            id="tf-remove",
            name="Remove",
            endpoint_pattern="/api/**",
            transformations=("remove_field:ssn",),
        )
        transformer.register_transform(tf)
        result = await transformer.apply_transforms(
            {"body": {"ssn": "123-45-6789", "name": "Alice"}, "headers": {}},
            "/api/v1/users",
        )
        assert "ssn" not in result["body"]
        assert "name" in result["body"]

    async def test_apply_set_header(self, transformer: ResponseTransformer) -> None:
        tf = ResponseTransform(
            id="tf-header",
            name="Add Header",
            endpoint_pattern="/api/**",
            transformations=("set_header:X-Custom:value123",),
        )
        transformer.register_transform(tf)
        result = await transformer.apply_transforms(
            {"body": {}, "headers": {}},
            "/api/v1/test",
        )
        assert result["headers"].get("X-Custom") == "value123"

    async def test_apply_remove_header(self, transformer: ResponseTransformer) -> None:
        tf = ResponseTransform(
            id="tf-rm-header",
            name="Remove Header",
            endpoint_pattern="/api/**",
            transformations=("remove_header:X-Internal",),
        )
        transformer.register_transform(tf)
        result = await transformer.apply_transforms(
            {"body": {}, "headers": {"X-Internal": "secret", "Content-Type": "json"}},
            "/api/v1/test",
        )
        assert "X-Internal" not in result["headers"]
        assert "Content-Type" in result["headers"]

    async def test_apply_map_status(self, transformer: ResponseTransformer) -> None:
        tf = ResponseTransform(
            id="tf-status",
            name="Map Status",
            endpoint_pattern="/api/**",
            transformations=("map_status:404:200",),
        )
        transformer.register_transform(tf)
        result = await transformer.apply_transforms(
            {"body": {}, "headers": {}, "status_code": 404},
            "/api/v1/test",
        )
        assert result["status_code"] == 200

    async def test_apply_filter_body(self, transformer: ResponseTransformer) -> None:
        tf = ResponseTransform(
            id="tf-filter",
            name="Filter Body",
            endpoint_pattern="/api/**",
            transformations=("filter_body:id,name",),
        )
        transformer.register_transform(tf)
        result = await transformer.apply_transforms(
            {"body": {"id": 1, "name": "Alice", "ssn": "secret"}, "headers": {}},
            "/api/v1/users",
        )
        assert set(result["body"].keys()) == {"id", "name"}

    async def test_pattern_matching_exact(self, transformer: ResponseTransformer) -> None:
        tf = ResponseTransform(
            id="tf-exact",
            name="Exact",
            endpoint_pattern="/api/v1/exact",
            transformations=("remove_field:x",),
        )
        transformer.register_transform(tf)
        result = await transformer.apply_transforms(
            {"body": {"x": 1}, "headers": {}},
            "/api/v1/exact",
        )
        assert "x" not in result["body"]

    async def test_pattern_no_match(self, transformer: ResponseTransformer) -> None:
        tf = ResponseTransform(
            id="tf-nomatch",
            name="No Match",
            endpoint_pattern="/api/v1/other",
            transformations=("remove_field:x",),
        )
        transformer.register_transform(tf)
        result = await transformer.apply_transforms(
            {"body": {"x": 1}, "headers": {}},
            "/api/v1/test",
        )
        assert "x" in result["body"]

    async def test_priority_order(self, transformer: ResponseTransformer) -> None:
        tf_low = ResponseTransform(
            id="tf-low",
            name="Low",
            endpoint_pattern="/api/**",
            transformations=("remove_field:a",),
            priority=0,
        )
        tf_high = ResponseTransform(
            id="tf-high",
            name="High",
            endpoint_pattern="/api/**",
            transformations=("rename_field:a:b",),
            priority=100,
        )
        transformer.register_transform(tf_low)
        transformer.register_transform(tf_high)
        result = await transformer.apply_transforms(
            {"body": {"a": 1}, "headers": {}},
            "/api/v1/data",
        )
        assert "b" in result["body"]
