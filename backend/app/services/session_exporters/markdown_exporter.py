"""
Markdown Session Exporter - Human-readable session transcript

Week 61: Enhanced Observability Integration
"""

from typing import List
from app.services.session_exporters.base import (
    BaseSessionExporter,
    SessionData,
    ThinkingBlockExport,
    ToolExecutionExport,
    MessageExport,
)


class MarkdownSessionExporter(BaseSessionExporter):
    """
    Export CCTrace session to Markdown format.

    Produces a human-readable transcript with:
    - Session header with metadata
    - Thinking blocks in collapsible sections
    - Tool executions with timing
    - Message conversation flow
    - Summary statistics
    """

    @property
    def format_name(self) -> str:
        return "markdown"

    @property
    def content_type(self) -> str:
        return "text/markdown"

    @property
    def file_extension(self) -> str:
        return "md"

    def export(
        self,
        session_data: SessionData,
        include_thinking: bool = True,
        include_tools: bool = True,
        include_messages: bool = True
    ) -> str:
        """Export session to Markdown format."""
        lines = []

        # Header
        lines.extend(self._render_header(session_data))

        # Metrics summary
        lines.extend(self._render_metrics(session_data))

        # Thinking blocks
        if include_thinking and session_data.thinking_blocks:
            lines.extend(self._render_thinking_blocks(session_data.thinking_blocks))

        # Tool executions
        if include_tools and session_data.tool_executions:
            lines.extend(self._render_tool_executions(session_data.tool_executions))

        # Messages
        if include_messages and session_data.messages:
            lines.extend(self._render_messages(session_data.messages))

        # Footer
        lines.extend(self._render_footer(session_data))

        return "\n".join(lines)

    def _render_header(self, session_data: SessionData) -> List[str]:
        """Render session header."""
        created = session_data.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if session_data.created_at else "Unknown"

        return [
            f"# CCTrace Session: {session_data.session_id}",
            "",
            "| Property | Value |",
            "|----------|-------|",
            f"| Session ID | `{session_data.session_id}` |",
            f"| Created | {created} |",
            f"| Provider | {session_data.provider} |",
            f"| Model | {session_data.model} |",
            "",
        ]

    def _render_metrics(self, session_data: SessionData) -> List[str]:
        """Render metrics summary."""
        cache_savings = session_data.cache_read_tokens
        total_tokens = session_data.total_input_tokens + session_data.total_output_tokens

        return [
            "## Metrics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Input Tokens | {session_data.total_input_tokens:,} |",
            f"| Output Tokens | {session_data.total_output_tokens:,} |",
            f"| Cache Created | {session_data.cache_creation_tokens:,} |",
            f"| Cache Read (Savings) | {cache_savings:,} |",
            f"| Total Duration | {session_data.total_duration_ms:,}ms |",
            f"| Estimated Cost | ${session_data.total_cost:.4f} |",
            "",
        ]

    def _render_thinking_blocks(self, blocks: List[ThinkingBlockExport]) -> List[str]:
        """Render thinking blocks section."""
        lines = [
            "## Thinking Blocks",
            "",
            f"*{len(blocks)} thinking block(s) captured*",
            "",
        ]

        for i, block in enumerate(blocks):
            token_info = f"{block.token_count:,} tokens" if block.token_count else "unknown tokens"
            signature_info = " ✓ signed" if block.signature else ""

            lines.extend([
                f"### Block {i + 1}: {block.block_type}{signature_info}",
                "",
                f"*{token_info}*",
                "",
                "<details>",
                "<summary>View thinking content</summary>",
                "",
                "```",
                block.content,
                "```",
                "",
                "</details>",
                "",
            ])

            # Add extra data if present
            if block.extra_data:
                steps = block.extra_data.get("steps", [])
                if steps:
                    lines.append("**Extracted Steps:**")
                    for j, step in enumerate(steps[:5], 1):
                        lines.append(f"{j}. {step}")
                    if len(steps) > 5:
                        lines.append(f"*...and {len(steps) - 5} more steps*")
                    lines.append("")

        return lines

    def _render_tool_executions(self, tools: List[ToolExecutionExport]) -> List[str]:
        """Render tool executions section."""
        successful = sum(1 for t in tools if t.success)
        failed = len(tools) - successful

        lines = [
            "## Tool Executions",
            "",
            f"*{len(tools)} tool call(s): {successful} successful, {failed} failed*",
            "",
            "| # | Tool | Duration | Status |",
            "|---|------|----------|--------|",
        ]

        for i, tool in enumerate(tools, 1):
            duration = f"{tool.duration_ms}ms" if tool.duration_ms else "-"
            status = "✅" if tool.success else "❌"
            lines.append(f"| {i} | `{tool.tool_name}` | {duration} | {status} |")

        lines.append("")

        # Detailed tool output
        for i, tool in enumerate(tools, 1):
            lines.extend([
                f"### Tool {i}: {tool.tool_name}",
                "",
            ])

            if tool.tool_input:
                lines.extend([
                    "**Input:**",
                    "```json",
                    str(tool.tool_input),
                    "```",
                    "",
                ])

            if tool.tool_output:
                # Truncate long output
                output = tool.tool_output
                if len(output) > 500:
                    output = output[:500] + "\n...[truncated]..."

                lines.extend([
                    "**Output:**",
                    "```",
                    output,
                    "```",
                    "",
                ])

            if tool.error_message:
                lines.extend([
                    f"**Error:** {tool.error_message}",
                    "",
                ])

        return lines

    def _render_messages(self, messages: List[MessageExport]) -> List[str]:
        """Render messages section."""
        lines = [
            "## Conversation",
            "",
        ]

        for msg in messages:
            role_icon = {
                "user": "👤",
                "assistant": "🤖",
                "system": "⚙️",
                "tool": "🔧",
            }.get(msg.role, "💬")

            lines.extend([
                f"### {role_icon} {msg.role.title()}",
                "",
            ])

            if msg.timestamp:
                lines.append(f"*{msg.timestamp.strftime('%H:%M:%S')}*")
                lines.append("")

            # Truncate very long content
            content = msg.content
            if len(content) > 1000:
                content = content[:1000] + "\n\n...[truncated]..."

            lines.extend([
                content,
                "",
            ])

        return lines

    def _render_footer(self, session_data: SessionData) -> List[str]:
        """Render session footer."""
        return [
            "---",
            "",
            f"*Exported by CCTrace | Session {session_data.session_id}*",
            "",
        ]
