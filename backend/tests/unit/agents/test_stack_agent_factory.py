"""
Tests for Stack Agent Factory

Week 56 Day 1: Unit tests for stack-specific agent instantiation.
"""

import pytest
from datetime import datetime

from app.services.stack_agent_factory import (
    StackAgentFactory,
    TechStack,
    AgentRole,
    StackAgentTemplate,
    StackAgentInstance,
    AgentCapability,
    STACK_TEMPLATES,
    get_stack_agent_factory,
)


# ============================================================================
# TEMPLATE DEFINITION TESTS
# ============================================================================

class TestTemplateDefinitions:
    """Test that all templates are properly defined."""

    def test_all_stacks_have_templates(self):
        """Verify all major stacks have at least one template."""
        required_stacks = ["python", "javascript", "go", "rust"]

        for stack in required_stacks:
            templates = []
            for role, stack_templates in STACK_TEMPLATES.items():
                if stack in stack_templates:
                    templates.append(stack_templates[stack])

            assert len(templates) > 0, f"No templates found for stack '{stack}'"

    def test_all_roles_have_templates(self):
        """Verify all roles have at least one template."""
        for role in STACK_TEMPLATES.keys():
            templates = STACK_TEMPLATES[role]
            assert len(templates) > 0, f"No templates for role '{role}'"

    def test_python_templates_complete(self):
        """Verify Python has all role templates."""
        expected_roles = ["backend_dev", "code_reviewer", "security_auditor", "tester"]

        for role in expected_roles:
            assert role in STACK_TEMPLATES, f"Role '{role}' not in templates"
            assert "python" in STACK_TEMPLATES[role], f"Python template missing for {role}"

    def test_javascript_templates_complete(self):
        """Verify JavaScript has all role templates."""
        expected_roles = ["backend_dev", "frontend_dev", "code_reviewer", "security_auditor", "tester"]

        for role in expected_roles:
            if role in STACK_TEMPLATES:
                assert "javascript" in STACK_TEMPLATES[role] or "typescript" in STACK_TEMPLATES.get(role, {}), \
                    f"JS/TS template missing for {role}"

    def test_template_has_required_fields(self):
        """Verify all templates have required fields."""
        for role, stack_templates in STACK_TEMPLATES.items():
            for stack, template in stack_templates.items():
                assert isinstance(template.role, AgentRole)
                assert isinstance(template.stack, TechStack)
                assert template.name_suffix, f"Missing name_suffix for {role}/{stack}"
                assert template.prompt_additions, f"Missing prompt_additions for {role}/{stack}"
                assert template.model_preference, f"Missing model_preference for {role}/{stack}"

    def test_template_capabilities_not_empty(self):
        """Verify templates have capabilities defined."""
        for role, stack_templates in STACK_TEMPLATES.items():
            for stack, template in stack_templates.items():
                assert len(template.capabilities) > 0, \
                    f"No capabilities for {role}/{stack}"

    def test_capability_expertise_level_valid(self):
        """Verify capability expertise levels are valid."""
        for role, stack_templates in STACK_TEMPLATES.items():
            for stack, template in stack_templates.items():
                for cap in template.capabilities:
                    assert 0.0 <= cap.expertise_level <= 1.0, \
                        f"Invalid expertise level for {cap.name} in {role}/{stack}"


# ============================================================================
# FACTORY BASIC TESTS
# ============================================================================

class TestFactoryBasics:
    """Test basic factory operations."""

    @pytest.fixture
    def factory(self):
        """Create fresh factory for each test."""
        return StackAgentFactory()

    def test_factory_singleton(self):
        """Test singleton factory access."""
        factory1 = get_stack_agent_factory()
        factory2 = get_stack_agent_factory()
        assert factory1 is factory2

    def test_get_available_stacks(self, factory):
        """Test listing available stacks."""
        stacks = factory.get_available_stacks()

        assert "python" in stacks
        assert "javascript" in stacks
        assert "go" in stacks
        assert "rust" in stacks
        assert "unknown" not in stacks

    def test_get_available_roles(self, factory):
        """Test listing available roles."""
        roles = factory.get_available_roles()

        assert "backend_dev" in roles
        assert "code_reviewer" in roles
        assert "security_auditor" in roles
        assert "tester" in roles

    def test_get_template(self, factory):
        """Test getting specific template."""
        template = factory.get_template("backend_dev", "python")

        assert template is not None
        assert template.role == AgentRole.BACKEND_DEV
        assert template.stack == TechStack.PYTHON
        assert template.name_suffix == "_py"

    def test_get_template_not_found(self, factory):
        """Test getting non-existent template."""
        template = factory.get_template("nonexistent", "python")
        assert template is None

        template = factory.get_template("backend_dev", "nonexistent")
        assert template is None

    def test_get_templates_for_stack(self, factory):
        """Test getting all templates for a stack."""
        templates = factory.get_templates_for_stack("python")

        assert len(templates) >= 4  # backend, reviewer, security, tester
        for template in templates:
            assert template.stack == TechStack.PYTHON


# ============================================================================
# INSTANCE CREATION TESTS
# ============================================================================

class TestInstanceCreation:
    """Test agent instance creation."""

    @pytest.fixture
    def factory(self):
        """Create fresh factory for each test."""
        return StackAgentFactory()

    def test_create_single_instance(self, factory):
        """Test creating a single agent instance."""
        instance = factory.create_agent_instance(
            project_id=1,
            role="backend_dev",
            stack="python"
        )

        assert instance is not None
        assert instance.project_id == 1
        assert instance.name == "backend_dev_py"
        assert instance.active is True
        assert instance.total_tasks == 0
        assert isinstance(instance.created_at, datetime)

    def test_create_instance_with_overrides(self, factory):
        """Test creating instance with config overrides."""
        overrides = {"max_tokens": 4000, "temperature": 0.7}

        instance = factory.create_agent_instance(
            project_id=1,
            role="code_reviewer",
            stack="python",
            config_overrides=overrides
        )

        assert instance.config_overrides == overrides

    def test_create_instance_invalid_template(self, factory):
        """Test creating instance with invalid template."""
        instance = factory.create_agent_instance(
            project_id=1,
            role="nonexistent",
            stack="python"
        )

        assert instance is None

    def test_create_agents_for_project(self, factory):
        """Test creating all agents for a project."""
        instances = factory.create_agents_for_project(
            project_id=1,
            stacks=["python", "javascript"]
        )

        assert len(instances) > 0

        # Should have agents for both stacks
        python_agents = [i for i in instances if i.template.stack == TechStack.PYTHON]
        js_agents = [i for i in instances if i.template.stack == TechStack.JAVASCRIPT]

        assert len(python_agents) > 0
        assert len(js_agents) > 0

    def test_create_agents_for_project_specific_roles(self, factory):
        """Test creating specific roles for a project."""
        instances = factory.create_agents_for_project(
            project_id=1,
            stacks=["python"],
            roles=["backend_dev", "tester"]
        )

        roles = {i.template.role for i in instances}
        assert AgentRole.BACKEND_DEV in roles
        assert AgentRole.TESTER in roles
        assert AgentRole.CODE_REVIEWER not in roles

    def test_unique_instance_ids(self, factory):
        """Test that instance IDs are unique."""
        instances = factory.create_agents_for_project(
            project_id=1,
            stacks=["python", "javascript", "go"]
        )

        ids = [i.id for i in instances]
        assert len(ids) == len(set(ids))  # All unique


# ============================================================================
# PROJECT AGENT MANAGEMENT TESTS
# ============================================================================

class TestProjectAgentManagement:
    """Test project-level agent management."""

    @pytest.fixture
    def factory_with_agents(self):
        """Create factory with some agents."""
        factory = StackAgentFactory()
        factory.create_agents_for_project(
            project_id=1,
            stacks=["python", "javascript"]
        )
        factory.create_agents_for_project(
            project_id=2,
            stacks=["go"]
        )
        return factory

    def test_get_project_agents(self, factory_with_agents):
        """Test getting all agents for a project."""
        agents = factory_with_agents.get_project_agents(1)

        assert len(agents) > 0
        for name, agent in agents.items():
            assert agent.project_id == 1

    def test_get_project_agents_empty(self, factory_with_agents):
        """Test getting agents for project with none."""
        agents = factory_with_agents.get_project_agents(999)
        assert len(agents) == 0

    def test_get_agent_by_name(self, factory_with_agents):
        """Test getting specific agent by name."""
        agent = factory_with_agents.get_agent_by_name(1, "backend_dev_py")

        assert agent is not None
        assert agent.name == "backend_dev_py"

    def test_get_agent_by_name_not_found(self, factory_with_agents):
        """Test getting non-existent agent."""
        agent = factory_with_agents.get_agent_by_name(1, "nonexistent")
        assert agent is None

    def test_agents_isolated_between_projects(self, factory_with_agents):
        """Test that projects don't share agents."""
        project1_agents = factory_with_agents.get_project_agents(1)
        project2_agents = factory_with_agents.get_project_agents(2)

        project1_names = set(project1_agents.keys())
        project2_names = set(project2_agents.keys())

        # Different stacks = different agent names
        assert "backend_dev_py" in project1_names
        assert "backend_dev_go" in project2_names


# ============================================================================
# PERFORMANCE TRACKING TESTS
# ============================================================================

class TestPerformanceTracking:
    """Test agent performance tracking."""

    @pytest.fixture
    def factory_with_agent(self):
        """Create factory with a single agent."""
        factory = StackAgentFactory()
        factory.create_agent_instance(1, "backend_dev", "python")
        return factory

    def test_initial_performance(self, factory_with_agent):
        """Test initial performance values."""
        agent = factory_with_agent.get_agent_by_name(1, "backend_dev_py")

        assert agent.total_tasks == 0
        assert agent.successful_tasks == 0
        assert agent.success_rate == 0.0
        assert agent.performance_score == 0.0

    def test_update_performance_success(self, factory_with_agent):
        """Test updating performance with success."""
        result = factory_with_agent.update_agent_performance(
            project_id=1,
            agent_name="backend_dev_py",
            success=True,
            performance_delta=0.1
        )

        assert result is True

        agent = factory_with_agent.get_agent_by_name(1, "backend_dev_py")
        assert agent.total_tasks == 1
        assert agent.successful_tasks == 1
        assert agent.success_rate == 1.0
        assert agent.performance_score == 0.1

    def test_update_performance_failure(self, factory_with_agent):
        """Test updating performance with failure."""
        # First success
        factory_with_agent.update_agent_performance(1, "backend_dev_py", True)
        # Then failure
        factory_with_agent.update_agent_performance(1, "backend_dev_py", False)

        agent = factory_with_agent.get_agent_by_name(1, "backend_dev_py")
        assert agent.total_tasks == 2
        assert agent.successful_tasks == 1
        assert agent.success_rate == 0.5

    def test_update_performance_agent_not_found(self, factory_with_agent):
        """Test updating non-existent agent."""
        result = factory_with_agent.update_agent_performance(
            project_id=1,
            agent_name="nonexistent",
            success=True
        )

        assert result is False


# ============================================================================
# AGENT DEACTIVATION TESTS
# ============================================================================

class TestAgentDeactivation:
    """Test agent deactivation."""

    @pytest.fixture
    def factory_with_agent(self):
        """Create factory with a single agent."""
        factory = StackAgentFactory()
        factory.create_agent_instance(1, "backend_dev", "python")
        return factory

    def test_deactivate_agent(self, factory_with_agent):
        """Test deactivating an agent."""
        result = factory_with_agent.deactivate_agent(1, "backend_dev_py")

        assert result is True

        agent = factory_with_agent.get_agent_by_name(1, "backend_dev_py")
        assert agent.active is False

    def test_deactivate_nonexistent_agent(self, factory_with_agent):
        """Test deactivating non-existent agent."""
        result = factory_with_agent.deactivate_agent(1, "nonexistent")
        assert result is False


# ============================================================================
# BEST AGENT SELECTION TESTS
# ============================================================================

class TestBestAgentSelection:
    """Test finding the best agent for a task."""

    @pytest.fixture
    def factory_with_agents(self):
        """Create factory with multiple agents."""
        factory = StackAgentFactory()
        factory.create_agents_for_project(1, ["python", "javascript"])

        # Simulate some performance data
        factory.update_agent_performance(1, "backend_dev_py", True, 0.5)
        factory.update_agent_performance(1, "backend_dev_py", True, 0.3)
        factory.update_agent_performance(1, "backend_dev_js", True, 0.2)
        factory.update_agent_performance(1, "backend_dev_js", False, 0.0)

        return factory

    def test_find_best_agent_for_task(self, factory_with_agents):
        """Test finding best agent for a task type."""
        agent = factory_with_agents.get_best_agent_for_task(
            project_id=1,
            task_type="api_development"
        )

        assert agent is not None
        assert agent.template.role == AgentRole.BACKEND_DEV
        # Should pick Python agent due to better success rate
        assert agent.name == "backend_dev_py"

    def test_find_best_agent_with_capability(self, factory_with_agents):
        """Test finding agent with specific capability."""
        agent = factory_with_agents.get_best_agent_for_task(
            project_id=1,
            task_type="api_development",
            required_capability="database"
        )

        assert agent is not None
        # Both Python and JS have database capability
        assert any(c.name == "database" for c in agent.template.capabilities)

    def test_find_best_agent_no_match(self, factory_with_agents):
        """Test finding agent when no match exists."""
        agent = factory_with_agents.get_best_agent_for_task(
            project_id=1,
            task_type="nonexistent_task"
        )

        assert agent is None

    def test_find_best_agent_excludes_inactive(self, factory_with_agents):
        """Test that inactive agents are excluded."""
        # Deactivate the better performer
        factory_with_agents.deactivate_agent(1, "backend_dev_py")

        agent = factory_with_agents.get_best_agent_for_task(
            project_id=1,
            task_type="api_development"
        )

        assert agent is not None
        assert agent.name == "backend_dev_js"


# ============================================================================
# SERIALIZATION TESTS
# ============================================================================

class TestSerialization:
    """Test export/serialization."""

    @pytest.fixture
    def factory_with_agents(self):
        """Create factory with some agents."""
        factory = StackAgentFactory()
        factory.create_agents_for_project(1, ["python"])
        factory.update_agent_performance(1, "backend_dev_py", True)
        return factory

    def test_to_dict(self, factory_with_agents):
        """Test exporting project agents as dictionary."""
        data = factory_with_agents.to_dict(1)

        assert "project_id" in data
        assert data["project_id"] == 1
        assert "agent_count" in data
        assert data["agent_count"] > 0
        assert "agents" in data

        for agent in data["agents"]:
            assert "id" in agent
            assert "name" in agent
            assert "role" in agent
            assert "stack" in agent
            assert "capabilities" in agent
            assert "validation_phases" in agent

    def test_to_dict_empty_project(self, factory_with_agents):
        """Test exporting empty project."""
        data = factory_with_agents.to_dict(999)

        assert data["project_id"] == 999
        assert data["agent_count"] == 0
        assert data["agents"] == []
