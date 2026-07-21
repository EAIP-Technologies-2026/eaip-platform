"""Tests for :mod:`eaip.quality.engine`."""

from __future__ import annotations

import pytest

from eaip.quality.engine import TestEngine
from eaip.quality.exceptions import SuiteNotFoundError, TestCaseNotFoundError, TestExecutionError
from eaip.quality.models import (
    TestCase,
    TestCaseStatus,
    TestCaseType,
    TestExecutionStatus,
    TestSuite,
)

# Prevent pytest from collecting source classes as test classes
TestEngine.__test__ = False
TestCase.__test__ = False
TestSuite.__test__ = False
TestCaseNotFoundError.__test__ = False
TestExecutionError.__test__ = False
TestCaseStatus.__test__ = False
TestCaseType.__test__ = False
TestExecutionStatus.__test__ = False


class TestRegisterTestCase:
    def test_register_and_get(self) -> None:
        engine = TestEngine()
        tc = TestCase(id="tc1", name="test one")
        engine.register_test_case(tc)
        assert engine.get_test_case("tc1") is tc

    def test_register_duplicate_overwrites(self) -> None:
        engine = TestEngine()
        tc1 = TestCase(id="tc1", name="first")
        tc2 = TestCase(id="tc1", name="second")
        engine.register_test_case(tc1)
        engine.register_test_case(tc2)
        assert engine.get_test_case("tc1").name == "second"

    def test_unregister_existing(self) -> None:
        engine = TestEngine()
        tc = TestCase(id="tc1", name="test one")
        engine.register_test_case(tc)
        engine.unregister_test_case("tc1")
        with pytest.raises(TestCaseNotFoundError):
            engine.get_test_case("tc1")

    def test_unregister_missing(self) -> None:
        engine = TestEngine()
        with pytest.raises(TestCaseNotFoundError):
            engine.unregister_test_case("nonexistent")

    def test_get_missing(self) -> None:
        engine = TestEngine()
        with pytest.raises(TestCaseNotFoundError):
            engine.get_test_case("nonexistent")


class TestListTestCases:
    def test_empty(self) -> None:
        engine = TestEngine()
        assert engine.list_test_cases() == []

    def test_all(self) -> None:
        engine = TestEngine()
        engine.register_test_case(TestCase(id="tc1", name="a", component="comp1"))
        engine.register_test_case(TestCase(id="tc2", name="b", component="comp2"))
        assert len(engine.list_test_cases()) == 2

    def test_filter_by_component(self) -> None:
        engine = TestEngine()
        engine.register_test_case(TestCase(id="tc1", name="a", component="comp1"))
        engine.register_test_case(TestCase(id="tc2", name="b", component="comp2"))
        result = engine.list_test_cases(component="comp1")
        assert len(result) == 1
        assert result[0].id == "tc1"

    def test_filter_by_type(self) -> None:
        engine = TestEngine()
        engine.register_test_case(TestCase(id="tc1", name="a", type=TestCaseType.UNIT))
        engine.register_test_case(TestCase(id="tc2", name="b", type=TestCaseType.INTEGRATION))
        result = engine.list_test_cases(type="integration")
        assert len(result) == 1

    def test_filter_by_status(self) -> None:
        engine = TestEngine()
        engine.register_test_case(TestCase(id="tc1", name="a", status=TestCaseStatus.ACTIVE))
        engine.register_test_case(TestCase(id="tc2", name="b", status=TestCaseStatus.DRAFT))
        result = engine.list_test_cases(status="active")
        assert len(result) == 1

    def test_filter_combined(self) -> None:
        engine = TestEngine()
        engine.register_test_case(
            TestCase(
                id="tc1",
                name="a",
                component="comp1",
                type=TestCaseType.UNIT,
                status=TestCaseStatus.ACTIVE,
            )
        )
        engine.register_test_case(
            TestCase(
                id="tc2",
                name="b",
                component="comp2",
                type=TestCaseType.INTEGRATION,
                status=TestCaseStatus.DRAFT,
            )
        )
        result = engine.list_test_cases(component="comp1", type="unit", status="active")
        assert len(result) == 1


class TestSuiteManagement:
    def test_register_and_get(self) -> None:
        engine = TestEngine()
        s = TestSuite(id="s1", name="suite one")
        engine.register_suite(s)
        assert engine.get_suite("s1") is s

    def test_unregister_existing(self) -> None:
        engine = TestEngine()
        engine.register_suite(TestSuite(id="s1", name="suite one"))
        engine.unregister_suite("s1")
        with pytest.raises(SuiteNotFoundError):
            engine.get_suite("s1")

    def test_unregister_missing(self) -> None:
        engine = TestEngine()
        with pytest.raises(SuiteNotFoundError):
            engine.unregister_suite("nonexistent")

    def test_list_suites(self) -> None:
        engine = TestEngine()
        engine.register_suite(TestSuite(id="s1", name="a"))
        engine.register_suite(TestSuite(id="s2", name="b"))
        assert len(engine.list_suites()) == 2


class TestExecuteTest:
    @pytest.mark.asyncio
    async def test_execute_passing(self) -> None:
        engine = TestEngine()
        tc = TestCase(id="tc1", name="test one", assertions=("eq",))
        engine.register_test_case(tc)
        execution = await engine.execute_test("tc1")
        assert execution.status is TestExecutionStatus.PASSED
        assert execution.duration_ms > 0

    @pytest.mark.asyncio
    async def test_execute_deprecated_skips(self) -> None:
        engine = TestEngine()
        tc = TestCase(id="tc1", name="deprecated", status=TestCaseStatus.DEPRECATED)
        engine.register_test_case(tc)
        execution = await engine.execute_test("tc1")
        assert execution.status is TestExecutionStatus.SKIPPED
        assert "deprecated" in execution.error

    @pytest.mark.asyncio
    async def test_execute_non_existent(self) -> None:
        engine = TestEngine()
        with pytest.raises(TestCaseNotFoundError):
            await engine.execute_test("nonexistent")

    @pytest.mark.asyncio
    async def test_execute_all_empty(self) -> None:
        engine = TestEngine()
        results = await engine.execute_all()
        assert results == []

    @pytest.mark.asyncio
    async def test_execute_all_for_component(self) -> None:
        engine = TestEngine()
        engine.register_test_case(TestCase(id="tc1", name="a", component="comp1"))
        engine.register_test_case(TestCase(id="tc2", name="b", component="comp2"))
        results = await engine.execute_all(component="comp1")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_execution_with_metadata(self) -> None:
        engine = TestEngine()
        tc = TestCase(id="tc1", name="test one")
        engine.register_test_case(tc)
        execution = await engine.execute_test("tc1", metadata={"trigger": "ci"})
        assert execution.metadata.get("trigger") == "ci"

    @pytest.mark.asyncio
    async def test_cancel_execution(self) -> None:
        engine = TestEngine()
        tc = TestCase(id="tc1", name="test one")
        engine.register_test_case(tc)
        execution = await engine.execute_test("tc1")
        assert execution.status is TestExecutionStatus.PASSED

    @pytest.mark.asyncio
    async def test_cancel_missing(self) -> None:
        engine = TestEngine()
        with pytest.raises(TestExecutionError):
            await engine.cancel_execution("nonexistent")


class TestExecuteSuite:
    @pytest.mark.asyncio
    async def test_execute_suite_sequential(self) -> None:
        engine = TestEngine()
        engine.register_test_case(TestCase(id="tc1", name="a"))
        engine.register_test_case(TestCase(id="tc2", name="b"))
        engine.register_suite(TestSuite(id="s1", name="suite", test_ids=("tc1", "tc2")))
        results = await engine.execute_suite("s1")
        assert len(results) == 2
        assert all(r.status is TestExecutionStatus.PASSED for r in results)

    @pytest.mark.asyncio
    async def test_execute_suite_parallel(self) -> None:
        engine = TestEngine()
        engine.register_test_case(TestCase(id="tc1", name="a"))
        engine.register_test_case(TestCase(id="tc2", name="b"))
        engine.register_suite(
            TestSuite(id="s1", name="suite", test_ids=("tc1", "tc2"), parallel_execution=True)
        )
        results = await engine.execute_suite("s1")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_execute_suite_empty(self) -> None:
        engine = TestEngine()
        engine.register_suite(TestSuite(id="s1", name="empty"))
        results = await engine.execute_suite("s1")
        assert results == []

    @pytest.mark.asyncio
    async def test_execute_suite_missing_test(self) -> None:
        engine = TestEngine()
        engine.register_suite(TestSuite(id="s1", name="suite", test_ids=("nonexistent",)))
        results = await engine.execute_suite("s1")
        assert len(results) == 1
        assert results[0].status is TestExecutionStatus.ERROR

    @pytest.mark.asyncio
    async def test_execute_suite_not_found(self) -> None:
        engine = TestEngine()
        with pytest.raises(SuiteNotFoundError):
            await engine.execute_suite("nonexistent")


class TestExecutionList:
    @pytest.mark.asyncio
    async def test_list_executions_empty(self) -> None:
        engine = TestEngine()
        results = await engine.list_executions()
        assert results == []

    @pytest.mark.asyncio
    async def test_list_executions_filter_by_test_id(self) -> None:
        engine = TestEngine()
        engine.register_test_case(TestCase(id="tc1", name="a"))
        engine.register_test_case(TestCase(id="tc2", name="b"))
        await engine.execute_test("tc1")
        await engine.execute_test("tc2")
        results = await engine.list_executions(test_id="tc1")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_list_executions_limit(self) -> None:
        engine = TestEngine()
        engine.register_test_case(TestCase(id="tc1", name="a"))
        for _ in range(5):
            await engine.execute_test("tc1")
        results = await engine.list_executions(limit=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_get_execution(self) -> None:
        engine = TestEngine()
        engine.register_test_case(TestCase(id="tc1", name="a"))
        execution = await engine.execute_test("tc1")
        fetched = await engine.get_execution(execution.id)
        assert fetched.id == execution.id

    @pytest.mark.asyncio
    async def test_get_execution_missing(self) -> None:
        engine = TestEngine()
        with pytest.raises(TestExecutionError):
            await engine.get_execution("nonexistent")
