from __future__ import annotations

import pytest

from eaip.datapipeline.exceptions import DataValidationError, StepExecutionError
from eaip.datapipeline.models import DataRecord, PipelineStep, StepType
from eaip.datapipeline.steps import StepExecutor


class TestTransformStep:
    @pytest.fixture
    def executor(self) -> StepExecutor:
        return StepExecutor()

    @pytest.fixture
    def record(self) -> DataRecord:
        return DataRecord(
            id="rec1",
            data={"name": "alice", "age": 30, "city": "nyc"},
            source="test",
        )

    @pytest.mark.asyncio
    async def test_transform_with_mapping(
        self,
        executor: StepExecutor,
        record: DataRecord,
    ) -> None:
        step = PipelineStep(
            id="st1",
            name="rename",
            type=StepType.TRANSFORM,
            config={"mapping": {"full_name": "name", "age_years": "age"}},
        )
        result = await executor.execute_transform(step, record, {})
        assert result.data["full_name"] == "alice"
        assert result.data["age_years"] == 30
        assert "name" not in result.data

    @pytest.mark.asyncio
    async def test_transform_empty_mapping(
        self,
        executor: StepExecutor,
        record: DataRecord,
    ) -> None:
        step = PipelineStep(id="st1", name="empty", type=StepType.TRANSFORM)
        result = await executor.execute_transform(step, record, {})
        assert result.data == {}


class TestFilterStep:
    @pytest.fixture
    def executor(self) -> StepExecutor:
        return StepExecutor()

    @pytest.fixture
    def record(self) -> DataRecord:
        return DataRecord(id="rec1", data={"age": 25, "name": "bob"}, source="test")

    @pytest.mark.asyncio
    async def test_filter_eq_pass(
        self,
        executor: StepExecutor,
        record: DataRecord,
    ) -> None:
        step = PipelineStep(
            id="st1",
            name="adult",
            type=StepType.FILTER,
            config={"condition": {"field": "age", "operator": "gte", "value": 18}},
        )
        result = await executor.execute_filter(step, record, {})
        assert result is not None

    @pytest.mark.asyncio
    async def test_filter_eq_fail(
        self,
        executor: StepExecutor,
        record: DataRecord,
    ) -> None:
        step = PipelineStep(
            id="st1",
            name="minor",
            type=StepType.FILTER,
            config={"condition": {"field": "age", "operator": "lt", "value": 18}},
        )
        result = await executor.execute_filter(step, record, {})
        assert result is None

    @pytest.mark.asyncio
    async def test_filter_no_condition(
        self,
        executor: StepExecutor,
        record: DataRecord,
    ) -> None:
        step = PipelineStep(id="st1", name="noop", type=StepType.FILTER)
        result = await executor.execute_filter(step, record, {})
        assert result is not None


class TestValidateStep:
    @pytest.fixture
    def executor(self) -> StepExecutor:
        return StepExecutor()

    @pytest.fixture
    def record(self) -> DataRecord:
        return DataRecord(id="rec1", data={"name": "alice", "age": 25}, source="test")

    @pytest.mark.asyncio
    async def test_validate_required_pass(
        self,
        executor: StepExecutor,
        record: DataRecord,
    ) -> None:
        step = PipelineStep(
            id="st1",
            name="validate",
            type=StepType.VALIDATE,
            config={"rules": [{"field": "name", "type": "required"}]},
        )
        result = await executor.execute_validate(step, record, {})
        assert result.data["name"] == "alice"

    @pytest.mark.asyncio
    async def test_validate_required_fail(
        self,
        executor: StepExecutor,
        record: DataRecord,
    ) -> None:
        step = PipelineStep(
            id="st1",
            name="validate",
            type=StepType.VALIDATE,
            config={"rules": [{"field": "missing", "type": "required"}]},
        )
        with pytest.raises(DataValidationError):
            await executor.execute_validate(step, record, {})

    @pytest.mark.asyncio
    async def test_validate_range_fail(
        self,
        executor: StepExecutor,
        record: DataRecord,
    ) -> None:
        step = PipelineStep(
            id="st1",
            name="range",
            type=StepType.VALIDATE,
            config={"rules": [{"field": "age", "type": "range", "min": 30, "max": 100}]},
        )
        with pytest.raises(DataValidationError):
            await executor.execute_validate(step, record, {})


class TestEnrichStep:
    @pytest.fixture
    def executor(self) -> StepExecutor:
        return StepExecutor()

    @pytest.fixture
    def record(self) -> DataRecord:
        return DataRecord(id="rec1", data={"name": "alice"}, source="test")

    @pytest.mark.asyncio
    async def test_enrich_with_static_values(
        self,
        executor: StepExecutor,
        record: DataRecord,
    ) -> None:
        step = PipelineStep(
            id="st1",
            name="enrich",
            type=StepType.ENRICH,
            config={"enrichments": {"source_system": "eaip", "version": 1}},
        )
        result = await executor.execute_enrich(step, record, {})
        assert result.data["source_system"] == "eaip"
        assert result.data["version"] == 1

    @pytest.mark.asyncio
    async def test_enrich_from_context(
        self,
        executor: StepExecutor,
        record: DataRecord,
    ) -> None:
        step = PipelineStep(
            id="st1",
            name="enrich",
            type=StepType.ENRICH,
            config={"enrichments": {"user": {"source_key": "user_id", "default": "unknown"}}},
        )
        result = await executor.execute_enrich(step, record, {"user_id": "u123"})
        assert result.data["user"] == "u123"


class TestAggregateStep:
    @pytest.fixture
    def executor(self) -> StepExecutor:
        return StepExecutor()

    @pytest.mark.asyncio
    async def test_aggregate_collect(self) -> None:
        executor = StepExecutor()
        records = [
            DataRecord(id="r1", data={"val": 1}, source="test"),
            DataRecord(id="r2", data={"val": 2}, source="test"),
        ]
        step = PipelineStep(
            id="st1",
            name="collect",
            type=StepType.AGGREGATE,
            config={"operation": "collect"},
        )
        result = await executor.execute_aggregate(step, records, {})
        assert len(result) == 1
        assert result[0].data["_count"] == 2

    @pytest.mark.asyncio
    async def test_aggregate_group_by(self) -> None:
        executor = StepExecutor()
        records = [
            DataRecord(id="r1", data={"group": "a", "val": 1}, source="test"),
            DataRecord(id="r2", data={"group": "a", "val": 2}, source="test"),
            DataRecord(id="r3", data={"group": "b", "val": 3}, source="test"),
        ]
        step = PipelineStep(
            id="st1",
            name="group",
            type=StepType.AGGREGATE,
            config={"operation": "group", "group_by": "group"},
        )
        result = await executor.execute_aggregate(step, records, {})
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_aggregate_empty_records(self) -> None:
        executor = StepExecutor()
        step = PipelineStep(
            id="st1",
            name="empty",
            type=StepType.AGGREGATE,
            config={"operation": "collect"},
        )
        result = await executor.execute_aggregate(step, [], {})
        assert result == []


class TestScriptStep:
    @pytest.fixture
    def executor(self) -> StepExecutor:
        return StepExecutor()

    @pytest.mark.asyncio
    async def test_script_modifies_data(
        self,
        executor: StepExecutor,
    ) -> None:
        record = DataRecord(id="r1", data={"value": 5}, source="test")
        step = PipelineStep(
            id="st1",
            name="script",
            type=StepType.SCRIPT,
            config={"script": "data['value'] = data['value'] * 2"},
        )
        result = await executor.execute_script(step, record, {})
        assert result.data["value"] == 10

    @pytest.mark.asyncio
    async def test_script_noop(self, executor: StepExecutor) -> None:
        record = DataRecord(id="r1", data={"x": 1}, source="test")
        step = PipelineStep(
            id="st1",
            name="noop",
            type=StepType.SCRIPT,
        )
        result = await executor.execute_script(step, record, {})
        assert result.data["x"] == 1

    @pytest.mark.asyncio
    async def test_script_failure(self, executor: StepExecutor) -> None:
        record = DataRecord(id="r1", data={}, source="test")
        step = PipelineStep(
            id="st1",
            name="crash",
            type=StepType.SCRIPT,
            config={"script": "raise ValueError('boom')"},
        )
        with pytest.raises(StepExecutionError):
            await executor.execute_script(step, record, {})


class TestRunStep:
    @pytest.fixture
    def executor(self) -> StepExecutor:
        return StepExecutor()

    @pytest.mark.asyncio
    async def test_run_step_disabled(self, executor: StepExecutor) -> None:
        record = DataRecord(id="r1", data={}, source="test")
        step = PipelineStep(
            id="st1",
            name="disabled",
            type=StepType.TRANSFORM,
            enabled=False,
        )
        result = await executor.run_step(step, record, {})
        assert result is record

    @pytest.mark.asyncio
    async def test_run_step_routes_correctly(self, executor: StepExecutor) -> None:
        record = DataRecord(id="r1", data={"name": "alice"}, source="test")
        step = PipelineStep(
            id="st1",
            name="xform",
            type=StepType.TRANSFORM,
            config={"mapping": {"name": "name"}},
        )
        result = await executor.run_step(step, record, {})
        assert result is not None
        assert result.data["name"] == "alice"

    @pytest.mark.asyncio
    async def test_run_step_unknown_type(self, executor: StepExecutor) -> None:
        record = DataRecord(id="r1", data={"x": 1}, source="test")
        step = PipelineStep(id="st1", name="unknown", type=StepType.TRANSFORM)
        result = await executor.run_step(step, record, {})
        assert result is not None
