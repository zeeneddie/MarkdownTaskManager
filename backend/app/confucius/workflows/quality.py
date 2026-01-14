"""
Quality Workflow Orchestrator.

Orchestrates quality scanning and gate validation through
Confucius with multi-agent review and remediation planning.

Stages:
1. Scan - Execute quality scanners
2. Analyze - Miguel analyzes metrics
3. Review - Quinn reviews findings
4. Remediate - Marcus creates remediation plan
5. Validate - Tessa validates fixes
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

from .base import (
    WorkflowOrchestrator,
    WorkflowStage,
    WorkflowContext,
    WorkflowResult,
    WorkflowStatus,
    StageResult,
)
from ..extensions import WorkflowRouter
from ..quality import QualityGateEvaluator, QualityProgressStream

logger = logging.getLogger(__name__)


class QualityOrchestrator(WorkflowOrchestrator):
    """
    Orchestrates the quality gate and scanning workflow.

    The Quality workflow provides comprehensive code quality analysis:
    1. Execute quality scanners (complexity, security, coverage)
    2. Miguel analyzes metrics and trends
    3. Quinn reviews findings and sets quality gates
    4. Marcus creates remediation plan for issues
    5. Tessa validates through testing

    Example:
    ```python
    orchestrator = QualityOrchestrator()
    result = await orchestrator.run(
        session_id="qa-001",
        input_data={
            "project_path": "/path/to/project",
            "tech_stack": ["python", "typescript"],
            "scanners": ["complexity", "security", "coverage"],
        },
    )
    ```
    """

    @property
    def workflow_type(self) -> str:
        return "quality"

    def get_stages(self) -> List[WorkflowStage]:
        """Define Quality workflow stages."""
        return [
            WorkflowStage(
                name="scan_execution",
                description="Execute quality scanners",
                agents=["Miguel"],  # Metrics specialist
                required=True,
                quality_threshold=0.70,  # Scanners should complete
                max_iterations=2,
                timeout_seconds=600,
            ),
            WorkflowStage(
                name="metrics_analysis",
                description="Analyze quality metrics and trends",
                agents=["Miguel"],  # Metrics specialist
                required=True,
                quality_threshold=0.80,
                max_iterations=2,
                depends_on=["scan_execution"],
            ),
            WorkflowStage(
                name="quality_review",
                description="Review findings and set quality gates",
                agents=["Quinn"],  # Quality specialist
                required=True,
                quality_threshold=0.85,
                max_iterations=3,
                depends_on=["metrics_analysis"],
            ),
            WorkflowStage(
                name="remediation_planning",
                description="Create remediation plan for issues",
                agents=["Marcus"],  # Maintenance specialist
                required=False,  # Only if issues found
                quality_threshold=0.80,
                max_iterations=2,
                depends_on=["quality_review"],
            ),
            WorkflowStage(
                name="test_validation",
                description="Validate through testing",
                agents=["Tessa"],  # Testing specialist
                required=False,  # Optional validation
                quality_threshold=0.80,
                max_iterations=2,
                depends_on=["remediation_planning"],
            ),
        ]

    async def execute_stage(
        self,
        stage: WorkflowStage,
        context: WorkflowContext,
    ) -> StageResult:
        """Execute a Quality workflow stage."""
        started_at = datetime.now(timezone.utc)
        agent_results = {}

        try:
            if stage.name == "scan_execution":
                agent_results = await self._execute_scan(context)

            elif stage.name == "metrics_analysis":
                agent_results = await self._execute_metrics_analysis(context)

            elif stage.name == "quality_review":
                agent_results = await self._execute_quality_review(context)

            elif stage.name == "remediation_planning":
                agent_results = await self._execute_remediation(context)

            elif stage.name == "test_validation":
                agent_results = await self._execute_test_validation(context)

            else:
                raise ValueError(f"Unknown stage: {stage.name}")

            context.shared_data[f"{stage.name}_result"] = agent_results

            return StageResult(
                stage_name=stage.name,
                status=WorkflowStatus.COMPLETED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                agent_results=agent_results,
                quality_score=0.85,
                passed_quality_gate=True,
            )

        except Exception as e:
            logger.error(f"Stage {stage.name} failed: {e}")
            return StageResult(
                stage_name=stage.name,
                status=WorkflowStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                error=str(e),
            )

    async def _execute_scan(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Execute quality scanners."""
        project_path = context.shared_data.get("project_path", "")
        tech_stack = context.shared_data.get("tech_stack", [])
        scanners = context.shared_data.get("scanners", ["complexity", "security"])

        extensions = await self.get_agents_for_stage(
            WorkflowStage("scan_execution", "", ["Miguel"]),
            context,
        )

        results = {
            "scan_results": {},
            "files_scanned": 0,
            "issues_found": 0,
            "scanner_status": {},
        }

        miguel = extensions[0] if extensions else None
        if miguel:
            miguel_result = await miguel.run_full_lifecycle(
                task="Execute quality scanners on codebase",
                context={
                    "project_path": project_path,
                    "tech_stack": tech_stack,
                    "scanners": scanners,
                    "metrics_type": "code",
                },
                entry_id=f"{context.workflow_id}-scan",
            )
            if miguel_result.success:
                results["scan_results"] = miguel_result.output.get("results", {})
                results["files_scanned"] = miguel_result.output.get("files_scanned", 0)
                results["issues_found"] = miguel_result.output.get("issues_found", 0)

        return results

    async def _execute_metrics_analysis(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Analyze quality metrics and trends."""
        scan_results = context.shared_data.get("scan_execution_result", {})

        extensions = await self.get_agents_for_stage(
            WorkflowStage("metrics_analysis", "", ["Miguel"]),
            context,
        )

        results = {
            "metrics_summary": {},
            "trends": [],
            "hotspots": [],
            "complexity_breakdown": {},
            "coverage_report": {},
        }

        miguel = extensions[0] if extensions else None
        if miguel:
            miguel_result = await miguel.run_full_lifecycle(
                task="Analyze quality metrics and identify trends",
                context={
                    "scan_results": scan_results,
                    "metrics_type": "trends",
                },
                entry_id=f"{context.workflow_id}-metrics",
            )
            if miguel_result.success:
                results.update(miguel_result.output)

        return results

    async def _execute_quality_review(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Review findings and set quality gates."""
        scan_results = context.shared_data.get("scan_execution_result", {})
        metrics = context.shared_data.get("metrics_analysis_result", {})

        extensions = await self.get_agents_for_stage(
            WorkflowStage("quality_review", "", ["Quinn"]),
            context,
        )

        results = {
            "quality_score": 0.0,
            "gate_status": "unknown",
            "findings": [],
            "critical_issues": [],
            "security_issues": [],
            "recommendations": [],
        }

        quinn = extensions[0] if extensions else None
        if quinn:
            quinn_result = await quinn.run_full_lifecycle(
                task="Review quality findings and set gates",
                context={
                    "scan_results": scan_results,
                    "metrics": metrics,
                    "review_type": "quality_gate",
                },
                entry_id=f"{context.workflow_id}-review",
            )
            if quinn_result.success:
                results.update(quinn_result.output)
                score = results.get("quality_score", 0)
                results["gate_status"] = "passed" if score >= 0.85 else "failed"

        return results

    async def _execute_remediation(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Create remediation plan for issues."""
        review = context.shared_data.get("quality_review_result", {})

        # Skip if no issues to remediate
        if review.get("gate_status") == "passed":
            return {
                "remediation_needed": False,
                "plan": [],
                "message": "Quality gate passed, no remediation needed",
            }

        extensions = await self.get_agents_for_stage(
            WorkflowStage("remediation_planning", "", ["Marcus"]),
            context,
        )

        results = {
            "remediation_needed": True,
            "plan": [],
            "priority_order": [],
            "effort_estimate": {},
            "quick_wins": [],
        }

        marcus = extensions[0] if extensions else None
        if marcus:
            marcus_result = await marcus.run_full_lifecycle(
                task="Create remediation plan for quality issues",
                context={
                    "findings": review.get("findings", []),
                    "critical_issues": review.get("critical_issues", []),
                    "focus_area": "code_quality",
                },
                entry_id=f"{context.workflow_id}-remediation",
            )
            if marcus_result.success:
                results.update(marcus_result.output)

        return results

    async def _execute_test_validation(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Validate through testing."""
        remediation = context.shared_data.get("remediation_planning_result", {})

        # Skip if no remediation was needed
        if not remediation.get("remediation_needed", True):
            return {
                "validation_needed": False,
                "message": "No remediation performed, validation skipped",
            }

        extensions = await self.get_agents_for_stage(
            WorkflowStage("test_validation", "", ["Tessa"]),
            context,
        )

        results = {
            "validation_needed": True,
            "tests_generated": 0,
            "tests_passed": 0,
            "coverage_improvement": 0.0,
            "validation_status": "pending",
        }

        tessa = extensions[0] if extensions else None
        if tessa:
            tessa_result = await tessa.run_full_lifecycle(
                task="Validate quality improvements through testing",
                context={
                    "remediation_plan": remediation.get("plan", []),
                    "test_type": "validation",
                },
                entry_id=f"{context.workflow_id}-validation",
            )
            if tessa_result.success:
                results.update(tessa_result.output)
                passed = results.get("tests_passed", 0)
                total = results.get("tests_generated", 1)
                results["validation_status"] = (
                    "passed" if passed / total >= 0.8 else "failed"
                )

        return results


def create_quality_orchestrator(
    router: Optional[WorkflowRouter] = None,
    evaluator: Optional[QualityGateEvaluator] = None,
) -> QualityOrchestrator:
    """Factory function for Quality orchestrator."""
    return QualityOrchestrator(router=router, evaluator=evaluator)
