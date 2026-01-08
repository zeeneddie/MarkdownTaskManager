"""
Gemini Adapter - Week 101

Transforms ProjectContext to Gemini-optimized JSON-friendly format.
Output: .gemini/context.json
"""

import json
from typing import TYPE_CHECKING
from .base import BaseAdapter

if TYPE_CHECKING:
    from ..project_context import ProjectContext


class GeminiAdapter(BaseAdapter):
    """
    Gemini-specific context adapter.

    Features:
    - JSON-friendly structured data
    - Cross-modal optimization
    - Structured output focus
    - Clear schema definitions
    """

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def output_filename(self) -> str:
        return "context.json"

    def transform(self, context: "ProjectContext") -> str:
        """Transform to Gemini JSON format."""

        data = {
            "schema_version": "1.0.0",
            "generator": "MarQed.ai LLM Context Adapter",
            "adapter": "Gemini (JSON-Structured)",
            "project": {
                "name": context.project_name,
                "version": context.version,
                "status": context.status,
            },
            "tech_stack": {
                "primary_language": context.tech_stack.primary_language,
                "framework": context.tech_stack.framework,
                "database": context.tech_stack.database,
                "cache": context.tech_stack.cache,
                "message_queue": context.tech_stack.message_queue,
            },
            "architecture": {
                "style": context.architecture.style,
                "layers": context.architecture.layers,
                "api_style": context.architecture.api_style,
            },
            "security": {
                "authentication": context.security.authentication,
                "authorization": context.security.authorization,
                "password_hashing": context.security.password_hashing,
                "compliance_requirements": context.security.compliance_requirements,
            },
            "naming_conventions": {
                "classes": {
                    "pattern": context.naming_conventions.classes,
                    "example": "UserService",
                },
                "functions": {
                    "pattern": context.naming_conventions.functions,
                    "example": "get_user_by_id",
                },
                "files": {
                    "pattern": context.naming_conventions.files,
                    "example": "user_service.py",
                },
                "constants": {
                    "pattern": context.naming_conventions.constants,
                    "example": "MAX_RETRY_COUNT",
                },
                "private_fields": {
                    "pattern": context.naming_conventions.private_fields,
                    "example": "_internal_cache",
                },
            },
            "domain_vocabulary": [
                {
                    "term": t.term,
                    "definition": t.definition,
                    "code_entity": t.code_entity,
                }
                for t in context.domain_vocabulary
            ],
            "implementation_order": [
                {"step": i + 1, "phase": step}
                for i, step in enumerate(context.implementation_order)
            ],
            "guidelines": {
                "dos": context.dos,
                "donts": context.donts,
            },
            "pre_implementation_questions": context.questions_to_ask,
            "code_generation_hints": {
                "use_result_pattern": True,
                "use_guard_clauses": True,
                "write_tests_alongside": True,
                "follow_existing_patterns": True,
            },
        }

        return json.dumps(data, indent=2, ensure_ascii=False)
