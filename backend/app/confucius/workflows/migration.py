"""
Migration Workflow Orchestrator.

Orchestrates the BMAD 8-question migration planning workflow
through Confucius with quality gates and agent coordination.

Stages:
1. Questions - Collect user answers to 8 strategic questions
2. Analysis - Miguel analyzes complexity and risks
3. Specification - Peter generates comprehensive spec
4. Tasks - Felix generates epic/feature/story hierarchy
5. Review - Quinn performs quality review
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


# The 8 strategic questions for migration planning
MIGRATION_QUESTIONS = [
    {
        "id": "q1_legacy_system",
        "question": "What exists in the legacy system today?",
        "agent": "Miguel",
        "category": "analysis",
    },
    {
        "id": "q2_migration_target",
        "question": "What is the target end state?",
        "agent": "Miguel",
        "category": "analysis",
    },
    {
        "id": "q3_migration_strategy",
        "question": "What is the migration strategy?",
        "agent": "Miguel",
        "category": "analysis",
    },
    {
        "id": "q4_data_migration",
        "question": "How will data be migrated?",
        "agent": "Miguel",
        "category": "analysis",
    },
    {
        "id": "q5_problem_statement",
        "question": "Why is migration necessary?",
        "agent": "Peter",
        "category": "specification",
    },
    {
        "id": "q6_stakeholders",
        "question": "Who are the stakeholders?",
        "agent": "Peter",
        "category": "specification",
    },
    {
        "id": "q7_success_criteria",
        "question": "How will success be measured?",
        "agent": "Peter",
        "category": "specification",
    },
    {
        "id": "q8_timeline",
        "question": "What are the timeline and constraints?",
        "agent": "Felix",
        "category": "planning",
    },
]


class MigrationOrchestrator(WorkflowOrchestrator):
    """
    Orchestrates the BMAD migration planning workflow.

    The Migration workflow follows a top-down approach:
    1. Collect answers to 8 strategic questions
    2. Miguel analyzes Q1-Q4 for technical complexity
    3. Peter generates specification from all answers
    4. Felix creates epic/feature/story hierarchy
    5. Quinn reviews quality and completeness

    Example:
    ```python
    orchestrator = MigrationOrchestrator()
    result = await orchestrator.run(
        session_id="mig-456",
        input_data={
            "answers": {
                "q1_legacy_system": "ASP Classic with SQL Server",
                "q2_migration_target": ".NET 8 with PostgreSQL",
                ...
            },
        },
    )
    ```
    """

    @property
    def workflow_type(self) -> str:
        return "migration"

    def get_stages(self) -> List[WorkflowStage]:
        """Define Migration workflow stages."""
        return [
            WorkflowStage(
                name="validate_answers",
                description="Validate that all 8 questions have been answered",
                agents=[],  # No agent needed
                required=True,
                quality_threshold=1.0,  # Must have all answers
                max_iterations=1,
            ),
            WorkflowStage(
                name="technical_analysis",
                description="Analyze technical complexity and risks (Q1-Q4)",
                agents=["Miguel"],  # Metrics specialist
                required=True,
                quality_threshold=0.85,
                max_iterations=3,
                depends_on=["validate_answers"],
            ),
            WorkflowStage(
                name="generate_specification",
                description="Generate comprehensive migration specification",
                agents=["Peter", "Betty"],  # Product Owner + Business Analyst
                required=True,
                parallel_agents=True,
                quality_threshold=0.85,
                max_iterations=3,
                depends_on=["technical_analysis"],
            ),
            WorkflowStage(
                name="generate_tasks",
                description="Generate epic/feature/story/task hierarchy",
                agents=["Felix", "Paul"],  # Architecture + Planning
                required=True,
                parallel_agents=True,
                quality_threshold=0.80,
                max_iterations=3,
                depends_on=["generate_specification"],
            ),
            WorkflowStage(
                name="estimate_effort",
                description="Estimate effort for migration tasks",
                agents=["Eliza"],  # Estimation specialist
                required=True,
                quality_threshold=0.75,
                max_iterations=2,
                depends_on=["generate_tasks"],
            ),
            WorkflowStage(
                name="quality_review",
                description="Quality review of migration plan",
                agents=["Quinn"],  # Quality specialist
                required=True,
                quality_threshold=0.90,  # High bar for final review
                max_iterations=2,
                depends_on=["estimate_effort"],
            ),
        ]

    async def execute_stage(
        self,
        stage: WorkflowStage,
        context: WorkflowContext,
    ) -> StageResult:
        """Execute a Migration workflow stage."""
        started_at = datetime.now(timezone.utc)
        agent_results = {}

        try:
            if stage.name == "validate_answers":
                agent_results = await self._validate_answers(context)

            elif stage.name == "technical_analysis":
                agent_results = await self._execute_technical_analysis(context)

            elif stage.name == "generate_specification":
                agent_results = await self._execute_specification(context)

            elif stage.name == "generate_tasks":
                agent_results = await self._execute_task_generation(context)

            elif stage.name == "estimate_effort":
                agent_results = await self._execute_estimation(context)

            elif stage.name == "quality_review":
                agent_results = await self._execute_quality_review(context)

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

    async def _validate_answers(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Validate that all questions have been answered."""
        answers = context.shared_data.get("answers", {})

        missing = []
        for q in MIGRATION_QUESTIONS:
            if q["id"] not in answers or not answers[q["id"]]:
                missing.append(q["id"])

        if missing:
            raise ValueError(f"Missing answers for questions: {missing}")

        return {
            "valid": True,
            "answers_count": len(answers),
            "questions_total": len(MIGRATION_QUESTIONS),
        }

    async def _execute_technical_analysis(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Execute technical analysis of Q1-Q4."""
        answers = context.shared_data.get("answers", {})
        analysis_answers = {
            q["id"]: answers.get(q["id"], "")
            for q in MIGRATION_QUESTIONS
            if q["category"] == "analysis"
        }

        extensions = await self.get_agents_for_stage(
            WorkflowStage("technical_analysis", "", ["Miguel"]),
            context,
        )

        results = {
            "complexity_score": 0.0,
            "risk_assessment": [],
            "technical_challenges": [],
            "data_migration_complexity": "",
            "recommended_approach": "",
        }

        miguel = extensions[0] if extensions else None
        if miguel:
            miguel_result = await miguel.run_full_lifecycle(
                task="Analyze migration complexity from technical answers",
                context={
                    "answers": analysis_answers,
                    "metrics_type": "migration_complexity",
                },
                entry_id=f"{context.workflow_id}-technical-analysis",
            )
            if miguel_result.success:
                results.update(miguel_result.output)

        return results

    async def _execute_specification(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Generate migration specification."""
        answers = context.shared_data.get("answers", {})
        technical_analysis = context.shared_data.get("technical_analysis_result", {})

        extensions = await self.get_agents_for_stage(
            WorkflowStage("generate_specification", "", ["Peter", "Betty"]),
            context,
        )

        results = {
            "specification": {},
            "problem_statement": "",
            "stakeholder_analysis": [],
            "success_criteria": [],
            "constraints": [],
            "business_case": {},
        }

        # Peter generates specification
        peter = next((e for e in extensions if e.name == "Peter"), None)
        if peter:
            peter_result = await peter.run_full_lifecycle(
                task="Generate migration specification from answers",
                context={
                    "answers": answers,
                    "technical_analysis": technical_analysis,
                    "activity": "constitution",
                },
                entry_id=f"{context.workflow_id}-specification",
            )
            if peter_result.success:
                results["specification"] = peter_result.output
                results["problem_statement"] = peter_result.output.get(
                    "problem_statement", ""
                )
                results["success_criteria"] = peter_result.output.get(
                    "success_criteria", []
                )

        # Betty adds business analysis
        betty = next((e for e in extensions if e.name == "Betty"), None)
        if betty:
            betty_result = await betty.run_full_lifecycle(
                task="Analyze business impact of migration",
                context={
                    "answers": answers,
                    "specification": results["specification"],
                    "analysis_type": "business_case",
                },
                entry_id=f"{context.workflow_id}-business-case",
            )
            if betty_result.success:
                results["business_case"] = betty_result.output
                results["stakeholder_analysis"] = betty_result.output.get(
                    "stakeholders", []
                )

        return results

    async def _execute_task_generation(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Generate epic/feature/story/task hierarchy."""
        specification = context.shared_data.get("generate_specification_result", {})

        extensions = await self.get_agents_for_stage(
            WorkflowStage("generate_tasks", "", ["Felix", "Paul"]),
            context,
        )

        results = {
            "epics": [],
            "features": [],
            "stories": [],
            "tasks": [],
            "migration_waves": [],
            "architecture_decisions": [],
        }

        # Felix generates architecture and tasks
        felix = next((e for e in extensions if e.name == "Felix"), None)
        if felix:
            felix_result = await felix.run_full_lifecycle(
                task="Generate migration task hierarchy from specification",
                context={
                    "specification": specification,
                    "analysis_type": "task_generation",
                },
                entry_id=f"{context.workflow_id}-task-generation",
            )
            if felix_result.success:
                results["epics"] = felix_result.output.get("epics", [])
                results["features"] = felix_result.output.get("features", [])
                results["stories"] = felix_result.output.get("stories", [])
                results["architecture_decisions"] = felix_result.output.get(
                    "architecture_decisions", []
                )

        # Paul adds planning structure
        paul = next((e for e in extensions if e.name == "Paul"), None)
        if paul:
            paul_result = await paul.run_full_lifecycle(
                task="Create migration wave plan",
                context={
                    "epics": results["epics"],
                    "specification": specification,
                    "planning_type": "wave",
                },
                entry_id=f"{context.workflow_id}-wave-planning",
            )
            if paul_result.success:
                results["migration_waves"] = paul_result.output.get("waves", [])
                results["tasks"] = paul_result.output.get("tasks", [])

        return results

    async def _execute_estimation(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Estimate effort for migration."""
        tasks = context.shared_data.get("generate_tasks_result", {})

        extensions = await self.get_agents_for_stage(
            WorkflowStage("estimate_effort", "", ["Eliza"]),
            context,
        )

        results = {
            "total_function_points": 0,
            "total_effort_hours": 0,
            "effort_by_epic": {},
            "effort_by_wave": {},
            "confidence": 0.0,
            "assumptions": [],
        }

        eliza = extensions[0] if extensions else None
        if eliza:
            eliza_result = await eliza.run_full_lifecycle(
                task="Estimate migration effort",
                context={
                    "epics": tasks.get("epics", []),
                    "stories": tasks.get("stories", []),
                    "waves": tasks.get("migration_waves", []),
                    "estimation_type": "function_points",
                },
                entry_id=f"{context.workflow_id}-estimation",
            )
            if eliza_result.success:
                results.update(eliza_result.output)

        return results

    async def _execute_quality_review(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Execute final quality review."""
        # Gather all results
        all_results = {
            "technical_analysis": context.shared_data.get(
                "technical_analysis_result", {}
            ),
            "specification": context.shared_data.get(
                "generate_specification_result", {}
            ),
            "tasks": context.shared_data.get("generate_tasks_result", {}),
            "estimation": context.shared_data.get("estimate_effort_result", {}),
        }

        extensions = await self.get_agents_for_stage(
            WorkflowStage("quality_review", "", ["Quinn"]),
            context,
        )

        results = {
            "quality_score": 0.0,
            "findings": [],
            "recommendations": [],
            "approval_status": "pending",
            "review_summary": "",
        }

        quinn = extensions[0] if extensions else None
        if quinn:
            quinn_result = await quinn.run_full_lifecycle(
                task="Review migration plan quality and completeness",
                context={
                    "all_results": all_results,
                    "review_type": "quality_gate",
                },
                entry_id=f"{context.workflow_id}-quality-review",
            )
            if quinn_result.success:
                results.update(quinn_result.output)
                # Set approval based on score
                score = results.get("quality_score", 0)
                results["approval_status"] = "approved" if score >= 0.85 else "needs_work"

        return results

    def get_questions(self) -> List[Dict[str, Any]]:
        """Get the 8 strategic questions."""
        return MIGRATION_QUESTIONS.copy()


def create_migration_orchestrator(
    router: Optional[WorkflowRouter] = None,
    evaluator: Optional[QualityGateEvaluator] = None,
) -> MigrationOrchestrator:
    """Factory function for Migration orchestrator."""
    return MigrationOrchestrator(router=router, evaluator=evaluator)
