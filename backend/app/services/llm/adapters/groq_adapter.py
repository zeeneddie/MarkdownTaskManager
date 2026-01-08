"""
Groq Adapter - Week 101

Transforms ProjectContext to Groq-optimized speed-focused format.
Output: .groq/context.md
"""

from typing import TYPE_CHECKING
from .base import BaseAdapter

if TYPE_CHECKING:
    from ..project_context import ProjectContext


class GroqAdapter(BaseAdapter):
    """
    Groq-specific context adapter.

    Features:
    - Speed-optimized format (840 TPS target)
    - Minimal token usage
    - Streaming-friendly structure
    - Fast inference priority
    """

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def output_filename(self) -> str:
        return "context.md"

    def transform(self, context: "ProjectContext") -> str:
        """Transform to Groq speed-optimized format."""

        # Ultra-compact format for speed
        tech_line = f"{context.tech_stack.primary_language}"
        if context.tech_stack.framework:
            tech_line += f"+{context.tech_stack.framework}"
        if context.tech_stack.database:
            tech_line += f"+{context.tech_stack.database}"

        # Compact vocab (5 max)
        vocab = ",".join(
            f"{t.term}:{t.code_entity}"
            for t in context.domain_vocabulary[:5]
        ) if context.domain_vocabulary else "-"

        # Compact order (first word only)
        order = "→".join(
            step.split()[0] if step else ""
            for step in context.implementation_order[:6]
        ) if context.implementation_order else "-"

        # Compact dos/donts (3 max each)
        dos = ";".join(d[:50] for d in context.dos[:3]) if context.dos else "-"
        donts = ";".join(d[:50] for d in context.donts[:3]) if context.donts else "-"

        return f"""# {context.project_name} v{context.version}
T:{tech_line}|A:{context.architecture.style}|S:{context.security.authentication}
N:C={context.naming_conventions.classes},F={context.naming_conventions.functions}
V:{vocab}
O:{order}
DO:{dos}
NO:{donts}
---
Use Result pattern. Guard clauses. Tests with code.
"""
