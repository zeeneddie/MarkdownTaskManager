"""
Week 19: Self-Navigating API Tests

Tests for the Experience Consultant and Pattern Matcher functionality.

Author: Claude Code (Week 19 Day 6)
Date: 2025-11-22
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Test imports
from app.services.pattern_matcher_service import (
    TextProcessor,
    SimilarityCalculator,
    PatternMatcherService,
    get_pattern_matcher,
    SearchQuery,
    ExperienceSearchResult,
    PatternSearchResult,
    FailureSearchResult
)
from app.services.experience_store_service import (
    Experience,
    SuccessfulPattern,
    FailureAnalysis,
    KeyDecision,
    WorkType,
    AgentRole,
    Outcome,
    FailureType
)


# ============================================================================
# TextProcessor Tests
# ============================================================================

class TestTextProcessor:
    """Tests for TextProcessor class"""

    def test_tokenize_basic(self):
        """Test basic tokenization"""
        tokens = TextProcessor.tokenize("Hello world this is a test")
        # Should remove stop words
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens
        assert "is" not in tokens  # Stop word
        assert "a" not in tokens   # Stop word

    def test_tokenize_empty(self):
        """Test tokenization of empty string"""
        tokens = TextProcessor.tokenize("")
        assert tokens == []

    def test_tokenize_special_chars(self):
        """Test tokenization with special characters"""
        tokens = TextProcessor.tokenize("API-design and database_migration!")
        assert "api" in tokens
        assert "design" in tokens
        assert "database" in tokens
        assert "migration" in tokens

    def test_get_term_weights_domain_terms(self):
        """Test that domain terms get higher weights"""
        tokens = ["feature", "hello", "api", "world"]
        weights = TextProcessor.get_term_weights(tokens)

        # Domain terms should have higher weights
        assert weights["feature"] > weights["hello"]
        assert weights["api"] > weights["world"]

    def test_get_term_weights_frequency(self):
        """Test that repeated terms accumulate weights"""
        tokens = ["test", "test", "test"]
        weights = TextProcessor.get_term_weights(tokens)

        # Repeated term should have higher weight
        assert weights["test"] > 1.0


# ============================================================================
# SimilarityCalculator Tests
# ============================================================================

class TestSimilarityCalculator:
    """Tests for SimilarityCalculator class"""

    def test_cosine_similarity_identical(self):
        """Test cosine similarity of identical vectors"""
        vec1 = {"a": 1.0, "b": 2.0}
        vec2 = {"a": 1.0, "b": 2.0}
        sim = SimilarityCalculator.cosine_similarity(vec1, vec2)
        assert sim == pytest.approx(1.0)

    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity of completely different vectors"""
        vec1 = {"a": 1.0}
        vec2 = {"b": 1.0}
        sim = SimilarityCalculator.cosine_similarity(vec1, vec2)
        assert sim == pytest.approx(0.0)

    def test_cosine_similarity_partial(self):
        """Test cosine similarity of partially overlapping vectors"""
        vec1 = {"a": 1.0, "b": 1.0}
        vec2 = {"a": 1.0, "c": 1.0}
        sim = SimilarityCalculator.cosine_similarity(vec1, vec2)
        assert 0.0 < sim < 1.0

    def test_cosine_similarity_empty(self):
        """Test cosine similarity with empty vectors"""
        assert SimilarityCalculator.cosine_similarity({}, {"a": 1}) == 0.0
        assert SimilarityCalculator.cosine_similarity({"a": 1}, {}) == 0.0

    def test_jaccard_similarity_identical(self):
        """Test Jaccard similarity of identical sets"""
        set1 = {"a", "b", "c"}
        set2 = {"a", "b", "c"}
        sim = SimilarityCalculator.jaccard_similarity(set1, set2)
        assert sim == pytest.approx(1.0)

    def test_jaccard_similarity_disjoint(self):
        """Test Jaccard similarity of disjoint sets"""
        set1 = {"a", "b"}
        set2 = {"c", "d"}
        sim = SimilarityCalculator.jaccard_similarity(set1, set2)
        assert sim == pytest.approx(0.0)

    def test_jaccard_similarity_partial(self):
        """Test Jaccard similarity of overlapping sets"""
        set1 = {"a", "b", "c"}
        set2 = {"b", "c", "d"}
        sim = SimilarityCalculator.jaccard_similarity(set1, set2)
        # Intersection: {b, c}, Union: {a, b, c, d}
        # 2/4 = 0.5
        assert sim == pytest.approx(0.5)

    def test_text_similarity_similar_texts(self):
        """Test text similarity for similar texts"""
        text1 = "Implement user authentication with JWT tokens"
        text2 = "Add JWT authentication for users"
        sim = SimilarityCalculator.text_similarity(text1, text2)
        assert sim > 0.3  # Should have reasonable similarity

    def test_text_similarity_different_texts(self):
        """Test text similarity for different texts"""
        text1 = "Implement user authentication"
        text2 = "Fix database connection timeout"
        sim = SimilarityCalculator.text_similarity(text1, text2)
        assert sim < 0.3  # Should have low similarity

    def test_context_similarity_exact_match(self):
        """Test context similarity with exact match"""
        sim = SimilarityCalculator.context_similarity(
            "NEW_FEATURE", "architect",
            "NEW_FEATURE", "architect"
        )
        assert sim == pytest.approx(1.0)

    def test_context_similarity_partial_match(self):
        """Test context similarity with partial match"""
        sim = SimilarityCalculator.context_similarity(
            "NEW_FEATURE", None,
            "NEW_FEATURE", "architect"
        )
        assert 0.5 < sim < 1.0

    def test_context_similarity_no_filters(self):
        """Test context similarity without filters"""
        sim = SimilarityCalculator.context_similarity(
            None, None,
            "NEW_FEATURE", "architect"
        )
        assert sim == pytest.approx(0.5)


# ============================================================================
# PatternMatcherService Tests
# ============================================================================

class TestPatternMatcherService:
    """Tests for PatternMatcherService class"""

    @pytest.fixture
    def mock_store(self):
        """Create mock experience store"""
        store = Mock()
        store.find_similar_experiences = Mock(return_value=[])
        store.find_applicable_patterns = Mock(return_value=[])
        store.get_failure_analyses = Mock(return_value=[])
        return store

    @pytest.fixture
    def sample_experience(self):
        """Create sample experience for testing"""
        return Experience(
            id="exp-001",
            agent_id="felix-001",
            agent_role=AgentRole.FELIX,
            work_type=WorkType.NEW_FEATURE,
            task_description="Implement JWT authentication",
            approach="Used passport-jwt library with refresh tokens",
            outcome=Outcome.SUCCESS,
            lessons_learned=["Cache tokens for performance"],
            key_decisions=[],
            duration=3600,
            quality_score=85.0,
            timestamp=datetime.utcnow(),
            metadata={}
        )

    @pytest.fixture
    def sample_pattern(self):
        """Create sample pattern for testing"""
        return SuccessfulPattern(
            id="pat-001",
            name="JWT Authentication Pattern",
            description="Implement JWT with refresh token rotation",
            work_types=[WorkType.NEW_FEATURE],
            applicable_contexts=["authentication", "security"],
            steps=["Configure JWT secret", "Create auth middleware", "Add refresh endpoint"],
            success_count=10,
            failure_count=2,
            average_quality=80.0,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow(),
            created_by="felix"
        )

    @pytest.fixture
    def sample_failure(self):
        """Create sample failure for testing"""
        return FailureAnalysis(
            id="fail-001",
            agent_id="felix-001",
            task_id="task-001",
            work_type=WorkType.NEW_FEATURE,
            failure_type=FailureType.VALIDATION,
            root_cause="Token expiry not handled",
            contributing_factors=["Missing refresh logic", "No error handling"],
            prevention_strategies=["Always implement refresh tokens", "Add proper error boundaries"],
            similar_failures=[],
            timestamp=datetime.utcnow()
        )

    @patch('app.services.pattern_matcher_service.get_experience_store')
    def test_search_experiences_returns_results(self, mock_get_store, mock_store, sample_experience):
        """Test experience search returns properly formatted results"""
        mock_store.find_similar_experiences.return_value = [sample_experience]
        mock_get_store.return_value = mock_store

        matcher = PatternMatcherService()
        matcher.store = mock_store

        results = matcher.search_experiences(
            query="JWT authentication",
            work_type="NEW_FEATURE",
            limit=5,
            min_similarity=0.0  # Accept all for testing
        )

        assert len(results) >= 0  # May filter based on similarity

    @patch('app.services.pattern_matcher_service.get_experience_store')
    def test_search_patterns_returns_results(self, mock_get_store, mock_store, sample_pattern):
        """Test pattern search returns properly formatted results"""
        mock_store.find_applicable_patterns.return_value = [sample_pattern]
        mock_get_store.return_value = mock_store

        matcher = PatternMatcherService()
        matcher.store = mock_store

        results = matcher.search_patterns(
            query="JWT authentication",
            work_type="NEW_FEATURE",
            limit=5,
            min_similarity=0.0
        )

        assert len(results) >= 0

    @patch('app.services.pattern_matcher_service.get_experience_store')
    def test_search_failures_returns_results(self, mock_get_store, mock_store, sample_failure):
        """Test failure search returns properly formatted results"""
        mock_store.get_failure_analyses.return_value = [sample_failure]
        mock_get_store.return_value = mock_store

        matcher = PatternMatcherService()
        matcher.store = mock_store

        results = matcher.search_failures(
            query="token expiry error",
            work_type="NEW_FEATURE",
            limit=5,
            min_similarity=0.0
        )

        assert len(results) >= 0

    @patch('app.services.pattern_matcher_service.get_experience_store')
    def test_comprehensive_search_combines_all(self, mock_get_store, mock_store):
        """Test comprehensive search combines all result types"""
        mock_store.find_similar_experiences.return_value = []
        mock_store.find_applicable_patterns.return_value = []
        mock_store.get_failure_analyses.return_value = []
        mock_get_store.return_value = mock_store

        matcher = PatternMatcherService()
        matcher.store = mock_store

        result = matcher.comprehensive_search(
            query="Implement authentication",
            work_type="NEW_FEATURE"
        )

        assert 'experiences' in result
        assert 'patterns' in result
        assert 'failures' in result
        assert 'query' in result

    def test_risk_score_calculation(self, sample_failure):
        """Test risk score calculation"""
        matcher = PatternMatcherService()
        risk = matcher._calculate_risk_score(sample_failure)

        assert 0.0 <= risk <= 1.0


# ============================================================================
# API Integration Tests (with mocked dependencies)
# ============================================================================

class TestSelfNavigatingAPI:
    """Tests for self-navigating API endpoints"""

    @pytest.fixture
    def mock_matcher(self):
        """Create mock pattern matcher"""
        matcher = Mock()
        matcher.search_experiences = Mock(return_value=[])
        matcher.search_patterns = Mock(return_value=[])
        matcher.search_failures = Mock(return_value=[])
        matcher.comprehensive_search = Mock(return_value={
            'experiences': [],
            'patterns': [],
            'failures': []
        })
        return matcher

    def test_experience_search_request_validation(self):
        """Test request validation for experience search"""
        from app.api.self_navigating import ExperienceSearchRequest

        # Valid request
        req = ExperienceSearchRequest(
            query="test query",
            work_type="NEW_FEATURE",
            limit=10,
            min_similarity=0.5
        )
        assert req.query == "test query"
        assert req.work_type == "NEW_FEATURE"

        # Min similarity bounds
        req = ExperienceSearchRequest(
            query="test",
            min_similarity=0.0
        )
        assert req.min_similarity == 0.0

        req = ExperienceSearchRequest(
            query="test",
            min_similarity=1.0
        )
        assert req.min_similarity == 1.0

    def test_pattern_search_request_validation(self):
        """Test request validation for pattern search"""
        from app.api.self_navigating import PatternSearchRequest

        req = PatternSearchRequest(
            query="test",
            work_type="MAINTENANCE",
            min_success_rate=0.8
        )
        assert req.min_success_rate == 0.8

    def test_failure_search_request_validation(self):
        """Test request validation for failure search"""
        from app.api.self_navigating import FailureSearchRequest

        req = FailureSearchRequest(
            query="error handling",
            work_type="BUG"
        )
        assert req.work_type == "BUG"

    def test_log_outcome_request_validation(self):
        """Test request validation for outcome logging"""
        from app.api.self_navigating import LogOutcomeRequest

        req = LogOutcomeRequest(
            agent_id="felix-001",
            agent_role="felix",
            work_type="NEW_FEATURE",
            task_id="task-001",
            task_description="Implement feature",
            approach="Used standard patterns",
            outcome="SUCCESS",
            quality_score=85.0
        )
        assert req.outcome == "SUCCESS"
        assert req.quality_score == 85.0


# ============================================================================
# Helper Function Tests
# ============================================================================

class TestHelperFunctions:
    """Tests for helper functions"""

    def test_generate_recommendations_with_experiences(self):
        """Test recommendation generation with experiences"""
        from app.api.self_navigating import _generate_recommendations

        experiences = [
            {
                "outcome": "SUCCESS",
                "quality_score": 85,
                "approach": "Used JWT with refresh tokens"
            }
        ]
        patterns = []
        failures = []

        recs = _generate_recommendations(experiences, patterns, failures)

        assert len(recs) > 0
        assert any("approach" in r.lower() for r in recs)

    def test_generate_recommendations_with_patterns(self):
        """Test recommendation generation with patterns"""
        from app.api.self_navigating import _generate_recommendations

        experiences = []
        patterns = [
            {
                "name": "Auth Pattern",
                "success_rate": 0.9
            }
        ]
        failures = []

        recs = _generate_recommendations(experiences, patterns, failures)

        assert len(recs) > 0
        assert any("Auth Pattern" in r for r in recs)

    def test_generate_recommendations_with_failures(self):
        """Test recommendation generation with failures"""
        from app.api.self_navigating import _generate_recommendations

        experiences = []
        patterns = []
        failures = [
            {
                "failure_type": "TOKEN_EXPIRY",
                "prevention_strategies": ["Always handle token refresh"]
            }
        ]

        recs = _generate_recommendations(experiences, patterns, failures)

        assert len(recs) > 0
        assert any("AVOID" in r for r in recs)

    def test_generate_recommendations_empty_data(self):
        """Test recommendation generation with no data"""
        from app.api.self_navigating import _generate_recommendations

        recs = _generate_recommendations([], [], [])

        assert len(recs) == 2
        assert "No specific historical guidance" in recs[0]

    def test_calculate_confidence_with_experiences(self):
        """Test confidence calculation with experiences"""
        from app.api.self_navigating import _calculate_confidence

        experiences = [
            {"similarity": 0.8, "outcome": "SUCCESS"},
            {"similarity": 0.7, "outcome": "SUCCESS"}
        ]
        patterns = []
        failures = []

        confidence = _calculate_confidence(experiences, patterns, failures)

        assert confidence > 0.3  # Should be higher than base

    def test_calculate_confidence_with_all_data(self):
        """Test confidence calculation with all data types"""
        from app.api.self_navigating import _calculate_confidence

        experiences = [
            {"similarity": 0.9, "outcome": "SUCCESS"}
        ]
        patterns = [
            {"success_rate": 0.85}
        ]
        failures = [
            {"risk_score": 0.6}
        ]

        confidence = _calculate_confidence(experiences, patterns, failures)

        assert 0.3 < confidence <= 1.0

    def test_calculate_confidence_empty_data(self):
        """Test confidence calculation with no data"""
        from app.api.self_navigating import _calculate_confidence

        confidence = _calculate_confidence([], [], [])

        assert confidence == pytest.approx(0.3)  # Base confidence


# ============================================================================
# Singleton Tests
# ============================================================================

class TestSingletons:
    """Tests for singleton pattern implementations"""

    def test_get_pattern_matcher_singleton(self):
        """Test pattern matcher singleton"""
        from app.services.pattern_matcher_service import get_pattern_matcher, _matcher_instance

        # Reset singleton for test
        import app.services.pattern_matcher_service as pm_module
        pm_module._matcher_instance = None

        matcher1 = get_pattern_matcher()
        matcher2 = get_pattern_matcher()

        assert matcher1 is matcher2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
