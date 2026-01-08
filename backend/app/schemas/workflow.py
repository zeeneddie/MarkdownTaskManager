"""
Workflow request/response schemas for AI agent integration
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# Work Types (matching TypeScript enum)
WorkType = Literal[
    "PROJECT_DEFINITION",
    "NEW_FEATURE",
    "MAINTENANCE",
    "QUALITY_AUDIT",
    "BUG",
    "ENHANCEMENT",
    "MIGRATION",
    "QUALITY_IMPROVEMENT",
    "TESTING",
    "GREEN_PAPER",      # Greenfield project definition (Spec-Kit)
    "BROWN_PAPER"       # Brownfield/Migration project definition
]


class WorkflowRequest(BaseModel):
    """Request to execute a workflow"""
    work_type: WorkType = Field(..., description="Type of workflow to execute (e.g., NEW_FEATURE, BUG, MAINTENANCE)")
    description: str = Field(..., description="Description of the work to be done")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context (files, dependencies, etc.)")
    priority: Optional[str] = Field("medium", description="Priority: low, medium, high, critical")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "work_type": "NEW_FEATURE",
            "description": "Add OAuth2 authentication with Google and GitHub providers",
            "context": {
                "files": ["src/auth/"],
                "dependencies": ["passport", "oauth2"]
            },
            "priority": "high"
        }
    })


class AgentResult(BaseModel):
    """Result from a single agent execution"""
    agent_name: str
    agent_role: str
    output: Dict[str, Any]
    execution_time: float
    status: Literal["success", "failed", "skipped"]


class WorkflowResult(BaseModel):
    """Result of workflow execution"""
    work_type: WorkType
    status: Literal["success", "failed", "partial"]
    agents_executed: List[AgentResult]
    total_execution_time: float
    result: Dict[str, Any]
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "work_type": "NEW_FEATURE",
            "status": "success",
            "agents_executed": [
                {
                    "agent_name": "Felix",
                    "agent_role": "Feature Architect",
                    "output": {"epic": "OAuth2 Authentication"},
                    "execution_time": 2.5,
                    "status": "success"
                }
            ],
            "total_execution_time": 8.3,
            "result": {
                "epic": "OAuth2 Authentication System",
                "features": ["Google OAuth", "GitHub OAuth"],
                "stories": ["User login with Google", "User login with GitHub"]
            },
            "error": None,
            "timestamp": "2025-11-13T10:00:00"
        }
    })


class WorkTypeInfo(BaseModel):
    """Information about a work type"""
    name: WorkType
    description: str
    agents: List[str]
    process: Literal["sequential", "parallel"]
    workflow: str

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "NEW_FEATURE",
            "description": "New feature development from concept to implementation plan",
            "agents": ["Felix", "Eliza", "Tessa", "Quinn", "Diana"],
            "process": "sequential",
            "workflow": "spec_kit_pipeline"
        }
    })


class AgentInfo(BaseModel):
    """Information about an agent"""
    name: str
    role: str
    description: str
    tools: List[str]
    status: Literal["ready", "not_configured", "error"]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Felix",
            "role": "Feature Architect",
            "description": "Spec Kit specialist who transforms ideas into structured epics",
            "tools": ["spec_kit_constitution", "epic_creator", "feasibility_checker"],
            "status": "ready"
        }
    })


class WorkflowStatistics(BaseModel):
    """Statistics about workflow execution"""
    total_workflows_executed: int
    workflows_by_type: Dict[WorkType, int]
    average_execution_time: float
    success_rate: float


class ProjectDefinitionRequest(BaseModel):
    """Request to define a new project"""
    project_name: str = Field(..., description="Name of the new project", min_length=1, max_length=100)
    description: str = Field(..., description="Project description and goals")
    business_goals: Optional[List[str]] = Field(None, description="Business objectives")
    target_audience: Optional[str] = Field(None, description="Target users/customers")
    constraints: Optional[List[str]] = Field(None, description="Budget, timeline, technical constraints")
    folder_path: Optional[str] = Field(None, description="Custom folder path for project")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "project_name": "E-commerce Platform",
            "description": "Online shop with payment processing, inventory management, and customer analytics",
            "business_goals": [
                "Increase online sales by 50%",
                "Reduce cart abandonment rate",
                "Improve customer retention"
            ],
            "target_audience": "Small to medium businesses selling physical products",
            "constraints": [
                "Budget: €50,000",
                "Timeline: 6 months",
                "Team: 5 developers"
            ],
            "folder_path": "projects/ecommerce"
        }
    })


class ProjectDefinitionResult(BaseModel):
    """Result of project definition workflow"""
    project_name: str
    business_case: Dict[str, Any]
    architecture: Dict[str, Any]
    epics: List[Dict[str, Any]]
    project_plan: Dict[str, Any]
    documentation: Dict[str, str]
    folder_structure: Dict[str, Any]
    workflow_execution: WorkflowResult

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "project_name": "E-commerce Platform",
            "business_case": {
                "value": "Enables online sales channel",
                "roi": "150% over 12 months",
                "risks": ["Market competition", "Technical complexity"]
            },
            "architecture": {
                "tech_stack": ["FastAPI", "Vue.js", "PostgreSQL"],
                "patterns": ["RESTful API", "Repository pattern"]
            },
            "epics": [
                {
                    "id": "EPIC-1",
                    "title": "User Management",
                    "estimated_effort": 21
                }
            ],
            "project_plan": {
                "phases": [],
                "sprints": [],
                "timeline": "6 months"
            },
            "documentation": {
                "readme": "# Project README",
                "setup_guide": "# Setup Guide"
            },
            "folder_structure": {
                "created": True,
                "path": "projects/ecommerce",
                "files": ["project.md", "README.md"]
            },
            "workflow_execution": {}
        }
    })


# ========================================
# SPEC-KIT WORKFLOW SCHEMAS
# ========================================

class TechnicalContext(BaseModel):
    """Technical context for Spec-Kit workflow"""
    existing_systems: Optional[List[str]] = Field(None, description="Existing systems to integrate with")
    technologies: Optional[List[str]] = Field(None, description="Preferred technologies or tech stack")
    team_size: Optional[int] = Field(None, description="Size of the development team", ge=1, le=100)
    timeline: Optional[str] = Field(None, description="Project timeline (e.g., '3 months', 'Q1 2026')")


class SpecKitWorkflowRequest(BaseModel):
    """Request to execute Spec-Kit workflow (Constitution → Specification → Tasks)"""
    business_case: str = Field(..., description="Business case or problem statement", min_length=10)
    stakeholders: List[str] = Field(..., description="Project stakeholders", min_length=1)
    constraints: List[str] = Field(..., description="Project constraints (budget, timeline, technical)", min_length=1)
    success_criteria: List[str] = Field(..., description="Success criteria and KPIs", min_length=1)
    technical_context: Optional[TechnicalContext] = Field(None, description="Technical context")
    project_path: Optional[str] = Field(None, description="Path for file generation")
    project_name: Optional[str] = Field(None, description="Project name for file naming")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "business_case": "Build an e-commerce platform to enable online sales for small businesses",
            "stakeholders": ["CEO", "CTO", "Sales Team", "End Users"],
            "constraints": [
                "Budget: €50,000",
                "Timeline: 6 months",
                "Team: 5 developers",
                "Must integrate with existing inventory system"
            ],
            "success_criteria": [
                "Support 10,000 concurrent users",
                "99.9% uptime",
                "< 2 second page load time",
                "Payment processing PCI-DSS compliant"
            ],
            "technical_context": {
                "existing_systems": ["Legacy Inventory DB", "CRM System"],
                "technologies": ["FastAPI", "Vue.js", "PostgreSQL"],
                "team_size": 5,
                "timeline": "6 months"
            },
            "project_path": "projects/ecommerce",
            "project_name": "E-commerce Platform"
        }
    })


class GeneratedFile(BaseModel):
    """Generated file from Spec-Kit workflow"""
    filename: str = Field(..., description="Name of the generated file")
    content: str = Field(..., description="File content")
    path: Optional[str] = Field(None, description="Full path if saved to disk")


class SpecKitWorkflowResult(BaseModel):
    """Result of Spec-Kit workflow execution"""
    success: bool
    constitution: Dict[str, Any]
    specification: Dict[str, Any]
    tasks: Dict[str, Any]
    files: List[GeneratedFile]
    summary: Dict[str, Any]
    total_execution_time: float
    error: Optional[str] = None

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True,
            "constitution": {
                "principles": ["User-centric design", "Security first"],
                "requirements": ["Payment processing", "Inventory management"],
                "constraints": ["Budget: €50k", "Timeline: 6 months"],
                "risks": ["Market competition", "Technical complexity"],
                "scope": {"in_scope": ["MVP features"], "out_of_scope": ["Mobile app"]}
            },
            "specification": {
                "architecture": {"pattern": "Microservices", "components": 5},
                "components": ["API Gateway", "Auth Service", "Product Service"],
                "interfaces": ["REST API", "GraphQL"],
                "data_model": ["User", "Product", "Order"],
                "quality": {"performance": "< 2s load", "security": "PCI-DSS"}
            },
            "tasks": {
                "epics": [{"id": "EPIC-1", "title": "User Management"}],
                "features": [{"id": "FEAT-1", "title": "User Registration"}],
                "stories": [{"id": "STORY-1", "title": "User can sign up"}],
                "dependencies": {"STORY-1": ["EPIC-1", "FEAT-1"]}
            },
            "files": [
                {"filename": "constitution.md", "content": "# Constitution...", "path": "projects/ecommerce/constitution.md"},
                {"filename": "specification.md", "content": "# Specification...", "path": "projects/ecommerce/specification.md"},
                {"filename": "tasks.md", "content": "# Tasks...", "path": "projects/ecommerce/tasks.md"}
            ],
            "summary": {
                "total_principles": 5,
                "total_components": 8,
                "total_epics": 3,
                "total_stories": 15,
                "files_generated": 5
            },
            "total_execution_time": 45.8,
            "error": None
        }
    })


# ========================================
# BROWN-PAPER WORKFLOW SCHEMAS
# ========================================

class LegacySystemInfo(BaseModel):
    """Legacy system information for Brown-Paper workflow"""
    technology_stack: List[str] = Field(..., description="Current technologies (languages, frameworks, databases)")
    estimated_size: str = Field(..., description="Size estimate (LOC, modules, pages, tables)")
    age_years: Optional[int] = Field(None, description="Age of the system in years")
    known_issues: Optional[List[str]] = Field(None, description="Known technical debt and pain points")
    deployment: Optional[str] = Field(None, description="Current deployment architecture")


class MigrationTarget(BaseModel):
    """Target state for migration"""
    technology_stack: List[str] = Field(..., description="Target technologies")
    architecture_pattern: str = Field(..., description="Target architecture (Clean Architecture, Microservices, etc.)")
    deployment_platform: str = Field(..., description="Target deployment (Azure, AWS, On-premise, etc.)")
    key_improvements: Optional[List[str]] = Field(None, description="Expected improvements")


class MigrationStrategy(BaseModel):
    """Migration strategy details"""
    strategy_type: Literal["strangler_fig", "big_bang", "parallel_run"] = Field(..., description="Primary migration strategy")
    phasing_approach: str = Field(..., description="How modules will be phased")
    coexistence_period: Optional[str] = Field(None, description="How long both systems will run")
    rollback_strategy: str = Field(..., description="How to rollback if needed")


class DataMigrationApproach(BaseModel):
    """Data migration approach"""
    schema_changes: str = Field(..., description="Schema change approach (preserve, evolve, redesign)")
    transformation_required: bool = Field(False, description="Whether data transformation is needed")
    validation_approach: str = Field(..., description="How data integrity will be validated")
    tooling: Optional[str] = Field(None, description="Migration tooling to be used")


class BrownPaperWorkflowRequest(BaseModel):
    """Request to execute Brown-Paper workflow (Migration Spec generation)"""
    # Q1-Q4: Migration-specific
    legacy_system: str = Field(..., description="Q1: Legacy system description", min_length=50)
    migration_target: str = Field(..., description="Q2: Target state description", min_length=50)
    migration_strategy: str = Field(..., description="Q3: Migration strategy", min_length=50)
    data_migration: str = Field(..., description="Q4: Data migration approach", min_length=30)

    # Q5-Q8: Similar to Green-Paper
    problem_statement: str = Field(..., description="Q5: Problems this migration solves", min_length=50)
    stakeholders: str = Field(..., description="Q6: Users and stakeholders affected", min_length=30)
    success_criteria: str = Field(..., description="Q7: Measurable success criteria", min_length=50)
    timeline_constraints: str = Field(..., description="Q8: Timeline and constraints", min_length=30)

    # Optional context
    project_name: Optional[str] = Field(None, description="Project name")
    project_path: Optional[str] = Field(None, description="Path for file generation")
    existing_documentation: Optional[List[str]] = Field(None, description="Paths to existing analysis docs")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "legacy_system": "ASP.NET Web Forms application (.NET Framework 4.8), ~150,000 LOC, 2,320 ASPX pages, SQL Server database with 180 tables. Built in 2008, last major update 2018.",
            "migration_target": ".NET 8 with ASP.NET Core and Blazor Server. Clean Architecture with CQRS pattern. Azure cloud deployment.",
            "migration_strategy": "Strangler Fig pattern with YARP reverse proxy. Phase 1: Authentication, Phase 2: User Management, Phase 3: Core Business Logic.",
            "data_migration": "Schema preserved - EF Core will map to existing SQL Server schema. Migration validation: row counts, checksum comparisons.",
            "problem_statement": "Critical security vulnerabilities, no MFA support, maintenance costs increasing 20% yearly.",
            "stakeholders": "200 healthcare workers (daily), 15 IT admins, CTO, Compliance Officer",
            "success_criteria": "100% functional parity, <2s page load, 100% test coverage, OWASP A+ rating, zero data loss",
            "timeline_constraints": "72 weeks total. Hard deadline: NEN 7510 audit in 18 months. Solo developer Phase 1, then 8-10 FTE.",
            "project_name": "HCI-CRS Migration",
            "project_path": "/opt/projecten/hci-crs"
        }
    })


class MigrationAnalysis(BaseModel):
    """Result of Miguel's migration analysis"""
    complexity: Literal["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]
    complexity_justification: str
    risk_register: List[Dict[str, Any]]
    recommended_phases: List[Dict[str, Any]]
    technical_spikes: List[str]
    go_no_go_checkpoints: List[str]


class BrownPaperWorkflowResult(BaseModel):
    """Result of Brown-Paper workflow execution"""
    success: bool
    migration_analysis: MigrationAnalysis
    specification: Dict[str, Any]
    tasks: Dict[str, Any]
    files: List[GeneratedFile]
    summary: Dict[str, Any]
    total_execution_time: float
    error: Optional[str] = None

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True,
            "migration_analysis": {
                "complexity": "HIGH",
                "complexity_justification": "Large legacy codebase, significant technology gap, critical data migration",
                "risk_register": [
                    {"risk": "EF Core mapping failures", "likelihood": "MEDIUM", "impact": "HIGH", "mitigation": "Early PoC"}
                ],
                "recommended_phases": [
                    {"phase": 1, "name": "Foundation", "modules": ["Auth", "Identity"], "weeks": 8}
                ],
                "technical_spikes": ["Database mapping validation", "MFA integration test"],
                "go_no_go_checkpoints": ["Week 14: Foundation complete", "Week 36: Core modules complete"]
            },
            "specification": {
                "executive_summary": "Migration of HCI-CRS from ASP.NET Web Forms to .NET 8/Blazor...",
                "current_state": {},
                "target_state": {},
                "migration_approach": {},
                "timeline": {}
            },
            "tasks": {
                "epics": [{"id": "EPIC-1", "title": "Security Foundation"}],
                "features": [{"id": "FEAT-1-1", "title": "ASP.NET Core Identity"}],
                "stories": [{"id": "STORY-1-1-1", "title": "User can login with existing credentials"}]
            },
            "files": [
                {"filename": "MIGRATION_SPECIFICATION.md", "content": "...", "path": "..."},
                {"filename": "TASKS.md", "content": "...", "path": "..."}
            ],
            "summary": {
                "total_epics": 8,
                "total_features": 24,
                "total_stories": 72,
                "total_fp": 1850,
                "estimated_weeks": 72
            },
            "total_execution_time": 120.5,
            "error": None
        }
    })
