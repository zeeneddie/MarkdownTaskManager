"""
Project Service - Handles new project creation and folder management

This service creates new project folders, executes the PROJECT_DEFINITION workflow,
and syncs the result with the backend database.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from app.schemas.workflow import ProjectDefinitionRequest, ProjectDefinitionResult
from app.services.agent_service import get_agent_service

logger = logging.getLogger(__name__)


class ProjectService:
    """
    Service for creating and managing new projects
    """

    def __init__(self, projects_base_path: Optional[str] = None):
        """
        Initialize project service

        Args:
            projects_base_path: Base directory for all projects (defaults to ./projects)
        """
        if projects_base_path:
            self.projects_base = Path(projects_base_path)
        else:
            # Default to projects/ directory in root
            self.projects_base = Path(__file__).parent.parent.parent.parent / "projects"

        logger.info(f"ProjectService initialized with base path: {self.projects_base}")

    async def create_project(
        self,
        request: ProjectDefinitionRequest
    ) -> ProjectDefinitionResult:
        """
        Create a new project with complete definition

        This method:
        1. Executes PROJECT_DEFINITION workflow
        2. Creates project folder structure
        3. Writes documentation files
        4. Syncs to backend database

        Args:
            request: Project definition request

        Returns:
            Complete project definition result

        Raises:
            ValueError: If project already exists or validation fails
        """
        logger.info(f"Creating new project: {request.project_name}")

        # Determine project folder path
        if request.folder_path:
            project_path = Path(request.folder_path)
        else:
            # Generate folder name from project name
            folder_name = request.project_name.lower().replace(' ', '-')
            project_path = self.projects_base / folder_name

        # Check if project already exists
        if project_path.exists():
            raise ValueError(f"Project already exists at: {project_path}")

        # Execute PROJECT_DEFINITION workflow via agent service
        agent_service = get_agent_service()

        workflow_request = {
            "description": f"Define new project: {request.project_name}. {request.description}",
            "context": {
                "projectName": request.project_name,
                "description": request.description,
                "businessGoals": request.business_goals or [],
                "targetAudience": request.target_audience,
                "constraints": request.constraints or [],
                "folderPath": str(project_path)
            },
            "priority": "high"
        }

        from app.schemas.workflow import WorkflowRequest
        workflow_result = await agent_service.execute_workflow(
            WorkflowRequest(**workflow_request)
        )

        # Parse the workflow result (mock data for now)
        project_data = workflow_result.result

        # Create folder structure
        folder_info = self._create_folder_structure(
            project_path,
            request.project_name,
            project_data
        )

        # Build final result
        result = ProjectDefinitionResult(
            project_name=request.project_name,
            business_case=project_data.get("businessCase", {}),
            architecture=project_data.get("architecture", {}),
            epics=project_data.get("epics", []),
            project_plan=project_data.get("projectPlan", {}),
            documentation=project_data.get("documentation", {}),
            folder_structure=folder_info,
            workflow_execution=workflow_result
        )

        logger.info(f"Project created successfully: {request.project_name} at {project_path}")

        return result

    def _create_folder_structure(
        self,
        project_path: Path,
        project_name: str,
        project_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create project folder structure and write files

        Args:
            project_path: Path to project directory
            project_name: Name of the project
            project_data: Project definition data from workflow

        Returns:
            Folder structure information
        """
        try:
            # Create main project directory
            project_path.mkdir(parents=True, exist_ok=False)
            logger.info(f"Created project directory: {project_path}")

            # Create subdirectories
            subdirs = ['epics', 'sprints', 'docs', 'architecture']
            for subdir in subdirs:
                (project_path / subdir).mkdir(exist_ok=True)
                logger.debug(f"Created subdirectory: {subdir}")

            created_files = []

            # Write project.md (main project file)
            project_md = self._generate_project_md(project_name, project_data)
            project_file = project_path / "project.md"
            project_file.write_text(project_md)
            created_files.append("project.md")
            logger.debug("Created project.md")

            # Write README.md
            readme = project_data.get("documentation", {}).get("readme", f"# {project_name}\n\nProject documentation pending...")
            readme_file = project_path / "README.md"
            readme_file.write_text(readme)
            created_files.append("README.md")
            logger.debug("Created README.md")

            # Write ARCHITECTURE.md
            arch = project_data.get("documentation", {}).get("architecture", "# Architecture\n\nArchitecture documentation pending...")
            arch_file = project_path / "architecture" / "ARCHITECTURE.md"
            arch_file.write_text(arch)
            created_files.append("architecture/ARCHITECTURE.md")
            logger.debug("Created ARCHITECTURE.md")

            # Write epics as individual files
            epics = project_data.get("epics", [])
            for epic in epics:
                epic_file = project_path / "epics" / f"{epic.get('id', 'EPIC')}.md"
                epic_content = self._generate_epic_md(epic)
                epic_file.write_text(epic_content)
                created_files.append(f"epics/{epic.get('id', 'EPIC')}.md")
                logger.debug(f"Created epic file: {epic.get('id')}")

            # Write project plan
            plan = project_data.get("projectPlan", {})
            plan_file = project_path / "docs" / "PROJECT_PLAN.md"
            plan_content = self._generate_plan_md(plan)
            plan_file.write_text(plan_content)
            created_files.append("docs/PROJECT_PLAN.md")
            logger.debug("Created PROJECT_PLAN.md")

            return {
                "created": True,
                "path": str(project_path),
                "files": created_files
            }

        except Exception as e:
            logger.error(f"Error creating folder structure: {str(e)}", exc_info=True)
            # Cleanup on error
            if project_path.exists():
                import shutil
                shutil.rmtree(project_path)
                logger.info(f"Cleaned up failed project directory: {project_path}")
            raise

    def _generate_project_md(self, project_name: str, project_data: Dict[str, Any]) -> str:
        """Generate project.md content"""
        project_info = project_data.get("project", {})

        content = f"""# {project_name}

## Vision
{project_info.get("vision", "Project vision pending...")}

## Business Case

### Value Proposition
{project_info.get("businessCase", {}).get("value", "Value proposition pending...")}

### Expected ROI
{project_info.get("businessCase", {}).get("roi", "ROI analysis pending...")}

### Risks
"""
        for risk in project_info.get("businessCase", {}).get("risks", []):
            content += f"- {risk}\n"

        content += "\n## Scope\n\n### Included\n"
        for item in project_info.get("scope", {}).get("included", []):
            content += f"- {item}\n"

        content += "\n### Excluded\n"
        for item in project_info.get("scope", {}).get("excluded", []):
            content += f"- {item}\n"

        content += "\n### Constraints\n"
        for item in project_info.get("scope", {}).get("constraints", []):
            content += f"- {item}\n"

        return content

    def _generate_epic_md(self, epic: Dict[str, Any]) -> str:
        """Generate individual epic markdown file"""
        content = f"""# {epic.get("title", "Epic")}

**ID:** {epic.get("id", "N/A")}
**Estimated Effort:** {epic.get("estimatedEffort", "TBD")} story points

## Description
{epic.get("description", "Description pending...")}

## Business Value
{epic.get("businessValue", "Business value pending...")}

## Acceptance Criteria
"""
        for criteria in epic.get("acceptanceCriteria", []):
            content += f"- [ ] {criteria}\n"

        return content

    def _generate_plan_md(self, plan: Dict[str, Any]) -> str:
        """Generate project plan markdown"""
        content = "# Project Plan\n\n"

        content += f"**Timeline:** {plan.get('timeline', 'TBD')}\n\n"

        content += "## Phases\n\n"
        for phase in plan.get("phases", []):
            content += f"### {phase.get('name', 'Phase')}\n"
            content += f"**Duration:** {phase.get('duration', 'TBD')}\n\n"
            content += "**Milestones:**\n"
            for milestone in phase.get("milestones", []):
                content += f"- {milestone}\n"
            content += "\n"

        content += "## Sprints\n\n"
        for sprint in plan.get("sprints", []):
            content += f"### Sprint {sprint.get('number', 'N/A')}\n"
            content += f"**Goal:** {sprint.get('goal', 'TBD')}\n"
            content += f"**Capacity:** {sprint.get('capacity', 'TBD')} points\n"
            content += f"**Epics:** {', '.join(sprint.get('epics', []))}\n\n"

        content += "## Risks\n\n"
        for risk in plan.get("risks", []):
            content += f"### {risk.get('description', 'Risk')}\n"
            content += f"- **Impact:** {risk.get('impact', 'TBD')}\n"
            content += f"- **Mitigation:** {risk.get('mitigation', 'TBD')}\n\n"

        return content


# Singleton instance
_project_service: Optional[ProjectService] = None


def get_project_service() -> ProjectService:
    """Get or create the ProjectService singleton"""
    global _project_service
    if _project_service is None:
        _project_service = ProjectService()
    return _project_service
