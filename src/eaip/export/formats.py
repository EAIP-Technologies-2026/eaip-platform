"""Format converters — CSV, JSON, XLSX, and PDF export conversions."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from eaip.export.exceptions import FormatNotSupportedError

_SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".csv": "csv",
    ".json": "json",
    ".xlsx": "xlsx",
    ".pdf": "pdf",
}


def detect_format(path_or_ext: str) -> str:
    ext = path_or_ext.lower().strip()
    if ext.startswith("."):
        fmt = _SUPPORTED_EXTENSIONS.get(ext)
        if fmt:
            return fmt
    for candidate_fmt in _SUPPORTED_EXTENSIONS.values():
        if ext == candidate_fmt or ext == candidate_fmt.upper():
            return candidate_fmt
    for _ext, candidate_fmt in _SUPPORTED_EXTENSIONS.items():
        if ext.endswith(_ext):
            return candidate_fmt
    raise FormatNotSupportedError(f"Unsupported format or extension: {path_or_ext}")


class FormatConverter:
    @staticmethod
    def convert_to_csv(data: list[dict[str, Any]], config: dict[str, Any] | None = None) -> str:
        cfg = config or {}
        delimiter = str(cfg.get("delimiter", ","))
        include_headers = bool(cfg.get("include_headers", True))

        if not data:
            return ""

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(data[0].keys()), delimiter=delimiter)
        if include_headers:
            writer.writeheader()
        writer.writerows(data)
        return output.getvalue()

    @staticmethod
    def convert_to_json(data: list[dict[str, Any]], config: dict[str, Any] | None = None) -> str:
        cfg = config or {}
        indent = int(cfg.get("indent", 2))
        include_schema = bool(cfg.get("include_schema", False))

        if include_schema:
            payload: Any = {
                "schema": list(data[0].keys()) if data else [],
                "records": data,
                "total_records": len(data),
            }
        else:
            payload = data

        return json.dumps(payload, indent=indent, default=str)

    @staticmethod
    def convert_to_xlsx(data: list[dict[str, Any]], config: dict[str, Any] | None = None) -> bytes:
        cfg = config or {}
        sheet_name = str(cfg.get("sheet_name", "Export"))

        try:
            import openpyxl  # type: ignore[import-untyped]
        except ImportError:
            raise FormatNotSupportedError(
                "openpyxl is required for XLSX export; install it with 'pip install openpyxl'"
            ) from None

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet_name[:31]

        if not data:
            wb.save(io.BytesIO())
            return io.BytesIO().getvalue()

        headers = list(data[0].keys())
        ws.append(headers)

        for row in data:
            ws.append([row.get(h, "") for h in headers])

        freeze = cfg.get("freeze_panes")
        if freeze:
            ws.freeze_panes = freeze
        elif cfg.get("freeze_panes") is None and data:
            ws.freeze_panes = "A2"

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

    @staticmethod
    def convert_to_pdf(data: list[dict[str, Any]], config: dict[str, Any] | None = None) -> bytes:
        cfg = config or {}

        try:
            from reportlab.lib import pagesizes  # type: ignore[import-untyped]
            from reportlab.lib.pagesizes import (  # type: ignore[import-untyped,unused-ignore]
                A4,
                landscape,
            )
            from reportlab.lib.styles import getSampleStyleSheet  # type: ignore[import-untyped]
            from reportlab.platypus import (  # type: ignore[import-untyped]
                Paragraph,
                SimpleDocTemplate,
                Table,
                TableStyle,
            )
        except ImportError:
            raise FormatNotSupportedError(
                "reportlab is required for PDF export; install it with 'pip install reportlab'"
            ) from None

        page_size_name = str(cfg.get("page_size", "A4")).upper()
        _page_sizes = {"A4": A4, "LETTER": pagesizes.LETTER, "LEGAL": pagesizes.LEGAL}
        base_size = _page_sizes.get(page_size_name, A4)

        if str(cfg.get("orientation", "landscape")).lower() == "landscape":
            page_size = landscape(base_size)
        else:
            page_size = base_size

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=page_size)
        styles = getSampleStyleSheet()
        elements: list[object] = []

        if data:
            headers = list(data[0].keys())
            table_data: list[list[str]] = [headers]
            for row in data:
                table_data.append([str(row.get(h, "")) for h in headers])

            col_count = len(headers)
            col_width = (page_size[0] - 72) / max(col_count, 1)
            table = Table(table_data, colWidths=[col_width] * col_count)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), (0.8, 0.8, 0.8)),
                        ("TEXTCOLOR", (0, 0), (-1, 0), (0, 0, 0)),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                        ("GRID", (0, 0), (-1, -1), 0.5, (0.5, 0.5, 0.5)),
                    ]
                )
            )
            elements.append(table)
        else:
            elements.append(Paragraph("No data available", styles["Normal"]))

        doc.build(elements)
        return buf.getvalue()

    @classmethod
    def convert(
        cls, data: list[dict[str, Any]], format: str, config: dict[str, Any] | None = None
    ) -> str | bytes:
        fmt = format.lower()
        if fmt == "csv":
            return cls.convert_to_csv(data, config)
        if fmt == "json":
            return cls.convert_to_json(data, config)
        if fmt == "xlsx":
            return cls.convert_to_xlsx(data, config)
        if fmt == "pdf":
            return cls.convert_to_pdf(data, config)
        raise FormatNotSupportedError(f"Unsupported format: {format}")


__all__ = ["FormatConverter", "detect_format"]
