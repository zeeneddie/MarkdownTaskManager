"""
Base Workflow Orchestrator for Confucius Integration.

Provides the foundation for orchestrating multi-stage workflows
through the Confucius agent system with quality gates,
progress streaming, and cross-session learning.
"""

from typing import Dict, Any, List, Optional, Callable, Awaitable, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from abc import ABC, abstractmethod
import asyncio
import logging

from ..extensions import ExtensionRouter, WorkflowRouter, create_default_router
from ..extensions.base import BaseAgentExtension, ExtensionResult
from ..quality import (
    QualityGateEvaluator,
    IterationController,
    EscalationService,
    QualityProgressStream,
    StreamEventType,
    GateDecision,
    create_evaluator,
    create_iteration_controller,
    create_escalation_service,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class WorkflowStatus(str, Enum):
    """Status of a workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


@dataclass
class WorkflowStage:
    """Definition of a workflow stage."""
    name: str
    description: str
    agents: List[str]
    required: bool = True
    parallel_agents: bool = False
    quality_threshold: float = 0.85
    max_iterations: int = 3
    timeout_seconds: int = 300
    depends_on: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "agents": self.agents,
            "required": self.required,
            "parallel_agents": self.parallel_agents,
            "quality_threshold": self.quality_threshold,
            "max_iterations": self.max_iterations,
            "timeout_seconds": self.timeout_seconds,
            "depends_on": self.depends_on,
        }


@dataclass
class StageResult:
    """Result of executing a workflow stage."""
    stage_name: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    agent_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    quality_score: float = 0.0
    passed_quality_gate: bool = False
    iterations_used: int = 1
    error: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_name": self.stage_name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "quality_score": round(self.quality_score, 3),
            "passed_quality_gate": self.passed_quality_gate,
            "iterations_used": self.iterations_used,
            "error": self.error,
        }


@dataclass
class WorkflowContext:
    """Context passed through workflow stages."""
    workflow_id: str
    workflow_type: str
    session_id: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    current_stage: Optional[str] = None
    completed_stages: List[str] = field(default_factory=list)
    stage_results: Dict[str, StageResult] = field(default_factory=dict)
    shared_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_stage_result(self, result: StageResult) -> None:
        """Add a stage result."""
        self.stage_results[result.stage_name] = result
        if result.status == WorkflowStatus.COMPLETED:
            self.completed_stages.append(result.stage_name)

    def get_stage_output(self, stage_name: str) -> Optional[Dict[str, Any]]:
        """Get output from a completed stage."""
        if stage_name in self.stage_results:
            return self.stage_results[stage_name].agent_results
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "current_stage": self.current_stage,
            "completed_stages": self.completed_stages,
            "stage_results": {k: v.to_dict() for k, v in self.stage_results.items()},
            "metadata": self.metadata,
        }


@dataclass
class WorkflowResult:
    """Final result of workflow execution."""
    workflow_id: str
    workflow_type: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    stages_completed: int = 0
    stages_total: int = 0
    overall_quality_score: float = 0.0
    context: Optional[WorkflowContext] = None
    final_output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def success(self) -> bool:
        return self.status == WorkflowStatus.COMPLETED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "status": self.status.value,
            "success": self.success,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "stages_completed": self.stages_completed,
            "stages_total": self.stages_total,
            "overall_quality_score": round(self.overall_quality_score, 3),
            "final_output": self.final_output,
            "error": self.error,
        }


# Type for stage executor
StageExecutor = Callable[[WorkflowStage, WorkflowContext], Awaitable[StageResult]]


class WorkflowOrchestrator(ABC):
    """
    Base class for workflow orchestration.

    Subclasses implement specific workflows (Brown Paper, Migration, etc.)
    while this base provides:
    - Stage execution with quality gates
    - Agent routing via Confucius extensions
    - Progress streaming via SSE
    - Error handling and escalation

    Example:
    ```python
    class MyWorkflow(WorkflowOrchestrator):
        def get_stages(self) -> List[WorkflowStage]:
            return [
                WorkflowStage("analyze", "Analyze code", ["Felix"]),
                WorkflowStage("review", "Review quality", ["Quinn"]),
            ]

        async def execute_stage(self, stage, context):
            ...

    workflow = MyWorkflow()
    result = await workflow.run(session_id="abc", input_data={...})
    ```
    """

    def __init__(
        self,
        router: Optional[WorkflowRouter] = None,
        evaluator: Optional[QualityGateEvaluator] = None,
        stream: Optional[QualityProgressStream] = None,
    ):
        """
        Initialize orchestrator.

        Args:
            router: Extension router (created if not provided)
            evaluator: Quality gate evaluator (created if not provided)
            stream: Progress stream (created if not provided)
        """
        self._router = router or create_default_router()
        self._evaluator = evaluator or create_evaluator()
        self._stream = stream or QualityProgressStream()
        self._escalation = create_escalation_service()
        self._running_workflows: Dict[str, WorkflowContext] = {}

    @property
    @abstractmethod
    def workflow_type(self) -> str:
        """Return workflow type identifier."""
        pass

    @abstractmethod
    def get_stages(self) -> List[WorkflowStage]:
        """Return list of workflow stages in execution order."""
        pass

    @abstractmethod
    async def execute_stage(
        self,
        stage: WorkflowStage,
        context: WorkflowContext,
    ) -> StageResult:
        """
        Execute a single workflow stage.

        Args:
            stage: Stage definition
            context: Workflow context

        Returns:
            StageResult with execution outcome
        """
        pass

    async def run(
        self,
        session_id: str,
        input_data: Dict[str, Any],
        start_from_stage: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """
        Execute the complete workflow.

        Args:
            session_id: Session identifier
            input_data: Input data for workflow
            start_from_stage: Stage to start from (for resume)
            metadata: Additional metadata

        Returns:
            WorkflowResult with final outcome
        """
        import uuid

        workflow_id = str(uuid.uuid4())[:8]
        stages = self.get_stages()
        started_at = datetime.now(timezone.utc)

        # Create context
        context = WorkflowContext(
            workflow_id=workflow_id,
            workflow_type=self.workflow_type,
            session_id=session_id,
            started_at=started_at,
            shared_data=input_data.copy(),
            metadata=metadata or {},
        )

        self._running_workflows[workflow_id] = context

        await self._emit_event(StreamEventType.TASK_STARTED, workflow_id, {
            "workflow_type": self.workflow_type,
            "session_id": session_id,
            "stages": [s.name for s in stages],
        })

        result = WorkflowResult(
            workflow_id=workflow_id,
            workflow_type=self.workflow_type,
            status=WorkflowStatus.RUNNING,
            started_at=started_at,
            stages_total=len(stages),
            context=context,
        )

        try:
            # Determine starting point
            start_index = 0
            if start_from_stage:
                for i, stage in enumerate(stages):
                    if stage.name == start_from_stage:
                        start_index = i
                        break

            # Execute stages
            for i, stage in enumerate(stages[start_index:], start=start_index):
                context.current_stage = stage.name

                # Check dependencies
                if not self._check_dependencies(stage, context):
                    logger.warning(f"Stage {stage.name} dependencies not met, skipping")
                    continue

                await self._emit_event(StreamEventType.ITERATION_STARTED, workflow_id, {
                    "stage": stage.name,
                    "stage_index": i + 1,
                    "stages_total": len(stages),
                })

                # Execute with quality gate
                stage_result = await self._execute_with_quality_gate(stage, context)
                context.add_stage_result(stage_result)

                await self._emit_event(StreamEventType.ITERATION_COMPLETED, workflow_id, {
                    "stage": stage.name,
                    "status": stage_result.status.value,
                    "quality_score": stage_result.quality_score,
                })

                if stage_result.status == WorkflowStatus.FAILED:
                    if stage.required:
                        result.status = WorkflowStatus.FAILED
                        result.error = f"Required stage {stage.name} failed: {stage_result.error}"
                        break
                elif stage_result.status == WorkflowStatus.ESCALATED:
                    result.status = WorkflowStatus.ESCALATED
                    break

                result.stages_completed += 1

            # Calculate final score
            if context.stage_results:
                scores = [r.quality_score for r in context.stage_results.values()]
                result.overall_quality_score = sum(scores) / len(scores)

            # Set final status
            if result.status == WorkflowStatus.RUNNING:
                result.status = WorkflowStatus.COMPLETED

            result.completed_at = datetime.now(timezone.utc)
            result.final_output = self._build_final_output(context)

        except Exception as e:
            logger.exception(f"Workflow {workflow_id} failed: {e}")
            result.status = WorkflowStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.now(timezone.utc)

        finally:
            self._running_workflows.pop(workflow_id, None)

        await self._emit_event(
            StreamEventType.TASK_COMPLETED if result.success else StreamEventType.TASK_FAILED,
            workflow_id,
            result.to_dict(),
        )

        return result

    async def _execute_with_quality_gate(
        self,
        stage: WorkflowStage,
        context: WorkflowContext,
    ) -> StageResult:
        """Execute stage with quality gate validation."""
        iteration_controller = create_iteration_controller(
            evaluator=self._evaluator,
            max_iterations=stage.max_iterations,
        )

        # Create executor wrapper
        async def stage_executor(task: str, exec_context: Dict[str, Any]) -> Dict[str, Any]:
            stage_result = await self.execute_stage(stage, context)
            return {
                "success": stage_result.status == WorkflowStatus.COMPLETED,
                "agent_results": stage_result.agent_results,
                "error": stage_result.error,
            }

        # Run with iteration controller
        output = await iteration_controller.run_with_quality_gate(
            task=stage.description,
            context={"domain": self._get_domain_for_stage(stage)},
            agent_executor=stage_executor,
            entry_id=f"{context.workflow_id}-{stage.name}",
            agent_name=stage.agents[0] if stage.agents else "Orchestrator",
            threshold_override=stage.quality_threshold,
        )

        # Extract metadata
        metadata = output.get("_iteration_metadata", {})

        return StageResult(
            stage_name=stage.name,
            status=WorkflowStatus.COMPLETED if output.get("success") else WorkflowStatus.FAILED,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            agent_results=output.get("agent_results", {}),
            quality_score=metadata.get("attempts_summary", [{}])[-1].get("evaluation_score", 0) or 0.85,
            passed_quality_gate=output.get("success", False),
            iterations_used=metadata.get("total_iterations", 1),
            error=output.get("error"),
        )

    def _check_dependencies(
        self,
        stage: WorkflowStage,
        context: WorkflowContext,
    ) -> bool:
        """Check if stage dependencies are met."""
        for dep in stage.depends_on:
            if dep not in context.completed_stages:
                return False
        return True

    def _get_domain_for_stage(self, stage: WorkflowStage) -> str:
        """Get quality domain for stage based on agents."""
        agent_domains = {
            "Felix": "architecture",
            "Quinn": "quality",
            "Eliza": "estimation",
            "Diana": "documentation",
            "Tessa": "testing",
            "Miguel": "metrics",
            "Marcus": "maintenance",
            "Peter": "product",
            "Paul": "planning",
            "Betty": "business",
            "Vicky": "design",
        }

        if stage.agents:
            return agent_domains.get(stage.agents[0], "general")
        return "general"

    def _build_final_output(self, context: WorkflowContext) -> Dict[str, Any]:
        """Build final output from all stage results."""
        output = {}
        for stage_name, result in context.stage_results.items():
            output[stage_name] = result.agent_results
        return output

    async def _emit_event(
        self,
        event_type: StreamEventType,
        workflow_id: str,
        data: Dict[str, Any],
    ) -> None:
        """Emit progress event."""
        try:
            await self._stream.emit(event_type, workflow_id, data)
        except Exception as e:
            logger.warning(f"Failed to emit event: {e}")

    async def get_agents_for_stage(
        self,
        stage: WorkflowStage,
        context: WorkflowContext,
    ) -> List[BaseAgentExtension]:
        """Get agent extensions for a stage."""
        extensions = []
        for agent_name in stage.agents:
            ext = self._router.get_extension(agent_name)
            if ext:
                extensions.append(ext)
        return extensions

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a running workflow."""
        context = self._running_workflows.get(workflow_id)
        if context:
            return context.to_dict()
        return None

    def list_running_workflows(self) -> List[str]:
        """List all running workflow IDs."""
        return list(self._running_workflows.keys())
