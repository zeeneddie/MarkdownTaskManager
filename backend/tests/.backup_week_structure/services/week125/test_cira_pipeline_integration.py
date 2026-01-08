# backend/tests/services/week125/test_cira_pipeline_integration.py
"""
Tests for CiRA Pipeline Integration - Week 125

Tests:
- HierarchicalStoryExtractionService CiRA integration
- TraceabilityMatrixService causal links
- INVESTValidatorService CausalContext
- Config settings validation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import asdict
from typing import Dict, List, Any
from uuid import uuid4


# =========================================================================
# Mock classes for testing without database
# =========================================================================

class MockCiRASession:
    """Mock CiRA session for testing."""

    def __init__(self):
        self.session_id = str(uuid4())
        self.sentences_analyzed = []
        self.relations = []
        self.graph_built = False

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "status": "completed",
        }


class MockCiRAService:
    """Mock CiRA service for testing."""

    def __init__(self):
        self.sessions = {}

    async def create_session(self, project_id: int, source_type: str, source_id: str):
        session = MockCiRASession()
        self.sessions[session.session_id] = session
        return {"session_id": session.session_id, "status": "created"}

    async def analyze_sentences(self, session_id: str, sentences: List[str]):
        session = self.sessions.get(session_id)
        if session:
            session.sentences_analyzed = sentences
            # Generate mock causal relations
            causal_count = sum(1 for s in sentences if any(m in s.lower() for m in ["if", "when", "because", "then"]))
            session.relations = [
                {
                    "id": str(uuid4()),
                    "cause": f"Cause {i}",
                    "effect": f"Effect {i}",
                    "confidence": 0.8,
                    "source_story_id": f"story_{i}",
                }
                for i in range(causal_count)
            ]
            return {
                "causal_sentence_count": causal_count,
                "total_sentences": len(sentences),
                "relations": session.relations,
                "avg_confidence": 0.8 if causal_count > 0 else 0.0,
            }
        return {"error": "Session not found"}

    async def build_dependency_graph(self, session_id: str):
        session = self.sessions.get(session_id)
        if session:
            session.graph_built = True
            node_count = len(session.relations)
            return {
                "has_graph": node_count > 0,
                "node_count": node_count,
                "edge_count": node_count - 1 if node_count > 1 else 0,
                "critical_path": [r["id"] for r in session.relations[:2]],
                "root_nodes": [session.relations[0]["id"]] if session.relations else [],
                "leaf_nodes": [session.relations[-1]["id"]] if session.relations else [],
                "topological_order": [r["id"] for r in session.relations],
                "cycles_detected": 0,
            }
        return {"has_graph": False}

    async def generate_test_cases(self, session_id: str):
        session = self.sessions.get(session_id)
        if session:
            return {
                "test_cases": [
                    {"type": "unit", "description": f"Test cause-effect {i}"}
                    for i in range(len(session.relations))
                ]
            }
        return {"test_cases": []}


# =========================================================================
# Test CausalContext for INVEST Validator
# =========================================================================

class TestCausalContext:
    """Test the CausalContext dataclass for INVEST validation."""

    def test_init_empty(self):
        """Test empty CausalContext initialization."""
        from app.services.invest_validator_service import CausalContext

        ctx = CausalContext()

        assert ctx.blocks == []
        assert ctx.blocked_by == []
        assert ctx.causes == []
        assert ctx.caused_by == []
        assert ctx.depends_on == []
        assert ctx.depended_by == []
        assert ctx.is_root_node is False
        assert ctx.is_leaf_node is False
        assert ctx.critical_path_position is None
        assert ctx.total_dependency_depth == 0
        assert ctx.suggested_tests == []
        assert ctx.cira_session_id is None

    def test_total_dependencies(self):
        """Test total_dependencies property calculation."""
        from app.services.invest_validator_service import CausalContext

        ctx = CausalContext(
            blocks=["story1", "story2"],
            blocked_by=["story3"],
            depends_on=["story4", "story5"],
        )

        # total = len(blocked_by) + len(depends_on)
        assert ctx.total_dependencies == 3  # 1 + 2

    def test_total_dependents(self):
        """Test total_dependents property calculation."""
        from app.services.invest_validator_service import CausalContext

        ctx = CausalContext(
            blocks=["story1", "story2"],
            depended_by=["story3", "story4"],
        )

        # total = len(blocks) + len(depended_by)
        assert ctx.total_dependents == 4  # 2 + 2

    def test_dependency_score_impact(self):
        """Test dependency_score_impact property calculation."""
        from app.services.invest_validator_service import CausalContext

        # No dependencies - no penalty
        ctx_empty = CausalContext()
        assert ctx_empty.dependency_score_impact == 0.0

        # Some dependencies - proportional penalty
        ctx_some = CausalContext(
            blocked_by=["story1"],
            depends_on=["story2"],
        )
        impact = ctx_some.dependency_score_impact
        assert 0.0 < impact <= 0.5


# =========================================================================
# Test INVEST Validator CiRA Integration
# =========================================================================

class TestINVESTValidatorCiRAIntegration:
    """Test CiRA integration in INVEST Validator."""

    @pytest.fixture
    def mock_story(self):
        """Create a mock story for testing."""
        return {
            "id": str(uuid4()),
            "title": "As a user, I want to login",
            "description": "If the user enters valid credentials, then authentication succeeds.",
            "acceptance_criteria": [
                "User should see login form",
                "When credentials are valid, user is redirected to dashboard",
                "User must be able to logout",
            ],
            "story_points": 3,
        }

    @pytest.fixture
    def causal_context(self):
        """Create a CausalContext for testing."""
        from app.services.invest_validator_service import CausalContext

        return CausalContext(
            blocks=["story2"],
            blocked_by=["story0"],
            depends_on=["story_auth"],
            is_root_node=False,
            is_leaf_node=True,
            critical_path_position=2,
            total_dependency_depth=2,
            suggested_tests=[
                {"type": "integration", "description": "Test auth flow"},
                {"type": "unit", "description": "Test credential validation"},
            ],
            cira_session_id=str(uuid4()),
        )

    def test_validate_independent_with_causal_context(self, mock_story, causal_context):
        """Test _validate_independent with CausalContext."""
        from app.services.invest_validator_service import INVESTValidatorService

        validator = INVESTValidatorService.__new__(INVESTValidatorService)
        validator.db = None  # Not needed for validation logic

        # Test with causal context (passed as keyword argument)
        result = validator._validate_independent(mock_story, causal_context=causal_context)

        assert result.criterion == "independent"
        assert result.score < 1.0  # Should be penalized for dependencies
        # Should have CiRA-related suggestions (mentions "CiRA" or "critical path")
        assert any("CiRA" in s or "critical path" in s for s in result.suggestions)

    def test_validate_independent_without_causal_context(self, mock_story):
        """Test _validate_independent without CausalContext."""
        from app.services.invest_validator_service import INVESTValidatorService

        validator = INVESTValidatorService.__new__(INVESTValidatorService)
        validator.db = None

        result = validator._validate_independent(mock_story, None)

        assert result.criterion == "independent"
        # Should not have CiRA suggestions
        assert not any("[CiRA]" in s for s in result.suggestions)

    def test_validate_estimable_with_causal_context(self, mock_story, causal_context):
        """Test _validate_estimable with CausalContext for dependency overhead."""
        from app.services.invest_validator_service import INVESTValidatorService

        validator = INVESTValidatorService.__new__(INVESTValidatorService)
        validator.db = None

        result = validator._validate_estimable(mock_story, causal_context)

        assert result.criterion == "estimable"
        # Story has dependencies, should mention overhead
        if causal_context.total_dependencies > 0:
            # Should have dependency overhead warning
            assert any("overhead" in s.lower() or "dependency" in s.lower() for s in result.suggestions)

    def test_validate_testable_with_cira_suggestions(self, mock_story, causal_context):
        """Test _validate_testable with CiRA test suggestions."""
        from app.services.invest_validator_service import INVESTValidatorService

        validator = INVESTValidatorService.__new__(INVESTValidatorService)
        validator.db = None

        result = validator._validate_testable(mock_story, causal_context)

        assert result.criterion == "testable"
        # Should include CiRA test suggestions
        assert any("[CiRA]" in s for s in result.suggestions)

    def test_validate_testable_leaf_node_suggestions(self, mock_story, causal_context):
        """Test that leaf nodes get edge case test suggestions."""
        from app.services.invest_validator_service import INVESTValidatorService

        validator = INVESTValidatorService.__new__(INVESTValidatorService)
        validator.db = None

        # Ensure causal_context is leaf node
        causal_context.is_leaf_node = True

        result = validator._validate_testable(mock_story, causal_context)

        # Should suggest edge case tests for leaf nodes
        assert any("leaf" in s.lower() and "edge" in s.lower() for s in result.suggestions)

    def test_check_causal_test_coverage(self, causal_context):
        """Test _check_causal_test_coverage helper method."""
        from app.services.invest_validator_service import INVESTValidatorService

        validator = INVESTValidatorService.__new__(INVESTValidatorService)
        validator.db = None

        # Good coverage - mentions dependencies
        good_criteria = [
            "Given the prerequisite auth is complete, user can access dashboard",
            "After setup, the workflow should proceed",
            "Integration test covers dependent modules",
        ]
        good_coverage = validator._check_causal_test_coverage(good_criteria, causal_context)
        assert good_coverage > 0.0

        # Poor coverage - no dependency mentions
        poor_criteria = [
            "Button is blue",
            "Text is visible",
        ]
        poor_coverage = validator._check_causal_test_coverage(poor_criteria, causal_context)
        assert poor_coverage == 0.0


# =========================================================================
# Test TraceabilityMatrixService CiRA Integration
# =========================================================================

class TestTraceabilityMatrixCiRAIntegration:
    """Test CiRA integration in TraceabilityMatrixService."""

    def test_causal_link_types(self):
        """Test new LinkType values for causal relationships."""
        from app.services.traceability_matrix_service import LinkType

        assert LinkType.CAUSES.value == "causes"
        assert LinkType.DEPENDS_ON.value == "depends_on"
        assert LinkType.BLOCKS.value == "blocks"

    def test_causal_story_link_dataclass(self):
        """Test CausalStoryLink dataclass."""
        from app.services.traceability_matrix_service import CausalStoryLink, LinkType
        from datetime import datetime, timezone

        link = CausalStoryLink(
            id="link1",
            cause_story_id="story1",
            effect_story_id="story2",
            link_type=LinkType.CAUSES,
            confidence=0.85,
            evidence="If auth succeeds, then access is granted",
            created_at=datetime.now(timezone.utc),
            created_by="cira",
            cira_session_id="session123",
        )

        assert link.id == "link1"
        assert link.cause_story_id == "story1"
        assert link.effect_story_id == "story2"
        assert link.link_type == LinkType.CAUSES
        assert link.confidence == 0.85
        assert link.created_by == "cira"

    def test_coverage_metrics_causal_fields(self):
        """Test CoverageMetrics includes causal link counts."""
        from app.services.traceability_matrix_service import CoverageMetrics

        metrics = CoverageMetrics(
            total_code_elements=100,
            linked_code_elements=80,
            orphan_code_elements=20,
            total_stories=50,
            implemented_stories=30,
            unimplemented_stories=15,
            partially_implemented_stories=5,
            code_coverage_percentage=80.0,
            story_coverage_percentage=60.0,
            high_confidence_links=40,
            medium_confidence_links=30,
            low_confidence_links=10,
            manual_links=5,
            verified_links=60,
            unverified_links=20,
            causal_links=3,
            dependency_links=2,
            blocking_links=1,
        )

        assert metrics.causal_links == 3
        assert metrics.dependency_links == 2
        assert metrics.blocking_links == 1

    def test_traceability_matrix_result_causal_fields(self):
        """Test TraceabilityMatrixResult includes causal links."""
        from app.services.traceability_matrix_service import (
            TraceabilityMatrixResult,
            CausalStoryLink,
            LinkType,
            CoverageMetrics,
        )
        from datetime import datetime, timezone

        causal_link = CausalStoryLink(
            id="link1",
            cause_story_id="story1",
            effect_story_id="story2",
            link_type=LinkType.CAUSES,
            confidence=0.85,
            evidence="Test evidence",
            created_at=datetime.now(timezone.utc),
        )

        metrics = CoverageMetrics(
            total_code_elements=100,
            linked_code_elements=80,
            orphan_code_elements=20,
            total_stories=50,
            implemented_stories=30,
            unimplemented_stories=15,
            partially_implemented_stories=5,
            code_coverage_percentage=80.0,
            story_coverage_percentage=60.0,
            high_confidence_links=40,
            medium_confidence_links=30,
            low_confidence_links=10,
            manual_links=5,
            verified_links=60,
            unverified_links=20,
        )

        result = TraceabilityMatrixResult(
            matrix_id="matrix1",
            project_id=1,
            created_at=datetime.now(timezone.utc),
            links=[],  # Empty for this test
            orphan_code=[],  # Empty for this test
            unimplemented_stories=[],  # Empty for this test
            metrics=metrics,
            causal_links=[causal_link],
            cira_session_id="session123",
            suggested_sprint_order=["story1", "story2"],
        )

        assert len(result.causal_links) == 1
        assert result.cira_session_id == "session123"
        assert result.suggested_sprint_order == ["story1", "story2"]


# =========================================================================
# Test HierarchicalStoryExtractionService CiRA Integration
# =========================================================================

class TestHierarchicalExtractionCiRAIntegration:
    """Test CiRA integration in HierarchicalStoryExtractionService."""

    def test_causal_dependency_info_dataclass(self):
        """Test CausalDependencyInfo dataclass."""
        from app.services.hierarchical_story_extraction_service import CausalDependencyInfo

        info = CausalDependencyInfo(
            session_id="session123",
            total_causal_sentences=10,
            total_relations=5,
            avg_confidence=0.82,
            has_graph=True,
            node_count=5,
            edge_count=4,
            critical_path=["story1", "story2", "story3"],
            root_nodes=["story1"],
            leaf_nodes=["story5"],
            suggested_sprint_order=["story1", "story2", "story3", "story4", "story5"],
            cycles_detected=0,
            relations_by_story={"story1": [{"cause": "A", "effect": "B"}]},
        )

        assert info.session_id == "session123"
        assert info.total_causal_sentences == 10
        assert info.total_relations == 5
        assert info.avg_confidence == 0.82
        assert info.has_graph is True
        assert len(info.critical_path) == 3
        assert len(info.root_nodes) == 1
        assert info.cycles_detected == 0

    def test_hierarchical_extraction_result_includes_causal(self):
        """Test HierarchicalExtractionResult includes causal_dependencies."""
        from app.services.hierarchical_story_extraction_service import (
            HierarchicalExtractionResult,
            CausalDependencyInfo,
        )

        causal_info = CausalDependencyInfo(
            session_id="test_session",
            total_relations=3,
        )

        result = HierarchicalExtractionResult(
            total_epics=1,
            total_features=3,
            total_stories=10,
            total_tasks=20,
            overall_confidence=0.75,
            causal_dependencies=causal_info,
        )

        assert result.causal_dependencies is not None
        assert result.causal_dependencies.session_id == "test_session"
        assert result.causal_dependencies.total_relations == 3


# =========================================================================
# Test Config Settings
# =========================================================================

class TestWeek125ConfigSettings:
    """Test Week 125 configuration settings."""

    def test_config_has_week125_settings(self):
        """Test that config includes Week 125 settings."""
        from app.config import settings

        assert hasattr(settings, "CIRA_PIPELINE_ENABLED")
        assert hasattr(settings, "CIRA_HIERARCHICAL_EXTRACTION_DEFAULT")
        assert hasattr(settings, "CIRA_TRACEABILITY_DEFAULT")
        assert hasattr(settings, "CIRA_INVEST_VALIDATION_DEFAULT")
        assert hasattr(settings, "CIRA_MIN_STORIES_FOR_GRAPH")
        assert hasattr(settings, "CIRA_MAX_GRAPH_NODES")
        assert hasattr(settings, "CIRA_SPRINT_ORDER_STRATEGY")
        assert hasattr(settings, "CIRA_CAUSAL_DEPENDENCY_WEIGHT")
        assert hasattr(settings, "CIRA_TEST_SUGGESTION_ENABLED")

    def test_config_default_values(self):
        """Test default values for Week 125 settings."""
        from app.config import settings

        assert settings.CIRA_PIPELINE_ENABLED is True
        assert settings.CIRA_HIERARCHICAL_EXTRACTION_DEFAULT is True
        assert settings.CIRA_TRACEABILITY_DEFAULT is True
        assert settings.CIRA_INVEST_VALIDATION_DEFAULT is True
        assert settings.CIRA_MIN_STORIES_FOR_GRAPH == 3
        assert settings.CIRA_MAX_GRAPH_NODES == 500
        assert settings.CIRA_SPRINT_ORDER_STRATEGY == "topological"
        assert settings.CIRA_CAUSAL_DEPENDENCY_WEIGHT == 0.3
        assert settings.CIRA_TEST_SUGGESTION_ENABLED is True


# =========================================================================
# Integration Tests (require running services)
# =========================================================================

@pytest.mark.integration
class TestCiRAPipelineIntegration:
    """Integration tests for the complete CiRA pipeline."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_hierarchical_extraction_with_cira(self, mock_db):
        """Test hierarchical extraction with CiRA analysis enabled."""
        # This test would run with actual services
        pass

    @pytest.mark.asyncio
    async def test_traceability_matrix_with_cira(self, mock_db):
        """Test traceability matrix building with CiRA links."""
        # This test would run with actual services
        pass

    @pytest.mark.asyncio
    async def test_invest_validation_with_cira(self, mock_db):
        """Test INVEST validation with CiRA context."""
        # This test would run with actual services
        pass
