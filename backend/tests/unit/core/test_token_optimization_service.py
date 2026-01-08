"""
Unit tests for Token Optimization Service

Week 143: Tests for Vector DB context token optimization.
"""

import pytest
from app.services.token_optimization_service import (
    TokenOptimizationService,
    TokenBudget,
    OptimizedContext,
    get_token_optimization_service,
)


class TestTokenBudget:
    """Test TokenBudget enum values."""

    def test_budget_values(self):
        """Budget levels should have correct token counts."""
        assert TokenBudget.MINIMAL.value == 500
        assert TokenBudget.COMPACT.value == 1000
        assert TokenBudget.STANDARD.value == 2000
        assert TokenBudget.EXTENDED.value == 4000
        assert TokenBudget.FULL.value == 8000

    def test_budget_ordering(self):
        """Budgets should be in ascending order."""
        budgets = [TokenBudget.MINIMAL, TokenBudget.COMPACT, TokenBudget.STANDARD,
                   TokenBudget.EXTENDED, TokenBudget.FULL]
        values = [b.value for b in budgets]
        assert values == sorted(values)


class TestOptimizedContext:
    """Test OptimizedContext dataclass."""

    def test_to_dict(self):
        """to_dict should return all fields."""
        context = OptimizedContext(
            content="test content",
            token_count=10,
            items_included=2,
            items_truncated=1,
            relevance_scores=[0.8, 0.9],
            budget_used_percent=50.0
        )

        result = context.to_dict()

        assert result["content"] == "test content"
        assert result["token_count"] == 10
        assert result["items_included"] == 2
        assert result["items_truncated"] == 1
        assert result["avg_relevance"] == pytest.approx(0.85)
        assert result["budget_used_percent"] == 50.0

    def test_to_dict_empty_scores(self):
        """to_dict should handle empty relevance scores."""
        context = OptimizedContext(
            content="",
            token_count=0,
            items_included=0,
            items_truncated=0,
            relevance_scores=[],
            budget_used_percent=0.0
        )

        result = context.to_dict()
        assert result["avg_relevance"] == 0


class TestTokenOptimizationService:
    """Test TokenOptimizationService methods."""

    @pytest.fixture
    def service(self):
        return TokenOptimizationService()

    def test_estimate_tokens(self, service):
        """Token estimation should use ~4 chars per token."""
        assert service.estimate_tokens("") == 0
        assert service.estimate_tokens("test") == 2  # 4 chars / 4 + 1
        assert service.estimate_tokens("a" * 100) == 26  # 100 / 4 + 1

    def test_calculate_relevance_score_default(self, service):
        """Default relevance score should be 0.5."""
        score = service.calculate_relevance_score({})
        assert score == 0.5

    def test_calculate_relevance_score_with_content_type(self, service):
        """Content type should affect relevance score."""
        score_code = service.calculate_relevance_score({}, content_type="code_pattern")
        score_doc = service.calculate_relevance_score({}, content_type="documentation")

        assert score_code > score_doc  # code_pattern has higher priority

    def test_calculate_relevance_score_with_query_terms(self, service):
        """Query term matches should boost score."""
        item = {"content": "authentication login system"}

        score_no_match = service.calculate_relevance_score(item, query_terms=["database"])
        score_one_match = service.calculate_relevance_score(item, query_terms=["login"])
        score_two_matches = service.calculate_relevance_score(item, query_terms=["login", "auth"])

        assert score_two_matches > score_one_match > score_no_match

    def test_calculate_relevance_score_with_similarity(self, service):
        """Provided similarity score should be factored in."""
        item = {"content": "test", "similarity": 0.95}
        score = service.calculate_relevance_score(item)

        # Should be average of base (0.5) and similarity (0.95)
        assert score > 0.5

    def test_truncate_at_boundary_short_text(self, service):
        """Short text should not be truncated."""
        text = "Short text"
        result = service.truncate_at_boundary(text, 100)
        assert result == text

    def test_truncate_at_boundary_sentence(self, service):
        """Long text should truncate at sentence boundary."""
        text = "First sentence. Second sentence. Third sentence."
        result = service.truncate_at_boundary(text, 35)

        # Should truncate at "First sentence. " (16 chars) - the first complete sentence
        assert result.endswith(".") or result.endswith("...")
        assert len(result) <= 40  # Allow some margin for boundary logic

    def test_truncate_at_boundary_word(self, service):
        """Without sentence boundary, truncate at word."""
        text = "word1 word2 word3 word4 word5 word6 word7"
        result = service.truncate_at_boundary(text, 25)

        assert result.endswith("...")
        assert " " not in result[-4:]  # No trailing space before ...

    def test_compress_context_removes_duplicates(self, service):
        """Compression should remove duplicate content."""
        items = [
            {"content": "duplicate content here"},
            {"content": "unique content"},
            {"content": "duplicate content here"},  # Duplicate
        ]

        compressed = service.compress_context(items)

        assert len(compressed) == 2

    def test_compress_context_normalizes_whitespace(self, service):
        """Compression should normalize whitespace."""
        items = [
            {"content": "content  with   extra   spaces"},
        ]

        compressed = service.compress_context(items)

        assert "  " not in compressed[0]["content"]

    def test_optimize_context_empty_items(self, service):
        """Empty items should return empty context."""
        result = service.optimize_context([])

        assert result.content == ""
        assert result.token_count == 0
        assert result.items_included == 0

    def test_optimize_context_within_budget(self, service):
        """Items within budget should all be included."""
        items = [
            {"content": "Item one"},
            {"content": "Item two"},
            {"content": "Item three"},
        ]

        result = service.optimize_context(items, budget=TokenBudget.STANDARD)

        assert result.items_included == 3
        assert "Item one" in result.content
        assert "Item two" in result.content
        assert "Item three" in result.content

    def test_optimize_context_exceeds_budget(self, service):
        """Items exceeding budget should be truncated/excluded."""
        items = [
            {"content": "a" * 1000},  # ~250 tokens
            {"content": "b" * 1000},  # ~250 tokens
            {"content": "c" * 1000},  # ~250 tokens
        ]

        result = service.optimize_context(items, budget=TokenBudget.MINIMAL)

        # MINIMAL = 500 tokens = ~2000 chars
        # Should include 2 items, possibly truncate 3rd
        assert result.items_included <= 3
        assert result.token_count <= TokenBudget.MINIMAL.value * 1.1  # Allow 10% margin

    def test_optimize_context_preserves_structure(self, service):
        """With preserve_structure=True, items should be separated."""
        items = [
            {"content": "Item A"},
            {"content": "Item B"},
        ]

        result = service.optimize_context(items, preserve_structure=True)

        assert "---" in result.content

    def test_optimize_context_no_structure(self, service):
        """With preserve_structure=False, items should be joined by newline."""
        items = [
            {"content": "Item A"},
            {"content": "Item B"},
        ]

        result = service.optimize_context(items, preserve_structure=False)

        assert "---" not in result.content
        assert "\n" in result.content

    def test_optimize_for_llm_empty_dict(self, service):
        """Empty context dict should return empty result."""
        result = service.optimize_for_llm({})

        assert result["categories"] == {}
        assert result["metadata"]["categories_processed"] == 0

    def test_optimize_for_llm_distributes_budget(self, service):
        """Budget should be distributed across categories."""
        context_dict = {
            "code_patterns": [{"content": "pattern code"}],
            "best_practices": [{"content": "best practice"}],
        }

        result = service.optimize_for_llm(
            context_dict,
            budget=TokenBudget.STANDARD
        )

        assert "code_patterns" in result["categories"]
        assert "best_practices" in result["categories"]
        assert result["metadata"]["categories_processed"] == 2


class TestGetTokenOptimizationService:
    """Test singleton accessor."""

    def test_returns_same_instance(self):
        """Should return the same service instance."""
        service1 = get_token_optimization_service()
        service2 = get_token_optimization_service()

        assert service1 is service2

    def test_returns_correct_type(self):
        """Should return TokenOptimizationService."""
        service = get_token_optimization_service()
        assert isinstance(service, TokenOptimizationService)
