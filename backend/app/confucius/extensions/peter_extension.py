"""
Peter Extension - Product Owner Specialist.

Wraps product management services for Confucius orchestrator integration.
Handles requirements, user stories, backlog management, and prioritization.
"""

from typing import Dict, Any, Optional, List
import logging

from .base import BaseAgentExtension, ExtensionMetadata

logger = logging.getLogger(__name__)


class PeterExtension(BaseAgentExtension):
    """
    Peter - Product Owner Agent Extension.

    Capabilities:
    - Requirements gathering and analysis
    - User story generation
    - Backlog management
    - Feature prioritization
    - Stakeholder communication
    - Acceptance criteria definition

    Position in workflow: First agent in project initiation.
    """

    def __init__(self):
        """Initialize Peter extension."""
        super().__init__(
            ExtensionMetadata(
                name="Peter",
                description="Product Owner - Requirements, stories, prioritization",
                capabilities=[
                    "requirements_analysis",
                    "user_story_generation",
                    "backlog_management",
                    "feature_prioritization",
                    "acceptance_criteria",
                    "stakeholder_analysis",
                    "constitution_generation",
                    "epic_creation",
                ],
                domains=[
                    "product",
                    "requirements",
                    "stories",
                    "backlog",
                    "prioritization",
                    "features",
                    "epics",
                ],
                priority=8,  # High - starts workflows
                parallel_safe=True,
                timeout_seconds=90,
                version="1.0.0",
            )
        )

    async def on_input_messages(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare context for Peter product work."""
        modified = context.copy()

        # Determine product activity
        activity = self._determine_activity(task)
        modified["peter_activity"] = activity

        # Set prioritization method if not specified
        if "prioritization_method" not in modified:
            modified["prioritization_method"] = "MoSCoW"

        return modified

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute product owner activities."""
        activity = context.get("peter_activity", "general")

        try:
            if activity == "requirements":
                result = await self._analyze_requirements(context)
            elif activity == "stories":
                result = await self._generate_stories(context)
            elif activity == "backlog":
                result = await self._manage_backlog(context)
            elif activity == "prioritization":
                result = await self._prioritize_features(context)
            elif activity == "constitution":
                result = await self._generate_constitution(context)
            else:
                result = await self._general_product_work(task, context)

            self.update_partial({
                "product_work_complete": True,
                "activity": activity,
            })

            return {
                "success": True,
                "activity": activity,
                "result": result,
                "agent": "Peter",
            }

        except Exception as e:
            logger.error(f"Peter product work failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "activity": activity,
                "partial_result": self.get_partial(),
            }

    async def on_llm_output(
        self,
        raw_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse Peter output into structured format."""
        if not raw_output.get("success"):
            return raw_output

        result = raw_output.get("result", {})
        parsed = raw_output.copy()

        parsed["requirements"] = result.get("requirements", [])
        parsed["user_stories"] = result.get("user_stories", [])
        parsed["backlog_items"] = result.get("backlog_items", [])
        parsed["priorities"] = result.get("priorities", {})

        return parsed

    async def on_post(
        self,
        executed_output: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """Post-processing: Record product artifacts."""
        if executed_output.get("success"):
            req_count = len(executed_output.get("requirements", []))
            story_count = len(executed_output.get("user_stories", []))
            backlog_count = len(executed_output.get("backlog_items", []))

            executed_output["peter_summary"] = {
                "requirements_count": req_count,
                "stories_count": story_count,
                "backlog_items_count": backlog_count,
                "activity": executed_output.get("activity"),
                "entry_id": entry_id,
            }

            logger.info(
                f"Peter completed: {req_count} requirements, "
                f"{story_count} stories, {backlog_count} backlog items"
            )

        return executed_output

    def _determine_activity(self, task: str) -> str:
        """Determine product activity from task description."""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["requirement", "need", "want"]):
            return "requirements"
        elif any(kw in task_lower for kw in ["story", "user story", "as a"]):
            return "stories"
        elif any(kw in task_lower for kw in ["backlog", "items", "manage"]):
            return "backlog"
        elif any(kw in task_lower for kw in ["priorit", "rank", "order", "moscow"]):
            return "prioritization"
        elif any(kw in task_lower for kw in ["constitution", "vision", "charter"]):
            return "constitution"
        else:
            return "general"

    async def _analyze_requirements(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and document requirements."""
        return {
            "requirements": [],
            "functional": [],
            "non_functional": [],
            "constraints": [],
        }

    async def _generate_stories(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate user stories."""
        return {
            "user_stories": [],
            "epics": [],
            "acceptance_criteria": [],
        }

    async def _manage_backlog(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage product backlog."""
        return {
            "backlog_items": [],
            "total_items": 0,
            "ready_for_sprint": 0,
        }

    async def _prioritize_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prioritize features using specified method."""
        method = context.get("prioritization_method", "MoSCoW")
        return {
            "priorities": {},
            "method": method,
            "ranked_items": [],
        }

    async def _generate_constitution(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate project constitution."""
        return {
            "constitution": {
                "vision": "",
                "mission": "",
                "objectives": [],
                "success_criteria": [],
                "stakeholders": [],
            },
        }

    async def _general_product_work(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute general product owner work."""
        return {
            "requirements": [],
            "user_stories": [],
            "backlog_items": [],
        }
