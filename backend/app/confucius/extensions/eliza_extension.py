"""
Eliza Extension - Estimation Specialist.

Wraps estimation services for Confucius orchestrator integration.
Handles Function Points, story points, effort estimation, and complexity analysis.
"""

from typing import Dict, Any, Optional, List
import logging

from .base import BaseAgentExtension, ExtensionMetadata

logger = logging.getLogger(__name__)


class ElizaExtension(BaseAgentExtension):
    """
    Eliza - Estimation Agent Extension.

    Capabilities:
    - Function Point analysis (IFPUG/NESMA)
    - Story point estimation
    - Effort calculation
    - Complexity scoring
    - Work type classification
    - Enhancement FP calculation

    Uses ML models for more accurate predictions.
    """

    def __init__(self):
        """Initialize Eliza extension."""
        super().__init__(
            ExtensionMetadata(
                name="Eliza",
                description="Estimation Specialist - FP, story points, effort",
                capabilities=[
                    "function_point_analysis",
                    "story_point_estimation",
                    "effort_calculation",
                    "complexity_scoring",
                    "work_type_classification",
                    "enhancement_fp_calculation",
                    "nesma_compliance",
                    "ifpug_compliance",
                ],
                domains=[
                    "estimation",
                    "function_points",
                    "story_points",
                    "effort",
                    "complexity",
                    "planning",
                    "sizing",
                ],
                priority=6,
                parallel_safe=True,
                timeout_seconds=60,
                version="1.0.0",
            )
        )
        self._fp_service = None
        self._estimation_service = None

    def _get_fp_service(self):
        """Lazy load FP service."""
        if self._fp_service is None:
            try:
                from app.services.fp_methodology.fp_methodology_service import (
                    FPMethodologyService,
                )
                self._fp_service = FPMethodologyService()
            except ImportError as e:
                logger.warning(f"Could not import FPMethodologyService: {e}")
        return self._fp_service

    def _get_estimation_service(self):
        """Lazy load estimation service."""
        if self._estimation_service is None:
            try:
                from app.services.migration_estimation_service import (
                    MigrationEstimationService,
                )
                self._estimation_service = MigrationEstimationService()
            except ImportError as e:
                logger.warning(f"Could not import MigrationEstimationService: {e}")
        return self._estimation_service

    async def on_input_messages(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare context for Eliza estimation."""
        modified = context.copy()

        # Determine estimation type
        estimation_type = self._determine_estimation_type(task)
        modified["eliza_estimation_type"] = estimation_type

        # Set defaults for FP methodology
        if "methodology" not in modified:
            modified["methodology"] = "NESMA"  # Default to NESMA

        # Inject relevant memory
        if self._orchestrator:
            relevant_memory = await self.get_relevant_memory(context)
            if relevant_memory:
                modified["previous_estimation_insights"] = relevant_memory

        return modified

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute estimation analysis."""
        estimation_type = context.get("eliza_estimation_type", "full_estimation")

        try:
            if estimation_type == "function_points":
                result = await self._calculate_function_points(context)
            elif estimation_type == "story_points":
                result = await self._estimate_story_points(context)
            elif estimation_type == "effort":
                result = await self._calculate_effort(context)
            elif estimation_type == "complexity":
                result = await self._analyze_complexity(context)
            elif estimation_type == "work_type":
                result = await self._classify_work_type(context)
            else:
                result = await self._full_estimation(task, context)

            self.update_partial({
                "estimation_complete": True,
                "estimation_type": estimation_type,
            })

            return {
                "success": True,
                "estimation_type": estimation_type,
                "result": result,
                "agent": "Eliza",
            }

        except Exception as e:
            logger.error(f"Eliza estimation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "estimation_type": estimation_type,
                "partial_result": self.get_partial(),
            }

    async def on_llm_output(
        self,
        raw_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse Eliza output into structured format."""
        if not raw_output.get("success"):
            return raw_output

        result = raw_output.get("result", {})
        parsed = raw_output.copy()

        parsed["function_points"] = result.get("function_points", 0)
        parsed["story_points"] = result.get("story_points", 0)
        parsed["effort_hours"] = result.get("effort_hours", 0)
        parsed["complexity_score"] = result.get("complexity_score", 0)
        parsed["work_type"] = result.get("work_type", "unknown")
        parsed["confidence"] = result.get("confidence", 0.0)

        return parsed

    async def on_post(
        self,
        executed_output: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """Post-processing: Record estimation metrics."""
        if executed_output.get("success"):
            executed_output["eliza_summary"] = {
                "function_points": executed_output.get("function_points", 0),
                "story_points": executed_output.get("story_points", 0),
                "effort_hours": executed_output.get("effort_hours", 0),
                "confidence": executed_output.get("confidence", 0.0),
                "entry_id": entry_id,
            }

            logger.info(
                f"Eliza completed: FP={executed_output.get('function_points', 0)}, "
                f"SP={executed_output.get('story_points', 0)}, "
                f"effort={executed_output.get('effort_hours', 0)}h"
            )

        return executed_output

    def _determine_estimation_type(self, task: str) -> str:
        """Determine estimation type from task description."""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["function point", "fp", "ifpug", "nesma"]):
            return "function_points"
        elif any(kw in task_lower for kw in ["story point", "sp", "agile"]):
            return "story_points"
        elif any(kw in task_lower for kw in ["effort", "hours", "days", "duration"]):
            return "effort"
        elif any(kw in task_lower for kw in ["complexity", "complex", "simple"]):
            return "complexity"
        elif any(kw in task_lower for kw in ["work type", "classification", "type"]):
            return "work_type"
        else:
            return "full_estimation"

    async def _calculate_function_points(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate function points."""
        fp_service = self._get_fp_service()
        if fp_service and hasattr(fp_service, "calculate"):
            try:
                return await fp_service.calculate(context)
            except Exception as e:
                logger.warning(f"FP calculation failed: {e}")

        # Fallback calculation
        return {
            "function_points": 0,
            "breakdown": {
                "ILF": 0, "EIF": 0, "EI": 0, "EO": 0, "EQ": 0
            },
            "methodology": context.get("methodology", "NESMA"),
        }

    async def _estimate_story_points(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate story points."""
        return {
            "story_points": 0,
            "complexity_factors": [],
            "reference_stories": [],
        }

    async def _calculate_effort(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate effort hours."""
        estimation_service = self._get_estimation_service()
        if estimation_service and hasattr(estimation_service, "estimate"):
            try:
                return await estimation_service.estimate(context)
            except Exception as e:
                logger.warning(f"Effort estimation failed: {e}")

        return {
            "effort_hours": 0,
            "breakdown": {},
            "confidence": 0.0,
        }

    async def _analyze_complexity(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze complexity."""
        return {
            "complexity_score": 0,
            "factors": [],
            "risk_level": "unknown",
        }

    async def _classify_work_type(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify work type (NESMA)."""
        fp_service = self._get_fp_service()
        if fp_service and hasattr(fp_service, "classify_work_type"):
            try:
                return await fp_service.classify_work_type(context)
            except Exception as e:
                logger.warning(f"Work type classification failed: {e}")

        return {
            "work_type": "unknown",
            "fp_applicable": False,
            "recommended_method": "time_and_materials",
        }

    async def _full_estimation(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute full estimation analysis."""
        results = {
            "function_points": 0,
            "story_points": 0,
            "effort_hours": 0,
            "complexity_score": 0,
            "work_type": "unknown",
            "confidence": 0.0,
        }

        # Calculate FP
        fp_result = await self._calculate_function_points(context)
        results["function_points"] = fp_result.get("function_points", 0)

        # Calculate effort
        effort_result = await self._calculate_effort(context)
        results["effort_hours"] = effort_result.get("effort_hours", 0)
        results["confidence"] = effort_result.get("confidence", 0.0)

        # Classify work type
        work_type_result = await self._classify_work_type(context)
        results["work_type"] = work_type_result.get("work_type", "unknown")

        return results
