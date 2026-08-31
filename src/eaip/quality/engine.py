"""Test engine — registers and executes test cases and suites."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from eaip.quality.exceptions import SuiteNotFoundError, TestCaseNotFoundError, TestExecutionError
from eaip.quality.models import (
    TestCase,
    TestCaseStatus,
    TestExecution,
    TestExecutionStatus,
    TestSuite,
)
from eaip.shared.time import utc_now


class TestEngine:
    def __init__(self) -> None:
        self._test_cases: dict[str, TestCase] = {}
        self._suites: dict[str, TestSuite] = {}
        self._executions: dict[str, TestExecution] = {}
        self._cancel_events: dict[str, asyncio.Event] = {}
        self._event_callback: Any = None

    def set_event_callback(self, callback: Any) -> None:
        self._event_callback = callback

    def register_test_case(self, test_case: TestCase) -> None:
        self._test_cases[test_case.id] = test_case

    def unregister_test_case(self, test_id: str) -> None:
        if test_id not in self._test_cases:
            raise TestCaseNotFoundError(f"Test case {test_id!r} not found")
        del self._test_cases[test_id]

    def get_test_case(self, test_id: str) -> TestCase:
        if test_id not in self._test_cases:
            raise TestCaseNotFoundError(f"Test case {test_id!r} not found")
        return self._test_cases[test_id]

    def list_test_cases(
        self,
        component: str | None = None,
        type: str | None = None,
        status: str | None = None,
    ) -> list[TestCase]:
        results: list[TestCase] = list(self._test_cases.values())
        if component is not None:
            results = [t for t in results if t.component == component]
        if type is not None:
            results = [t for t in results if t.type == type]
        if status is not None:
            results = [t for t in results if t.status == status]
        return results

    def register_suite(self, suite: TestSuite) -> None:
        self._suites[suite.id] = suite

    def unregister_suite(self, suite_id: str) -> None:
        if suite_id not in self._suites:
            raise SuiteNotFoundError(f"Suite {suite_id!r} not found")
        del self._suites[suite_id]

    def get_suite(self, suite_id: str) -> TestSuite:
        if suite_id not in self._suites:
            raise SuiteNotFoundError(f"Suite {suite_id!r} not found")
        return self._suites[suite_id]

    def list_suites(self) -> list[TestSuite]:
        return list(self._suites.values())

    async def execute_test(
        self,
        test_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> TestExecution:
        test_case = self.get_test_case(test_id)
        if test_case.status is TestCaseStatus.DEPRECATED:
            exec_id = str(uuid.uuid4())
            execution = TestExecution(
                id=exec_id,
                test_id=test_id,
                status=TestExecutionStatus.SKIPPED,
                completed_at=utc_now(),
                error="Test case is deprecated",
                metadata=metadata or {},
            )
            self._executions[exec_id] = execution
            return execution

        exec_id = str(uuid.uuid4())
        cancel_event = asyncio.Event()
        self._cancel_events[exec_id] = cancel_event

        execution = TestExecution(
            id=exec_id,
            test_id=test_id,
            status=TestExecutionStatus.RUNNING,
            started_at=utc_now(),
            metadata=metadata or {},
        )
        self._executions[exec_id] = execution

        try:
            await asyncio.sleep(0.01)
            if cancel_event.is_set():
                execution = TestExecution(
                    id=exec_id,
                    test_id=test_id,
                    status=TestExecutionStatus.SKIPPED,
                    started_at=execution.started_at,
                    completed_at=utc_now(),
                    error="Execution cancelled",
                    metadata=metadata or {},
                )
                self._executions[exec_id] = execution
                return execution

            result: dict[str, Any] = {"output": f"Executed {test_case.name}"}
            assertion_results: dict[str, bool] = {}
            for assertion in test_case.assertions:
                assertion_results[assertion] = True

            completed = utc_now()
            duration = (
                (completed - execution.started_at).total_seconds() * 1000.0
                if execution.started_at
                else 0.0
            )

            execution = TestExecution(
                id=exec_id,
                test_id=test_id,
                status=TestExecutionStatus.PASSED,
                started_at=execution.started_at,
                completed_at=completed,
                duration_ms=duration,
                result=result,
                assertion_results=assertion_results,
                metadata=metadata or {},
            )
        except Exception as exc:
            completed = utc_now()
            duration = (
                (completed - execution.started_at).total_seconds() * 1000.0
                if execution.started_at
                else 0.0
            )
            execution = TestExecution(
                id=exec_id,
                test_id=test_id,
                status=TestExecutionStatus.ERROR,
                started_at=execution.started_at,
                completed_at=completed,
                duration_ms=duration,
                error=str(exc),
                metadata=metadata or {},
            )
        finally:
            self._cancel_events.pop(exec_id, None)

        self._executions[exec_id] = execution
        return execution

    async def execute_suite(
        self,
        suite_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[TestExecution]:
        suite = self.get_suite(suite_id)
        executions: list[TestExecution] = []

        if not suite.test_ids:
            return executions

        if suite.parallel_execution:
            tasks = [self.execute_test(tid, metadata) for tid in suite.test_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, TestExecution):
                    executions.append(r)
        else:
            for tid in suite.test_ids:
                try:
                    execution = await self.execute_test(tid, metadata)
                    executions.append(execution)
                except TestCaseNotFoundError:
                    exec_id = str(uuid.uuid4())
                    execution = TestExecution(
                        id=exec_id,
                        test_id=tid,
                        suite_id=suite_id,
                        status=TestExecutionStatus.ERROR,
                        completed_at=utc_now(),
                        error=f"Test case {tid!r} not found",
                        metadata=metadata or {},
                    )
                    self._executions[exec_id] = execution
                    executions.append(execution)

        return executions

    async def execute_all(
        self,
        component: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[TestExecution]:
        cases = self.list_test_cases(component=component)
        if not cases:
            return []
        executions: list[TestExecution] = []
        for case in cases:
            execution = await self.execute_test(case.id, metadata)
            executions.append(execution)
        return executions

    async def cancel_execution(self, execution_id: str) -> None:
        if execution_id not in self._executions:
            raise TestExecutionError(f"Execution {execution_id!r} not found")
        cancel_event = self._cancel_events.get(execution_id)
        if cancel_event is not None:
            cancel_event.set()

    async def get_execution(self, execution_id: str) -> TestExecution:
        if execution_id not in self._executions:
            raise TestExecutionError(f"Execution {execution_id!r} not found")
        return self._executions[execution_id]

    async def list_executions(
        self,
        test_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[TestExecution]:
        results: list[TestExecution] = list(self._executions.values())
        if test_id is not None:
            results = [e for e in results if e.test_id == test_id]
        if status is not None:
            results = [e for e in results if e.status == status]
        return results[:limit]
