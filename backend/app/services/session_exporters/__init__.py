"""
Session Exporters - Export CCTrace sessions to various formats

Week 61: Enhanced Observability Integration

Supports:
- Markdown: Human-readable session transcript
- JSON: Structured data for analysis
- XML: Interop with external tools
- JSONL: Line-delimited JSON for streaming/ML
- CSV: Tabular data for spreadsheet analysis
- Excel: Multi-sheet workbook for analysis
"""

from app.services.session_exporters.base import BaseSessionExporter, SessionData
from app.services.session_exporters.markdown_exporter import MarkdownSessionExporter
from app.services.session_exporters.json_exporter import JSONSessionExporter
from app.services.session_exporters.xml_exporter import XMLSessionExporter
from app.services.session_exporters.jsonl_exporter import JSONLSessionExporter
from app.services.session_exporters.csv_exporter import CSVSessionExporter
from app.services.session_exporters.excel_exporter import ExcelSessionExporter

__all__ = [
    "BaseSessionExporter",
    "SessionData",
    "MarkdownSessionExporter",
    "JSONSessionExporter",
    "XMLSessionExporter",
    "JSONLSessionExporter",
    "CSVSessionExporter",
    "ExcelSessionExporter",
]


def get_exporter(format: str) -> BaseSessionExporter:
    """
    Get exporter instance for format.

    Args:
        format: Export format (md, json, xml, jsonl, csv, xlsx, excel)

    Returns:
        Exporter instance

    Raises:
        ValueError: If format not supported
    """
    exporters = {
        "md": MarkdownSessionExporter,
        "markdown": MarkdownSessionExporter,
        "json": JSONSessionExporter,
        "xml": XMLSessionExporter,
        "jsonl": JSONLSessionExporter,
        "csv": CSVSessionExporter,
        "xlsx": ExcelSessionExporter,
        "excel": ExcelSessionExporter,
    }

    format_lower = format.lower()
    if format_lower not in exporters:
        raise ValueError(f"Unsupported format: {format}. Supported: {list(exporters.keys())}")

    return exporters[format_lower]()
