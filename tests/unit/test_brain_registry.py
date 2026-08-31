"""Tests for BrainRegistry."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from eaip.brain.brain_registry import BrainRegistry
from eaip.brain.department_brain import DepartmentBrain
from eaip.brain.enterprise_brain import EnterpriseBrain


class TestBrainRegistryInit:
    def test_init_without_enterprise(self) -> None:
        registry = BrainRegistry()
        with pytest.raises(RuntimeError):
            registry.get_enterprise()

    def test_init_with_enterprise(self) -> None:
        enterprise = EnterpriseBrain()
        registry = BrainRegistry(enterprise=enterprise)
        assert registry.get_enterprise() is enterprise

    def test_list_departments_empty(self) -> None:
        registry = BrainRegistry()
        assert registry.list_departments() == ()


class TestBrainRegistryRegister:
    def test_register_department(self) -> None:
        enterprise = EnterpriseBrain()
        brain = DepartmentBrain(department_id="eng", enterprise=enterprise)
        registry = BrainRegistry()
        registry.register_department("eng", brain)
        assert registry.list_departments() == ("eng",)

    def test_register_duplicate_raises(self) -> None:
        enterprise = EnterpriseBrain()
        brain = DepartmentBrain(department_id="eng", enterprise=enterprise)
        registry = BrainRegistry()
        registry.register_department("eng", brain)
        with pytest.raises(ValueError, match="already registered"):
            registry.register_department("eng", brain)

    def test_get_department(self) -> None:
        enterprise = EnterpriseBrain()
        brain = DepartmentBrain(department_id="eng", enterprise=enterprise)
        registry = BrainRegistry()
        registry.register_department("eng", brain)
        assert registry.get_department("eng") is brain

    def test_get_missing_department_raises(self) -> None:
        registry = BrainRegistry()
        with pytest.raises(KeyError, match="not found"):
            registry.get_department("nonexistent")

    def test_list_departments_multiple(self) -> None:
        enterprise = EnterpriseBrain()
        eng = DepartmentBrain(department_id="eng", enterprise=enterprise)
        hr = DepartmentBrain(department_id="hr", enterprise=enterprise)
        fin = DepartmentBrain(department_id="finance", enterprise=enterprise)
        registry = BrainRegistry()
        registry.register_department("eng", eng)
        registry.register_department("hr", hr)
        registry.register_department("finance", fin)
        depts = registry.list_departments()
        assert len(depts) == 3
        assert "eng" in depts
        assert "hr" in depts
        assert "finance" in depts


class TestBrainRegistryQueryAll:
    @pytest.mark.asyncio
    async def test_query_all_empty_returns_empty(self) -> None:
        registry = BrainRegistry()
        results = await registry.query_all("test")
        assert results == {}

    @pytest.mark.asyncio
    async def test_query_all_queries_all_departments(self) -> None:
        enterprise = EnterpriseBrain()
        eng = DepartmentBrain(department_id="eng", enterprise=enterprise)
        hr = DepartmentBrain(department_id="hr", enterprise=enterprise)
        registry = BrainRegistry()
        registry.register_department("eng", eng)
        registry.register_department("hr", hr)

        eng.query = AsyncMock(wraps=eng.query)
        hr.query = AsyncMock(wraps=hr.query)

        results = await registry.query_all("test query", top_k=5)
        assert len(results) == 2
        assert "eng" in results
        assert "hr" in results
        eng.query.assert_awaited_once()
        hr.query.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_query_all_continues_on_error(self) -> None:
        enterprise = EnterpriseBrain()
        eng = DepartmentBrain(department_id="eng", enterprise=enterprise)
        hr = DepartmentBrain(department_id="hr", enterprise=enterprise)
        bad = DepartmentBrain(department_id="bad", enterprise=enterprise)

        registry = BrainRegistry()
        registry.register_department("eng", eng)
        registry.register_department("hr", hr)
        registry.register_department("bad", bad)

        bad.query = AsyncMock(side_effect=RuntimeError("broken"))

        results = await registry.query_all("test")
        assert len(results) == 2
        assert "eng" in results
        assert "hr" in results
        assert "bad" not in results


class TestBrainRegistryQueryDepartments:
    @pytest.mark.asyncio
    async def test_query_departments_specific(self) -> None:
        enterprise = EnterpriseBrain()
        eng = DepartmentBrain(department_id="eng", enterprise=enterprise)
        hr = DepartmentBrain(department_id="hr", enterprise=enterprise)
        registry = BrainRegistry()
        registry.register_department("eng", eng)
        registry.register_department("hr", hr)

        eng.query = AsyncMock(wraps=eng.query)

        results = await registry.query_departments(["eng"], "test")
        assert len(results) == 1
        assert "eng" in results
        eng.query.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_query_departments_missing_skips(self) -> None:
        enterprise = EnterpriseBrain()
        eng = DepartmentBrain(department_id="eng", enterprise=enterprise)
        registry = BrainRegistry()
        registry.register_department("eng", eng)

        results = await registry.query_departments(["eng", "nonexistent"], "test")
        assert len(results) == 1
        assert "eng" in results


class TestBrainRegistryGetEnterprise:
    def test_get_enterprise_configured(self) -> None:
        enterprise = EnterpriseBrain()
        registry = BrainRegistry(enterprise=enterprise)
        assert registry.get_enterprise() is enterprise

    def test_get_enterprise_not_configured_raises(self) -> None:
        registry = BrainRegistry()
        with pytest.raises(RuntimeError, match="not configured"):
            registry.get_enterprise()
