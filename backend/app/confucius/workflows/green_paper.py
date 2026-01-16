"""
Green Paper Workflow Orchestrator.

Orchestrates the greenfield project specification workflow
through Confucius with quality gates and agent coordination.

Stages:
1. Vision Definition - Collect project vision and goals
2. Requirements - Peter generates requirements constitution
3. Design - Vicky creates UI/UX specifications
4. Architecture - Felix designs system architecture
5. Planning - Paul creates implementation plan
6. Review - Quinn performs quality review
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


# Green Paper questions for greenfield projects
GREEN_PAPER_QUESTIONS = [
    {
        "id": "vision",
        "question": "What is the product vision?",
        "description": "Describe the core purpose and value proposition",
    },
    {
        "id": "users",
        "question": "Who are the target users?",
        "description": "Describe primary and secondary user personas",
    },
    {
        "id": "problems",
        "question": "What problems does it solve?",
        "description": "List the key pain points being addressed",
    },
    {
        "id": "features",
        "question": "What are the core features?",
        "description": "List must-have features for MVP",
    },
    {
        "id": "constraints",
        "question": "What are the constraints?",
        "description": "Technical, budget, timeline, or regulatory constraints",
    },
    {
        "id": "success",
        "question": "How will success be measured?",
        "description": "Key metrics and success criteria",
    },
]


class GreenPaperOrchestrator(WorkflowOrchestrator):
    """
    Orchestrates the Green Paper greenfield project workflow.

    The Green Paper workflow follows a top-down approach:
    1. Define vision and collect answers to 6 questions
    2. Peter generates requirements constitution
    3. Vicky creates UI/UX design specifications
    4. Felix designs system architecture
    5. Paul creates implementation roadmap
    6. Quinn reviews quality and completeness

    Example:
    ```python
    orchestrator = GreenPaperOrchestrator()
    result = await orchestrator.run(
        session_id="gp-789",
        input_data={
            "project_name": "TaskFlow Pro",
            "answers": {
                "vision": "A collaborative task management platform...",
                "users": "Small to medium development teams...",
                ...
            },
        },
    )
    ```
    """

    @property
    def workflow_type(self) -> str:
        return "green_paper"

    def get_stages(self) -> List[WorkflowStage]:
        """Define Green Paper workflow stages."""
        return [
            WorkflowStage(
                name="validate_vision",
                description="Validate vision and answers completeness",
                agents=[],  # No agent needed
                required=True,
                quality_threshold=1.0,
                max_iterations=1,
            ),
            WorkflowStage(
                name="requirements_constitution",
                description="Generate requirements constitution from vision",
                agents=["Peter", "Betty"],  # Product Owner + Business Analyst
                required=True,
                parallel_agents=True,
                quality_threshold=0.85,
                max_iterations=3,
                depends_on=["validate_vision"],
            ),
            WorkflowStage(
                name="ux_design",
                description="Create UI/UX design specifications",
                agents=["Vicky"],  # Visual Designer
                required=True,
                quality_threshold=0.80,
                max_iterations=3,
                depends_on=["requirements_constitution"],
            ),
            WorkflowStage(
                name="architecture_design",
                description="Design system architecture",
                agents=["Felix"],  # Architecture specialist
                required=True,
                quality_threshold=0.85,
                max_iterations=3,
                depends_on=["requirements_constitution", "ux_design"],
            ),
            # Fase 37: Security requirements review stage
            WorkflowStage(
                name="security_requirements",
                description="Review architecture security requirements",
                agents=["Quinn"],  # Security specialist
                required=True,
                quality_threshold=0.80,
                max_iterations=2,
                depends_on=["architecture_design"],
            ),
            WorkflowStage(
                name="implementation_planning",
                description="Create implementation roadmap and sprints",
                agents=["Paul", "Eliza"],  # Planning + Estimation
                required=True,
                parallel_agents=True,
                quality_threshold=0.80,
                max_iterations=2,
                depends_on=["security_requirements"],  # Fase 37: Now depends on security review
            ),
            WorkflowStage(
                name="quality_review",
                description="Final quality review of all specifications",
                agents=["Quinn"],  # Quality specialist
                required=True,
                quality_threshold=0.90,
                max_iterations=2,
                depends_on=["implementation_planning"],
            ),
        ]

    async def execute_stage(
        self,
        stage: WorkflowStage,
        context: WorkflowContext,
    ) -> StageResult:
        """Execute a Green Paper workflow stage."""
        started_at = datetime.now(timezone.utc)
        agent_results = {}

        try:
            if stage.name == "validate_vision":
                agent_results = await self._validate_vision(context)

            elif stage.name == "requirements_constitution":
                agent_results = await self._execute_requirements(context)

            elif stage.name == "ux_design":
                agent_results = await self._execute_ux_design(context)

            elif stage.name == "architecture_design":
                agent_results = await self._execute_architecture(context)

            # Fase 37: Security requirements review
            elif stage.name == "security_requirements":
                agent_results = await self._execute_security_requirements(context)

            elif stage.name == "implementation_planning":
                agent_results = await self._execute_planning(context)

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

    async def _validate_vision(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Validate vision and answers."""
        answers = context.shared_data.get("answers", {})
        project_name = context.shared_data.get("project_name", "")

        if not project_name:
            raise ValueError("Project name is required")

        missing = []
        for q in GREEN_PAPER_QUESTIONS:
            if q["id"] not in answers or not answers[q["id"]]:
                missing.append(q["id"])

        if missing:
            raise ValueError(f"Missing answers for: {missing}")

        return {
            "valid": True,
            "project_name": project_name,
            "answers_count": len(answers),
        }

    async def _execute_requirements(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Generate requirements constitution."""
        answers = context.shared_data.get("answers", {})
        project_name = context.shared_data.get("project_name", "")

        extensions = await self.get_agents_for_stage(
            WorkflowStage("requirements_constitution", "", ["Peter", "Betty"]),
            context,
        )

        results = {
            "constitution": {},
            "user_personas": [],
            "user_stories": [],
            "acceptance_criteria": [],
            "business_requirements": [],
        }

        # Peter generates constitution
        peter = next((e for e in extensions if e.name == "Peter"), None)
        if peter:
            peter_result = await peter.run_full_lifecycle(
                task=f"Generate requirements constitution for {project_name}",
                context={
                    "answers": answers,
                    "project_name": project_name,
                    "activity": "constitution",
                },
                entry_id=f"{context.workflow_id}-constitution",
            )
            if peter_result.success:
                results["constitution"] = peter_result.output
                results["user_stories"] = peter_result.output.get("stories", [])

        # Betty adds business requirements
        betty = next((e for e in extensions if e.name == "Betty"), None)
        if betty:
            betty_result = await betty.run_full_lifecycle(
                task="Define business requirements and personas",
                context={
                    "answers": answers,
                    "constitution": results["constitution"],
                    "analysis_type": "requirements",
                },
                entry_id=f"{context.workflow_id}-business-req",
            )
            if betty_result.success:
                results["user_personas"] = betty_result.output.get("personas", [])
                results["business_requirements"] = betty_result.output.get(
                    "requirements", []
                )

        return results

    async def _execute_ux_design(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Create UI/UX design specifications."""
        requirements = context.shared_data.get("requirements_constitution_result", {})
        project_name = context.shared_data.get("project_name", "")

        extensions = await self.get_agents_for_stage(
            WorkflowStage("ux_design", "", ["Vicky"]),
            context,
        )

        results = {
            "ui_specs": [],
            "design_tokens": {},
            "wireframes": [],
            "user_flows": [],
            "component_library": [],
        }

        vicky = extensions[0] if extensions else None
        if vicky:
            vicky_result = await vicky.run_full_lifecycle(
                task=f"Create UI/UX design for {project_name}",
                context={
                    "requirements": requirements,
                    "personas": requirements.get("user_personas", []),
                    "vicky_activity": "ui_spec",
                    "tier": "PROFESSIONAL",
                },
                entry_id=f"{context.workflow_id}-ux-design",
            )
            if vicky_result.success:
                results.update(vicky_result.output)

        return results

    async def _execute_architecture(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Design system architecture."""
        requirements = context.shared_data.get("requirements_constitution_result", {})
        ux_design = context.shared_data.get("ux_design_result", {})
        project_name = context.shared_data.get("project_name", "")

        extensions = await self.get_agents_for_stage(
            WorkflowStage("architecture_design", "", ["Felix"]),
            context,
        )

        results = {
            "architecture_decisions": [],
            "component_diagram": {},
            "technology_stack": [],
            "api_design": {},
            "data_model": {},
            "infrastructure": {},
        }

        felix = extensions[0] if extensions else None
        if felix:
            felix_result = await felix.run_full_lifecycle(
                task=f"Design architecture for {project_name}",
                context={
                    "requirements": requirements,
                    "ux_design": ux_design,
                    "analysis_type": "pattern_recommendation",
                },
                entry_id=f"{context.workflow_id}-architecture",
            )
            if felix_result.success:
                results.update(felix_result.output)

        return results

    # Fase 37: Security requirements review stage
    async def _execute_security_requirements(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Execute security requirements review for new project."""
        architecture = context.shared_data.get("architecture_design_result", {})
        requirements = context.shared_data.get("requirements_constitution_result", {})
        project_name = context.shared_data.get("project_name", "")

        # Extract tech stack from architecture
        tech_stack = architecture.get("technology_stack", [])

        extensions = await self.get_agents_for_stage(
            WorkflowStage("security_requirements", "", ["Quinn"]),
            context,
        )

        results = {
            "security_requirements": {
                "authentication": [],
                "authorization": [],
                "data_protection": [],
                "input_validation": [],
                "logging_audit": [],
                "dependency_policy": {},
                "recommended_scanners": [],
                "cwe_focus_areas": [],
            },
            "passes_gate": True,
        }

        quinn = extensions[0] if extensions else None
        if quinn:
            quinn_result = await quinn.run_full_lifecycle(
                task=f"Review security requirements for new {', '.join(tech_stack) if tech_stack else 'unknown'} project architecture",
                context={
                    "architecture": architecture,
                    "tech_stack": tech_stack,
                    "requirements": requirements,
                    "review_type": "security_requirements",
                    "project_path": context.input_data.get("project_path"),
                },
                entry_id=f"{context.workflow_id}-security-requirements",
            )
            if quinn_result.success:
                output = quinn_result.output
                results["security_requirements"].update({
                    "authentication": output.get("auth_requirements", []),
                    "authorization": output.get("authz_requirements", []),
                    "data_protection": output.get("data_requirements", []),
                    "input_validation": output.get("input_requirements", []),
                    "logging_audit": output.get("logging_requirements", []),
                    "dependency_policy": output.get("dependency_policy", {}),
                    "recommended_scanners": output.get("recommended_scanners", []),
                    "cwe_focus_areas": output.get("cwe_focus", []),
                })
                results["passes_gate"] = output.get("passes_gate", True)

                # Also store security issues if any
                if output.get("security_issues"):
                    results["security_issues"] = output.get("security_issues", [])

        # Store in shared data for Diana and other agents
        context.shared_data["security_requirements"] = results["security_requirements"]

        return results

    async def _execute_planning(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Create implementation plan."""
        requirements = context.shared_data.get("requirements_constitution_result", {})
        architecture = context.shared_data.get("architecture_design_result", {})

        extensions = await self.get_agents_for_stage(
            WorkflowStage("implementation_planning", "", ["Paul", "Eliza"]),
            context,
        )

        results = {
            "roadmap": [],
            "sprints": [],
            "milestones": [],
            "dependencies": [],
            "effort_estimate": {},
            "risk_assessment": [],
        }

        # Paul creates roadmap
        paul = next((e for e in extensions if e.name == "Paul"), None)
        if paul:
            paul_result = await paul.run_full_lifecycle(
                task="Create implementation roadmap",
                context={
                    "requirements": requirements,
                    "architecture": architecture,
                    "planning_type": "release",
                },
                entry_id=f"{context.workflow_id}-roadmap",
            )
            if paul_result.success:
                results["roadmap"] = paul_result.output.get("roadmap", [])
                results["sprints"] = paul_result.output.get("sprints", [])
                results["milestones"] = paul_result.output.get("milestones", [])

        # Eliza estimates effort
        eliza = next((e for e in extensions if e.name == "Eliza"), None)
        if eliza:
            eliza_result = await eliza.run_full_lifecycle(
                task="Estimate implementation effort",
                context={
                    "stories": requirements.get("user_stories", []),
                    "sprints": results["sprints"],
                    "estimation_type": "effort",
                },
                entry_id=f"{context.workflow_id}-estimation",
            )
            if eliza_result.success:
                results["effort_estimate"] = eliza_result.output

        return results

    async def _execute_quality_review(
        self,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Execute final quality review."""
        all_results = {
            "requirements": context.shared_data.get(
                "requirements_constitution_result", {}
            ),
            "ux_design": context.shared_data.get("ux_design_result", {}),
            "architecture": context.shared_data.get("architecture_design_result", {}),
            "planning": context.shared_data.get("implementation_planning_result", {}),
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
            "completeness_check": {},
        }

        quinn = extensions[0] if extensions else None
        if quinn:
            quinn_result = await quinn.run_full_lifecycle(
                task="Review greenfield project specifications",
                context={
                    "all_results": all_results,
                    "review_type": "quality_gate",
                },
                entry_id=f"{context.workflow_id}-quality-review",
            )
            if quinn_result.success:
                results.update(quinn_result.output)
                score = results.get("quality_score", 0)
                results["approval_status"] = "approved" if score >= 0.85 else "needs_work"

        return results

    def get_questions(self) -> List[Dict[str, Any]]:
        """Get the 6 Green Paper questions."""
        return GREEN_PAPER_QUESTIONS.copy()


def create_green_paper_orchestrator(
    router: Optional[WorkflowRouter] = None,
    evaluator: Optional[QualityGateEvaluator] = None,
) -> GreenPaperOrchestrator:
    """Factory function for Green Paper orchestrator."""
    return GreenPaperOrchestrator(router=router, evaluator=evaluator)
