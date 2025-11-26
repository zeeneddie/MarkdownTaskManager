"""
Project Wizard Service

Handles the business logic for the project wizard:
- Template parsing and defaults
- Project configuration generation
- Agent assignment based on workflow
- Folder structure creation
- Integration with existing project service
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging
import os
import json
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class TechStackConfig:
    """Technology stack configuration"""
    language: str
    framework: Optional[str] = None
    database: Optional[str] = None
    additional_tools: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language,
            "framework": self.framework,
            "database": self.database,
            "additional_tools": self.additional_tools
        }


@dataclass
class TeamMemberConfig:
    """Team member configuration"""
    name: str
    email: Optional[str] = None
    role: str = "developer"
    capacity_hours: int = 8

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "capacity_hours": self.capacity_hours
        }


@dataclass
class WorkflowConfig:
    """Workflow configuration"""
    workflow_type: str
    quality_gates: str = "standard"
    auto_assign_agents: bool = True
    agents: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_type": self.workflow_type,
            "quality_gates": self.quality_gates,
            "auto_assign_agents": self.auto_assign_agents,
            "agents": self.agents
        }


@dataclass
class ProjectConfig:
    """Complete project configuration"""
    name: str
    description: str
    template: str
    repo_url: Optional[str] = None
    tech_stack: Optional[TechStackConfig] = None
    team: List[TeamMemberConfig] = field(default_factory=list)
    sprint_duration_weeks: int = 2
    working_hours_per_day: int = 8
    workflow: Optional[WorkflowConfig] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "template": self.template,
            "repo_url": self.repo_url,
            "tech_stack": self.tech_stack.to_dict() if self.tech_stack else None,
            "team": [m.to_dict() for m in self.team],
            "sprint_duration_weeks": self.sprint_duration_weeks,
            "working_hours_per_day": self.working_hours_per_day,
            "workflow": self.workflow.to_dict() if self.workflow else None,
            "created_at": self.created_at.isoformat()
        }


# ============================================================================
# TEMPLATE DEFINITIONS
# ============================================================================

TEMPLATE_DEFAULTS = {
    "web-app": {
        "language": "typescript",
        "framework": "nextjs",
        "database": "postgresql",
        "workflow": "spec-kit",
        "quality_gates": "standard",
        "recommended_team_size": 4,
        "folder_structure": [
            "src/",
            "src/components/",
            "src/pages/",
            "src/api/",
            "src/utils/",
            "public/",
            "tests/",
            "docs/"
        ],
        "initial_epics": [
            "Project Setup & Infrastructure",
            "User Authentication",
            "Core Features",
            "Testing & QA"
        ]
    },
    "api-service": {
        "language": "python",
        "framework": "fastapi",
        "database": "postgresql",
        "workflow": "spec-kit",
        "quality_gates": "standard",
        "recommended_team_size": 3,
        "folder_structure": [
            "app/",
            "app/api/",
            "app/models/",
            "app/services/",
            "app/schemas/",
            "tests/",
            "docs/",
            "alembic/"
        ],
        "initial_epics": [
            "API Foundation",
            "Authentication & Authorization",
            "Core Endpoints",
            "Documentation & Testing"
        ]
    },
    "migration": {
        "language": "csharp",
        "framework": "dotnet",
        "database": "sqlserver",
        "workflow": "bmad",
        "quality_gates": "full",
        "recommended_team_size": 5,
        "folder_structure": [
            "src/",
            "src/Legacy/",
            "src/Modern/",
            "src/Migration/",
            "tests/",
            "docs/",
            "scripts/"
        ],
        "initial_epics": [
            "Legacy Code Analysis",
            "Migration Strategy",
            "Core Migration",
            "Data Migration",
            "Validation & Testing"
        ]
    },
    "custom": {
        "language": "typescript",
        "framework": None,
        "database": None,
        "workflow": "custom",
        "quality_gates": "minimal",
        "recommended_team_size": 2,
        "folder_structure": [
            "src/",
            "tests/",
            "docs/"
        ],
        "initial_epics": [
            "Project Setup",
            "Core Implementation"
        ]
    }
}


# ============================================================================
# AGENT MAPPINGS
# ============================================================================

WORKFLOW_AGENT_MAPPING = {
    "spec-kit": {
        "agents": ["Peter", "Felix", "Diana"],
        "description": "Full specification pipeline with Product Owner, Architect, and Documentation",
        "stages": ["Constitution", "Specification", "Tasks"]
    },
    "bmad": {
        "agents": ["Peter", "Felix", "Paul"],
        "description": "Strategic business analysis with 6-question framework",
        "stages": ["Green Paper", "Constitution", "Planning"]
    },
    "maintenance": {
        "agents": ["Marcus", "Quinn", "Tessa"],
        "description": "Code health and maintenance automation",
        "stages": ["Audit", "Plan", "Execute", "Test"]
    },
    "custom": {
        "agents": [],
        "description": "Manual agent configuration",
        "stages": ["Custom"]
    }
}

QUALITY_GATE_LEVELS = {
    "full": {
        "gates": 7,
        "rules": 42,
        "types": ["Architecture", "Code Quality", "Test Coverage", "Security", "Documentation", "Performance", "Accessibility"]
    },
    "standard": {
        "gates": 5,
        "rules": 28,
        "types": ["Architecture", "Code Quality", "Test Coverage", "Security", "Documentation"]
    },
    "minimal": {
        "gates": 3,
        "rules": 15,
        "types": ["Code Quality", "Test Coverage", "Security"]
    },
    "none": {
        "gates": 0,
        "rules": 0,
        "types": []
    }
}


# ============================================================================
# SERVICE CLASS
# ============================================================================

class ProjectWizardService:
    """Service for handling project wizard operations"""

    def __init__(self, projects_base_path: Optional[str] = None):
        """
        Initialize the service

        Args:
            projects_base_path: Base path for project folders (default: ./projects)
        """
        self.projects_base_path = Path(projects_base_path or "./projects")

    def get_template_defaults(self, template_id: str) -> Dict[str, Any]:
        """
        Get default configuration for a template

        Args:
            template_id: Template identifier

        Returns:
            Dictionary with template defaults
        """
        if template_id not in TEMPLATE_DEFAULTS:
            raise ValueError(f"Unknown template: {template_id}")

        return TEMPLATE_DEFAULTS[template_id].copy()

    def get_workflow_config(self, workflow_type: str) -> Dict[str, Any]:
        """
        Get workflow configuration including agents

        Args:
            workflow_type: Workflow type identifier

        Returns:
            Dictionary with workflow configuration
        """
        if workflow_type not in WORKFLOW_AGENT_MAPPING:
            raise ValueError(f"Unknown workflow: {workflow_type}")

        return WORKFLOW_AGENT_MAPPING[workflow_type].copy()

    def get_quality_gate_config(self, level: str) -> Dict[str, Any]:
        """
        Get quality gate configuration

        Args:
            level: Quality gate level (full, standard, minimal, none)

        Returns:
            Dictionary with quality gate configuration
        """
        if level not in QUALITY_GATE_LEVELS:
            raise ValueError(f"Unknown quality gate level: {level}")

        return QUALITY_GATE_LEVELS[level].copy()

    def create_project_config(
        self,
        name: str,
        description: str,
        template: str = "web-app",
        repo_url: Optional[str] = None,
        language: Optional[str] = None,
        framework: Optional[str] = None,
        database: Optional[str] = None,
        team: Optional[List[Dict[str, Any]]] = None,
        sprint_duration: int = 2,
        working_hours: int = 8,
        workflow: str = "spec-kit",
        quality_gates: str = "standard",
        auto_assign: bool = True
    ) -> ProjectConfig:
        """
        Create a complete project configuration

        Args:
            name: Project name
            description: Project description
            template: Template ID
            repo_url: Repository URL
            language: Primary programming language
            framework: Framework
            database: Database
            team: List of team members
            sprint_duration: Sprint duration in weeks
            working_hours: Working hours per day
            workflow: Workflow type
            quality_gates: Quality gate level
            auto_assign: Auto-assign agents

        Returns:
            ProjectConfig object
        """
        # Get template defaults
        defaults = self.get_template_defaults(template)

        # Create tech stack config
        tech_stack = TechStackConfig(
            language=language or defaults["language"],
            framework=framework or defaults.get("framework"),
            database=database or defaults.get("database")
        )

        # Create team config
        team_members = []
        if team:
            for member in team:
                team_members.append(TeamMemberConfig(
                    name=member.get("name", "Unknown"),
                    email=member.get("email"),
                    role=member.get("role", "developer"),
                    capacity_hours=working_hours
                ))

        # Get workflow agents
        workflow_config_data = self.get_workflow_config(workflow)
        agents = workflow_config_data["agents"] if auto_assign else []

        # Create workflow config
        workflow_config = WorkflowConfig(
            workflow_type=workflow,
            quality_gates=quality_gates,
            auto_assign_agents=auto_assign,
            agents=agents
        )

        # Create and return project config
        return ProjectConfig(
            name=name,
            description=description,
            template=template,
            repo_url=repo_url,
            tech_stack=tech_stack,
            team=team_members,
            sprint_duration_weeks=sprint_duration,
            working_hours_per_day=working_hours,
            workflow=workflow_config
        )

    def create_folder_structure(
        self,
        project_name: str,
        template: str = "web-app"
    ) -> Dict[str, Any]:
        """
        Create folder structure for a project

        Args:
            project_name: Project name (used for folder name)
            template: Template ID

        Returns:
            Dictionary with creation results
        """
        defaults = self.get_template_defaults(template)
        folders = defaults.get("folder_structure", ["src/", "tests/", "docs/"])

        # Sanitize project name for folder
        folder_name = project_name.lower().replace(" ", "-").replace("_", "-")
        project_path = self.projects_base_path / folder_name

        created_folders = []
        errors = []

        try:
            # Create base project folder
            project_path.mkdir(parents=True, exist_ok=True)
            created_folders.append(str(project_path))

            # Create subfolders
            for folder in folders:
                folder_path = project_path / folder
                try:
                    folder_path.mkdir(parents=True, exist_ok=True)
                    created_folders.append(str(folder_path))
                except Exception as e:
                    errors.append(f"Failed to create {folder}: {str(e)}")

            return {
                "success": len(errors) == 0,
                "project_path": str(project_path),
                "created_folders": created_folders,
                "errors": errors
            }

        except Exception as e:
            logger.error(f"Failed to create folder structure: {e}")
            return {
                "success": False,
                "project_path": str(project_path),
                "created_folders": created_folders,
                "errors": [str(e)]
            }

    def generate_project_metadata(
        self,
        config: ProjectConfig
    ) -> Dict[str, Any]:
        """
        Generate project metadata file content

        Args:
            config: Project configuration

        Returns:
            Dictionary representing project.json content
        """
        workflow_data = self.get_workflow_config(config.workflow.workflow_type)
        quality_data = self.get_quality_gate_config(config.workflow.quality_gates)

        return {
            "name": config.name,
            "description": config.description,
            "version": "1.0.0",
            "created_at": config.created_at.isoformat(),
            "template": config.template,
            "repository": config.repo_url,
            "tech_stack": config.tech_stack.to_dict() if config.tech_stack else {},
            "team": {
                "members": [m.to_dict() for m in config.team],
                "sprint_duration_weeks": config.sprint_duration_weeks,
                "working_hours_per_day": config.working_hours_per_day,
                "total_capacity_per_sprint": sum(
                    m.capacity_hours * config.sprint_duration_weeks * 5
                    for m in config.team
                )
            },
            "workflow": {
                "type": config.workflow.workflow_type,
                "stages": workflow_data.get("stages", []),
                "agents": config.workflow.agents,
                "description": workflow_data.get("description", "")
            },
            "quality": {
                "level": config.workflow.quality_gates,
                "gates_enabled": quality_data.get("gates", 0),
                "total_rules": quality_data.get("rules", 0),
                "gate_types": quality_data.get("types", [])
            }
        }

    def save_project_metadata(
        self,
        project_path: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Save project metadata to file

        Args:
            project_path: Path to project folder
            metadata: Metadata dictionary

        Returns:
            True if successful
        """
        try:
            metadata_path = Path(project_path) / "project.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved project metadata to {metadata_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save project metadata: {e}")
            return False

    def generate_readme(self, config: ProjectConfig) -> str:
        """
        Generate README.md content for the project

        Args:
            config: Project configuration

        Returns:
            README content as string
        """
        tech_stack_items = []
        if config.tech_stack:
            if config.tech_stack.language:
                tech_stack_items.append(f"- **Language**: {config.tech_stack.language}")
            if config.tech_stack.framework:
                tech_stack_items.append(f"- **Framework**: {config.tech_stack.framework}")
            if config.tech_stack.database:
                tech_stack_items.append(f"- **Database**: {config.tech_stack.database}")

        tech_stack_section = "\n".join(tech_stack_items) if tech_stack_items else "- To be defined"

        team_items = []
        for member in config.team:
            team_items.append(f"- **{member.name}** - {member.role.title()}")
        team_section = "\n".join(team_items) if team_items else "- Team to be assigned"

        return f"""# {config.name}

{config.description}

## Tech Stack

{tech_stack_section}

## Team

{team_section}

## Workflow

- **Type**: {config.workflow.workflow_type if config.workflow else 'Not configured'}
- **Quality Gates**: {config.workflow.quality_gates if config.workflow else 'standard'}
- **Agents**: {', '.join(config.workflow.agents) if config.workflow and config.workflow.agents else 'None assigned'}

## Project Structure

```
{config.name.lower().replace(' ', '-')}/
├── src/           # Source code
├── tests/         # Test files
├── docs/          # Documentation
└── project.json   # Project metadata
```

## Getting Started

1. Clone the repository
2. Install dependencies
3. Configure environment
4. Run the project

## Sprint Information

- **Sprint Duration**: {config.sprint_duration_weeks} weeks
- **Working Hours/Day**: {config.working_hours_per_day} hours

---

*Generated by Project Wizard - Multi-Stack AI Agent Platform*
"""


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_service_instance: Optional[ProjectWizardService] = None


def get_wizard_service() -> ProjectWizardService:
    """Get or create the wizard service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ProjectWizardService()
    return _service_instance
