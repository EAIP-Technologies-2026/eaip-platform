"""Tests for :mod:`eaip.shared.sandbox` — AST-validated safe execution sandbox."""

from __future__ import annotations

import pytest

from eaip.shared.sandbox import safe_exec


class TestSafeExecRejectsDangerousAttributes:
    """Regression tests for SR-01: attribute-based sandbox escape prevention."""

    @pytest.mark.parametrize(
        "code, attr",
        [
            ("x.__class__", "__class__"),
            ("x.__subclasses__()", "__subclasses__"),
            ("x.__globals__", "__globals__"),
            ("x.__mro__", "__mro__"),
            ("x.__bases__", "__bases__"),
            ("x.__dict__", "__dict__"),
            ("x.__code__", "__code__"),
            ("x.__func__", "__func__"),
            ("x.__closure__", "__closure__"),
            ("x.__self__", "__self__"),
            ("x.__getattribute__()", "__getattribute__"),
            ("x.__reduce__()", "__reduce__"),
            ("x.__reduce_ex__()", "__reduce_ex__"),
        ],
    )
    def test_rejects_dangerous_attribute(self, code: str, attr: str) -> None:
        local = {"x": {}}
        with pytest.raises(ValueError, match=attr):
            safe_exec(code, local_scope=local)

    def test_rejects_chained_dangerous_traversal(self) -> None:
        """Class hierarchy traversal chain must be rejected at any link."""
        local = {"x": {}}
        with pytest.raises(ValueError) as exc:
            safe_exec("x.__class__.__mro__[1].__subclasses__()", local_scope=local)
        assert any(d in str(exc.value) for d in ("__class__", "__mro__", "__subclasses__")), (
            f"expected a dangerous-attribute error, got: {exc.value}"
        )

    def test_rejects_attribute_on_constant(self) -> None:
        """Dangerous attribute access on a constant string."""
        with pytest.raises(ValueError, match="__class__"):
            safe_exec("'hello'.__class__", local_scope={})

    def test_rejects_globals_inside_attribute_chain(self) -> None:
        """__globals__ access must be rejected even in chained expression."""
        local = {"x": {}}
        with pytest.raises(ValueError, match="__globals__"):
            safe_exec("x.__init__.__globals__", local_scope=local)

    def test_rejects_subclasses_on_type_result(self) -> None:
        """type(x).__subclasses__() must be rejected."""
        local = {"x": {}}
        with pytest.raises(ValueError, match="__subclasses__"):
            safe_exec("type(x).__subclasses__()", local_scope=local)


class TestSafeExecAcceptsLegitimateScripts:
    """Verify that valid pipeline/transform scripts continue to work."""

    def test_simple_assignment(self) -> None:
        local = {"data": {"value": 5}}
        safe_exec("data['value'] = data['value'] * 2", local_scope=local)
        assert local["data"]["value"] == 10

    def test_dict_methods(self) -> None:
        local = {"data": {"a": 1, "b": 2}}
        safe_exec("data['c'] = len(data) + data['a']", local_scope=local)
        assert local["data"]["c"] == 3

    def test_multiple_statements(self) -> None:
        local = {"data": {"price": 10, "qty": 3}}
        code = (
            "data['total'] = data['price'] * data['qty']\ndata['after_tax'] = data['total'] * 1.1"
        )
        safe_exec(code, local_scope=local)
        assert local["data"]["total"] == 30
        assert local["data"]["after_tax"] == 33.0

    def test_augmented_assignment(self) -> None:
        local = {"data": {"counter": 1}}
        safe_exec("data['counter'] += 1", local_scope=local)
        assert local["data"]["counter"] == 2

    def test_conditional_expression(self) -> None:
        local = {"data": {"qty": 150, "price": 10}}
        safe_exec(
            "data['total'] = data['price'] * data['qty'] * 0.9 if data['qty'] > 100 else data['price'] * data['qty']",
            local_scope=local,
        )
        assert local["data"]["total"] == 1350.0

    def test_list_comprehension_not_allowed(self) -> None:
        with pytest.raises(ValueError, match="ListComp"):
            safe_exec("[x * 2 for x in [1, 2, 3]]", local_scope={})

    def test_pydantic_model_copy_pattern(self) -> None:
        """Verify that legitimate record attribute access works."""
        local = {"data": {"name": "test"}}
        safe_exec("data['name'] = data.get('name', 'default')", local_scope=local)
        assert local["data"]["name"] == "test"

    def test_transform_result_pattern(self) -> None:
        """Integration transform pattern: assign to result and reference payload."""
        local = {"payload": {"x": 10, "y": 20}}
        safe_exec(
            "result = {'sum': payload['x'] + payload['y'], 'product': payload['x'] * payload['y']}",
            local_scope=local,
        )
        assert local["result"]["sum"] == 30
        assert local["result"]["product"] == 200

    def test_builtin_function_calls(self) -> None:
        local = {"data": {"values": [3, 1, 2]}}
        safe_exec("data['sorted'] = sorted(data['values'])", local_scope=local)
        assert local["data"]["sorted"] == [1, 2, 3]


class TestSafeExecEdgeCases:
    """Edge cases and error handling."""

    def test_empty_code(self) -> None:
        local = {"data": {}}
        safe_exec("", local_scope=local)

    def test_only_comment(self) -> None:
        local = {"data": {}}
        safe_exec("# just a comment", local_scope=local)

    def test_syntax_error(self) -> None:
        with pytest.raises(ValueError, match="syntax error"):
            safe_exec("data = ", local_scope={})

    def test_import_rejected(self) -> None:
        with pytest.raises(ValueError, match="Import"):
            safe_exec("import os", local_scope={})

    def test_eval_rejected(self) -> None:
        with pytest.raises(ValueError, match="eval"):
            safe_exec("eval('1+1')", local_scope={})
