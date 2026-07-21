"""Tests for export format converters."""

from __future__ import annotations

import json

import pytest

from eaip.export.exceptions import FormatNotSupportedError
from eaip.export.formats import FormatConverter, detect_format

openpyxl_available = True
reportlab_available = True
try:
    import openpyxl  # noqa: F401
except ImportError:
    openpyxl_available = False

try:
    import reportlab  # noqa: F401
except ImportError:
    reportlab_available = False


class TestDetectFormat:
    def test_csv_extension(self) -> None:
        assert detect_format("report.csv") == "csv"

    def test_json_extension(self) -> None:
        assert detect_format("data.json") == "json"

    def test_xlsx_extension(self) -> None:
        assert detect_format("export.xlsx") == "xlsx"

    def test_pdf_extension(self) -> None:
        assert detect_format("output.pdf") == "pdf"

    def test_no_extension(self) -> None:
        assert detect_format("csv") == "csv"

    def test_unknown_extension_raises(self) -> None:
        with pytest.raises(FormatNotSupportedError):
            detect_format("data.xyz")


class TestConvertToCSV:
    def test_empty_data(self) -> None:
        result = FormatConverter.convert_to_csv([])
        assert result == ""

    def test_single_row(self) -> None:
        data = [{"name": "Alice", "age": 30}]
        result = FormatConverter.convert_to_csv(data)
        assert "name,age" in result
        assert "Alice,30" in result

    def test_multiple_rows(self) -> None:
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        result = FormatConverter.convert_to_csv(data)
        lines = result.strip().splitlines()
        assert len(lines) == 3
        assert lines[0] == "name,age"

    def test_custom_delimiter(self) -> None:
        data = [{"name": "Alice", "age": 30}]
        result = FormatConverter.convert_to_csv(data, {"delimiter": "|"})
        assert "name|age" in result
        assert "Alice|30" in result

    def test_no_headers(self) -> None:
        data = [{"name": "Alice", "age": 30}]
        result = FormatConverter.convert_to_csv(data, {"include_headers": False})
        assert "name" not in result
        assert "Alice" in result

    def test_csv_is_string(self) -> None:
        data = [{"col": "val"}]
        result = FormatConverter.convert_to_csv(data)
        assert isinstance(result, str)


class TestConvertToJSON:
    def test_empty_data(self) -> None:
        result = FormatConverter.convert_to_json([])
        assert result == "[]"

    def test_basic(self) -> None:
        data = [{"name": "Alice", "age": 30}]
        result = FormatConverter.convert_to_json(data)
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["name"] == "Alice"

    def test_with_schema(self) -> None:
        data = [{"name": "Alice", "age": 30}]
        result = FormatConverter.convert_to_json(data, {"include_schema": True})
        parsed = json.loads(result)
        assert "schema" in parsed
        assert "records" in parsed
        assert parsed["total_records"] == 1
        assert parsed["schema"] == ["name", "age"]

    def test_custom_indent(self) -> None:
        data = [{"x": 1}]
        result = FormatConverter.convert_to_json(data, {"indent": 4})
        assert "    " in result

    def test_json_is_string(self) -> None:
        data = [{"col": "val"}]
        result = FormatConverter.convert_to_json(data)
        assert isinstance(result, str)


class TestConvertToXLSX:
    @pytest.mark.skipif(not openpyxl_available, reason="openpyxl not installed")
    def test_empty_data_returns_bytes(self) -> None:
        result = FormatConverter.convert_to_xlsx([])
        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.skipif(not openpyxl_available, reason="openpyxl not installed")
    def test_with_data_returns_bytes(self) -> None:
        result = FormatConverter.convert_to_xlsx([{"a": 1, "b": 2}])
        assert isinstance(result, bytes)

    @pytest.mark.skipif(not openpyxl_available, reason="openpyxl not installed")
    def test_custom_sheet_name(self) -> None:
        result = FormatConverter.convert_to_xlsx([{"a": 1}], {"sheet_name": "MySheet"})
        assert isinstance(result, bytes)


class TestConvertToPDF:
    @pytest.mark.skipif(not reportlab_available, reason="reportlab not installed")
    def test_empty_data_returns_bytes(self) -> None:
        result = FormatConverter.convert_to_pdf([])
        assert isinstance(result, bytes)

    @pytest.mark.skipif(not reportlab_available, reason="reportlab not installed")
    def test_with_data_returns_bytes(self) -> None:
        result = FormatConverter.convert_to_pdf([{"a": 1, "b": 2}])
        assert isinstance(result, bytes)

    @pytest.mark.skipif(not reportlab_available, reason="reportlab not installed")
    def test_portrait_orientation(self) -> None:
        result = FormatConverter.convert_to_pdf([{"a": 1}], {"orientation": "portrait"})
        assert isinstance(result, bytes)


class TestConvertDispatch:
    def test_csv_via_dispatch(self) -> None:
        result = FormatConverter.convert([{"x": 1}], "csv")
        assert isinstance(result, str)

    def test_json_via_dispatch(self) -> None:
        result = FormatConverter.convert([{"x": 1}], "json")
        assert isinstance(result, str)

    @pytest.mark.skipif(not openpyxl_available, reason="openpyxl not installed")
    def test_xlsx_via_dispatch(self) -> None:
        result = FormatConverter.convert([{"x": 1}], "xlsx")
        assert isinstance(result, bytes)

    @pytest.mark.skipif(not reportlab_available, reason="reportlab not installed")
    def test_pdf_via_dispatch(self) -> None:
        result = FormatConverter.convert([{"x": 1}], "pdf")
        assert isinstance(result, bytes)

    def test_unsupported_format_raises(self) -> None:
        with pytest.raises(FormatNotSupportedError):
            FormatConverter.convert([], "xml")
