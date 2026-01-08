"""
Stack Agents API Routes

Week 56: REST API for stack-specific agent management.

Endpoints:
- GET    /stacks                          - List supported stacks
- GET    /roles                           - List agent roles
- GET    /templates                       - List all templates
- GET    /templates/{role}/{stack}        - Get specific template
- POST   /projects/{id}/agents            - Create agents for project
- GET    /projects/{id}/agents            - List project agents
- GET    /projects/{id}/agents/{name}     - Get specific agent
- POST   /projects/{id}/agents/{name}/task - Record task result
- DELETE /projects/{id}/agents/{name}     - Deactivate agent
- GET    /projects/{id}/best-agent        - Find best agent for task
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict

from app.services.stack_agent_factory import (
    get_stack_agent_factory,
    STACK_TEMPLATES,
    TechStack,
    AgentRole,
)
from app.services.stack_agent_executor import (
    get_stack_agent_executor,
    AgentTaskType,
    AgentTaskRequest,
)
from app.services.stack_detection_service import (
    get_stack_detection_service,
)


router = APIRouter(prefix="/api/stack-agents", tags=["Stack Agents"])


# ==================== SCHEMAS ====================

class TemplateResponse(BaseModel):
    """Stack agent template response."""
    role: str
    stack: str
    name_suffix: str
    model_preference: str
    capabilities: List[str]
    specialized_tools: List[str]
    validation_phases: List[str]

    model_config = ConfigDict(protected_namespaces=())


class AgentInstanceResponse(BaseModel):
    """Stack agent instance response."""
    id: str
    name: str
    project_id: int
    role: str
    stack: str
    model_preference: str
    active: bool
    total_tasks: int
    successful_tasks: int
    success_rate: float
    performance_score: float
    capabilities: List[str]
    validation_phases: List[str]

    model_config = ConfigDict(protected_namespaces=())


class CreateAgentsRequest(BaseModel):
    """Request to create agents for a project."""
    stacks: List[str] = Field(..., description="Tech stacks detected in project")
    roles: Optional[List[str]] = Field(None, description="Specific roles to create (defaults to all)")


class TaskResultRequest(BaseModel):
    """Request to record a task result."""
    success: bool
    performance_delta: float = Field(0.0, description="Performance score change")


class BestAgentRequest(BaseModel):
    """Request to find best agent for a task."""
    task_type: str = Field(..., description="Type of task")
    required_capability: Optional[str] = Field(None, description="Required capability")


# ==================== STACK & ROLE ENDPOINTS ====================

@router.get("/stacks", response_model=List[str])
async def list_stacks():
    """List all supported technology stacks."""
    factory = get_stack_agent_factory()
    return factory.get_available_stacks()


@router.get("/roles", response_model=List[str])
async def list_roles():
    """List all available agent roles."""
    factory = get_stack_agent_factory()
    return factory.get_available_roles()


# ==================== TEMPLATE ENDPOINTS ====================

@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(
    stack: Optional[str] = Query(None, description="Filter by stack"),
    role: Optional[str] = Query(None, description="Filter by role")
):
    """List all available stack agent templates."""
    templates = []

    for role_name, stack_templates in STACK_TEMPLATES.items():
        if role and role_name != role:
            continue

        for stack_name, template in stack_templates.items():
            if stack and stack_name != stack:
                continue

            templates.append(TemplateResponse(
                role=template.role.value,
                stack=template.stack.value,
                name_suffix=template.name_suffix,
                model_preference=template.model_preference,
                capabilities=[c.name for c in template.capabilities],
                specialized_tools=template.specialized_tools,
                validation_phases=template.validation_phases,
            ))

    return templates


@router.get("/templates/{role}/{stack}", response_model=TemplateResponse)
async def get_template(role: str, stack: str):
    """Get a specific template by role and stack."""
    factory = get_stack_agent_factory()
    template = factory.get_template(role, stack)

    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found for role '{role}' and stack '{stack}'"
        )

    return TemplateResponse(
        role=template.role.value,
        stack=template.stack.value,
        name_suffix=template.name_suffix,
        model_preference=template.model_preference,
        capabilities=[c.name for c in template.capabilities],
        specialized_tools=template.specialized_tools,
        validation_phases=template.validation_phases,
    )


# ==================== PROJECT AGENT ENDPOINTS ====================

@router.post("/projects/{project_id}/agents", response_model=List[AgentInstanceResponse])
async def create_project_agents(project_id: int, request: CreateAgentsRequest):
    """Create stack agents for a project based on detected stacks."""
    factory = get_stack_agent_factory()

    # Validate stacks
    valid_stacks = factory.get_available_stacks()
    invalid_stacks = [s for s in request.stacks if s not in valid_stacks]
    if invalid_stacks:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stacks: {invalid_stacks}. Valid: {valid_stacks}"
        )

    # Validate roles if provided
    if request.roles:
        valid_roles = list(STACK_TEMPLATES.keys())
        invalid_roles = [r for r in request.roles if r not in valid_roles]
        if invalid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid roles: {invalid_roles}. Valid: {valid_roles}"
            )

    # Create agents
    instances = factory.create_agents_for_project(
        project_id=project_id,
        stacks=request.stacks,
        roles=request.roles
    )

    return [
        AgentInstanceResponse(
            id=agent.id,
            name=agent.name,
            project_id=agent.project_id,
            role=agent.template.role.value,
            stack=agent.template.stack.value,
            model_preference=agent.template.model_preference,
            active=agent.active,
            total_tasks=agent.total_tasks,
            successful_tasks=agent.successful_tasks,
            success_rate=agent.success_rate,
            performance_score=agent.performance_score,
            capabilities=[c.name for c in agent.template.capabilities],
            validation_phases=agent.template.validation_phases,
        )
        for agent in instances
    ]


@router.get("/projects/{project_id}/agents", response_model=List[AgentInstanceResponse])
async def list_project_agents(
    project_id: int,
    active_only: bool = Query(False, description="Only return active agents")
):
    """List all agents for a project."""
    factory = get_stack_agent_factory()
    project_agents = factory.get_project_agents(project_id)

    agents = list(project_agents.values())
    if active_only:
        agents = [a for a in agents if a.active]

    return [
        AgentInstanceResponse(
            id=agent.id,
            name=agent.name,
            project_id=agent.project_id,
            role=agent.template.role.value,
            stack=agent.template.stack.value,
            model_preference=agent.template.model_preference,
            active=agent.active,
            total_tasks=agent.total_tasks,
            successful_tasks=agent.successful_tasks,
            success_rate=agent.success_rate,
            performance_score=agent.performance_score,
            capabilities=[c.name for c in agent.template.capabilities],
            validation_phases=agent.template.validation_phases,
        )
        for agent in agents
    ]


@router.get("/projects/{project_id}/agents/{agent_name}", response_model=AgentInstanceResponse)
async def get_project_agent(project_id: int, agent_name: str):
    """Get a specific agent for a project."""
    factory = get_stack_agent_factory()
    agent = factory.get_agent_by_name(project_id, agent_name)

    if not agent:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_name}' not found for project {project_id}"
        )

    return AgentInstanceResponse(
        id=agent.id,
        name=agent.name,
        project_id=agent.project_id,
        role=agent.template.role.value,
        stack=agent.template.stack.value,
        model_preference=agent.template.model_preference,
        active=agent.active,
        total_tasks=agent.total_tasks,
        successful_tasks=agent.successful_tasks,
        success_rate=agent.success_rate,
        performance_score=agent.performance_score,
        capabilities=[c.name for c in agent.template.capabilities],
        validation_phases=agent.template.validation_phases,
    )


@router.post("/projects/{project_id}/agents/{agent_name}/task")
async def record_agent_task(
    project_id: int,
    agent_name: str,
    request: TaskResultRequest
):
    """Record a task result for an agent."""
    factory = get_stack_agent_factory()

    success = factory.update_agent_performance(
        project_id=project_id,
        agent_name=agent_name,
        success=request.success,
        performance_delta=request.performance_delta
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_name}' not found for project {project_id}"
        )

    agent = factory.get_agent_by_name(project_id, agent_name)

    return {
        "message": "Task result recorded",
        "agent": agent_name,
        "total_tasks": agent.total_tasks,
        "success_rate": agent.success_rate,
        "performance_score": agent.performance_score,
    }


@router.delete("/projects/{project_id}/agents/{agent_name}")
async def deactivate_agent(project_id: int, agent_name: str):
    """Deactivate an agent for a project."""
    factory = get_stack_agent_factory()

    success = factory.deactivate_agent(project_id, agent_name)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_name}' not found for project {project_id}"
        )

    return {
        "message": f"Agent '{agent_name}' deactivated",
        "project_id": project_id,
    }


@router.post("/projects/{project_id}/best-agent", response_model=Optional[AgentInstanceResponse])
async def find_best_agent(project_id: int, request: BestAgentRequest):
    """Find the best agent for a specific task type."""
    factory = get_stack_agent_factory()

    agent = factory.get_best_agent_for_task(
        project_id=project_id,
        task_type=request.task_type,
        required_capability=request.required_capability
    )

    if not agent:
        raise HTTPException(
            status_code=404,
            detail=f"No suitable agent found for task type '{request.task_type}'"
        )

    return AgentInstanceResponse(
        id=agent.id,
        name=agent.name,
        project_id=agent.project_id,
        role=agent.template.role.value,
        stack=agent.template.stack.value,
        model_preference=agent.template.model_preference,
        active=agent.active,
        total_tasks=agent.total_tasks,
        successful_tasks=agent.successful_tasks,
        success_rate=agent.success_rate,
        performance_score=agent.performance_score,
        capabilities=[c.name for c in agent.template.capabilities],
        validation_phases=agent.template.validation_phases,
    )


# ==================== EXECUTION ENDPOINTS (Week 56 Day 2) ====================

class ExecuteTaskRequest(BaseModel):
    """Request to execute an agent task."""
    task_type: str = Field(..., description="Type of task: code_generation, code_review, security_audit, etc.")
    instructions: str = Field(..., description="Task instructions")
    code_files: Dict[str, str] = Field(default_factory=dict, description="Files to analyze/modify")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    max_tokens: int = Field(default=4000, description="Max response tokens")
    temperature: float = Field(default=0.3, description="LLM temperature")
    prefer_local: bool = Field(default=False, description="Prefer local Ollama")


class ExecutionResultResponse(BaseModel):
    """Response from task execution."""
    success: bool
    agent_name: str
    task_type: str
    output: str
    code_changes: Dict[str, str]
    analysis: Dict[str, Any]
    validation_passed: bool
    validation_errors: List[str]
    execution_time_ms: int
    provider_used: str
    tokens_used: int
    error: Optional[str] = None


@router.post("/projects/{project_id}/agents/{agent_name}/execute", response_model=ExecutionResultResponse)
async def execute_agent_task(
    project_id: int,
    agent_name: str,
    request: ExecuteTaskRequest
):
    """
    Execute a task using a specific agent.

    This is the main execution endpoint for stack agents.
    The agent will use the appropriate LLM provider based on task type.
    """
    executor = get_stack_agent_executor()

    # Validate task type
    try:
        task_type = AgentTaskType(request.task_type)
    except ValueError:
        valid_types = [t.value for t in AgentTaskType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task type '{request.task_type}'. Valid types: {valid_types}"
        )

    # Create the task request
    task_request = AgentTaskRequest(
        project_id=project_id,
        agent_name=agent_name,
        task_type=task_type,
        context=request.context,
        code_files=request.code_files,
        instructions=request.instructions,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        prefer_local=request.prefer_local,
    )

    # Execute the task
    result = await executor.execute_task(task_request)

    if result.error and not result.success:
        # Don't raise exception - return the error in the response
        pass

    return ExecutionResultResponse(
        success=result.success,
        agent_name=result.agent_name,
        task_type=result.task_type.value,
        output=result.output,
        code_changes=result.code_changes,
        analysis=result.analysis,
        validation_passed=result.validation_passed,
        validation_errors=result.validation_errors,
        execution_time_ms=result.execution_time_ms,
        provider_used=result.provider_used,
        tokens_used=result.tokens_used,
        error=result.error,
    )


@router.get("/projects/{project_id}/execution-history")
async def get_execution_history(
    project_id: int,
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    limit: int = Query(100, description="Max results to return")
):
    """Get execution history for a project."""
    executor = get_stack_agent_executor()

    history = executor.get_execution_history(
        project_id=project_id,
        agent_name=agent_name,
        limit=limit
    )

    return {
        "project_id": project_id,
        "count": len(history),
        "executions": [
            {
                "agent_name": r.agent_name,
                "task_type": r.task_type.value,
                "success": r.success,
                "validation_passed": r.validation_passed,
                "execution_time_ms": r.execution_time_ms,
                "provider_used": r.provider_used,
            }
            for r in history
        ]
    }


@router.get("/metrics")
async def get_execution_metrics():
    """Get aggregate execution metrics."""
    executor = get_stack_agent_executor()
    return executor.get_success_metrics()


@router.get("/task-types")
async def list_task_types():
    """List all available task types."""
    return [
        {
            "value": t.value,
            "name": t.name,
            "description": _get_task_type_description(t)
        }
        for t in AgentTaskType
    ]


def _get_task_type_description(task_type: AgentTaskType) -> str:
    """Get description for a task type."""
    descriptions = {
        AgentTaskType.CODE_GENERATION: "Generate new code based on requirements",
        AgentTaskType.CODE_REVIEW: "Review code for quality, bugs, and best practices",
        AgentTaskType.SECURITY_AUDIT: "Audit code for security vulnerabilities",
        AgentTaskType.REFACTORING: "Refactor code for better quality",
        AgentTaskType.TEST_GENERATION: "Generate tests for existing code",
        AgentTaskType.BUG_FIX: "Analyze and fix bugs in code",
        AgentTaskType.DOCUMENTATION: "Generate documentation for code",
        AgentTaskType.ARCHITECTURE_REVIEW: "Review code architecture and design",
        AgentTaskType.PERFORMANCE_ANALYSIS: "Analyze code for performance issues",
        AgentTaskType.DEPENDENCY_UPDATE: "Update and manage dependencies",
    }
    return descriptions.get(task_type, "")


# ==================== STACK DETECTION (Week 56 Day 4) ====================

class DetectStacksRequest(BaseModel):
    """Request to detect stacks in a project."""
    project_path: str = Field(..., description="Path to the project directory")
    max_files: int = Field(default=1000, description="Maximum files to scan")
    scan_depth: int = Field(default=5, description="Maximum directory depth")


@router.post("/detect")
async def detect_project_stacks(request: DetectStacksRequest):
    """
    Detect technology stacks in a project directory.

    Scans the project for programming languages, frameworks, and tools.
    Returns detected stacks with confidence scores and recommended agents.
    """
    service = get_stack_detection_service()

    try:
        result = service.detect_stacks(
            project_path=request.project_path,
            max_files=request.max_files,
            scan_depth=request.scan_depth,
        )

        recommendations = service.get_recommended_agents(result)

        return {
            **service.to_dict(result),
            "recommended_agents": [
                {"role": role, "stack": stack}
                for role, stack in recommendations
            ],
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/detect-and-create/{project_id}")
async def detect_and_create_agents(
    project_id: int,
    request: DetectStacksRequest,
    roles: Optional[List[str]] = Query(None, description="Specific roles to create")
):
    """
    Detect stacks and automatically create agents for a project.

    This is a convenience endpoint that combines detection and agent creation.
    """
    service = get_stack_detection_service()
    factory = get_stack_agent_factory()

    try:
        # Detect stacks
        result = service.detect_stacks(
            project_path=request.project_path,
            max_files=request.max_files,
            scan_depth=request.scan_depth,
        )

        if not result.primary_stacks:
            return {
                "message": "No stacks detected",
                "detection": service.to_dict(result),
                "agents_created": [],
            }

        # Create agents for detected stacks
        instances = factory.create_agents_for_project(
            project_id=project_id,
            stacks=result.primary_stacks,
            roles=roles,
        )

        return {
            "message": f"Created {len(instances)} agents for {len(result.primary_stacks)} stacks",
            "detection": service.to_dict(result),
            "agents_created": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.template.role.value,
                    "stack": agent.template.stack.value,
                }
                for agent in instances
            ],
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection/creation failed: {str(e)}")


# ==================== HEALTH CHECK ====================

@router.get("/health")
async def health_check():
    """Health check for stack agents system."""
    factory = get_stack_agent_factory()

    template_count = sum(
        len(stack_templates)
        for stack_templates in STACK_TEMPLATES.values()
    )

    return {
        "status": "healthy",
        "supported_stacks": len(factory.get_available_stacks()),
        "available_roles": len(factory.get_available_roles()),
        "total_templates": template_count,
    }
