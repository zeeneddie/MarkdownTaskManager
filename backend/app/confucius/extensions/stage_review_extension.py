"""
Stage Review Extension for Confucius Orchestrator.

Fase 23.6 Phase 24.3: Automatic stage-based LLM council review integration.
Hooks into the on_post lifecycle to trigger reviews on completed stage artifacts.
"""

from typing import Dict, Any, Optional, List
import logging

from .base import BaseAgentExtension, ExtensionMetadata

logger = logging.getLogger(__name__)


# Stage mapping from workflow stages to review stage types
WORKFLOW_TO_REVIEW_STAGE: Dict[str, str] = {
    # Brown Paper workflow stages
    "codebase_analysis": "analysis",
    "domain_extraction": "architecture",
    "complexity_assessment": "analysis",
    "risk_analysis": "analysis",
    "quality_review": "testing",
    "output_generation": "programming",

    # Migration workflow stages
    "assessment": "analysis",
    "planning": "architecture",
    "design": "design",
    "implementation": "programming",
    "testing": "testing",
    "deployment": "infrastructure",

    # Green Paper workflow stages
    "requirements": "analysis",
    "architecture": "architecture",
    "api_design": "design",
    "database_design": "design",
    "implementation_planning": "programming",

    # Quality workflow stages
    "static_analysis": "programming",
    "security_scan": "testing",
    "quality_gate": "testing",

    # Generic mappings
    "code": "programming",
    "test": "testing",
    "config": "infrastructure",
    "document": "analysis",
}


class StageReviewExtension(BaseAgentExtension):
    """
    Stage Review Extension - Automatic Quality Gates.

    Hooks into the Confucius PIV loop to automatically trigger
    stage-based LLM council reviews after each agent completes work.

    Features:
    - Automatic stage type detection from workflow context
    - Configurable auto-improvement on review failure
    - Integration with StageReviewService
    - Performance tracking for review metrics

    Position in workflow: Post-processing for all agents.
    """

    def __init__(
        self,
        auto_improve: bool = True,
        min_consensus_for_block: float = 0.6,
        review_all_stages: bool = False,
    ):
        """
        Initialize Stage Review Extension.

        Args:
            auto_improve: Automatically improve artifacts that fail review
            min_consensus_for_block: Minimum consensus to block progression
            review_all_stages: Review all stages (vs only critical ones)
        """
        super().__init__(
            ExtensionMetadata(
                name="StageReview",
                description="Automatic stage-based LLM council review",
                capabilities=[
                    "stage_review",
                    "multi_model_consensus",
                    "automatic_improvement",
                    "quality_gate",
                ],
                domains=[
                    "review",
                    "quality",
                    "validation",
                ],
                priority=10,  # Highest - runs after all other extensions
                parallel_safe=False,  # Must run sequentially for reviews
                timeout_seconds=180,  # Reviews can take time
                version="1.0.0",
            )
        )
        self.auto_improve = auto_improve
        self.min_consensus_for_block = min_consensus_for_block
        self.review_all_stages = review_all_stages

        # Lazy-loaded services
        self._review_service = None
        self._improvement_service = None

        # Critical stages that always get reviewed
        self._critical_stages = {
            "architecture",
            "security_scan",
            "implementation",
            "deployment",
        }

        # Review statistics
        self._stats = {
            "reviews_triggered": 0,
            "reviews_passed": 0,
            "reviews_failed": 0,
            "improvements_applied": 0,
        }

    def _get_review_service(self):
        """Lazy load stage review service."""
        if self._review_service is None:
            try:
                from app.services.stage_review.stage_review_service import (
                    StageReviewService,
                )
                self._review_service = StageReviewService()
            except ImportError as e:
                logger.warning(f"Could not import StageReviewService: {e}")
        return self._review_service

    def _get_improvement_service(self):
        """Lazy load artifact improvement service."""
        if self._improvement_service is None:
            try:
                from app.services.stage_review.artifact_improvement_service import (
                    ArtifactImprovementService,
                )
                self._improvement_service = ArtifactImprovementService()
            except ImportError as e:
                logger.warning(f"Could not import ArtifactImprovementService: {e}")
        return self._improvement_service

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute stage review.

        This extension doesn't have its own execute logic - it operates
        through the on_post hook to review other agents' output.
        """
        return {
            "success": True,
            "message": "StageReview operates via on_post hook",
            "stats": self._stats.copy(),
        }

    async def on_post(
        self,
        executed_output: Dict[str, Any],
        entry_id: str,
    ) -> Dict[str, Any]:
        """
        Post-processing: Trigger stage review on completed artifacts.

        This is the main integration point with the Confucius PIV loop.
        Reviews artifacts and optionally triggers improvement cycle.
        """
        # Check if review should be triggered
        if not self._should_review(executed_output):
            return executed_output

        # Extract artifact and stage info
        artifact = self._extract_artifact(executed_output)
        if not artifact:
            logger.debug("No artifact found for review")
            return executed_output

        stage_type = self._determine_stage_type(executed_output)
        if not stage_type:
            logger.debug("Could not determine stage type for review")
            return executed_output

        logger.info(f"Triggering stage review for {stage_type}")
        self._stats["reviews_triggered"] += 1

        # Get review service
        review_service = self._get_review_service()
        if not review_service:
            logger.warning("Review service not available")
            return executed_output

        try:
            # Execute review
            review_result = await review_service.review_artifact(
                stage_type=stage_type,
                artifact=artifact,
                artifact_type=self._get_artifact_type(executed_output),
                context=self._build_review_context(executed_output),
            )

            # Add review result to output
            executed_output["stage_review"] = {
                "session_id": review_result.session_id,
                "stage_type": stage_type,
                "decision": review_result.decision.value,
                "approved": review_result.approved,
                "issues_count": len(review_result.issues),
                "consensus_level": review_result.consensus_level,
                "rounds_completed": review_result.rounds_completed,
            }

            if review_result.approved:
                self._stats["reviews_passed"] += 1
                logger.info(f"Stage review PASSED for {stage_type}")
            else:
                self._stats["reviews_failed"] += 1
                logger.info(
                    f"Stage review FAILED for {stage_type}: "
                    f"{len(review_result.issues)} issues"
                )

                # Handle improvement if enabled
                if self.auto_improve and review_result.improved_artifact:
                    executed_output["improved_artifact"] = review_result.improved_artifact
                    executed_output["stage_review"]["improvement_applied"] = True
                    self._stats["improvements_applied"] += 1

                # Determine if this should block progression
                should_block = (
                    review_result.consensus_level >= self.min_consensus_for_block * 100
                    and any(
                        issue.severity.value in ("critical", "major")
                        for issue in review_result.issues
                    )
                )

                if should_block:
                    executed_output["stage_review"]["blocks_progression"] = True
                    executed_output["should_retry"] = True

            return executed_output

        except Exception as e:
            logger.error(f"Stage review failed: {e}")
            executed_output["stage_review"] = {
                "error": str(e),
                "approved": True,  # Don't block on review failure
            }
            return executed_output

    def _should_review(self, output: Dict[str, Any]) -> bool:
        """Determine if output should be reviewed."""
        # Skip if already reviewed
        if output.get("stage_review"):
            return False

        # Skip failures
        if not output.get("success", True):
            return False

        # Get workflow stage
        stage = output.get("workflow_stage", output.get("stage", ""))

        # Always review critical stages
        if stage in self._critical_stages:
            return True

        # Check if review all stages is enabled
        if self.review_all_stages:
            return True

        # Check for explicit review request
        if output.get("request_review", False):
            return True

        return False

    def _extract_artifact(self, output: Dict[str, Any]) -> Optional[str]:
        """Extract artifact content from output."""
        # Try common artifact locations
        for key in ["artifact", "output", "content", "code", "result", "document"]:
            if key in output and isinstance(output[key], str):
                return output[key]

        # Try nested result
        result = output.get("result", {})
        if isinstance(result, dict):
            for key in ["artifact", "output", "content", "code"]:
                if key in result and isinstance(result[key], str):
                    return result[key]

        return None

    def _determine_stage_type(self, output: Dict[str, Any]) -> Optional[str]:
        """Determine review stage type from output context."""
        # Check explicit stage type
        if "stage_type" in output:
            return output["stage_type"]

        # Check workflow stage mapping
        workflow_stage = output.get("workflow_stage", output.get("stage", ""))
        if workflow_stage in WORKFLOW_TO_REVIEW_STAGE:
            return WORKFLOW_TO_REVIEW_STAGE[workflow_stage]

        # Check artifact type mapping
        artifact_type = output.get("artifact_type", "")
        type_mapping = {
            "architecture_document": "architecture",
            "design_document": "design",
            "code": "programming",
            "test": "testing",
            "config": "infrastructure",
            "analysis_report": "analysis",
        }
        if artifact_type in type_mapping:
            return type_mapping[artifact_type]

        # Default based on agent
        agent = output.get("agent", "")
        agent_mapping = {
            "Felix": "architecture",
            "Peter": "architecture",
            "Betty": "design",
            "Paul": "programming",
            "Tessa": "testing",
            "Quinn": "testing",
            "Marcus": "analysis",
            "Vicky": "infrastructure",
        }
        return agent_mapping.get(agent)

    def _get_artifact_type(self, output: Dict[str, Any]) -> str:
        """Get artifact type from output."""
        return output.get("artifact_type", "code")

    def _build_review_context(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Build context for review."""
        context = {}

        # Add relevant output metadata
        for key in ["agent", "workflow", "workflow_stage", "project_id"]:
            if key in output:
                context[key] = output[key]

        # Add any existing context
        if "context" in output and isinstance(output["context"], dict):
            context.update(output["context"])

        return context

    def get_stats(self) -> Dict[str, Any]:
        """Get review statistics."""
        total = self._stats["reviews_triggered"]
        return {
            **self._stats,
            "pass_rate": (
                self._stats["reviews_passed"] / total * 100 if total > 0 else 0
            ),
            "improvement_rate": (
                self._stats["improvements_applied"] / self._stats["reviews_failed"] * 100
                if self._stats["reviews_failed"] > 0 else 0
            ),
        }

    def reset_stats(self) -> None:
        """Reset review statistics."""
        self._stats = {
            "reviews_triggered": 0,
            "reviews_passed": 0,
            "reviews_failed": 0,
            "improvements_applied": 0,
        }
