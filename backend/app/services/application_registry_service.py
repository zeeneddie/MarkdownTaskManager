"""
Application Registry Service

Week 57 Day 1: Hierarchical application management for multi-project repositories.

Architecture:
    Application (top-level)
        ├── Project (component with agents)
        ├── Project (component with agents)
        ├── Library (shared code, special handling)
        └── Project (component with agents)

This enables:
- Cross-project context awareness
- Shared library detection
- Dependency tracking between projects
- Application-level agents (architects, integrators)
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.application import (
    Application as ApplicationModel,
    Component as ComponentModel,
    StackAgent as StackAgentModel,
)

from app.services.project_registration_service import (
    ProjectRegistrationService,
    RegisteredProject,
    get_project_registration_service,
)
from app.services.stack_detection_service import (
    StackDetectionService,
    get_stack_detection_service,
)
from app.services.documentation_templates import (
    get_template,
    get_default,
    get_domain_overrides,
    render_template,
    detect_domain,
)

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class ComponentType(Enum):
    """Type of component within an application."""
    PROJECT = "project"      # Regular project (backend, frontend, etc.)
    LIBRARY = "library"      # Shared library
    SERVICE = "service"      # Microservice
    TOOL = "tool"            # Build tools, scripts, etc.
    CONFIG = "config"        # Configuration/infrastructure


@dataclass
class ApplicationComponent:
    """A component (project/library) within an application."""
    id: int
    name: str
    path: str
    component_type: ComponentType
    stacks: List[str]
    frameworks: Dict[str, List[str]]
    dependencies: List[int] = field(default_factory=list)  # IDs of dependent components
    dependents: List[int] = field(default_factory=list)    # IDs that depend on this
    agents: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Application:
    """Top-level application containing multiple projects."""
    id: int
    name: str
    root_path: str
    description: str
    created_at: datetime
    components: Dict[int, ApplicationComponent]  # component_id -> component
    primary_stacks: List[str]  # All stacks across all components
    application_type: str  # monolith, microservices, monorepo, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApplicationScanResult:
    """Result of scanning an application directory."""
    success: bool
    application: Optional[Application]
    components_found: int
    libraries_found: int
    total_stacks: List[str]
    scan_time_ms: int
    errors: List[str] = field(default_factory=list)


# ============================================================================
# COMPONENT DETECTION PATTERNS
# ============================================================================

# Patterns that indicate a directory is a separate project/component
COMPONENT_INDICATORS = {
    # Package managers
    "package.json": ComponentType.PROJECT,
    "pyproject.toml": ComponentType.PROJECT,
    "Cargo.toml": ComponentType.PROJECT,
    "go.mod": ComponentType.PROJECT,
    "pom.xml": ComponentType.PROJECT,
    "build.gradle": ComponentType.PROJECT,

    # Library indicators
    "setup.py": ComponentType.LIBRARY,
    "setup.cfg": ComponentType.LIBRARY,
}

# Directory names that typically indicate component types
DIRECTORY_TYPE_HINTS = {
    # Projects
    "backend": ComponentType.PROJECT,
    "frontend": ComponentType.PROJECT,
    "api": ComponentType.PROJECT,
    "web": ComponentType.PROJECT,
    "mobile": ComponentType.PROJECT,
    "app": ComponentType.PROJECT,
    "server": ComponentType.PROJECT,
    "client": ComponentType.PROJECT,

    # Libraries
    "lib": ComponentType.LIBRARY,
    "libs": ComponentType.LIBRARY,
    "packages": ComponentType.LIBRARY,
    "shared": ComponentType.LIBRARY,
    "common": ComponentType.LIBRARY,
    "core": ComponentType.LIBRARY,
    "utils": ComponentType.LIBRARY,

    # Services
    "services": ComponentType.SERVICE,
    "microservices": ComponentType.SERVICE,

    # Tools
    "tools": ComponentType.TOOL,
    "scripts": ComponentType.TOOL,
    "build": ComponentType.TOOL,

    # Config
    "infra": ComponentType.CONFIG,
    "infrastructure": ComponentType.CONFIG,
    "deploy": ComponentType.CONFIG,
    "k8s": ComponentType.CONFIG,
    "terraform": ComponentType.CONFIG,
}

# Directories to skip during scanning
SKIP_DIRECTORIES = {
    "node_modules", "__pycache__", ".git", ".venv", "venv",
    "dist", "build", "target", ".next", ".nuxt", "coverage",
    ".tox", ".eggs", "*.egg-info", ".mypy_cache", ".pytest_cache",
}


# ============================================================================
# APPLICATION REGISTRY SERVICE
# ============================================================================

class ApplicationRegistryService:
    """
    Manages hierarchical applications with multiple projects.

    Example:
        service = ApplicationRegistryService()

        # Scan a monorepo
        result = service.scan_application(
            name="my-platform",
            root_path="/path/to/monorepo"
        )

        # Get cross-project dependencies
        deps = service.get_dependency_graph(app_id=1)

        # Get all agents across the application
        agents = service.get_application_agents(app_id=1)
    """

    def __init__(
        self,
        project_service: Optional[ProjectRegistrationService] = None,
        detection_service: Optional[StackDetectionService] = None,
    ):
        self.project_service = project_service or get_project_registration_service()
        self._detection_service = detection_service  # Created lazily per application

        # In-memory registries
        self._applications: Dict[int, Application] = {}
        self._next_app_id = 1
        self._next_component_id = 1

    def scan_application(
        self,
        name: str,
        root_path: str,
        description: str = "",
        max_depth: int = 3,
        auto_create_agents: bool = True,
    ) -> ApplicationScanResult:
        """
        Scan a directory to discover and register all components.

        Args:
            name: Application name
            root_path: Path to application root
            description: Application description
            max_depth: How deep to scan for components
            auto_create_agents: Whether to create agents for each component

        Returns:
            ApplicationScanResult with discovered components
        """
        import time
        start_time = time.time()
        errors = []

        root = Path(root_path)
        if not root.exists():
            return ApplicationScanResult(
                success=False,
                application=None,
                components_found=0,
                libraries_found=0,
                total_stacks=[],
                scan_time_ms=0,
                errors=[f"Path not found: {root_path}"],
            )

        # Discover components
        components: Dict[int, ApplicationComponent] = {}
        all_stacks: Set[str] = set()
        libraries_count = 0

        discovered = self._discover_components(root, max_depth)

        for comp_path, comp_type in discovered:
            try:
                # Detect stacks for this component - create detection service lazily
                detection_service = self._detection_service or get_stack_detection_service(str(comp_path))
                detection = detection_service.detect_stacks(
                    str(comp_path),
                    max_files=200,
                )

                comp_id = self._next_component_id
                self._next_component_id += 1

                # Create component
                component = ApplicationComponent(
                    id=comp_id,
                    name=comp_path.name,
                    path=str(comp_path),
                    component_type=comp_type,
                    stacks=detection.primary_stacks,
                    frameworks=detection.frameworks,
                    metadata={
                        "project_type": detection.project_type,
                        "files_scanned": detection.total_files,
                    },
                )

                # Create agents if requested
                if auto_create_agents and detection.technologies:
                    agents = self._create_component_agents(comp_id, component, detection)
                    component.agents = agents

                components[comp_id] = component
                # Use technologies for complete list of detected techs
                all_stacks.update(detection.technologies)

                if comp_type == ComponentType.LIBRARY:
                    libraries_count += 1

            except Exception as e:
                errors.append(f"Failed to process {comp_path}: {str(e)}")
                logger.error(f"Component scan error: {e}")

        # Detect dependencies between components
        self._detect_dependencies(components)

        # Determine application type
        app_type = self._determine_application_type(components)

        # Create application
        app_id = self._next_app_id
        self._next_app_id += 1

        application = Application(
            id=app_id,
            name=name,
            root_path=str(root),
            description=description,
            created_at=datetime.now(),
            components=components,
            primary_stacks=sorted(list(all_stacks)),
            application_type=app_type,
            metadata={
                "total_components": len(components),
                "total_libraries": libraries_count,
            },
        )

        self._applications[app_id] = application

        # Note: Database save is handled by save_application_to_database()
        # which should be called from async context (e.g., API endpoint)

        # Save configuration
        self._save_application_config(application)

        # Generate standard documentation
        self._generate_documentation(application)

        scan_time_ms = int((time.time() - start_time) * 1000)

        return ApplicationScanResult(
            success=True,
            application=application,
            components_found=len(components),
            libraries_found=libraries_count,
            total_stacks=sorted(list(all_stacks)),
            scan_time_ms=scan_time_ms,
            errors=errors,
        )

    def get_application(self, app_id: int) -> Optional[Application]:
        """Get an application by ID."""
        return self._applications.get(app_id)

    def list_applications(self) -> List[Application]:
        """List all registered applications."""
        return list(self._applications.values())

    def get_component(self, app_id: int, component_id: int) -> Optional[ApplicationComponent]:
        """Get a specific component from an application."""
        app = self.get_application(app_id)
        if not app:
            return None
        return app.components.get(component_id)

    def get_application_agents(self, app_id: int) -> List[Dict[str, Any]]:
        """Get all agents across all components in an application."""
        app = self.get_application(app_id)
        if not app:
            return []

        all_agents = []
        for component in app.components.values():
            for agent in component.agents:
                all_agents.append({
                    **agent,
                    "component_id": component.id,
                    "component_name": component.name,
                    "component_type": component.component_type.value,
                })

        return all_agents

    def get_dependency_graph(self, app_id: int) -> Dict[str, Any]:
        """
        Get the dependency graph for an application.

        Returns a structure showing which components depend on which.
        """
        app = self.get_application(app_id)
        if not app:
            return {"error": "Application not found"}

        nodes = []
        edges = []

        for comp_id, comp in app.components.items():
            nodes.append({
                "id": comp_id,
                "name": comp.name,
                "type": comp.component_type.value,
                "stacks": comp.stacks,
            })

            for dep_id in comp.dependencies:
                edges.append({
                    "from": comp_id,
                    "to": dep_id,
                    "type": "depends_on",
                })

        return {
            "application": app.name,
            "nodes": nodes,
            "edges": edges,
            "libraries": [
                n for n in nodes
                if n["type"] == ComponentType.LIBRARY.value
            ],
        }

    def get_component_context(
        self,
        app_id: int,
        component_id: int,
    ) -> Dict[str, Any]:
        """
        Get full context for a component including dependencies.

        This is what agents need to understand cross-project context.
        """
        app = self.get_application(app_id)
        if not app:
            return {"error": "Application not found"}

        component = app.components.get(component_id)
        if not component:
            return {"error": "Component not found"}

        # Get dependencies
        dependencies = []
        for dep_id in component.dependencies:
            dep = app.components.get(dep_id)
            if dep:
                dependencies.append({
                    "id": dep.id,
                    "name": dep.name,
                    "type": dep.component_type.value,
                    "stacks": dep.stacks,
                    "path": dep.path,
                })

        # Get dependents (what depends on this component)
        dependents = []
        for dep_id in component.dependents:
            dep = app.components.get(dep_id)
            if dep:
                dependents.append({
                    "id": dep.id,
                    "name": dep.name,
                    "type": dep.component_type.value,
                })

        # Get sibling components (same level, same app)
        siblings = []
        for comp_id, comp in app.components.items():
            if comp_id != component_id:
                siblings.append({
                    "id": comp.id,
                    "name": comp.name,
                    "type": comp.component_type.value,
                    "stacks": comp.stacks,
                })

        return {
            "component": {
                "id": component.id,
                "name": component.name,
                "path": component.path,
                "type": component.component_type.value,
                "stacks": component.stacks,
                "frameworks": component.frameworks,
            },
            "application": {
                "id": app.id,
                "name": app.name,
                "type": app.application_type,
                "total_stacks": app.primary_stacks,
            },
            "dependencies": dependencies,
            "dependents": dependents,
            "siblings": siblings,
            "agents": component.agents,
        }

    def get_libraries_for_component(
        self,
        app_id: int,
        component_id: int,
    ) -> List[ApplicationComponent]:
        """Get all library components that a component depends on."""
        app = self.get_application(app_id)
        if not app:
            return []

        component = app.components.get(component_id)
        if not component:
            return []

        libraries = []
        for dep_id in component.dependencies:
            dep = app.components.get(dep_id)
            if dep and dep.component_type == ComponentType.LIBRARY:
                libraries.append(dep)

        return libraries

    def get_application_summary(self, app_id: int) -> Dict[str, Any]:
        """Get a summary of the application structure."""
        app = self.get_application(app_id)
        if not app:
            return {"error": "Application not found"}

        # Count by type
        type_counts = {}
        for comp in app.components.values():
            t = comp.component_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        # Count agents by role
        agent_counts = {}
        for comp in app.components.values():
            for agent in comp.agents:
                role = agent.get("role", "unknown")
                agent_counts[role] = agent_counts.get(role, 0) + 1

        return {
            "id": app.id,
            "name": app.name,
            "root_path": app.root_path,
            "description": app.description,
            "created_at": app.created_at.isoformat(),
            "application_type": app.application_type,
            "primary_stacks": app.primary_stacks,
            "total_components": len(app.components),
            "components_by_type": type_counts,
            "total_agents": sum(len(c.agents) for c in app.components.values()),
            "agents_by_role": agent_counts,
        }

    # ========================================================================
    # PRIVATE METHODS
    # ========================================================================

    def _discover_components(
        self,
        root: Path,
        max_depth: int,
    ) -> List[tuple]:
        """Discover components in a directory tree."""
        components = []

        def scan_dir(path: Path, depth: int):
            if depth > max_depth:
                return

            if path.name in SKIP_DIRECTORIES:
                return

            # Check if this directory is a component
            comp_type = self._identify_component_type(path)
            if comp_type:
                components.append((path, comp_type))
                # Don't scan deeper into identified components
                return

            # Scan subdirectories
            try:
                for item in path.iterdir():
                    if item.is_dir() and not item.name.startswith("."):
                        scan_dir(item, depth + 1)
            except PermissionError:
                pass

        scan_dir(root, 0)
        return components

    def _identify_component_type(self, path: Path) -> Optional[ComponentType]:
        """Identify if a directory is a component and what type."""
        # Check for component indicator files
        for indicator, comp_type in COMPONENT_INDICATORS.items():
            if (path / indicator).exists():
                # Check directory name hints for more specific type
                dir_hint = DIRECTORY_TYPE_HINTS.get(path.name.lower())
                if dir_hint:
                    return dir_hint
                return comp_type

        # Check directory name
        dir_hint = DIRECTORY_TYPE_HINTS.get(path.name.lower())
        if dir_hint:
            # Verify it has some code files
            has_code = any(
                path.glob(pattern) for pattern in ["*.py", "*.ts", "*.js", "*.go", "*.rs"]
            )
            if has_code or list(path.glob("**/package.json")) or list(path.glob("**/pyproject.toml")):
                return dir_hint

        return None

    def _create_component_agents(
        self,
        comp_id: int,
        component: ApplicationComponent,
        detection,
    ) -> List[Dict[str, Any]]:
        """Create agents for a component based on its type and stacks."""
        agents = []

        # Get recommendations from detection service - create lazily
        detection_service = self._detection_service or get_stack_detection_service(component.path)
        recommendations = detection_service.get_recommended_agents(detection)

        for role, stack in recommendations:
            try:
                agent = self.project_service.agent_factory.create_agent_instance(
                    project_id=comp_id,
                    stack=stack,
                    role=role,
                )
                # BUG-002 FIX: Check if agent was created successfully before accessing attributes
                if agent is None:
                    logger.warning(
                        f"No agent template available for component {component.name} (role={role}, stack={stack})"
                    )
                    continue

                agents.append({
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.template.role.value,
                    "stack": agent.template.stack.value,
                })
            except Exception as e:
                logger.debug(f"Could not create agent {role}/{stack}: {e}")

        return agents

    def _detect_dependencies(
        self,
        components: Dict[int, ApplicationComponent],
    ) -> None:
        """Detect dependencies between components."""
        # Build path to ID mapping
        path_to_id = {Path(c.path).name: c.id for c in components.values()}

        for comp_id, comp in components.items():
            comp_path = Path(comp.path)

            # Check package.json for JS/TS dependencies
            pkg_json = comp_path / "package.json"
            if pkg_json.exists():
                try:
                    pkg = json.loads(pkg_json.read_text())
                    all_deps = {
                        **pkg.get("dependencies", {}),
                        **pkg.get("devDependencies", {}),
                    }
                    for dep_name in all_deps:
                        # Check if it's a workspace reference
                        if dep_name in path_to_id and path_to_id[dep_name] != comp_id:
                            dep_id = path_to_id[dep_name]
                            comp.dependencies.append(dep_id)
                            components[dep_id].dependents.append(comp_id)
                except Exception:
                    pass

            # Check pyproject.toml for Python dependencies
            pyproject = comp_path / "pyproject.toml"
            if pyproject.exists():
                try:
                    content = pyproject.read_text()
                    for name, other_id in path_to_id.items():
                        if name in content and other_id != comp_id:
                            comp.dependencies.append(other_id)
                            components[other_id].dependents.append(comp_id)
                except Exception:
                    pass

    def _determine_application_type(
        self,
        components: Dict[int, ApplicationComponent],
    ) -> str:
        """Determine the type of application based on components."""
        if not components:
            return "empty"

        type_counts = {}
        for comp in components.values():
            t = comp.component_type
            type_counts[t] = type_counts.get(t, 0) + 1

        num_projects = type_counts.get(ComponentType.PROJECT, 0)
        num_services = type_counts.get(ComponentType.SERVICE, 0)
        num_libraries = type_counts.get(ComponentType.LIBRARY, 0)

        if num_services > 2:
            return "microservices"
        elif num_projects > 3:
            return "monorepo"
        elif num_projects == 1 and num_libraries == 0:
            return "single-project"
        elif num_libraries > 0:
            return "monorepo-with-libs"
        else:
            return "multi-project"

    def _save_application_config(self, app: Application) -> None:
        """Save application configuration to file."""
        config_path = Path(app.root_path) / ".application-config.json"

        try:
            config = {
                "id": app.id,
                "name": app.name,
                "description": app.description,
                "created_at": app.created_at.isoformat(),
                "application_type": app.application_type,
                "primary_stacks": app.primary_stacks,
                "components": {
                    str(comp_id): {
                        "name": comp.name,
                        "path": comp.path,
                        "type": comp.component_type.value,
                        "stacks": comp.stacks,
                        "dependencies": comp.dependencies,
                    }
                    for comp_id, comp in app.components.items()
                },
            }
            config_path.write_text(json.dumps(config, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save application config: {e}")

    def _generate_documentation(self, app: Application) -> None:
        """
        Generate standard documentation for the application using templates.

        Creates:
        - doc/README.md - Entry point, navigation
        - doc/PROJECT_GOAL.md - Business context (template, needs manual completion)
        - doc/ARCHITECTURE.md - Technical architecture (auto-generated)
        - doc/PROJECT_INTAKE.md - Stack detection results

        Uses templates from documentation_templates.py for consistent structure.
        """
        doc_path = Path(app.root_path) / "doc"
        doc_path.mkdir(exist_ok=True)

        # Detect domain for domain-specific templates
        all_frameworks: Dict[str, List[str]] = {}
        for comp in app.components.values():
            for stack, frameworks in comp.frameworks.items():
                if stack not in all_frameworks:
                    all_frameworks[stack] = []
                all_frameworks[stack].extend(frameworks)

        domain = detect_domain(app.primary_stacks, all_frameworks)
        domain_overrides = get_domain_overrides(domain)

        try:
            # Prepare common template values
            template_values = self._prepare_template_values(app, domain_overrides)

            # Generate README.md
            self._generate_from_template(
                doc_path / "README.md",
                get_template("README"),
                template_values,
                overwrite=True,
            )

            # Generate PROJECT_INTAKE.md (auto-generated from scan)
            self._generate_from_template(
                doc_path / "PROJECT_INTAKE.md",
                get_template("PROJECT_INTAKE"),
                template_values,
                overwrite=True,
            )

            # Generate ARCHITECTURE.md (auto-generated from scan)
            self._generate_from_template(
                doc_path / "ARCHITECTURE.md",
                get_template("ARCHITECTURE"),
                template_values,
                overwrite=True,
            )

            # Generate PROJECT_GOAL.md (template - don't overwrite if exists)
            self._generate_from_template(
                doc_path / "PROJECT_GOAL.md",
                get_template("PROJECT_GOAL"),
                template_values,
                overwrite=False,  # Don't overwrite manual edits
            )

            logger.info(f"Documentation generated at {doc_path} (domain: {domain})")

        except Exception as e:
            logger.error(f"Failed to generate documentation: {e}")

    def _prepare_template_values(
        self, app: Application, domain_overrides: Dict[str, str]
    ) -> Dict[str, Any]:
        """Prepare all values needed for documentation templates."""
        # Build component tree for README
        component_tree = ""
        for comp in app.components.values():
            rel_path = Path(comp.path).name
            component_tree += f"    └── {rel_path}/  # {comp.component_type.value}\n"

        # Build stack analysis table
        stack_usage: Dict[str, List[str]] = {}
        for comp in app.components.values():
            for stack in comp.stacks:
                if stack not in stack_usage:
                    stack_usage[stack] = []
                stack_usage[stack].append(comp.name)

        stack_analysis_table = ""
        for stack, components in sorted(stack_usage.items(), key=lambda x: len(x[1]), reverse=True):
            comp_list = ', '.join(components[:3]) + ('...' if len(components) > 3 else '')
            stack_analysis_table += f"| **{stack}** | - | High | {comp_list} |\n"

        # Build stack table for architecture
        stack_table = ""
        for stack in app.primary_stacks:
            using = stack_usage.get(stack, [])
            stack_table += f"| **{stack}** | Primary technology | {', '.join(using[:2])} |\n"

        # Build frameworks section
        frameworks_section = ""
        all_frameworks: Dict[str, set] = {}
        for comp in app.components.values():
            for stack, frameworks in comp.frameworks.items():
                if stack not in all_frameworks:
                    all_frameworks[stack] = set()
                all_frameworks[stack].update(frameworks)

        if all_frameworks:
            for stack, frameworks in all_frameworks.items():
                frameworks_section += f"**{stack}:** {', '.join(frameworks)}\n\n"
        else:
            frameworks_section = "*Geen frameworks gedetecteerd.*"

        frameworks_table = frameworks_section

        # Build component table
        component_table = ""
        for comp in app.components.values():
            stacks = ', '.join(comp.stacks[:3]) + ('...' if len(comp.stacks) > 3 else '')
            component_table += f"| {comp.id} | {comp.name} | {comp.component_type.value} | {stacks} | {len(comp.agents)} |\n"

        # Build agent table
        agent_table = ""
        for comp in app.components.values():
            for agent in comp.agents:
                agent_table += f"| {agent.get('name', 'Unknown')} | {agent.get('role', 'Unknown')} | {comp.name} | {agent.get('stack', '-')} | {agent.get('model', '-')} |\n"

        if not agent_table:
            agent_table = "| *No agents created* | | | | |\n"

        # Build dependency section
        dependency_section = ""
        has_deps = False
        for comp in app.components.values():
            if comp.dependencies:
                has_deps = True
                dep_names = [app.components[d].name for d in comp.dependencies if d in app.components]
                dependency_section += f"- **{comp.name}** depends on: {', '.join(dep_names)}\n"

        if not has_deps:
            dependency_section = "*Geen inter-component dependencies gedetecteerd.*"

        # Build component details for architecture
        component_details = ""
        for comp in app.components.values():
            component_details += f"""### {comp.name}

| Property | Value |
|----------|-------|
| **Type** | {comp.component_type.value} |
| **Path** | `{comp.path}` |
| **Stacks** | {', '.join(comp.stacks)} |
| **Agents** | {len(comp.agents)} |

"""
            if comp.frameworks:
                component_details += "**Frameworks:**\n"
                for stack, frameworks in comp.frameworks.items():
                    component_details += f"- {stack}: {', '.join(frameworks)}\n"
                component_details += "\n"

        # Build system diagram
        system_diagram = f"{app.name}/\n"
        for comp in app.components.values():
            rel_path = Path(comp.path).name
            system_diagram += f"├── {rel_path}/  ({comp.component_type.value})\n"

        # Build integration table
        integration_table = ""
        # Detect integrations from frameworks
        integration_keywords = {
            "zorgmail": "Healthcare Email",
            "medmij": "PGO Integration",
            "afas": "ERP Integration",
            "stripe": "Payment Processing",
            "oauth": "Authentication",
        }
        detected_integrations = []
        for fw_set in all_frameworks.values():
            for fw in fw_set:
                fw_lower = fw.lower()
                for keyword, description in integration_keywords.items():
                    if keyword in fw_lower and description not in detected_integrations:
                        detected_integrations.append(description)
                        integration_table += f"| **{description}** | {fw} |\n"

        if not integration_table:
            integration_table = "| *No integrations detected* | |\n"

        integration_methods = "> **TODO:** Beschrijf integratie methodes (REST, SOAP, etc.)"

        # Combine all values
        values = {
            # Common
            "name": app.name,
            "application_type": app.application_type,
            "root_path": app.root_path,
            "registration_date": app.created_at.strftime('%Y-%m-%d'),
            "generation_date": datetime.now().strftime('%Y-%m-%d'),
            "primary_stacks": ', '.join(app.primary_stacks),
            "component_count": len(app.components),

            # README specific
            "component_tree": component_tree,

            # INTAKE specific
            "stack_analysis_table": stack_analysis_table,
            "frameworks_table": frameworks_table,
            "component_table": component_table,
            "agent_table": agent_table,
            "dependency_section": dependency_section,

            # ARCHITECTURE specific
            "system_diagram": system_diagram,
            "stack_table": stack_table,
            "frameworks_section": frameworks_section,
            "component_details": component_details,
            "integration_table": integration_table,
            "integration_methods": integration_methods,
        }

        # Apply domain overrides
        values.update(domain_overrides)

        return values

    def _generate_from_template(
        self,
        file_path: Path,
        template: str,
        values: Dict[str, Any],
        overwrite: bool = True,
    ) -> None:
        """Generate a file from a template."""
        if not overwrite and file_path.exists():
            logger.info(f"{file_path.name} already exists, skipping")
            return

        content = render_template(template, values)
        file_path.write_text(content)
        logger.debug(f"Generated {file_path.name}")

    # Legacy methods removed - now using template system above

    # ========================================================================
    # DATABASE PERSISTENCE METHODS
    # ========================================================================

    async def _save_to_database(self, application: Application) -> None:
        """Save application and its components to the database."""
        async with AsyncSessionLocal() as session:
            try:
                # Check if application already exists by name and path
                result = await session.execute(
                    select(ApplicationModel).where(
                        ApplicationModel.name == application.name,
                        ApplicationModel.root_path == application.root_path,
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing
                    existing.primary_stacks = application.primary_stacks
                    existing.application_type = application.application_type
                    existing.updated_at = datetime.now()
                    existing.last_scan_at = datetime.now()
                    db_app = existing
                else:
                    # Create new
                    db_app = ApplicationModel(
                        name=application.name,
                        root_path=application.root_path,
                        description=application.description,
                        application_type=application.application_type,
                        primary_stacks=application.primary_stacks,
                        created_at=application.created_at,
                        last_scan_at=datetime.now(),
                    )
                    session.add(db_app)
                    await session.flush()  # Get the ID

                # Delete existing components for this app
                await session.execute(
                    delete(ComponentModel).where(
                        ComponentModel.application_id == db_app.id
                    )
                )

                # Add new components
                for comp in application.components.values():
                    db_comp = ComponentModel(
                        application_id=db_app.id,
                        name=comp.name,
                        path=comp.path,
                        component_type=comp.component_type.value,
                        stacks=comp.stacks,
                        file_count=comp.metadata.get("files_scanned", 0),
                        created_at=datetime.now(),
                        last_scan_at=datetime.now(),
                    )
                    session.add(db_comp)

                    # Add agents for this component
                    for agent in comp.agents:
                        db_agent = StackAgentModel(
                            application_id=db_app.id,
                            stack=agent.get("stack", "unknown"),
                            role=agent.get("role", "developer"),
                            model_preference=agent.get("model"),
                            capabilities=agent.get("capabilities", []),
                            is_active=True,
                        )
                        session.add(db_agent)

                await session.commit()
                logger.info(f"Saved application '{application.name}' to database (id={db_app.id})")

            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to save application to database: {e}")
                raise

    async def save_application_to_database(self, app_id: int) -> bool:
        """
        Public async method to save an application to the database.
        Should be called from async context (e.g., API endpoint).
        """
        application = self._applications.get(app_id)
        if not application:
            logger.error(f"Application {app_id} not found in memory")
            return False

        try:
            await self._save_to_database(application)
            return True
        except Exception as e:
            logger.error(f"Failed to persist application {app_id}: {e}")
            return False

    async def _load_from_database(self) -> None:
        """Load all applications from database into memory."""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(ApplicationModel).where(ApplicationModel.is_active == True)
                )
                db_apps = result.scalars().all()

                for db_app in db_apps:
                    # Load components
                    comp_result = await session.execute(
                        select(ComponentModel).where(
                            ComponentModel.application_id == db_app.id
                        )
                    )
                    db_components = comp_result.scalars().all()

                    # Load agents
                    agent_result = await session.execute(
                        select(StackAgentModel).where(
                            StackAgentModel.application_id == db_app.id
                        )
                    )
                    db_agents = agent_result.scalars().all()

                    # Build components dict
                    components: Dict[int, ApplicationComponent] = {}
                    for db_comp in db_components:
                        # Find agents for this component's stacks
                        comp_agents = [
                            {
                                "stack": a.stack,
                                "role": a.role,
                                "model": a.model_preference,
                                "capabilities": a.capabilities or [],
                            }
                            for a in db_agents
                            if a.stack in (db_comp.stacks or [])
                        ]

                        components[db_comp.id] = ApplicationComponent(
                            id=db_comp.id,
                            name=db_comp.name,
                            path=db_comp.path,
                            component_type=ComponentType(db_comp.component_type),
                            stacks=db_comp.stacks or [],
                            frameworks={},
                            agents=comp_agents,
                            metadata={"files_scanned": db_comp.file_count},
                        )

                    # Create application object
                    app = Application(
                        id=db_app.id,
                        name=db_app.name,
                        root_path=db_app.root_path,
                        description=db_app.description or "",
                        created_at=db_app.created_at or datetime.now(),
                        components=components,
                        primary_stacks=db_app.primary_stacks or [],
                        application_type=db_app.application_type or "single-project",
                        metadata={
                            "total_components": len(components),
                            "total_agents": len(db_agents),
                        },
                    )

                    self._applications[db_app.id] = app
                    if db_app.id >= self._next_app_id:
                        self._next_app_id = db_app.id + 1

                logger.info(f"Loaded {len(db_apps)} applications from database")

            except Exception as e:
                logger.error(f"Failed to load applications from database: {e}")

    def load_from_database_sync(self) -> None:
        """Synchronous wrapper to load from database.

        Note: When called from within an async context (like FastAPI),
        prefer using load_from_database() directly.
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Skip sync load if loop is running - will load on first API call
                logger.info("Event loop running, skipping sync database load")
                return
            else:
                loop.run_until_complete(self._load_from_database())
        except RuntimeError:
            asyncio.run(self._load_from_database())

    async def load_from_database(self) -> None:
        """Public async method to load applications from database.
        Call this from async context (e.g., FastAPI lifespan or first request).
        """
        await self._load_from_database()


# ============================================================================
# SINGLETON ACCESS
# ============================================================================

_service: Optional[ApplicationRegistryService] = None
_loaded_from_db: bool = False


def get_application_registry_service(load_from_db: bool = False) -> ApplicationRegistryService:
    """Get the global application registry service instance.

    Note: load_from_db is False by default in async contexts like FastAPI.
    Use get_application_registry_service_async() for proper async loading.

    Args:
        load_from_db: Whether to attempt sync load (only works outside async context).
    """
    global _service
    if _service is None:
        _service = ApplicationRegistryService()
        if load_from_db:
            _service.load_from_database_sync()
    return _service


async def get_application_registry_service_async() -> ApplicationRegistryService:
    """Get the service with async database loading.

    This should be used from FastAPI endpoints to ensure applications
    are loaded from the database.
    """
    global _service, _loaded_from_db
    if _service is None:
        _service = ApplicationRegistryService()

    if not _loaded_from_db:
        await _service._load_from_database()
        _loaded_from_db = True

    return _service


# NOTE: Old inline documentation methods have been replaced by the template
# system in documentation_templates.py for consistent, maintainable structure.
