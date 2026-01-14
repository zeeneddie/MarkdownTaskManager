"""
Brown Paper Workflow Orchestrator.

Orchestrates the 6-phase Brown Paper analysis workflow through
Confucius for legacy code analysis with quality gates.

Phases:
1. Code Understanding (DependencyGraph, CodeAnalysis, LayeredAnalysis)
2. Domain Extraction (Peter agent)
3. Story Extraction (HierarchicalStoryExtractionService)
4. Deep Extraction (LLM Council)
5. Estimation (FP/Effort estimation)
6. Output Consolidation
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


class BrownPaperOrchestrator(WorkflowOrchestrator):
    """
    Orchestrates the Brown Paper legacy analysis workflow.

    The Brown Paper workflow analyzes legacy codebases bottom-up:
    1. Scan and understand code structure
    2. Extract business domains
    3. Generate user stories from code
    4. Deep extraction with LLM council
    5. Estimate effort (FP methodology)
    6. Consolidate outputs

    Example:
    ```python
    orchestrator = BrownPaperOrchestrator()
    result = await orchestrator.run(
        session_id="bp-123",
        input_data={
            "application_id": "legacy-app",
            "scan_path": "/path/to/code",
            "tech_stack": ["asp", "vbnet", "sql"],
        },
    )
    ```
    """

    @property
    def workflow_type(self) -> str:
        return "brown_paper"

    def get_stages(self) -> List[WorkflowStage]:
        """Define Brown Paper workflow stages."""
        return [
            WorkflowStage(
                name="code_understanding",
                description="Analyze code structure, dependencies, and layers",
                agents=["Miguel"],  # Metrics specialist
                required=True,
                quality_threshold=0.80,
                max_iterations=2,
                timeout_seconds=600,
            ),
            WorkflowStage(
                name="domain_extraction",
                description="Extract business domains from code analysis",
                agents=["Peter", "Betty"],  # Product Owner + Business Analyst
                required=True,
                parallel_agents=True,
                quality_threshold=0.85,
                max_iterations=3,
                depends_on=["code_understanding"],
            ),
            WorkflowStage(
                name="story_extraction",
                description="Generate user stories from domains",
                agents=["Peter"],  # Product Owner
                required=True,
                quality_threshold=0.80,
                max_iterations=3,
                depends_on=["domain_extraction"],
            ),
            WorkflowStage(
                name="deep_extraction",
                description="Deep analysis with LLM council review",
                agents=["Felix", "Quinn", "Marcus"],  # Architecture, Quality, Maintenance
                required=False,  # Optional enhancement
                parallel_agents=True,
                quality_threshold=0.85,
                max_iterations=2,
                depends_on=["story_extraction"],
            ),
            WorkflowStage(
                name="estimation",
                description="Estimate effort using FP methodology",
                agents=["Eliza"],  # Estimation specialist
                required=True,
                quality_threshold=0.75,
                max_iterations=2,
                depends_on=["story_extraction"],
            ),
            WorkflowStage(
                name="output_consolidation",
                description="Consolidate all outputs into final report",
                agents=["Diana"],  # Documentation specialist
                required=True,
                quality_threshold=0.80,
                max_iterations=2,
                depends_on=["estimation"],
            ),
        ]

    async def execute_stage(
        self,
        stage: WorkflowStage,
        context: WorkflowContext,
    ) -> StageResult:
        """Execute a Brown Paper workflow stage."""
        started_at = datetime.now(timezone.utc)
        agent_results = {}

        try:
            if stage.name == "code_understanding":
                agent_results = await self._execute_code_understanding(context)

            elif stage.name == "domain_extraction":
                agent_results = await self._execute_domain_extraction(context)

            elif stage.name == "story_extraction":
                agent_results = await self._execute_story_extraction(context)

            elif stage.name == "deep_extraction":
                agent_results = await self._execute_deep_extraction(context)

            elif stage.name == "estimation":
                agent_results = await self._execute_estimation(context)

            elif stage.name == "output_consolidation":
                agent_results = await self._execute_consolidation(context)

            else:
                raise ValueError(f"Unknown stage: {stage.name}")

            # Store results in shared data
            context.shared_data[f"{stage.name}_result"] = agent_results

            return StageResult(
                stage_name=stage.name,
                status=WorkflowStatus.COMPLETED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                agent_results=agent_results,
                quality_score=0.85,  # Will be set by quality gate
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

    async def _execute_code_understanding(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Execute code understanding phase."""
        scan_path = context.shared_data.get("scan_path", "")
        tech_stack = context.shared_data.get("tech_stack", [])

        # Get Miguel extension for metrics
        extensions = await self.get_agents_for_stage(
            WorkflowStage("code_understanding", "", ["Miguel"]),
            context,
        )

        results = {
            "files_scanned": 0,
            "lines_of_code": 0,
            "complexity_score": 0.0,
            "dependency_graph": {},
            "layer_analysis": {},
            "tech_stack_detected": tech_stack,
        }

        if extensions:
            miguel = extensions[0]
            ext_result = await miguel.run_full_lifecycle(
                task=f"Analyze code structure at {scan_path}",
                context={
                    "scan_path": scan_path,
                    "tech_stack": tech_stack,
                    "analysis_type": "code_metrics",
                },
                entry_id=f"{context.workflow_id}-code-understanding",
            )

            if ext_result.success:
                results.update(ext_result.output.get("metrics", {}))

        return results

    async def _execute_domain_extraction(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Execute domain extraction phase."""
        code_analysis = context.shared_data.get("code_understanding_result", {})

        extensions = await self.get_agents_for_stage(
            WorkflowStage("domain_extraction", "", ["Peter", "Betty"]),
            context,
        )

        results = {
            "domains": [],
            "domain_boundaries": {},
            "business_capabilities": [],
        }

        # Peter extracts domains
        peter = next((e for e in extensions if e.name == "Peter"), None)
        if peter:
            peter_result = await peter.run_full_lifecycle(
                task="Extract business domains from code analysis",
                context={
                    "code_analysis": code_analysis,
                    "activity": "domain_extraction",
                },
                entry_id=f"{context.workflow_id}-domain-extraction",
            )
            if peter_result.success:
                results["domains"] = peter_result.output.get("domains", [])

        # Betty analyzes business capabilities
        betty = next((e for e in extensions if e.name == "Betty"), None)
        if betty:
            betty_result = await betty.run_full_lifecycle(
                task="Identify business capabilities from domains",
                context={
                    "domains": results["domains"],
                    "code_analysis": code_analysis,
                },
                entry_id=f"{context.workflow_id}-business-capabilities",
            )
            if betty_result.success:
                results["business_capabilities"] = betty_result.output.get(
                    "capabilities", []
                )

        return results

    async def _execute_story_extraction(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Execute story extraction phase."""
        domains = context.shared_data.get("domain_extraction_result", {}).get(
            "domains", []
        )

        extensions = await self.get_agents_for_stage(
            WorkflowStage("story_extraction", "", ["Peter"]),
            context,
        )

        results = {
            "epics": [],
            "stories": [],
            "story_count": 0,
        }

        peter = extensions[0] if extensions else None
        if peter:
            peter_result = await peter.run_full_lifecycle(
                task="Generate user stories from business domains",
                context={
                    "domains": domains,
                    "activity": "stories",
                },
                entry_id=f"{context.workflow_id}-story-extraction",
            )
            if peter_result.success:
                results["epics"] = peter_result.output.get("epics", [])
                results["stories"] = peter_result.output.get("stories", [])
                results["story_count"] = len(results["stories"])

        return results

    async def _execute_deep_extraction(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Execute deep extraction with LLM council."""
        stories = context.shared_data.get("story_extraction_result", {}).get(
            "stories", []
        )
        code_analysis = context.shared_data.get("code_understanding_result", {})

        extensions = await self.get_agents_for_stage(
            WorkflowStage("deep_extraction", "", ["Felix", "Quinn", "Marcus"]),
            context,
        )

        results = {
            "architecture_insights": {},
            "quality_findings": [],
            "maintenance_recommendations": [],
            "council_consensus": {},
        }

        # Run agents in parallel (simplified - in practice use asyncio.gather)
        for ext in extensions:
            if ext.name == "Felix":
                felix_result = await ext.run_full_lifecycle(
                    task="Analyze architecture patterns in legacy code",
                    context={"code_analysis": code_analysis, "stories": stories},
                    entry_id=f"{context.workflow_id}-felix-deep",
                )
                if felix_result.success:
                    results["architecture_insights"] = felix_result.output

            elif ext.name == "Quinn":
                quinn_result = await ext.run_full_lifecycle(
                    task="Review code quality and identify issues",
                    context={"code_analysis": code_analysis},
                    entry_id=f"{context.workflow_id}-quinn-deep",
                )
                if quinn_result.success:
                    results["quality_findings"] = quinn_result.output.get(
                        "findings", []
                    )

            elif ext.name == "Marcus":
                marcus_result = await ext.run_full_lifecycle(
                    task="Assess maintainability and technical debt",
                    context={"code_analysis": code_analysis},
                    entry_id=f"{context.workflow_id}-marcus-deep",
                )
                if marcus_result.success:
                    results["maintenance_recommendations"] = marcus_result.output.get(
                        "recommendations", []
                    )

        return results

    async def _execute_estimation(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Execute estimation phase."""
        stories = context.shared_data.get("story_extraction_result", {}).get(
            "stories", []
        )

        extensions = await self.get_agents_for_stage(
            WorkflowStage("estimation", "", ["Eliza"]),
            context,
        )

        results = {
            "total_function_points": 0,
            "effort_hours": 0,
            "confidence": 0.0,
            "story_estimates": [],
        }

        eliza = extensions[0] if extensions else None
        if eliza:
            eliza_result = await eliza.run_full_lifecycle(
                task="Estimate effort using function point methodology",
                context={
                    "stories": stories,
                    "estimation_type": "function_points",
                },
                entry_id=f"{context.workflow_id}-estimation",
            )
            if eliza_result.success:
                results.update(eliza_result.output)

        return results

    async def _execute_consolidation(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Execute output consolidation phase."""
        extensions = await self.get_agents_for_stage(
            WorkflowStage("output_consolidation", "", ["Diana"]),
            context,
        )

        # Gather all previous results
        all_results = {
            "code_analysis": context.shared_data.get("code_understanding_result", {}),
            "domains": context.shared_data.get("domain_extraction_result", {}),
            "stories": context.shared_data.get("story_extraction_result", {}),
            "deep_analysis": context.shared_data.get("deep_extraction_result", {}),
            "estimation": context.shared_data.get("estimation_result", {}),
        }

        results = {
            "summary": "",
            "report_sections": [],
            "recommendations": [],
            "next_steps": [],
        }

        diana = extensions[0] if extensions else None
        if diana:
            diana_result = await diana.run_full_lifecycle(
                task="Generate comprehensive Brown Paper analysis report",
                context={
                    "all_results": all_results,
                    "doc_type": "analysis_report",
                },
                entry_id=f"{context.workflow_id}-consolidation",
            )
            if diana_result.success:
                results.update(diana_result.output)

        return results


def create_brown_paper_orchestrator(
    router: Optional[WorkflowRouter] = None,
    evaluator: Optional[QualityGateEvaluator] = None,
) -> BrownPaperOrchestrator:
    """Factory function for Brown Paper orchestrator."""
    return BrownPaperOrchestrator(router=router, evaluator=evaluator)
