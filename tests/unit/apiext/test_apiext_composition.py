"""Tests for :mod:`eaip.apiext.composition`."""

from __future__ import annotations

import pytest

from eaip.apiext.composition import ApiComposer
from eaip.apiext.exceptions import CompositionError
from eaip.apiext.models import ApiComposition, MergeStrategy


class TestApiComposer:
    @pytest.fixture
    def composer(self) -> ApiComposer:
        return ApiComposer()

    @pytest.fixture
    def sample_composition(self) -> ApiComposition:
        return ApiComposition(
            id="comp-1",
            name="Test Composition",
            endpoint_path="/api/composed",
            method="GET",
            source_endpoints=("/api/a", "/api/b"),
        )

    def test_register_composition(
        self, composer: ApiComposer, sample_composition: ApiComposition
    ) -> None:
        composer.register_composition(sample_composition)
        assert composer.get_composition("comp-1") == sample_composition

    def test_register_duplicate_raises(
        self, composer: ApiComposer, sample_composition: ApiComposition
    ) -> None:
        composer.register_composition(sample_composition)
        with pytest.raises(CompositionError):
            composer.register_composition(sample_composition)

    def test_unregister_composition(
        self, composer: ApiComposer, sample_composition: ApiComposition
    ) -> None:
        composer.register_composition(sample_composition)
        composer.unregister_composition("comp-1")
        assert composer.get_composition("comp-1") is None

    def test_unregister_nonexistent_raises(self, composer: ApiComposer) -> None:
        with pytest.raises(CompositionError):
            composer.unregister_composition("nonexistent")

    def test_get_composition_returns_none(self, composer: ApiComposer) -> None:
        assert composer.get_composition("nonexistent") is None

    def test_list_compositions_empty(self, composer: ApiComposer) -> None:
        assert composer.list_compositions() == []

    def test_list_compositions(
        self, composer: ApiComposer, sample_composition: ApiComposition
    ) -> None:
        composer.register_composition(sample_composition)
        comps = composer.list_compositions()
        assert len(comps) == 1
        assert comps[0].id == "comp-1"

    async def test_execute_composition_concat(
        self, composer: ApiComposer, sample_composition: ApiComposition
    ) -> None:
        composer.register_composition(sample_composition)
        result = await composer.execute_composition(sample_composition)
        assert "source_0" in result
        assert "source_1" in result
        assert result["source_0"]["source"] == "/api/a"
        assert result["source_1"]["source"] == "/api/b"

    async def test_execute_composition_merge(self, composer: ApiComposer) -> None:
        comp = ApiComposition(
            id="comp-merge",
            name="Merge Test",
            endpoint_path="/api/merged",
            method="GET",
            source_endpoints=("/api/a", "/api/b"),
            merge_strategy=MergeStrategy.MERGE,
        )
        composer.register_composition(comp)
        result = await composer.execute_composition(comp)
        assert "source" in result
        assert "context" in result

    async def test_execute_composition_chain(self, composer: ApiComposer) -> None:
        comp = ApiComposition(
            id="comp-chain",
            name="Chain Test",
            endpoint_path="/api/chained",
            method="GET",
            source_endpoints=("/api/a", "/api/b"),
            merge_strategy=MergeStrategy.CHAIN,
        )
        composer.register_composition(comp)
        result = await composer.execute_composition(comp)
        assert "source" in result

    async def test_execute_composition_zip(self, composer: ApiComposer) -> None:
        comp = ApiComposition(
            id="comp-zip",
            name="Zip Test",
            endpoint_path="/api/zipped",
            method="GET",
            source_endpoints=("/api/a", "/api/b"),
            merge_strategy=MergeStrategy.ZIP,
        )
        composer.register_composition(comp)
        result = await composer.execute_composition(comp)
        assert result is not None

    async def test_execute_disabled_composition_raises(self, composer: ApiComposer) -> None:
        comp = ApiComposition(
            id="comp-disabled",
            name="Disabled",
            endpoint_path="/api/disabled",
            method="GET",
            source_endpoints=("/api/a",),
            enabled=False,
        )
        composer.register_composition(comp)
        with pytest.raises(CompositionError):
            await composer.execute_composition(comp)

    async def test_execute_with_response_mapping(self, composer: ApiComposer) -> None:
        comp = ApiComposition(
            id="comp-mapped",
            name="Mapped",
            endpoint_path="/api/mapped",
            method="GET",
            source_endpoints=("/api/a",),
            response_mapping={"source_0": "data"},
        )
        composer.register_composition(comp)
        result = await composer.execute_composition(comp)
        assert "data" in result
        assert "source_0" not in result

    async def test_execute_with_request_context(self, composer: ApiComposer) -> None:
        comp = ApiComposition(
            id="comp-ctx",
            name="Context Test",
            endpoint_path="/api/ctx",
            method="GET",
            source_endpoints=("/api/a",),
        )
        composer.register_composition(comp)
        result = await composer.execute_composition(comp, {"user": "test"})
        assert result["source_0"]["context"] == {"user": "test"}

    def test_merge_results_concat(self, composer: ApiComposer) -> None:
        results = [{"a": 1}, {"b": 2}]
        merged = composer._merge_results(results, MergeStrategy.CONCAT)
        assert merged["source_0"] == {"a": 1}
        assert merged["source_1"] == {"b": 2}

    def test_merge_results_merge(self, composer: ApiComposer) -> None:
        results = [{"a": 1}, {"b": 2}]
        merged = composer._merge_results(results, MergeStrategy.MERGE)
        assert merged == {"a": 1, "b": 2}

    def test_merge_results_chain(self, composer: ApiComposer) -> None:
        results = [{"a": 1, "c": 3}, {"b": 2}]
        merged = composer._merge_results(results, MergeStrategy.CHAIN)
        assert merged == {"a": 1, "c": 3, "b": 2}

    def test_apply_mapping(self, composer: ApiComposer) -> None:
        data = {"old_key": "value", "other": 42}
        mapped = composer._apply_mapping(data, {"old_key": "new_key"})
        assert mapped == {"new_key": "value"}
