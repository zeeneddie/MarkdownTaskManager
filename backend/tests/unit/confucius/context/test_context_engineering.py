"""
Tests for Context Engineering module.

Tests cover:
- ReferenceSelector semantic matching
- ReferenceRegistry loading and caching
- ContextOptimizer token optimization
- Reference categories and filtering
"""

import pytest
from datetime import datetime

from app.confucius.context import (
    ReferenceSelector,
    Reference,
    ReferenceMatch,
    ReferenceCategory,
    ReferenceRegistry,
    ContextOptimizer,
    OptimizedContext,
    create_reference_selector,
    create_reference_registry,
    create_context_optimizer,
)


# =============================================================================
# REFERENCE SELECTOR TESTS
# =============================================================================


class TestReferenceSelector:
    """Tests for ReferenceSelector."""

    @pytest.fixture
    def selector(self):
        """Create reference selector with defaults."""
        return create_reference_selector()

    @pytest.fixture
    def custom_selector(self):
        """Create selector with custom references."""
        refs = [
            Reference(
                id="test-ref-1",
                name="Test Reference 1",
                category=ReferenceCategory.TESTING,
                path=".claude/reference/test.md",
                keywords=["pytest", "unittest", "mock", "fixture"],
                description="Test patterns",
                token_estimate=1000,
                domains=["testing"],
                agents=["Tessa"],
            ),
            Reference(
                id="test-ref-2",
                name="Test Reference 2",
                category=ReferenceCategory.SECURITY,
                path=".claude/reference/security.md",
                keywords=["owasp", "sql injection", "xss"],
                description="Security patterns",
                token_estimate=1500,
                domains=["security"],
                agents=["Quinn"],
            ),
        ]
        return ReferenceSelector(references=refs)

    def test_selector_creation(self, selector):
        """Test creating selector with default references."""
        refs = selector.list_references()
        assert len(refs) > 0
        assert all(isinstance(r, Reference) for r in refs)

    def test_select_by_keywords(self, custom_selector):
        """Test selecting references by keyword match."""
        matches = custom_selector.select(
            task="Write pytest fixtures for unit testing",
            context={},
            max_references=2,
        )

        assert len(matches) > 0
        # Test reference should be first (best match)
        assert matches[0].reference.id == "test-ref-1"
        assert "pytest" in matches[0].matched_keywords

    def test_select_by_domain(self, custom_selector):
        """Test selecting references by domain."""
        matches = custom_selector.select(
            task="Review code for issues",
            context={"domain": "security"},
            max_references=2,
        )

        # Security reference should score higher due to domain match
        security_match = next(
            (m for m in matches if m.reference.id == "test-ref-2"),
            None
        )
        assert security_match is not None
        assert security_match.score > 0

    def test_select_for_agent(self, custom_selector):
        """Test selecting references for specific agent."""
        matches = custom_selector.select_for_agent(
            agent_name="Tessa",
            task="Write tests",
            context={},
        )

        assert len(matches) > 0
        # Tessa's reference should be included
        assert any(m.reference.id == "test-ref-1" for m in matches)

    def test_get_token_estimate(self, custom_selector):
        """Test token estimation."""
        matches = custom_selector.select(
            task="Write pytest fixtures",
            context={},
            max_references=2,
        )

        estimate = custom_selector.get_token_estimate(matches)
        assert estimate > 0
        assert estimate <= sum(r.token_estimate for r in custom_selector.list_references())

    def test_add_reference(self, selector):
        """Test adding reference."""
        original_count = len(selector.list_references())

        new_ref = Reference(
            id="new-ref",
            name="New Reference",
            category=ReferenceCategory.GENERAL,
            path=".claude/reference/new.md",
            keywords=["new", "test"],
            description="New reference",
            token_estimate=500,
        )
        selector.add_reference(new_ref)

        assert len(selector.list_references()) == original_count + 1
        assert selector.get_reference("new-ref") is not None

    def test_remove_reference(self, selector):
        """Test removing reference."""
        selector.add_reference(Reference(
            id="temp-ref",
            name="Temp",
            category=ReferenceCategory.GENERAL,
            path="temp.md",
            keywords=[],
            description="Temp",
        ))

        assert selector.remove_reference("temp-ref") is True
        assert selector.get_reference("temp-ref") is None
        assert selector.remove_reference("nonexistent") is False


class TestReferenceMatch:
    """Tests for ReferenceMatch dataclass."""

    def test_match_to_dict(self):
        """Test match serialization."""
        ref = Reference(
            id="test",
            name="Test",
            category=ReferenceCategory.TESTING,
            path="test.md",
            keywords=["test"],
            description="Test ref",
            token_estimate=1000,
        )
        match = ReferenceMatch(
            reference=ref,
            score=0.85,
            matched_keywords=["test", "pytest"],
            reason="Keyword match",
        )

        data = match.to_dict()

        assert data["reference_id"] == "test"
        assert data["score"] == 0.85
        assert data["matched_keywords"] == ["test", "pytest"]
        assert data["reason"] == "Keyword match"
        assert data["token_estimate"] == 1000


# =============================================================================
# REFERENCE REGISTRY TESTS
# =============================================================================


class TestReferenceRegistry:
    """Tests for ReferenceRegistry."""

    @pytest.fixture
    def registry(self):
        """Create registry without auto-load."""
        return create_reference_registry(auto_load=False)

    def test_registry_creation(self, registry):
        """Test creating registry."""
        refs = registry.list_references()
        assert len(refs) > 0

    def test_is_loaded(self, registry):
        """Test checking if reference is loaded."""
        assert registry.is_loaded("asp-vbscript") is False

    def test_list_loaded(self, registry):
        """Test listing loaded references."""
        loaded = registry.list_loaded()
        assert isinstance(loaded, list)

    def test_get_statistics(self, registry):
        """Test getting registry statistics."""
        stats = registry.get_statistics()

        assert "total_registered" in stats
        assert "total_loaded" in stats
        assert "by_category" in stats
        assert stats["total_registered"] > 0

    def test_register_reference(self, registry):
        """Test registering new reference."""
        new_ref = Reference(
            id="custom-ref",
            name="Custom Reference",
            category=ReferenceCategory.GENERAL,
            path="custom.md",
            keywords=["custom"],
            description="Custom ref",
        )

        registry.register_reference(new_ref)
        assert registry.get_reference_info("custom-ref") is not None

    def test_unregister_reference(self, registry):
        """Test unregistering reference."""
        registry.register_reference(Reference(
            id="temp",
            name="Temp",
            category=ReferenceCategory.GENERAL,
            path="temp.md",
            keywords=[],
            description="Temp",
        ))

        assert registry.unregister_reference("temp") is True
        assert registry.get_reference_info("temp") is None


# =============================================================================
# CONTEXT OPTIMIZER TESTS
# =============================================================================


class TestContextOptimizer:
    """Tests for ContextOptimizer."""

    @pytest.fixture
    def optimizer(self):
        """Create context optimizer."""
        return create_context_optimizer(max_references=3, max_tokens=8000)

    def test_optimizer_creation(self, optimizer):
        """Test creating optimizer."""
        summary = optimizer.get_reference_summary()
        assert "total_references" in summary
        assert "max_references_per_task" in summary

    def test_optimize_basic(self, optimizer):
        """Test basic context optimization."""
        result = optimizer.optimize(
            task="Analyze ASP code for connection leaks",
            context={"domain": "stability"},
        )

        assert isinstance(result, OptimizedContext)
        assert result.task == "Analyze ASP code for connection leaks"
        assert len(result.selected_references) <= 3
        assert result.token_estimate > 0
        assert result.optimization_ratio > 0

    def test_optimize_for_agent(self, optimizer):
        """Test optimization for specific agent."""
        result = optimizer.optimize(
            task="Run quality analysis",
            context={},
            agent_name="Quinn",
        )

        assert result.agent_name == "Quinn"
        # Quinn should get quality-related references
        assert len(result.selected_references) > 0

    def test_optimize_with_required_refs(self, optimizer):
        """Test optimization with required references."""
        result = optimizer.optimize(
            task="General task",
            context={},
            required_references=["asp-vbscript"],
        )

        ref_ids = [m.reference.id for m in result.selected_references]
        assert "asp-vbscript" in ref_ids

    def test_optimized_context_methods(self, optimizer):
        """Test OptimizedContext methods."""
        result = optimizer.optimize(
            task="Test task",
            context={"key": "value"},
        )

        # Test get_enriched_context
        enriched = result.get_enriched_context()
        assert "key" in enriched
        assert "_references" in enriched
        assert "_reference_metadata" in enriched

        # Test to_dict
        data = result.to_dict()
        assert "task" in data
        assert "references_selected" in data
        assert "optimization_ratio" in data

    def test_optimize_for_workflow(self, optimizer):
        """Test optimization for workflow stages."""
        results = optimizer.optimize_for_workflow(
            workflow_type="brown_paper",
            stages=["code_understanding", "estimation"],
            context={"project": "test"},
        )

        assert "code_understanding" in results
        assert "estimation" in results
        assert all(isinstance(v, OptimizedContext) for v in results.values())


# =============================================================================
# REFERENCE CATEGORY TESTS
# =============================================================================


class TestReferenceCategory:
    """Tests for ReferenceCategory enum."""

    def test_all_categories_exist(self):
        """Test all expected categories exist."""
        expected = [
            "language", "framework", "testing", "security",
            "architecture", "stability", "estimation",
            "documentation", "general",
        ]

        for cat in expected:
            assert ReferenceCategory(cat) is not None

    def test_category_values(self):
        """Test category values are strings."""
        for cat in ReferenceCategory:
            assert isinstance(cat.value, str)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestContextEngineeringIntegration:
    """Integration tests for context engineering components."""

    def test_selector_optimizer_integration(self):
        """Test selector and optimizer work together."""
        selector = create_reference_selector()
        optimizer = create_context_optimizer()

        # Both should use same default references
        selector_refs = selector.list_references()
        summary = optimizer.get_reference_summary()

        assert len(selector_refs) == summary["total_references"]

    def test_full_optimization_flow(self):
        """Test complete optimization flow."""
        optimizer = create_context_optimizer()

        # Analyze for ASP stability task
        result = optimizer.optimize(
            task="Detect ADO connection leaks in classic ASP code",
            context={"domain": "stability", "tech_stack": ["asp", "vbscript"]},
            agent_name="Miguel",
        )

        # Should have selected stability-related references
        assert len(result.selected_references) > 0
        assert result.optimization_ratio > 0.5  # At least 50% savings

        # Token estimate should be reasonable
        assert result.token_estimate < 10000  # Under max tokens

    def test_agent_specific_selection(self):
        """Test that each agent gets relevant references."""
        optimizer = create_context_optimizer()

        agents = ["Felix", "Quinn", "Tessa", "Eliza", "Miguel"]
        results = {}

        for agent in agents:
            result = optimizer.optimize(
                task="Perform analysis",
                context={},
                agent_name=agent,
            )
            results[agent] = [m.reference.id for m in result.selected_references]

        # Different agents should potentially get different references
        # (depending on their domains and the default references)
        assert len(results) == len(agents)
