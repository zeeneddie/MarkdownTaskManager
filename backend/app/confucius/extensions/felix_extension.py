"""
Felix Extension - Architecture Specialist.

Wraps MigrationArchitectureService for Confucius orchestrator integration.
Handles architecture analysis, component mapping, API contracts,
and migration planning.
"""

from typing import Dict, Any, Optional, List
import logging

from .base import BaseAgentExtension, ExtensionMetadata

logger = logging.getLogger(__name__)


class FelixExtension(BaseAgentExtension):
    """
    Felix - Architecture Agent Extension.

    Capabilities:
    - Architecture pattern recommendation
    - Legacy to target component mapping
    - API contract generation
    - Data migration planning
    - Architecture Decision Records (ADRs)
    - Dependency analysis and visualization

    Position in workflow: Between Peter (Product) and implementation teams.
    """

    def __init__(self):
        """Initialize Felix extension."""
        super().__init__(
            ExtensionMetadata(
                name="Felix",
                description="Architecture Specialist - Design, patterns, migration planning",
                capabilities=[
                    "architecture_analysis",
                    "pattern_recommendation",
                    "component_mapping",
                    "api_contract_generation",
                    "data_migration_planning",
                    "adr_generation",
                    "dependency_analysis",
                    "technology_stack_recommendation",
                ],
                domains=[
                    "architecture",
                    "design",
                    "patterns",
                    "migration",
                    "api",
                    "data",
                    "components",
                    "dependencies",
                ],
                priority=8,  # High priority for architecture decisions
                parallel_safe=True,
                timeout_seconds=180,  # Architecture analysis can be complex
                version="1.0.0",
            )
        )
        self._architecture_service = None

    def _get_architecture_service(self):
        """Lazy load architecture service."""
        if self._architecture_service is None:
            try:
                from app.services.migration_architecture_service import (
                    MigrationArchitectureService,
                )
                self._architecture_service = MigrationArchitectureService()
            except ImportError as e:
                logger.warning(f"Could not import MigrationArchitectureService: {e}")
        return self._architecture_service

    async def on_input_messages(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Prepare context for Felix analysis.

        Adds architecture-specific context and determines analysis type.
        """
        modified = context.copy()

        # Determine analysis type from task
        analysis_type = self._determine_analysis_type(task)
        modified["felix_analysis_type"] = analysis_type

        # Extract source system info if available
        if "source_code" in context or "legacy_system" in context:
            modified["has_source_context"] = True

        # Inject relevant memory if available
        if self._orchestrator:
            relevant_memory = await self.get_relevant_memory(context)
            if relevant_memory:
                modified["previous_architecture_insights"] = relevant_memory

        return modified

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute architecture analysis.

        Routes to appropriate Felix capability based on task/context.
        """
        analysis_type = context.get("felix_analysis_type", "full_analysis")

        service = self._get_architecture_service()
        if not service:
            return {
                "success": False,
                "error": "Architecture service not available",
                "agent": "Felix",
            }

        try:
            # Route to appropriate analysis method
            if analysis_type == "pattern_recommendation":
                result = await self._analyze_patterns(context, service)
            elif analysis_type == "component_mapping":
                result = await self._map_components(context, service)
            elif analysis_type == "api_generation":
                result = await self._generate_api_contracts(context, service)
            elif analysis_type == "data_migration":
                result = await self._plan_data_migration(context, service)
            elif analysis_type == "adr_generation":
                result = await self._generate_adrs(context, service)
            else:
                result = await self._full_analysis(task, context, service)

            self.update_partial({
                "analysis_complete": True,
                "analysis_type": analysis_type,
            })

            return {
                "success": True,
                "analysis_type": analysis_type,
                "result": result,
                "agent": "Felix",
            }

        except Exception as e:
            logger.error(f"Felix analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis_type": analysis_type,
                "partial_result": self.get_partial(),
            }

    async def on_llm_output(
        self,
        raw_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Parse Felix output into structured format.

        Extracts architecture decisions, recommendations, and risks.
        """
        if not raw_output.get("success"):
            return raw_output

        result = raw_output.get("result", {})
        parsed = raw_output.copy()

        # Extract key architecture elements
        parsed["architecture_decisions"] = self._extract_decisions(result)
        parsed["recommendations"] = self._extract_recommendations(result)
        parsed["risks"] = self._extract_risks(result)
        parsed["components"] = self._extract_components(result)

        return parsed

    async def on_post(
        self,
        executed_output: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """
        Post-processing: Record architecture insights.
        """
        if executed_output.get("success"):
            decisions_count = len(executed_output.get("architecture_decisions", []))
            risks_count = len(executed_output.get("risks", []))

            executed_output["felix_summary"] = {
                "decisions_count": decisions_count,
                "risks_count": risks_count,
                "analysis_type": executed_output.get("analysis_type"),
                "entry_id": entry_id,
            }

            logger.info(
                f"Felix completed: {decisions_count} decisions, "
                f"{risks_count} risks identified"
            )

        return executed_output

    def _determine_analysis_type(self, task: str) -> str:
        """Determine analysis type from task description."""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["pattern", "architecture pattern", "design pattern"]):
            return "pattern_recommendation"
        elif any(kw in task_lower for kw in ["component", "mapping", "map"]):
            return "component_mapping"
        elif any(kw in task_lower for kw in ["api", "contract", "endpoint"]):
            return "api_generation"
        elif any(kw in task_lower for kw in ["data", "migration", "database"]):
            return "data_migration"
        elif any(kw in task_lower for kw in ["adr", "decision record", "architecture decision"]):
            return "adr_generation"
        else:
            return "full_analysis"

    async def _full_analysis(
        self,
        task: str,
        context: Dict[str, Any],
        service,
    ) -> Dict[str, Any]:
        """Execute full architecture analysis."""
        source_analysis = context.get("source_analysis", {})

        # Use service's analyze method if available
        if hasattr(service, "analyze"):
            return await service.analyze(
                source_analysis=source_analysis,
                task=task,
                context=context,
            )

        # Fallback to basic analysis
        return {
            "analysis_type": "full",
            "source_summary": source_analysis,
            "recommendations": [],
            "patterns": [],
            "status": "analysis_performed",
        }

    async def _analyze_patterns(
        self,
        context: Dict[str, Any],
        service,
    ) -> Dict[str, Any]:
        """Analyze and recommend architecture patterns."""
        if hasattr(service, "recommend_patterns"):
            return await service.recommend_patterns(context)
        return {"patterns": [], "recommendations": []}

    async def _map_components(
        self,
        context: Dict[str, Any],
        service,
    ) -> Dict[str, Any]:
        """Map legacy components to target architecture."""
        if hasattr(service, "map_components"):
            return await service.map_components(context)
        return {"mappings": [], "unmapped": []}

    async def _generate_api_contracts(
        self,
        context: Dict[str, Any],
        service,
    ) -> Dict[str, Any]:
        """Generate API contracts from legacy analysis."""
        if hasattr(service, "generate_api_contracts"):
            return await service.generate_api_contracts(context)
        return {"contracts": [], "openapi_spec": None}

    async def _plan_data_migration(
        self,
        context: Dict[str, Any],
        service,
    ) -> Dict[str, Any]:
        """Plan data migration strategy."""
        if hasattr(service, "plan_data_migration"):
            return await service.plan_data_migration(context)
        return {"migration_plan": [], "dependencies": []}

    async def _generate_adrs(
        self,
        context: Dict[str, Any],
        service,
    ) -> Dict[str, Any]:
        """Generate Architecture Decision Records."""
        if hasattr(service, "generate_adrs"):
            return await service.generate_adrs(context)
        return {"adrs": []}

    def _extract_decisions(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract architecture decisions from result."""
        decisions = []
        if "architecture_decisions" in result:
            decisions.extend(result["architecture_decisions"])
        if "decisions" in result:
            decisions.extend(result["decisions"])
        return decisions

    def _extract_recommendations(self, result: Dict[str, Any]) -> List[str]:
        """Extract recommendations from result."""
        recommendations = []
        if "recommendations" in result:
            recommendations.extend(result["recommendations"])
        if "suggested_patterns" in result:
            recommendations.extend([
                f"Consider using {p}" for p in result["suggested_patterns"]
            ])
        return recommendations

    def _extract_risks(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract risks from result."""
        risks = []
        if "risks" in result:
            for risk in result["risks"]:
                if isinstance(risk, str):
                    risks.append({"description": risk, "severity": "medium"})
                else:
                    risks.append(risk)
        return risks

    def _extract_components(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract component information from result."""
        return {
            "legacy": result.get("legacy_components", []),
            "target": result.get("target_components", []),
            "mappings": result.get("component_mappings", []),
        }
