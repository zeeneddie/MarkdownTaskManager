"""
Codex (GPT-5.2) Adapter - Week 101

Transforms ProjectContext to Codex-optimized comment-block format.
Output: .codex/context.md
"""

from typing import TYPE_CHECKING
from .base import BaseAdapter

if TYPE_CHECKING:
    from ..project_context import ProjectContext


class CodexAdapter(BaseAdapter):
    """
    Codex/GPT-specific context adapter.

    Features:
    - Comment-block style instructions
    - Inline code hints
    - Completion-optimized format
    - Code generation focus
    """

    @property
    def provider_name(self) -> str:
        return "codex"

    @property
    def output_filename(self) -> str:
        return "context.md"

    def transform(self, context: "ProjectContext") -> str:
        """Transform to Codex comment-block format."""

        # Build vocabulary inline hints
        vocab_hints = ""
        if context.domain_vocabulary:
            vocab_hints = "\n".join(
                f"# {t.term}: {t.definition} (maps to: {t.code_entity})"
                for t in context.domain_vocabulary
            )

        # Build implementation checklist
        impl_checklist = "\n".join(
            f"# [ ] {i+1}. {step}"
            for i, step in enumerate(context.implementation_order)
        ) if context.implementation_order else ""

        return f"""# ============================================================================
# PROJECT CONTEXT: {context.project_name}
# Version: {context.version} | Status: {context.status}
# ============================================================================

# TECH STACK
# ----------
# Language:      {context.tech_stack.primary_language}
# Framework:     {context.tech_stack.framework}
# Database:      {context.tech_stack.database}
# Cache:         {context.tech_stack.cache}
# Queue:         {context.tech_stack.message_queue}

# ARCHITECTURE
# ------------
# Style:         {context.architecture.style}
# Layers:        {context.architecture.layers}
# API:           {context.architecture.api_style}

# SECURITY
# --------
# Auth:          {context.security.authentication}
# Authorization: {context.security.authorization}
# Compliance:    {', '.join(context.security.compliance_requirements) or 'None specified'}

# ============================================================================
# NAMING CONVENTIONS
# ============================================================================
# Classes:       {context.naming_conventions.classes}     # e.g., UserService, OrderRepository
# Functions:     {context.naming_conventions.functions}   # e.g., get_user_by_id
# Files:         {context.naming_conventions.files}       # e.g., user_service.py
# Constants:     {context.naming_conventions.constants}   # e.g., MAX_RETRY_COUNT
# Private:       {context.naming_conventions.private_fields} # e.g., _internal_cache

# ============================================================================
# DOMAIN VOCABULARY (use these terms consistently)
# ============================================================================
{vocab_hints}

# ============================================================================
# IMPLEMENTATION ORDER (follow this sequence)
# ============================================================================
{impl_checklist}

# ============================================================================
# GUIDELINES
# ============================================================================

# DO:
{self._format_comment_list(context.dos)}

# DON'T:
{self._format_comment_list(context.donts)}

# ============================================================================
# BEFORE IMPLEMENTING, ASK:
# ============================================================================
{self._format_comment_list(context.questions_to_ask)}

# ============================================================================
# CODE GENERATION HINTS
# ============================================================================
# - Start with domain layer (entities, value objects)
# - Use Result pattern for error handling
# - Apply guard clauses for validation
# - Write tests alongside implementation
# - Follow existing patterns in codebase
# ============================================================================
"""

    def _format_comment_list(self, items: list) -> str:
        """Format list items as comments."""
        if not items:
            return "# (none specified)"
        return "\n".join(f"# - {item}" for item in items)
