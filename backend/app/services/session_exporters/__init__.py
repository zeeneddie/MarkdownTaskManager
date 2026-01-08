"""
Session Exporters - Export CCTrace sessions to various formats

Week 61: Enhanced Observability Integration

Supports:
- Markdown: Human-readable session transcript
- JSON: Structured data for analysis
- XML: Interop with external tools
- JSONL: Line-delimited JSON for streaming/ML
"""

from app.services.session_exporters.base import BaseSessionExporter, SessionData
from app.services.session_exporters.markdown_exporter import MarkdownSessionExporter
from app.services.session_exporters.json_exporter import JSONSessionExporter
from app.services.session_exporters.xml_exporter import XMLSessionExporter
from app.services.session_exporters.jsonl_exporter import JSONLSessionExporter

__all__ = [
    "BaseSessionExporter",
    "SessionData",
    "MarkdownSessionExporter",
    "JSONSessionExporter",
    "XMLSessionExporter",
    "JSONLSessionExporter",
]


def get_exporter(format: str) -> BaseSessionExporter:
    """
    Get exporter instance for format.

    Args:
        format: Export format (md, json, xml, jsonl)

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
    }

    format_lower = format.lower()
    if format_lower not in exporters:
        raise ValueError(f"Unsupported format: {format}. Supported: {list(exporters.keys())}")

    return exporters[format_lower]()
