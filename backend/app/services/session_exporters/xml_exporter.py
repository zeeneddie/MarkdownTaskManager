"""
XML Session Exporter - Interop format for external tools

Week 61: Enhanced Observability Integration
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from xml.dom import minidom
from app.services.session_exporters.base import BaseSessionExporter, SessionData


class XMLSessionExporter(BaseSessionExporter):
    """
    Export CCTrace session to XML format.

    Produces well-formed XML with:
    - Namespaced elements
    - CDATA sections for content
    - Schema-compatible structure
    """

    NAMESPACE = "https://marqed.ai/cctrace/v1"

    @property
    def format_name(self) -> str:
        return "xml"

    @property
    def content_type(self) -> str:
        return "application/xml"

    @property
    def file_extension(self) -> str:
        return "xml"

    def export(
        self,
        session_data: SessionData,
        include_thinking: bool = True,
        include_tools: bool = True,
        include_messages: bool = True
    ) -> str:
        """Export session to XML format."""
        root = ET.Element("cctrace")
        root.set("xmlns", self.NAMESPACE)
        root.set("version", "1.0")
        root.set("exported", datetime.utcnow().isoformat())

        # Session info
        self._add_session_element(root, session_data)

        # Metrics
        self._add_metrics_element(root, session_data)

        # Thinking blocks
        if include_thinking and session_data.thinking_blocks:
            self._add_thinking_blocks(root, session_data)

        # Tool executions
        if include_tools and session_data.tool_executions:
            self._add_tool_executions(root, session_data)

        # Messages
        if include_messages and session_data.messages:
            self._add_messages(root, session_data)

        # Pretty print
        return self._prettify(root)

    def _add_session_element(self, root: ET.Element, session_data: SessionData) -> None:
        """Add session metadata element."""
        session = ET.SubElement(root, "session")
        session.set("id", session_data.session_id)

        created = ET.SubElement(session, "created")
        created.text = session_data.created_at.isoformat() if session_data.created_at else ""

        provider = ET.SubElement(session, "provider")
        provider.text = session_data.provider

        model = ET.SubElement(session, "model")
        model.text = session_data.model

    def _add_metrics_element(self, root: ET.Element, session_data: SessionData) -> None:
        """Add metrics element."""
        metrics = ET.SubElement(root, "metrics")

        # Tokens
        tokens = ET.SubElement(metrics, "tokens")
        ET.SubElement(tokens, "input").text = str(session_data.total_input_tokens)
        ET.SubElement(tokens, "output").text = str(session_data.total_output_tokens)
        ET.SubElement(tokens, "total").text = str(
            session_data.total_input_tokens + session_data.total_output_tokens
        )

        # Cache
        cache = ET.SubElement(metrics, "cache")
        ET.SubElement(cache, "creation").text = str(session_data.cache_creation_tokens)
        ET.SubElement(cache, "read").text = str(session_data.cache_read_tokens)

        # Timing
        timing = ET.SubElement(metrics, "timing")
        ET.SubElement(timing, "duration_ms").text = str(session_data.total_duration_ms)

        # Cost
        cost = ET.SubElement(metrics, "cost")
        ET.SubElement(cost, "total_usd").text = f"{session_data.total_cost:.6f}"

    def _add_thinking_blocks(self, root: ET.Element, session_data: SessionData) -> None:
        """Add thinking blocks element."""
        blocks = ET.SubElement(root, "thinking_blocks")
        blocks.set("count", str(len(session_data.thinking_blocks)))

        for block in session_data.thinking_blocks:
            block_elem = ET.SubElement(blocks, "block")
            block_elem.set("type", block.block_type)
            block_elem.set("sequence", str(block.sequence_number))
            block_elem.set("tokens", str(block.token_count))

            if block.signature:
                block_elem.set("signature", block.signature)

            if block.content_hash:
                block_elem.set("hash", block.content_hash)

            # Content as CDATA
            content = ET.SubElement(block_elem, "content")
            content.text = block.content

            # Extra data
            if block.extra_data:
                extra = ET.SubElement(block_elem, "extra")
                for key, value in block.extra_data.items():
                    if isinstance(value, (list, dict)):
                        item = ET.SubElement(extra, key)
                        item.text = str(value)
                    else:
                        item = ET.SubElement(extra, key)
                        item.text = str(value)

    def _add_tool_executions(self, root: ET.Element, session_data: SessionData) -> None:
        """Add tool executions element."""
        tools = ET.SubElement(root, "tool_executions")
        tools.set("count", str(len(session_data.tool_executions)))

        successful = sum(1 for t in session_data.tool_executions if t.success)
        tools.set("successful", str(successful))
        tools.set("failed", str(len(session_data.tool_executions) - successful))

        for tool in session_data.tool_executions:
            tool_elem = ET.SubElement(tools, "execution")
            tool_elem.set("name", tool.tool_name)
            tool_elem.set("success", str(tool.success).lower())

            if tool.duration_ms:
                tool_elem.set("duration_ms", str(tool.duration_ms))

            if tool.executed_at:
                tool_elem.set("executed_at", tool.executed_at.isoformat())

            # Input
            input_elem = ET.SubElement(tool_elem, "input")
            input_elem.text = str(tool.tool_input)

            # Output
            if tool.tool_output:
                output_elem = ET.SubElement(tool_elem, "output")
                output_elem.text = tool.tool_output[:5000]  # Truncate

            # Error
            if tool.error_message:
                error_elem = ET.SubElement(tool_elem, "error")
                error_elem.text = tool.error_message

    def _add_messages(self, root: ET.Element, session_data: SessionData) -> None:
        """Add messages element."""
        messages = ET.SubElement(root, "messages")
        messages.set("count", str(len(session_data.messages)))

        for msg in session_data.messages:
            msg_elem = ET.SubElement(messages, "message")
            msg_elem.set("role", msg.role)

            if msg.message_id:
                msg_elem.set("id", msg.message_id)

            if msg.parent_id:
                msg_elem.set("parent_id", msg.parent_id)

            if msg.timestamp:
                msg_elem.set("timestamp", msg.timestamp.isoformat())

            content = ET.SubElement(msg_elem, "content")
            content.text = msg.content

    def _prettify(self, elem: ET.Element) -> str:
        """Return pretty-printed XML string."""
        rough_string = ET.tostring(elem, encoding="unicode")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
