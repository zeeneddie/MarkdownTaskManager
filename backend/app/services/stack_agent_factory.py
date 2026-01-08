"""
Stack Agent Factory - Multi-Stack Agent Instantiation

Week 56 Day 1: Factory for creating stack-specific agent instances.

Features:
- Per-project agent instantiation based on detected tech stack
- Stack templates (Python, JavaScript, Go, Rust)
- Specialized capabilities per stack
- Provider routing based on task complexity
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


class TechStack(Enum):
    """Supported technology stacks."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    CSHARP = "csharp"
    UNKNOWN = "unknown"


class AgentRole(Enum):
    """Stack agent roles."""
    BACKEND_DEV = "backend_dev"
    FRONTEND_DEV = "frontend_dev"
    CODE_REVIEWER = "code_reviewer"
    SECURITY_AUDITOR = "security_auditor"
    TESTER = "tester"
    DEVOPS = "devops"


@dataclass
class AgentCapability:
    """Individual agent capability."""
    name: str
    description: str
    expertise_level: float = 0.8  # 0.0 - 1.0


@dataclass
class StackAgentTemplate:
    """Template for creating stack-specific agents."""
    role: AgentRole
    stack: TechStack
    name_suffix: str  # e.g., "_py", "_js"
    prompt_additions: str
    model_preference: str = "qwen2.5-coder:7b"
    capabilities: List[AgentCapability] = field(default_factory=list)
    specialized_tools: List[str] = field(default_factory=list)
    validation_phases: List[str] = field(default_factory=list)


@dataclass
class StackAgentInstance:
    """Instantiated stack agent for a specific project."""
    id: str
    project_id: int
    template: StackAgentTemplate
    created_at: datetime
    active: bool = True
    performance_score: float = 0.0
    total_tasks: int = 0
    successful_tasks: int = 0
    config_overrides: Dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        """Generate agent name from template."""
        return f"{self.template.role.value}{self.template.name_suffix}"

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks


# ============================================================================
# STACK TEMPLATES DEFINITIONS
# ============================================================================

STACK_TEMPLATES: Dict[str, Dict[str, StackAgentTemplate]] = {
    # Backend Developer templates
    "backend_dev": {
        "python": StackAgentTemplate(
            role=AgentRole.BACKEND_DEV,
            stack=TechStack.PYTHON,
            name_suffix="_py",
            prompt_additions="""Expert Python backend developer specializing in:
- FastAPI, Django, Flask framework development
- SQLAlchemy, Tortoise ORM, async database patterns
- Pydantic data validation and serialization
- Async programming with asyncio and HTTPX
- RESTful and GraphQL API design
- SOLID principles and clean architecture
- Poetry/pip dependency management
- Type hints and mypy compliance""",
            model_preference="qwen2.5-coder:7b",
            capabilities=[
                AgentCapability("api_design", "RESTful and GraphQL API architecture", 0.95),
                AgentCapability("database", "SQL and NoSQL database patterns", 0.9),
                AgentCapability("async", "Asynchronous programming patterns", 0.9),
                AgentCapability("testing", "pytest, unittest, coverage", 0.85),
                AgentCapability("security", "Authentication, authorization, OWASP", 0.8),
            ],
            specialized_tools=["ruff", "mypy", "black", "pytest", "bandit"],
            validation_phases=["linting", "type_check", "style", "unit_tests"],
        ),
        "javascript": StackAgentTemplate(
            role=AgentRole.BACKEND_DEV,
            stack=TechStack.JAVASCRIPT,
            name_suffix="_js",
            prompt_additions="""Expert JavaScript/Node.js backend developer specializing in:
- Express, Fastify, Nest.js framework development
- TypeORM, Prisma, Sequelize ORM patterns
- Node.js async patterns and event loop optimization
- RESTful and GraphQL (Apollo) API design
- ES6+ modern JavaScript features
- npm/yarn/pnpm package management
- TypeScript integration and configuration""",
            model_preference="qwen2.5-coder:7b",
            capabilities=[
                AgentCapability("api_design", "RESTful and GraphQL API architecture", 0.9),
                AgentCapability("database", "SQL with TypeORM/Prisma", 0.85),
                AgentCapability("async", "Node.js async patterns, Promises", 0.9),
                AgentCapability("testing", "Jest, Mocha, Supertest", 0.85),
            ],
            specialized_tools=["eslint", "prettier", "jest", "tsc"],
            validation_phases=["linting", "type_check", "style", "unit_tests"],
        ),
        "go": StackAgentTemplate(
            role=AgentRole.BACKEND_DEV,
            stack=TechStack.GO,
            name_suffix="_go",
            prompt_additions="""Expert Go backend developer specializing in:
- Gin, Echo, Chi HTTP frameworks
- GORM, sqlx database patterns
- Goroutines and channels for concurrency
- gRPC and protocol buffers
- Go module dependency management
- Standard library patterns and idioms
- Error handling patterns""",
            model_preference="deepseek-coder:latest",
            capabilities=[
                AgentCapability("api_design", "RESTful and gRPC API design", 0.9),
                AgentCapability("database", "SQL with GORM/sqlx", 0.85),
                AgentCapability("concurrency", "Goroutines, channels, sync", 0.9),
                AgentCapability("testing", "go test, testify", 0.85),
            ],
            specialized_tools=["go vet", "golangci-lint", "go test"],
            validation_phases=["linting", "vet", "unit_tests"],
        ),
        "rust": StackAgentTemplate(
            role=AgentRole.BACKEND_DEV,
            stack=TechStack.RUST,
            name_suffix="_rs",
            prompt_additions="""Expert Rust backend developer specializing in:
- Actix-web, Axum, Rocket frameworks
- Diesel, SeaORM database patterns
- Async runtime (Tokio, async-std)
- Memory safety and ownership patterns
- Error handling with Result and Option
- Cargo dependency management
- Zero-cost abstractions""",
            model_preference="deepseek-coder:latest",
            capabilities=[
                AgentCapability("api_design", "RESTful API with type safety", 0.9),
                AgentCapability("database", "SQL with Diesel/SeaORM", 0.85),
                AgentCapability("async", "Tokio async runtime", 0.9),
                AgentCapability("memory_safety", "Ownership, borrowing, lifetimes", 0.95),
            ],
            specialized_tools=["cargo clippy", "cargo fmt", "cargo test"],
            validation_phases=["clippy", "fmt", "unit_tests"],
        ),
    },

    # Frontend Developer templates
    "frontend_dev": {
        "javascript": StackAgentTemplate(
            role=AgentRole.FRONTEND_DEV,
            stack=TechStack.JAVASCRIPT,
            name_suffix="_js",
            prompt_additions="""Expert JavaScript frontend developer specializing in:
- React, Vue.js, Angular frameworks
- State management (Redux, Vuex, MobX)
- Modern CSS (Tailwind, styled-components)
- Responsive design and accessibility
- Build tools (Webpack, Vite, esbuild)
- Testing (Jest, React Testing Library, Cypress)
- Browser APIs and performance optimization""",
            model_preference="qwen2.5-coder:7b",
            capabilities=[
                AgentCapability("ui_components", "React/Vue component architecture", 0.9),
                AgentCapability("state_management", "Redux, Context, Zustand", 0.85),
                AgentCapability("styling", "CSS-in-JS, Tailwind, SCSS", 0.85),
                AgentCapability("accessibility", "WCAG compliance, a11y", 0.8),
                AgentCapability("testing", "Jest, RTL, Cypress", 0.85),
            ],
            specialized_tools=["eslint", "prettier", "jest", "cypress"],
            validation_phases=["linting", "style", "unit_tests", "e2e"],
        ),
        "typescript": StackAgentTemplate(
            role=AgentRole.FRONTEND_DEV,
            stack=TechStack.TYPESCRIPT,
            name_suffix="_ts",
            prompt_additions="""Expert TypeScript frontend developer specializing in:
- React with TypeScript, Next.js
- Type-safe state management
- Advanced TypeScript patterns (generics, utility types)
- Modern CSS (Tailwind, styled-components)
- Build optimization and code splitting
- Type-safe API integration (tRPC, OpenAPI)""",
            model_preference="qwen2.5-coder:7b",
            capabilities=[
                AgentCapability("typescript", "Advanced TS patterns", 0.95),
                AgentCapability("ui_components", "Type-safe React components", 0.9),
                AgentCapability("state_management", "Type-safe Redux/Zustand", 0.85),
                AgentCapability("api_integration", "tRPC, OpenAPI, GraphQL codegen", 0.9),
            ],
            specialized_tools=["tsc", "eslint", "prettier", "jest"],
            validation_phases=["type_check", "linting", "style", "unit_tests"],
        ),
    },

    # Code Reviewer templates
    "code_reviewer": {
        "python": StackAgentTemplate(
            role=AgentRole.CODE_REVIEWER,
            stack=TechStack.PYTHON,
            name_suffix="_py",
            prompt_additions="""Expert Python code reviewer focusing on:
- PEP 8 style guide compliance
- Type hint correctness and coverage
- Pythonic idioms and best practices
- Performance optimization opportunities
- Security vulnerability detection
- Test coverage assessment
- Documentation quality""",
            model_preference="deepseek-r1:latest",
            capabilities=[
                AgentCapability("style_review", "PEP 8 compliance", 0.95),
                AgentCapability("security_review", "Vulnerability detection", 0.9),
                AgentCapability("performance_review", "Optimization suggestions", 0.85),
                AgentCapability("architecture_review", "Design pattern assessment", 0.85),
            ],
            specialized_tools=["ruff", "mypy", "bandit", "radon"],
            validation_phases=["linting", "security", "complexity"],
        ),
        "javascript": StackAgentTemplate(
            role=AgentRole.CODE_REVIEWER,
            stack=TechStack.JAVASCRIPT,
            name_suffix="_js",
            prompt_additions="""Expert JavaScript/TypeScript code reviewer focusing on:
- ESLint rule compliance
- TypeScript type safety
- Modern JS patterns and antipatterns
- Performance and bundle size optimization
- Security best practices
- Test coverage and quality""",
            model_preference="deepseek-r1:latest",
            capabilities=[
                AgentCapability("style_review", "ESLint compliance", 0.95),
                AgentCapability("security_review", "npm audit, vulnerability detection", 0.9),
                AgentCapability("performance_review", "Bundle optimization", 0.85),
            ],
            specialized_tools=["eslint", "tsc", "npm audit"],
            validation_phases=["linting", "type_check", "security"],
        ),
        "go": StackAgentTemplate(
            role=AgentRole.CODE_REVIEWER,
            stack=TechStack.GO,
            name_suffix="_go",
            prompt_additions="""Expert Go code reviewer focusing on:
- Go idioms and best practices
- Effective Go guidelines
- Concurrency pattern review
- Error handling patterns
- Performance optimization""",
            model_preference="deepseek-r1:latest",
            capabilities=[
                AgentCapability("style_review", "Go idioms compliance", 0.95),
                AgentCapability("concurrency_review", "Goroutine safety", 0.9),
                AgentCapability("performance_review", "Memory and CPU optimization", 0.85),
            ],
            specialized_tools=["go vet", "golangci-lint", "go test -race"],
            validation_phases=["vet", "lint", "race_detection"],
        ),
        "rust": StackAgentTemplate(
            role=AgentRole.CODE_REVIEWER,
            stack=TechStack.RUST,
            name_suffix="_rs",
            prompt_additions="""Expert Rust code reviewer focusing on:
- Clippy lint compliance
- Memory safety patterns
- Ownership and borrowing correctness
- Error handling with Result
- Performance and zero-cost abstractions""",
            model_preference="deepseek-r1:latest",
            capabilities=[
                AgentCapability("style_review", "Clippy compliance", 0.95),
                AgentCapability("memory_review", "Ownership pattern review", 0.95),
                AgentCapability("performance_review", "Zero-cost abstraction usage", 0.9),
            ],
            specialized_tools=["cargo clippy", "cargo fmt --check"],
            validation_phases=["clippy", "fmt_check"],
        ),
    },

    # Security Auditor templates
    "security_auditor": {
        "python": StackAgentTemplate(
            role=AgentRole.SECURITY_AUDITOR,
            stack=TechStack.PYTHON,
            name_suffix="_py",
            prompt_additions="""Expert Python security auditor specializing in:
- OWASP Top 10 vulnerability detection
- SQL injection, XSS, CSRF prevention
- Dependency vulnerability scanning (Safety, pip-audit)
- Authentication and authorization review
- Secrets detection
- Input validation patterns""",
            model_preference="claude/sonnet",
            capabilities=[
                AgentCapability("vulnerability_scan", "OWASP Top 10 detection", 0.95),
                AgentCapability("dependency_audit", "CVE detection in dependencies", 0.9),
                AgentCapability("secrets_detection", "API keys, passwords in code", 0.95),
                AgentCapability("auth_review", "AuthN/AuthZ patterns", 0.9),
            ],
            specialized_tools=["bandit", "safety", "pip-audit", "semgrep"],
            validation_phases=["security_scan", "dependency_audit", "secrets_scan"],
        ),
        "javascript": StackAgentTemplate(
            role=AgentRole.SECURITY_AUDITOR,
            stack=TechStack.JAVASCRIPT,
            name_suffix="_js",
            prompt_additions="""Expert JavaScript security auditor specializing in:
- OWASP Top 10 for frontend and Node.js
- XSS prevention and CSP
- npm dependency vulnerability scanning
- Authentication flow review
- Secrets in client-side code detection""",
            model_preference="claude/sonnet",
            capabilities=[
                AgentCapability("vulnerability_scan", "OWASP detection", 0.95),
                AgentCapability("dependency_audit", "npm audit, Snyk", 0.9),
                AgentCapability("xss_prevention", "XSS pattern detection", 0.9),
            ],
            specialized_tools=["npm audit", "snyk", "eslint-plugin-security"],
            validation_phases=["security_scan", "dependency_audit"],
        ),
        "go": StackAgentTemplate(
            role=AgentRole.SECURITY_AUDITOR,
            stack=TechStack.GO,
            name_suffix="_go",
            prompt_additions="""Expert Go security auditor specializing in:
- Go security best practices
- Race condition detection
- Input validation patterns
- Cryptography usage review
- Dependency vulnerability scanning""",
            model_preference="claude/sonnet",
            capabilities=[
                AgentCapability("vulnerability_scan", "Go security patterns", 0.9),
                AgentCapability("race_detection", "Concurrent access issues", 0.9),
                AgentCapability("crypto_review", "Cryptography usage", 0.85),
            ],
            specialized_tools=["gosec", "go test -race", "govulncheck"],
            validation_phases=["security_scan", "race_detection"],
        ),
        "rust": StackAgentTemplate(
            role=AgentRole.SECURITY_AUDITOR,
            stack=TechStack.RUST,
            name_suffix="_rs",
            prompt_additions="""Expert Rust security auditor specializing in:
- Memory safety verification
- Unsafe block review
- Dependency vulnerability scanning
- Cryptography usage patterns""",
            model_preference="claude/sonnet",
            capabilities=[
                AgentCapability("memory_safety", "Unsafe code review", 0.95),
                AgentCapability("dependency_audit", "cargo audit", 0.9),
                AgentCapability("crypto_review", "Cryptography patterns", 0.85),
            ],
            specialized_tools=["cargo audit", "cargo clippy"],
            validation_phases=["audit", "unsafe_review"],
        ),
    },

    # Tester templates
    "tester": {
        "python": StackAgentTemplate(
            role=AgentRole.TESTER,
            stack=TechStack.PYTHON,
            name_suffix="_py",
            prompt_additions="""Expert Python tester specializing in:
- pytest test framework
- Test-driven development (TDD)
- Mocking with unittest.mock, pytest-mock
- Coverage analysis with pytest-cov
- Integration and E2E testing
- Property-based testing with Hypothesis""",
            model_preference="qwen2.5-coder:7b",
            capabilities=[
                AgentCapability("unit_testing", "pytest mastery", 0.95),
                AgentCapability("integration_testing", "API and DB testing", 0.9),
                AgentCapability("mocking", "Mock patterns", 0.9),
                AgentCapability("coverage", "Coverage optimization", 0.85),
            ],
            specialized_tools=["pytest", "pytest-cov", "pytest-mock", "hypothesis"],
            validation_phases=["unit_tests", "coverage_check"],
        ),
        "javascript": StackAgentTemplate(
            role=AgentRole.TESTER,
            stack=TechStack.JAVASCRIPT,
            name_suffix="_js",
            prompt_additions="""Expert JavaScript tester specializing in:
- Jest test framework
- React Testing Library
- Cypress for E2E testing
- Mock Service Worker (MSW)
- Coverage with Istanbul/c8""",
            model_preference="qwen2.5-coder:7b",
            capabilities=[
                AgentCapability("unit_testing", "Jest mastery", 0.95),
                AgentCapability("component_testing", "RTL patterns", 0.9),
                AgentCapability("e2e_testing", "Cypress automation", 0.9),
                AgentCapability("mocking", "MSW, jest.mock", 0.85),
            ],
            specialized_tools=["jest", "cypress", "msw"],
            validation_phases=["unit_tests", "e2e", "coverage_check"],
        ),
        "go": StackAgentTemplate(
            role=AgentRole.TESTER,
            stack=TechStack.GO,
            name_suffix="_go",
            prompt_additions="""Expert Go tester specializing in:
- go test framework
- Table-driven tests
- Testify assertions and mocks
- Coverage with go test -cover
- Benchmark testing""",
            model_preference="qwen2.5-coder:7b",
            capabilities=[
                AgentCapability("unit_testing", "go test mastery", 0.95),
                AgentCapability("table_tests", "Table-driven patterns", 0.9),
                AgentCapability("benchmarking", "Performance testing", 0.85),
            ],
            specialized_tools=["go test", "testify"],
            validation_phases=["unit_tests", "coverage_check", "benchmarks"],
        ),
        "rust": StackAgentTemplate(
            role=AgentRole.TESTER,
            stack=TechStack.RUST,
            name_suffix="_rs",
            prompt_additions="""Expert Rust tester specializing in:
- cargo test framework
- Unit and integration tests
- Documentation tests
- Property testing with proptest
- Benchmark testing with criterion""",
            model_preference="qwen2.5-coder:7b",
            capabilities=[
                AgentCapability("unit_testing", "cargo test mastery", 0.95),
                AgentCapability("doc_testing", "Documentation tests", 0.9),
                AgentCapability("property_testing", "Proptest patterns", 0.85),
            ],
            specialized_tools=["cargo test", "cargo tarpaulin"],
            validation_phases=["unit_tests", "doc_tests", "coverage_check"],
        ),
    },
}


class StackAgentFactory:
    """
    Factory for creating stack-specific agent instances.

    Responsibilities:
    - Instantiate agents from templates based on project tech stack
    - Track agent instances per project
    - Provide agent configuration for execution
    """

    def __init__(self):
        """Initialize the factory."""
        self._instances: Dict[int, Dict[str, StackAgentInstance]] = {}
        self._instance_counter = 0

    def _generate_instance_id(self) -> str:
        """Generate unique instance ID."""
        self._instance_counter += 1
        return f"agent_{self._instance_counter:06d}"

    def get_available_stacks(self) -> List[str]:
        """Get list of supported tech stacks."""
        return [s.value for s in TechStack if s != TechStack.UNKNOWN]

    def get_available_roles(self) -> List[str]:
        """Get list of available agent roles."""
        return [r.value for r in AgentRole]

    def get_template(self, role: str, stack: str) -> Optional[StackAgentTemplate]:
        """
        Get template for a specific role and stack.

        Args:
            role: Agent role (e.g., "backend_dev")
            stack: Tech stack (e.g., "python")

        Returns:
            Template if found, None otherwise
        """
        role_templates = STACK_TEMPLATES.get(role, {})
        return role_templates.get(stack)

    def get_templates_for_stack(self, stack: str) -> List[StackAgentTemplate]:
        """
        Get all templates available for a specific stack.

        Args:
            stack: Tech stack (e.g., "python")

        Returns:
            List of available templates
        """
        templates = []
        for role, stack_templates in STACK_TEMPLATES.items():
            if stack in stack_templates:
                templates.append(stack_templates[stack])
        return templates

    def create_agent_instance(
        self,
        project_id: int,
        role: str,
        stack: str,
        config_overrides: Optional[Dict[str, Any]] = None
    ) -> Optional[StackAgentInstance]:
        """
        Create an agent instance for a project.

        Args:
            project_id: Project ID
            role: Agent role (e.g., "backend_dev")
            stack: Tech stack (e.g., "python")
            config_overrides: Optional configuration overrides

        Returns:
            Created instance or None if template not found
        """
        template = self.get_template(role, stack)
        if not template:
            return None

        instance = StackAgentInstance(
            id=self._generate_instance_id(),
            project_id=project_id,
            template=template,
            created_at=datetime.utcnow(),
            config_overrides=config_overrides or {},
        )

        # Store instance
        if project_id not in self._instances:
            self._instances[project_id] = {}

        self._instances[project_id][instance.name] = instance

        return instance

    def create_agents_for_project(
        self,
        project_id: int,
        stacks: List[str],
        roles: Optional[List[str]] = None
    ) -> List[StackAgentInstance]:
        """
        Create all relevant agents for a project based on detected stacks.

        Args:
            project_id: Project ID
            stacks: List of detected tech stacks
            roles: Optional list of roles to create (defaults to all)

        Returns:
            List of created instances
        """
        if roles is None:
            roles = list(STACK_TEMPLATES.keys())

        instances = []
        for stack in stacks:
            for role in roles:
                instance = self.create_agent_instance(project_id, role, stack)
                if instance:
                    instances.append(instance)

        return instances

    def get_project_agents(self, project_id: int) -> Dict[str, StackAgentInstance]:
        """Get all agent instances for a project."""
        return self._instances.get(project_id, {})

    def get_agent_by_name(
        self,
        project_id: int,
        agent_name: str
    ) -> Optional[StackAgentInstance]:
        """Get a specific agent instance by name."""
        project_agents = self._instances.get(project_id, {})
        return project_agents.get(agent_name)

    def update_agent_performance(
        self,
        project_id: int,
        agent_name: str,
        success: bool,
        performance_delta: float = 0.0
    ) -> bool:
        """
        Update agent performance metrics.

        Args:
            project_id: Project ID
            agent_name: Agent name
            success: Whether task was successful
            performance_delta: Performance score change

        Returns:
            True if updated, False if agent not found
        """
        agent = self.get_agent_by_name(project_id, agent_name)
        if not agent:
            return False

        agent.total_tasks += 1
        if success:
            agent.successful_tasks += 1
        agent.performance_score += performance_delta

        return True

    def deactivate_agent(self, project_id: int, agent_name: str) -> bool:
        """Deactivate an agent instance."""
        agent = self.get_agent_by_name(project_id, agent_name)
        if agent:
            agent.active = False
            return True
        return False

    def get_best_agent_for_task(
        self,
        project_id: int,
        task_type: str,
        required_capability: Optional[str] = None
    ) -> Optional[StackAgentInstance]:
        """
        Find the best agent for a specific task.

        Args:
            project_id: Project ID
            task_type: Type of task (maps to role)
            required_capability: Optional required capability

        Returns:
            Best matching agent or None
        """
        project_agents = self.get_project_agents(project_id)
        if not project_agents:
            return None

        # Map task types to roles
        task_role_map = {
            "api_development": AgentRole.BACKEND_DEV,
            "database_work": AgentRole.BACKEND_DEV,
            "ui_development": AgentRole.FRONTEND_DEV,
            "code_review": AgentRole.CODE_REVIEWER,
            "security_audit": AgentRole.SECURITY_AUDITOR,
            "testing": AgentRole.TESTER,
            "deployment": AgentRole.DEVOPS,
        }

        target_role = task_role_map.get(task_type)
        if not target_role:
            return None

        # Filter by role and capability
        candidates = []
        for agent in project_agents.values():
            if not agent.active:
                continue
            if agent.template.role != target_role:
                continue

            if required_capability:
                has_capability = any(
                    c.name == required_capability
                    for c in agent.template.capabilities
                )
                if not has_capability:
                    continue

            candidates.append(agent)

        if not candidates:
            return None

        # Return agent with best success rate
        return max(candidates, key=lambda a: (a.success_rate, a.performance_score))

    def to_dict(self, project_id: int) -> Dict[str, Any]:
        """Export project agents as dictionary."""
        project_agents = self.get_project_agents(project_id)

        return {
            "project_id": project_id,
            "agent_count": len(project_agents),
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.template.role.value,
                    "stack": agent.template.stack.value,
                    "model": agent.template.model_preference,
                    "active": agent.active,
                    "success_rate": agent.success_rate,
                    "total_tasks": agent.total_tasks,
                    "capabilities": [c.name for c in agent.template.capabilities],
                    "validation_phases": agent.template.validation_phases,
                }
                for agent in project_agents.values()
            ],
        }


# Singleton factory instance
_factory_instance: Optional[StackAgentFactory] = None


def get_stack_agent_factory() -> StackAgentFactory:
    """Get or create the stack agent factory singleton."""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = StackAgentFactory()
    return _factory_instance
