"""
Diana Extension - Documentation Specialist.

Wraps documentation services for Confucius orchestrator integration.
Handles technical documentation, API docs, and knowledge transfer.
"""

from typing import Dict, Any, Optional, List
import logging

from .base import BaseAgentExtension, ExtensionMetadata

logger = logging.getLogger(__name__)


class DianaExtension(BaseAgentExtension):
    """
    Diana - Documentation Agent Extension.

    Capabilities:
    - Technical documentation generation
    - API documentation (OpenAPI/Swagger)
    - Migration reports
    - Architecture Decision Records
    - Knowledge transfer documentation
    - README generation

    Position in workflow: Final documentation after implementation.
    """

    def __init__(self):
        """Initialize Diana extension."""
        super().__init__(
            ExtensionMetadata(
                name="Diana",
                description="Documentation Specialist - Tech docs, API docs, reports",
                capabilities=[
                    "technical_documentation",
                    "api_documentation",
                    "migration_reports",
                    "adr_documentation",
                    "knowledge_transfer",
                    "readme_generation",
                    "changelog_generation",
                    "user_guide_creation",
                ],
                domains=[
                    "documentation",
                    "docs",
                    "api",
                    "reports",
                    "readme",
                    "changelog",
                    "knowledge",
                ],
                priority=4,
                parallel_safe=True,
                timeout_seconds=90,
                version="1.0.0",
            )
        )
        self._report_service = None

    def _get_report_service(self):
        """Lazy load report service."""
        if self._report_service is None:
            try:
                from app.services.migration_report_service import (
                    MigrationReportService,
                )
                self._report_service = MigrationReportService()
            except ImportError as e:
                logger.warning(f"Could not import MigrationReportService: {e}")
        return self._report_service

    async def on_input_messages(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare context for Diana documentation."""
        modified = context.copy()

        # Determine documentation type
        doc_type = self._determine_doc_type(task)
        modified["diana_doc_type"] = doc_type

        # Set output format if not specified
        if "output_format" not in modified:
            modified["output_format"] = "markdown"

        # Inject relevant memory
        if self._orchestrator:
            relevant_memory = await self.get_relevant_memory(context)
            if relevant_memory:
                modified["previous_documentation"] = relevant_memory

        return modified

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute documentation generation."""
        doc_type = context.get("diana_doc_type", "general")

        try:
            if doc_type == "api":
                result = await self._generate_api_docs(context)
            elif doc_type == "technical":
                result = await self._generate_tech_docs(context)
            elif doc_type == "migration_report":
                result = await self._generate_migration_report(context)
            elif doc_type == "adr":
                result = await self._generate_adr(context)
            elif doc_type == "readme":
                result = await self._generate_readme(context)
            else:
                result = await self._generate_general_docs(task, context)

            self.update_partial({
                "documentation_complete": True,
                "doc_type": doc_type,
            })

            return {
                "success": True,
                "doc_type": doc_type,
                "result": result,
                "agent": "Diana",
            }

        except Exception as e:
            logger.error(f"Diana documentation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "doc_type": doc_type,
                "partial_result": self.get_partial(),
            }

    async def on_llm_output(
        self,
        raw_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse Diana output into structured format."""
        if not raw_output.get("success"):
            return raw_output

        result = raw_output.get("result", {})
        parsed = raw_output.copy()

        parsed["documents"] = result.get("documents", [])
        parsed["content"] = result.get("content", "")
        parsed["format"] = result.get("format", "markdown")
        parsed["sections"] = result.get("sections", [])

        return parsed

    async def on_post(
        self,
        executed_output: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """Post-processing: Record documentation artifacts."""
        if executed_output.get("success"):
            docs_count = len(executed_output.get("documents", []))
            content_length = len(executed_output.get("content", ""))

            executed_output["diana_summary"] = {
                "documents_count": docs_count,
                "content_length": content_length,
                "doc_type": executed_output.get("doc_type"),
                "format": executed_output.get("format", "markdown"),
                "entry_id": entry_id,
            }

            logger.info(
                f"Diana completed: {docs_count} docs, "
                f"{content_length} chars"
            )

        return executed_output

    def _determine_doc_type(self, task: str) -> str:
        """Determine documentation type from task description."""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["api", "swagger", "openapi", "endpoint"]):
            return "api"
        elif any(kw in task_lower for kw in ["technical", "architecture", "system"]):
            return "technical"
        elif any(kw in task_lower for kw in ["migration", "report", "status"]):
            return "migration_report"
        elif any(kw in task_lower for kw in ["adr", "decision record"]):
            return "adr"
        elif any(kw in task_lower for kw in ["readme", "getting started"]):
            return "readme"
        else:
            return "general"

    async def _generate_api_docs(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API documentation."""
        return {
            "documents": [],
            "content": "",
            "format": "openapi",
            "sections": ["endpoints", "schemas", "examples"],
        }

    async def _generate_tech_docs(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate technical documentation."""
        return {
            "documents": [],
            "content": "",
            "format": "markdown",
            "sections": ["overview", "architecture", "components", "deployment"],
        }

    async def _generate_migration_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate migration report."""
        service = self._get_report_service()
        if service and hasattr(service, "generate"):
            try:
                return await service.generate(context)
            except Exception as e:
                logger.warning(f"Report generation failed: {e}")

        return {
            "documents": [],
            "content": "",
            "format": "markdown",
            "sections": ["summary", "progress", "issues", "next_steps"],
        }

    async def _generate_adr(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Architecture Decision Record."""
        return {
            "documents": [],
            "content": "",
            "format": "markdown",
            "sections": ["context", "decision", "consequences", "alternatives"],
        }

    async def _generate_readme(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate README documentation."""
        return {
            "documents": [],
            "content": "",
            "format": "markdown",
            "sections": ["overview", "installation", "usage", "contributing"],
        }

    async def _generate_general_docs(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate general documentation."""
        return {
            "documents": [],
            "content": "",
            "format": context.get("output_format", "markdown"),
            "sections": [],
        }
