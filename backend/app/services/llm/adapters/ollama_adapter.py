"""
Ollama Adapter - Week 101

Transforms ProjectContext to Ollama-optimized minimal system prompt.
Output: .ollama/system.md
"""

from typing import TYPE_CHECKING
from .base import BaseAdapter

if TYPE_CHECKING:
    from ..project_context import ProjectContext


class OllamaAdapter(BaseAdapter):
    """
    Ollama-specific context adapter.

    Features:
    - Minimal system prompt for efficiency
    - Local inference optimized
    - Privacy-focused (no external data)
    - Cost-efficient context usage
    """

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def output_filename(self) -> str:
        return "system.md"

    def transform(self, context: "ProjectContext") -> str:
        """Transform to Ollama minimal format."""

        # Compact tech stack
        tech = f"{context.tech_stack.primary_language}/{context.tech_stack.framework}"
        if context.tech_stack.database:
            tech += f"/{context.tech_stack.database}"

        # Compact vocabulary (max 10 terms)
        vocab_compact = ""
        if context.domain_vocabulary:
            terms = context.domain_vocabulary[:10]
            vocab_compact = ", ".join(f"{t.term}={t.code_entity}" for t in terms)

        # Compact guidelines
        dos_compact = "; ".join(context.dos[:5]) if context.dos else ""
        donts_compact = "; ".join(context.donts[:5]) if context.donts else ""

        return f"""# {context.project_name} ({context.version})

Stack: {tech}
Arch: {context.architecture.style} ({context.architecture.layers})
Auth: {context.security.authentication}

## Naming
- Class: {context.naming_conventions.classes}
- Func: {context.naming_conventions.functions}
- File: {context.naming_conventions.files}

## Terms
{vocab_compact}

## Order
{self._format_numbered_compact(context.implementation_order)}

## Do
{dos_compact}

## Don't
{donts_compact}
"""

    def _format_numbered_compact(self, items: list) -> str:
        """Format as compact numbered list."""
        if not items:
            return "-"
        return " → ".join(f"{i+1}.{item.split()[0]}" for i, item in enumerate(items[:6]))
