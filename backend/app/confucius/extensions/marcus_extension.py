"""
Marcus Extension - Maintenance Specialist.

Wraps MarcusAgent for Confucius orchestrator integration.
Handles code maintenance, tech debt analysis, dependency updates,
and security scanning.
"""

from typing import Dict, Any, Optional, List
import logging

from .base import BaseAgentExtension, ExtensionMetadata
from app.services.marcus_integration import (
    MarcusAgent,
    FocusArea,
    MaintenanceScope,
    Urgency,
)

logger = logging.getLogger(__name__)


class MarcusExtension(BaseAgentExtension):
    """
    Marcus - Maintenance Specialist Agent Extension.

    Capabilities:
    - Tech debt analysis and prioritization
    - Dependency updates and security patches
    - Code quality assessment
    - Refactoring recommendations
    - Code health monitoring

    Uses Ollama qwen2.5-coder:7b for local LLM processing.
    """

    def __init__(self, marcus_agent: Optional[MarcusAgent] = None):
        """
        Initialize Marcus extension.

        Args:
            marcus_agent: Existing MarcusAgent instance (creates new if None)
        """
        super().__init__(
            ExtensionMetadata(
                name="Marcus",
                description="Maintenance Specialist - Tech debt, dependencies, code health",
                capabilities=[
                    "tech_debt_analysis",
                    "dependency_scan",
                    "security_scan",
                    "code_quality_check",
                    "refactoring_recommendations",
                    "maintenance_planning",
                ],
                domains=[
                    "maintenance",
                    "tech_debt",
                    "dependencies",
                    "security",
                    "code_quality",
                    "refactoring",
                ],
                priority=5,  # High priority for maintenance tasks
                parallel_safe=True,
                timeout_seconds=120,  # LLM calls can take time
                version="1.0.0",
            )
        )
        self._marcus = marcus_agent or MarcusAgent()
        self._is_available: Optional[bool] = None

    @property
    def marcus(self) -> MarcusAgent:
        """Get underlying Marcus agent."""
        return self._marcus

    async def _ensure_available(self) -> bool:
        """Ensure Marcus agent is available."""
        if self._is_available is None:
            self._is_available = await self._marcus.check_availability()
        return self._is_available

    async def on_input_messages(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Prepare context for Marcus analysis.

        Adds maintenance-specific context and determines focus area.
        """
        modified = context.copy()

        # Determine focus area from task
        focus_area = self._determine_focus_area(task)
        modified["marcus_focus_area"] = focus_area.value

        # Add maintenance scope if not specified
        if "scope" not in modified:
            modified["scope"] = MaintenanceScope.FULL_CODEBASE.value

        # Inject relevant memory if available
        if self._orchestrator:
            relevant_memory = await self.get_relevant_memory(context)
            if relevant_memory:
                modified["previous_maintenance_insights"] = relevant_memory

        return modified

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute maintenance analysis.

        Routes to appropriate Marcus capability based on task/context.
        """
        # Check availability
        if not await self._ensure_available():
            logger.warning("Marcus not available - returning fallback response")
            return {
                "success": False,
                "error": "Marcus agent not available (Ollama/qwen2.5-coder not running)",
                "fallback": True,
                "recommendations": [
                    "Start Ollama: ollama serve",
                    "Pull model: ollama pull qwen2.5-coder:7b",
                ],
            }

        # Get focus area
        focus_area_str = context.get("marcus_focus_area", FocusArea.TECH_DEBT.value)
        try:
            focus_area = FocusArea(focus_area_str)
        except ValueError:
            focus_area = FocusArea.TECH_DEBT

        # Get content to analyze
        content = context.get("content") or context.get("code") or task

        try:
            # Execute Marcus analysis
            result = await self._marcus.analyze(
                focus_area=focus_area,
                content=content,
            )

            self.update_partial({
                "analysis_complete": True,
                "focus_area": focus_area.value,
            })

            return {
                "success": True,
                "focus_area": focus_area.value,
                "analysis": result,
                "agent": "Marcus",
                "llm_model": self._marcus.config.get("llm", "qwen2.5-coder:7b"),
            }

        except Exception as e:
            logger.error(f"Marcus analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "focus_area": focus_area.value,
                "partial_result": self.get_partial(),
            }

    async def on_llm_output(
        self,
        raw_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Parse Marcus output into structured format.

        Extracts findings, recommendations, and scores.
        """
        if not raw_output.get("success"):
            return raw_output

        analysis = raw_output.get("analysis", {})

        # Normalize output structure
        parsed = raw_output.copy()
        parsed["findings"] = analysis.get("findings", [])
        parsed["recommendations"] = self._extract_recommendations(analysis)
        parsed["scores"] = self._extract_scores(analysis)
        parsed["priority_items"] = self._extract_priorities(analysis)

        return parsed

    async def on_post(
        self,
        executed_output: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """
        Post-processing: Record insights and update metrics.
        """
        if executed_output.get("success"):
            # Generate maintenance summary for note-taking
            findings_count = len(executed_output.get("findings", []))
            priority_count = len(executed_output.get("priority_items", []))

            executed_output["maintenance_summary"] = {
                "findings_count": findings_count,
                "priority_items_count": priority_count,
                "focus_area": executed_output.get("focus_area"),
                "entry_id": entry_id,
            }

            logger.info(
                f"Marcus completed: {findings_count} findings, "
                f"{priority_count} priority items"
            )

        return executed_output

    def _determine_focus_area(self, task: str) -> FocusArea:
        """Determine focus area from task description."""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["dependency", "package", "update", "npm", "pip"]):
            return FocusArea.DEPENDENCIES
        elif any(kw in task_lower for kw in ["security", "vulnerability", "owasp", "cve"]):
            return FocusArea.SECURITY
        elif any(kw in task_lower for kw in ["quality", "smell", "lint", "clean"]):
            return FocusArea.CODE_QUALITY
        elif any(kw in task_lower for kw in ["performance", "speed", "optimize", "slow"]):
            return FocusArea.PERFORMANCE
        elif any(kw in task_lower for kw in ["document", "docs", "readme", "comment"]):
            return FocusArea.DOCUMENTATION
        elif any(kw in task_lower for kw in ["test", "coverage", "spec", "unit"]):
            return FocusArea.TESTING
        else:
            return FocusArea.TECH_DEBT

    def _extract_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract recommendations from analysis."""
        recommendations = []

        # Check various possible recommendation fields
        if "recommendations" in analysis:
            recommendations.extend(analysis["recommendations"])
        if "refactoring_suggestions" in analysis:
            recommendations.extend(analysis["refactoring_suggestions"])
        if "immediate_actions" in analysis:
            recommendations.extend(analysis["immediate_actions"])
        if "priority_updates" in analysis:
            recommendations.extend(analysis["priority_updates"])

        return recommendations

    def _extract_scores(self, analysis: Dict[str, Any]) -> Dict[str, float]:
        """Extract score metrics from analysis."""
        scores = {}

        score_fields = [
            "quality_score",
            "risk_score",
            "total_debt_score",
            "health_score",
        ]

        for field in score_fields:
            if field in analysis:
                scores[field] = float(analysis[field])

        return scores

    def _extract_priorities(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract prioritized items from analysis."""
        priorities = []

        if "prioritized_items" in analysis:
            priorities.extend(analysis["prioritized_items"])
        if "priority_updates" in analysis:
            priorities.extend(analysis["priority_updates"])

        return priorities
