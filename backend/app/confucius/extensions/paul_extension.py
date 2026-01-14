"""
Paul Extension - Planning Specialist.

Wraps planning services for Confucius orchestrator integration.
Handles sprint planning, release planning, and project scheduling.
"""

from typing import Dict, Any, Optional, List
import logging

from .base import BaseAgentExtension, ExtensionMetadata

logger = logging.getLogger(__name__)


class PaulExtension(BaseAgentExtension):
    """
    Paul - Planning Agent Extension.

    Capabilities:
    - Sprint planning
    - Release planning
    - Capacity planning
    - Timeline estimation
    - Resource allocation
    - Milestone tracking
    - Dependency management

    Position in workflow: After Peter, before implementation.
    """

    def __init__(self):
        """Initialize Paul extension."""
        super().__init__(
            ExtensionMetadata(
                name="Paul",
                description="Planning Specialist - Sprints, releases, timelines",
                capabilities=[
                    "sprint_planning",
                    "release_planning",
                    "capacity_planning",
                    "timeline_estimation",
                    "resource_allocation",
                    "milestone_tracking",
                    "dependency_management",
                    "velocity_calculation",
                ],
                domains=[
                    "planning",
                    "sprint",
                    "release",
                    "timeline",
                    "schedule",
                    "capacity",
                    "resources",
                ],
                priority=7,
                parallel_safe=True,
                timeout_seconds=60,
                version="1.0.0",
            )
        )
        self._wave_planner = None

    def _get_wave_planner(self):
        """Lazy load wave planner service."""
        if self._wave_planner is None:
            try:
                from app.services.wave_planner_service import (
                    WavePlannerService,
                )
                self._wave_planner = WavePlannerService()
            except ImportError as e:
                logger.warning(f"Could not import WavePlannerService: {e}")
        return self._wave_planner

    async def on_input_messages(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare context for Paul planning."""
        modified = context.copy()

        # Determine planning type
        planning_type = self._determine_planning_type(task)
        modified["paul_planning_type"] = planning_type

        # Set sprint duration if not specified
        if "sprint_duration_days" not in modified:
            modified["sprint_duration_days"] = 14

        return modified

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute planning activities."""
        planning_type = context.get("paul_planning_type", "general")

        try:
            if planning_type == "sprint":
                result = await self._plan_sprint(context)
            elif planning_type == "release":
                result = await self._plan_release(context)
            elif planning_type == "capacity":
                result = await self._plan_capacity(context)
            elif planning_type == "timeline":
                result = await self._estimate_timeline(context)
            elif planning_type == "wave":
                result = await self._plan_migration_wave(context)
            else:
                result = await self._general_planning(task, context)

            self.update_partial({
                "planning_complete": True,
                "planning_type": planning_type,
            })

            return {
                "success": True,
                "planning_type": planning_type,
                "result": result,
                "agent": "Paul",
            }

        except Exception as e:
            logger.error(f"Paul planning failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "planning_type": planning_type,
                "partial_result": self.get_partial(),
            }

    async def on_llm_output(
        self,
        raw_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse Paul output into structured format."""
        if not raw_output.get("success"):
            return raw_output

        result = raw_output.get("result", {})
        parsed = raw_output.copy()

        parsed["sprints"] = result.get("sprints", [])
        parsed["milestones"] = result.get("milestones", [])
        parsed["timeline"] = result.get("timeline", {})
        parsed["capacity"] = result.get("capacity", {})

        return parsed

    async def on_post(
        self,
        executed_output: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """Post-processing: Record planning artifacts."""
        if executed_output.get("success"):
            sprint_count = len(executed_output.get("sprints", []))
            milestone_count = len(executed_output.get("milestones", []))

            executed_output["paul_summary"] = {
                "sprints_planned": sprint_count,
                "milestones_defined": milestone_count,
                "planning_type": executed_output.get("planning_type"),
                "entry_id": entry_id,
            }

            logger.info(
                f"Paul completed: {sprint_count} sprints, "
                f"{milestone_count} milestones"
            )

        return executed_output

    def _determine_planning_type(self, task: str) -> str:
        """Determine planning type from task description."""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["sprint", "iteration"]):
            return "sprint"
        elif any(kw in task_lower for kw in ["release", "version", "deploy"]):
            return "release"
        elif any(kw in task_lower for kw in ["capacity", "team", "resource"]):
            return "capacity"
        elif any(kw in task_lower for kw in ["timeline", "schedule", "when"]):
            return "timeline"
        elif any(kw in task_lower for kw in ["wave", "migration", "phase"]):
            return "wave"
        else:
            return "general"

    async def _plan_sprint(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Plan sprint."""
        duration = context.get("sprint_duration_days", 14)
        return {
            "sprints": [],
            "duration_days": duration,
            "velocity": 0,
            "committed_points": 0,
        }

    async def _plan_release(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Plan release."""
        return {
            "milestones": [],
            "release_date": None,
            "features_included": [],
            "risks": [],
        }

    async def _plan_capacity(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Plan capacity."""
        return {
            "capacity": {
                "available_hours": 0,
                "committed_hours": 0,
                "utilization": 0.0,
            },
            "team_allocation": [],
        }

    async def _estimate_timeline(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate project timeline."""
        return {
            "timeline": {
                "start_date": None,
                "end_date": None,
                "duration_weeks": 0,
            },
            "phases": [],
            "critical_path": [],
        }

    async def _plan_migration_wave(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Plan migration wave."""
        service = self._get_wave_planner()
        if service and hasattr(service, "plan"):
            try:
                return await service.plan(context)
            except Exception as e:
                logger.warning(f"Wave planning failed: {e}")

        return {
            "waves": [],
            "dependencies": [],
            "parallel_streams": 0,
        }

    async def _general_planning(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute general planning."""
        return {
            "sprints": [],
            "milestones": [],
            "timeline": {},
        }
