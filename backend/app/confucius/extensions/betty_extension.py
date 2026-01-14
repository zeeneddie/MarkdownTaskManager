"""
Betty Extension - Business Analyst Specialist.

Wraps business analysis services for Confucius orchestrator integration.
Handles business process analysis, ROI calculation, and stakeholder management.
"""

from typing import Dict, Any, Optional, List
import logging

from .base import BaseAgentExtension, ExtensionMetadata

logger = logging.getLogger(__name__)


class BettyExtension(BaseAgentExtension):
    """
    Betty - Business Analyst Agent Extension.

    Capabilities:
    - Business process analysis
    - ROI calculation
    - Cost-benefit analysis
    - Stakeholder management
    - Business case creation
    - Impact assessment
    - Value stream mapping

    Position in workflow: Works alongside Peter for business context.
    """

    def __init__(self):
        """Initialize Betty extension."""
        super().__init__(
            ExtensionMetadata(
                name="Betty",
                description="Business Analyst - Processes, ROI, stakeholders",
                capabilities=[
                    "business_process_analysis",
                    "roi_calculation",
                    "cost_benefit_analysis",
                    "stakeholder_management",
                    "business_case_creation",
                    "impact_assessment",
                    "value_stream_mapping",
                    "gap_analysis",
                ],
                domains=[
                    "business",
                    "process",
                    "roi",
                    "cost",
                    "benefit",
                    "stakeholder",
                    "value",
                ],
                priority=6,
                parallel_safe=True,
                timeout_seconds=60,
                version="1.0.0",
            )
        )

    async def on_input_messages(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare context for Betty business analysis."""
        modified = context.copy()

        # Determine analysis type
        analysis_type = self._determine_analysis_type(task)
        modified["betty_analysis_type"] = analysis_type

        return modified

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute business analysis."""
        analysis_type = context.get("betty_analysis_type", "general")

        try:
            if analysis_type == "process":
                result = await self._analyze_process(context)
            elif analysis_type == "roi":
                result = await self._calculate_roi(context)
            elif analysis_type == "cost_benefit":
                result = await self._analyze_cost_benefit(context)
            elif analysis_type == "stakeholder":
                result = await self._manage_stakeholders(context)
            elif analysis_type == "business_case":
                result = await self._create_business_case(context)
            else:
                result = await self._general_analysis(task, context)

            self.update_partial({
                "analysis_complete": True,
                "analysis_type": analysis_type,
            })

            return {
                "success": True,
                "analysis_type": analysis_type,
                "result": result,
                "agent": "Betty",
            }

        except Exception as e:
            logger.error(f"Betty business analysis failed: {e}")
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
        """Parse Betty output into structured format."""
        if not raw_output.get("success"):
            return raw_output

        result = raw_output.get("result", {})
        parsed = raw_output.copy()

        parsed["processes"] = result.get("processes", [])
        parsed["roi_metrics"] = result.get("roi_metrics", {})
        parsed["stakeholders"] = result.get("stakeholders", [])
        parsed["business_case"] = result.get("business_case", {})

        return parsed

    async def on_post(
        self,
        executed_output: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """Post-processing: Record business analysis artifacts."""
        if executed_output.get("success"):
            process_count = len(executed_output.get("processes", []))
            stakeholder_count = len(executed_output.get("stakeholders", []))

            executed_output["betty_summary"] = {
                "processes_analyzed": process_count,
                "stakeholders_identified": stakeholder_count,
                "analysis_type": executed_output.get("analysis_type"),
                "entry_id": entry_id,
            }

            logger.info(
                f"Betty completed: {process_count} processes, "
                f"{stakeholder_count} stakeholders"
            )

        return executed_output

    def _determine_analysis_type(self, task: str) -> str:
        """Determine analysis type from task description."""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["process", "workflow", "bpmn"]):
            return "process"
        elif any(kw in task_lower for kw in ["roi", "return", "investment"]):
            return "roi"
        elif any(kw in task_lower for kw in ["cost", "benefit", "expense"]):
            return "cost_benefit"
        elif any(kw in task_lower for kw in ["stakeholder", "sponsor", "owner"]):
            return "stakeholder"
        elif any(kw in task_lower for kw in ["business case", "justification"]):
            return "business_case"
        else:
            return "general"

    async def _analyze_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze business process."""
        return {
            "processes": [],
            "pain_points": [],
            "improvement_opportunities": [],
        }

    async def _calculate_roi(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate ROI."""
        return {
            "roi_metrics": {
                "investment": 0,
                "return": 0,
                "roi_percentage": 0.0,
                "payback_period_months": 0,
            },
        }

    async def _analyze_cost_benefit(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cost-benefit."""
        return {
            "costs": [],
            "benefits": [],
            "net_benefit": 0,
            "benefit_cost_ratio": 0.0,
        }

    async def _manage_stakeholders(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage stakeholders."""
        return {
            "stakeholders": [],
            "communication_plan": [],
            "engagement_strategy": [],
        }

    async def _create_business_case(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create business case."""
        return {
            "business_case": {
                "executive_summary": "",
                "problem_statement": "",
                "proposed_solution": "",
                "benefits": [],
                "costs": [],
                "risks": [],
                "timeline": {},
                "recommendation": "",
            },
        }

    async def _general_analysis(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute general business analysis."""
        return {
            "processes": [],
            "stakeholders": [],
            "roi_metrics": {},
        }
