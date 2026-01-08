"""
Project Registration Service

Week 56 Day 5: Unified project registration with automatic stack detection
and agent creation.

This service combines:
- Project folder creation
- Automatic stack detection
- Stack-specific agent creation
- Project metadata management
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from app.services.stack_detection_service import (
    StackDetectionService,
    DetectionResult,
    get_stack_detection_service,
)
from app.services.stack_agent_factory import (
    StackAgentFactory,
    StackAgentInstance,
    get_stack_agent_factory,
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ProjectConfig:
    """Configuration for a new project."""
    name: str
    path: str
    description: str = ""
    business_goals: List[str] = field(default_factory=list)
    target_audience: str = ""
    constraints: List[str] = field(default_factory=list)
    auto_detect_stacks: bool = True
    auto_create_agents: bool = True
    custom_stacks: List[str] = field(default_factory=list)


@dataclass
class RegisteredProject:
    """A registered project with stack agents."""
    id: int
    name: str
    path: str
    description: str
    created_at: datetime
    stacks: List[str]
    agents: List[Dict[str, Any]]
    detection_result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RegistrationResult:
    """Result of project registration."""
    success: bool
    project: Optional[RegisteredProject]
    message: str
    stacks_detected: List[str]
    agents_created: int
    detection_time_ms: int
    errors: List[str] = field(default_factory=list)


# ============================================================================
# PROJECT REGISTRATION SERVICE
# ============================================================================

class ProjectRegistrationService:
    """
    Unified service for project registration with stack detection.

    Example:
        service = ProjectRegistrationService()

        # Register an existing project
        result = service.register_existing_project(
            name="my-project",
            path="/path/to/project"
        )

        # Create a new project with agents
        result = service.create_new_project(
            name="new-project",
            description="My new Python API",
            stacks=["python"]
        )
    """

    def __init__(
        self,
        base_path: Optional[str] = None,
        detection_service: Optional[StackDetectionService] = None,
        agent_factory: Optional[StackAgentFactory] = None,
    ):
        # Use PROJECTS_ROOT from config, fallback to /opt/projecten or ./projects
        from app.config import settings
        if base_path:
            self.base_path = Path(base_path)
        elif hasattr(settings, 'PROJECTS_ROOT') and settings.PROJECTS_ROOT:
            self.base_path = Path(settings.PROJECTS_ROOT)
        else:
            self.base_path = Path("./projects")

        self._detection_service = detection_service  # Created lazily per project
        self.agent_factory = agent_factory or get_stack_agent_factory()

        # In-memory project registry (in production, use database)
        self._projects: Dict[int, RegisteredProject] = {}
        self._next_id = 1

        # Ensure base path exists (only if writable)
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Path may already exist or we don't need to create it
            pass

    def register_existing_project(
        self,
        name: str,
        path: str,
        description: str = "",
        auto_create_agents: bool = True,
        max_files: int = 1000,
    ) -> RegistrationResult:
        """
        Register an existing project directory.

        Detects stacks automatically and creates appropriate agents.

        Args:
            name: Project display name
            path: Path to existing project directory
            description: Project description
            auto_create_agents: Whether to create agents automatically
            max_files: Maximum files to scan for detection

        Returns:
            RegistrationResult with project details and created agents
        """
        errors = []

        # Validate path exists
        project_path = Path(path)
        if not project_path.exists():
            return RegistrationResult(
                success=False,
                project=None,
                message=f"Project path does not exist: {path}",
                stacks_detected=[],
                agents_created=0,
                detection_time_ms=0,
                errors=[f"Path not found: {path}"],
            )

        try:
            # Detect stacks - create detection service for this project
            detection_service = self._detection_service or get_stack_detection_service(str(project_path))
            detection_result = detection_service.detect_stacks(
                project_path=str(project_path),
                max_files=max_files,
            )

            # Use technologies (new terminology) for complete list
            stacks_detected = detection_result.technologies
            detection_dict = detection_service.to_dict(detection_result)

            logger.info(
                f"Detected stacks for {name}: {stacks_detected} "
                f"(type: {detection_result.project_type})"
            )

        except Exception as e:
            logger.error(f"Stack detection failed: {e}")
            errors.append(f"Stack detection failed: {str(e)}")
            stacks_detected = []
            detection_dict = {}
            detection_result = None

        # Create project record
        project_id = self._next_id
        self._next_id += 1

        agents_created = []

        # Create agents if requested
        if auto_create_agents and stacks_detected:
            try:
                # Get recommendations
                if detection_result:
                    recommendations = detection_service.get_recommended_agents(
                        detection_result
                    )
                else:
                    recommendations = [
                        ("backend_dev", stack) for stack in stacks_detected
                    ]

                # Create agents
                for role, stack in recommendations:
                    agent = self.agent_factory.create_agent_instance(
                        project_id=project_id,
                        stack=stack,
                        role=role,
                    )
                    # BUG-002 FIX: Check if agent was created successfully
                    if agent is not None:
                        agents_created.append({
                            "id": agent.id,
                            "name": agent.name,
                            "role": agent.template.role.value,
                            "stack": agent.template.stack.value,
                        })
                    else:
                        logger.warning(f"Failed to create agent for role={role}, stack={stack}")

                logger.info(f"Created {len(agents_created)} agents for project {name}")

            except Exception as e:
                logger.error(f"Agent creation failed: {e}")
                errors.append(f"Agent creation failed: {str(e)}")

        # Create project record
        project = RegisteredProject(
            id=project_id,
            name=name,
            path=str(project_path),
            description=description,
            created_at=datetime.now(),
            stacks=stacks_detected,
            agents=agents_created,
            detection_result=detection_dict,
            metadata={
                "project_type": detection_result.project_type if detection_result else "unknown",
                "total_files": detection_result.total_files if detection_result else 0,
                "frameworks": detection_result.frameworks if detection_result else [],
            },
        )

        self._projects[project_id] = project

        # Save project config
        self._save_project_config(project)

        detection_time = detection_result.detection_time_ms if detection_result else 0

        return RegistrationResult(
            success=True,
            project=project,
            message=f"Registered project {name} with {len(stacks_detected)} stacks and {len(agents_created)} agents",
            stacks_detected=stacks_detected,
            agents_created=len(agents_created),
            detection_time_ms=detection_time,
            errors=errors,
        )

    def create_new_project(
        self,
        name: str,
        description: str = "",
        stacks: Optional[List[str]] = None,
        template: str = "default",
        auto_create_agents: bool = True,
    ) -> RegistrationResult:
        """
        Create a new project with specified stacks.

        Args:
            name: Project name
            description: Project description
            stacks: List of stacks (e.g., ["python", "typescript"])
            template: Project template to use
            auto_create_agents: Whether to create agents automatically

        Returns:
            RegistrationResult with project details
        """
        # Create project directory
        project_path = self.base_path / self._sanitize_name(name)

        if project_path.exists():
            return RegistrationResult(
                success=False,
                project=None,
                message=f"Project already exists: {name}",
                stacks_detected=stacks or [],
                agents_created=0,
                detection_time_ms=0,
                errors=[f"Directory exists: {project_path}"],
            )

        try:
            project_path.mkdir(parents=True)

            # Create basic structure
            self._create_project_structure(project_path, template, stacks or [])

        except Exception as e:
            return RegistrationResult(
                success=False,
                project=None,
                message=f"Failed to create project directory: {str(e)}",
                stacks_detected=[],
                agents_created=0,
                detection_time_ms=0,
                errors=[str(e)],
            )

        # Register the new project
        return self.register_existing_project(
            name=name,
            path=str(project_path),
            description=description,
            auto_create_agents=auto_create_agents,
        )

    def get_project(self, project_id: int) -> Optional[RegisteredProject]:
        """Get a registered project by ID."""
        return self._projects.get(project_id)

    def get_project_by_name(self, name: str) -> Optional[RegisteredProject]:
        """Get a registered project by name."""
        for project in self._projects.values():
            if project.name == name:
                return project
        return None

    def list_projects(self) -> List[RegisteredProject]:
        """List all registered projects."""
        return list(self._projects.values())

    def get_project_agents(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all agents for a project."""
        project = self.get_project(project_id)
        if not project:
            return []
        return project.agents

    def add_stack_to_project(
        self,
        project_id: int,
        stack: str,
        create_agents: bool = True,
    ) -> Dict[str, Any]:
        """
        Add a new stack to an existing project.

        Args:
            project_id: Project ID
            stack: Stack to add (e.g., "python", "rust")
            create_agents: Whether to create agents for the stack

        Returns:
            Dict with added stack info and agents
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        if stack in project.stacks:
            return {
                "message": f"Stack {stack} already exists in project",
                "agents_created": [],
            }

        # Add stack
        project.stacks.append(stack)

        agents_created = []

        if create_agents:
            # Create standard agents for this stack
            roles = ["backend_dev", "code_reviewer", "tester"]
            if stack in ["javascript", "typescript"]:
                roles.append("frontend_dev")
            if stack in ["python", "javascript", "go", "rust"]:
                roles.append("security_auditor")

            for role in roles:
                agent = self.agent_factory.create_agent_instance(
                    project_id=project_id,
                    stack=stack,
                    role=role,
                )
                # BUG-002 FIX: Check if agent was created successfully
                if agent is not None:
                    agent_info = {
                        "id": agent.id,
                        "name": agent.name,
                        "role": agent.template.role.value,
                        "stack": agent.template.stack.value,
                    }
                    agents_created.append(agent_info)
                    project.agents.append(agent_info)
                else:
                    logger.warning(f"Failed to create agent for role={role}, stack={stack}")

        # Update config
        self._save_project_config(project)

        return {
            "message": f"Added stack {stack} to project",
            "agents_created": agents_created,
        }

    def remove_stack_from_project(
        self,
        project_id: int,
        stack: str,
        remove_agents: bool = True,
    ) -> Dict[str, Any]:
        """Remove a stack from a project."""
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        if stack not in project.stacks:
            return {
                "message": f"Stack {stack} not in project",
                "agents_removed": [],
            }

        # Remove stack
        project.stacks.remove(stack)

        agents_removed = []

        if remove_agents:
            # Remove agents for this stack
            agents_to_keep = []
            for agent in project.agents:
                if agent.get("stack") == stack:
                    agents_removed.append(agent)
                else:
                    agents_to_keep.append(agent)
            project.agents = agents_to_keep

        # Update config
        self._save_project_config(project)

        return {
            "message": f"Removed stack {stack} from project",
            "agents_removed": agents_removed,
        }

    def refresh_project_stacks(
        self,
        project_id: int,
        update_agents: bool = True,
    ) -> RegistrationResult:
        """
        Re-detect stacks for a project and update agents.

        Useful when project code has changed significantly.
        """
        project = self.get_project(project_id)
        if not project:
            return RegistrationResult(
                success=False,
                project=None,
                message=f"Project not found: {project_id}",
                stacks_detected=[],
                agents_created=0,
                detection_time_ms=0,
                errors=["Project not found"],
            )

        # Re-detect stacks
        try:
            detection_service = self._detection_service or get_stack_detection_service(project.path)
            detection_result = detection_service.detect_stacks(project.path)
            new_stacks = detection_result.technologies  # Use technologies for complete list

            # Find new stacks
            added_stacks = [s for s in new_stacks if s not in project.stacks]
            removed_stacks = [s for s in project.stacks if s not in new_stacks]

            # Update project
            project.stacks = new_stacks
            project.detection_result = detection_service.to_dict(detection_result)
            project.metadata["project_type"] = detection_result.project_type
            project.metadata["frameworks"] = detection_result.frameworks

            agents_created = 0

            if update_agents:
                # Add agents for new stacks
                for stack in added_stacks:
                    result = self.add_stack_to_project(
                        project_id, stack, create_agents=True
                    )
                    agents_created += len(result.get("agents_created", []))

                # Optionally remove agents for removed stacks
                for stack in removed_stacks:
                    self.remove_stack_from_project(
                        project_id, stack, remove_agents=True
                    )

            self._save_project_config(project)

            return RegistrationResult(
                success=True,
                project=project,
                message=f"Refreshed project stacks: +{len(added_stacks)} -{len(removed_stacks)}",
                stacks_detected=new_stacks,
                agents_created=agents_created,
                detection_time_ms=detection_result.detection_time_ms,
            )

        except Exception as e:
            return RegistrationResult(
                success=False,
                project=project,
                message=f"Failed to refresh stacks: {str(e)}",
                stacks_detected=project.stacks,
                agents_created=0,
                detection_time_ms=0,
                errors=[str(e)],
            )

    def get_project_summary(self, project_id: int) -> Dict[str, Any]:
        """Get a summary of project status."""
        project = self.get_project(project_id)
        if not project:
            return {"error": "Project not found"}

        # Count agents by role
        role_counts = {}
        for agent in project.agents:
            role = agent.get("role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1

        return {
            "id": project.id,
            "name": project.name,
            "path": project.path,
            "description": project.description,
            "created_at": project.created_at.isoformat(),
            "stacks": project.stacks,
            "project_type": project.metadata.get("project_type", "unknown"),
            "total_agents": len(project.agents),
            "agents_by_role": role_counts,
            "frameworks": project.metadata.get("frameworks", {}),
        }

    # ========================================================================
    # PRIVATE METHODS
    # ========================================================================

    def _sanitize_name(self, name: str) -> str:
        """Sanitize project name for use as directory name."""
        # Replace spaces and special chars
        sanitized = name.lower().strip()
        sanitized = sanitized.replace(" ", "-")
        sanitized = "".join(c for c in sanitized if c.isalnum() or c == "-")
        return sanitized or "project"

    def _create_project_structure(
        self,
        project_path: Path,
        template: str,
        stacks: List[str],
    ) -> None:
        """Create initial project structure."""
        # Create basic directories
        (project_path / "src").mkdir()
        (project_path / "tests").mkdir()
        (project_path / "docs").mkdir()

        # Create stack-specific files
        for stack in stacks:
            if stack == "python":
                (project_path / "requirements.txt").write_text("# Python dependencies\n")
                (project_path / "pyproject.toml").write_text(
                    f'[project]\nname = "{project_path.name}"\nversion = "0.1.0"\n'
                )
            elif stack in ["javascript", "typescript"]:
                (project_path / "package.json").write_text(
                    json.dumps({
                        "name": project_path.name,
                        "version": "0.1.0",
                        "private": True,
                    }, indent=2)
                )
                if stack == "typescript":
                    (project_path / "tsconfig.json").write_text(
                        json.dumps({
                            "compilerOptions": {
                                "target": "ES2020",
                                "module": "commonjs",
                                "strict": True,
                            }
                        }, indent=2)
                    )
            elif stack == "go":
                (project_path / "go.mod").write_text(
                    f"module {project_path.name}\n\ngo 1.21\n"
                )
            elif stack == "rust":
                (project_path / "Cargo.toml").write_text(
                    f'[package]\nname = "{project_path.name}"\nversion = "0.1.0"\nedition = "2021"\n'
                )

        # Create README
        (project_path / "README.md").write_text(
            f"# {project_path.name}\n\n"
            f"Stacks: {', '.join(stacks) or 'Not specified'}\n"
        )

    def delete_project(self, project_id: int, delete_files: bool = False) -> Dict[str, Any]:
        """
        Delete a project and all related data.

        Args:
            project_id: Project ID to delete
            delete_files: If True, also delete .project-config.json file

        Returns:
            Dict with deletion results
        """
        project = self.get_project(project_id)
        if not project:
            return {
                "success": False,
                "message": f"Project not found: {project_id}",
            }

        deleted_items = {
            "project_id": project_id,
            "project_name": project.name,
            "stacks": project.stacks,
            "agents_count": len(project.agents),
        }

        # Remove from in-memory registry
        if project_id in self._projects:
            del self._projects[project_id]

        # Optionally delete config file
        if delete_files:
            config_path = Path(project.path) / ".project-config.json"
            if config_path.exists():
                try:
                    config_path.unlink()
                    deleted_items["config_file_deleted"] = True
                except Exception as e:
                    logger.warning(f"Failed to delete config file: {e}")
                    deleted_items["config_file_deleted"] = False

        logger.info(f"Deleted project {project_id}: {project.name}")

        return {
            "success": True,
            "message": f"Project '{project.name}' deleted successfully",
            "deleted": deleted_items,
        }

    def _save_project_config(self, project: RegisteredProject) -> None:
        """Save project configuration to file."""
        config_path = Path(project.path) / ".project-config.json"

        try:
            config = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at.isoformat(),
                "stacks": project.stacks,
                "agents": project.agents,
                "metadata": project.metadata,
            }
            config_path.write_text(json.dumps(config, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save project config: {e}")

    def _load_project_config(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load project configuration from file."""
        config_path = path / ".project-config.json"

        if not config_path.exists():
            return None

        try:
            return json.loads(config_path.read_text())
        except Exception as e:
            logger.warning(f"Failed to load project config: {e}")
            return None


# ============================================================================
# SINGLETON ACCESS
# ============================================================================

_service: Optional[ProjectRegistrationService] = None


def get_project_registration_service() -> ProjectRegistrationService:
    """Get the global project registration service instance."""
    global _service
    if _service is None:
        _service = ProjectRegistrationService()
    return _service
