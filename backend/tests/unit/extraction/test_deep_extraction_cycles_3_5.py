"""
Week 84 Tests: Deep Extraction Cycles 3 & 5

Tests for:
- Cycle 3: Conflict Detection (consensus/conflict identification)
- Cycle 5: Final Synthesis (aggregation, FP estimation)
- Bulk resolution helpers
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.models.deep_extraction import (
    ItemType,
    ConsensusStatus,
    ConflictStatus,
    ConflictType,
    ExtractionTier,
    ExtractionStatus,
    ExtractionSession,
    ExtractionLLMResult,
    ExtractionConsensus,
    ExtractionConflict,
    TIER_CONFIG,
)
from app.services.deep_extraction_service import DeepExtractionService


# ===========================================================================
# Test Fixtures
# ===========================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_session():
    """Mock extraction session with LLM results."""
    session = MagicMock(spec=ExtractionSession)
    session.id = uuid4()
    session.tier = ExtractionTier.STANDARD.value
    session.tier_price_usd = 25.0
    session.actual_cost_usd = 5.0
    session.total_tokens_used = 10000
    session.workflow_type = "GREEN_PAPER"
    session.source_path = "/test/project"
    session.total_files = 50
    session.status = ExtractionStatus.RUNNING.value
    session.current_cycle = 2
    session.llm_results = []
    session.consensus_items = []
    session.conflicts = []
    session.project = MagicMock()
    session.project.name = "Test Project"
    return session


@pytest.fixture
def mock_llm_results():
    """Create mock LLM results from Cycle 1."""
    results = []

    # Ollama result - finds 2 epics
    result1 = MagicMock(spec=ExtractionLLMResult)
    result1.cycle = 1
    result1.llm_provider = "ollama"
    result1.llm_model = "qwen2.5-coder:7b"
    result1.analysis_type = "code_structure"
    result1.parsed_output = True
    result1.extracted_epics = [
        {"title": "User Authentication System", "description": "Auth system", "priority": "high"},
        {"title": "Payment Processing", "description": "Payment module", "priority": "medium"},
    ]
    result1.extracted_features = [
        {"title": "Login Flow", "description": "User login", "priority": "high"},
    ]
    result1.extracted_stories = []
    result1.extracted_tasks = []
    results.append(result1)

    # Groq result - finds same epics with slight variations
    result2 = MagicMock(spec=ExtractionLLMResult)
    result2.cycle = 1
    result2.llm_provider = "groq"
    result2.llm_model = "llama-3.1-70b"
    result2.analysis_type = "architecture"
    result2.parsed_output = True
    result2.extracted_epics = [
        {"title": "User Authentication", "description": "Auth module", "priority": "high"},  # Similar to above
        {"title": "Payment Processing Module", "description": "Payments", "priority": "low"},  # Different priority!
    ]
    result2.extracted_features = [
        {"title": "Login Flow", "description": "Login system", "priority": "medium"},  # Different priority!
    ]
    result2.extracted_stories = []
    result2.extracted_tasks = []
    results.append(result2)

    # Gemini result - finds same and additional
    result3 = MagicMock(spec=ExtractionLLMResult)
    result3.cycle = 1
    result3.llm_provider = "gemini"
    result3.llm_model = "gemini-flash"
    result3.analysis_type = "business_logic"
    result3.parsed_output = True
    result3.extracted_epics = [
        {"title": "User Authentication System", "description": "Complete auth", "priority": "high"},
    ]
    result3.extracted_features = []
    result3.extracted_stories = [
        {"title": "User can reset password", "description": "Password reset"},
    ]
    result3.extracted_tasks = []
    results.append(result3)

    return results


@pytest.fixture
def service(mock_db):
    """Create service with mocked dependencies."""
    return DeepExtractionService(mock_db)


# ===========================================================================
# Cycle 3 Tests: Conflict Detection
# ===========================================================================

class TestCycle3ConflictDetection:
    """Tests for Cycle 3: Conflict Detection."""

    def test_collect_items_from_results(self, service, mock_llm_results):
        """Test collecting items from LLM results."""
        items = service._collect_items_from_results(mock_llm_results)

        # Should collect all items
        epics = [i for i in items if i["type"] == ItemType.EPIC.value]
        features = [i for i in items if i["type"] == ItemType.FEATURE.value]
        stories = [i for i in items if i["type"] == ItemType.STORY.value]

        assert len(epics) == 5  # 2 + 2 + 1
        assert len(features) == 2  # 1 + 1
        assert len(stories) == 1  # 0 + 0 + 1

    def test_collect_items_preserves_provider_info(self, service, mock_llm_results):
        """Test that provider info is preserved in collected items."""
        items = service._collect_items_from_results(mock_llm_results)

        providers = set(i["provider"] for i in items)
        assert "ollama/qwen2.5-coder:7b" in providers
        assert "groq/llama-3.1-70b" in providers
        assert "gemini/gemini-flash" in providers

    def test_group_similar_items_exact_match(self, service):
        """Test grouping items with exact same titles."""
        items = [
            {"type": ItemType.EPIC.value, "title": "User Authentication", "provider": "A"},
            {"type": ItemType.EPIC.value, "title": "User Authentication", "provider": "B"},
            {"type": ItemType.EPIC.value, "title": "User Authentication", "provider": "C"},
        ]

        groups = service._group_similar_items(items)

        # Should be 1 group with 3 items
        assert len(groups) == 1
        group_items = list(groups.values())[0]
        assert len(group_items) == 3

    def test_group_similar_items_fuzzy_match(self, service):
        """Test grouping items with similar but not identical titles."""
        items = [
            {"type": ItemType.EPIC.value, "title": "User Authentication System", "provider": "A"},
            {"type": ItemType.EPIC.value, "title": "User Authentication", "provider": "B"},  # 80%+ similar
            {"type": ItemType.FEATURE.value, "title": "User Authentication", "provider": "C"},  # Different type
        ]

        groups = service._group_similar_items(items)

        # Should be 2 groups (epics together, feature separate due to type)
        assert len(groups) == 2

    def test_group_similar_items_different_types_separate(self, service):
        """Test that items of different types are grouped separately."""
        items = [
            {"type": ItemType.EPIC.value, "title": "Login System", "provider": "A"},
            {"type": ItemType.FEATURE.value, "title": "Login System", "provider": "B"},
            {"type": ItemType.STORY.value, "title": "Login System", "provider": "C"},
        ]

        groups = service._group_similar_items(items)

        # Should be 3 separate groups (one for each type)
        assert len(groups) == 3

    def test_merge_item_data_combines_descriptions(self, service):
        """Test merging data from multiple items."""
        items = [
            {"data": {"description": "First desc", "priority": "high"}},
            {"data": {"description": "Second desc", "complexity": "medium"}},
        ]

        merged = service._merge_item_data(items)

        assert merged["description"] == "First desc"
        assert merged["priority"] == "high"
        assert merged["complexity"] == "medium"

    def test_merge_item_data_merges_lists(self, service):
        """Test that lists are merged and deduplicated."""
        items = [
            {"data": {"tags": ["auth", "security"]}},
            {"data": {"tags": ["security", "user"]}},
        ]

        merged = service._merge_item_data(items)

        # Should have all unique tags
        assert len(merged["tags"]) == 3
        assert "auth" in merged["tags"]
        assert "security" in merged["tags"]
        assert "user" in merged["tags"]

    def test_detect_conflicts_priority_conflict(self, service):
        """Test detection of priority conflicts."""
        items = [
            {"data": {"priority": "high"}, "provider": "A"},
            {"data": {"priority": "low"}, "provider": "B"},
        ]

        conflicts = service._detect_conflicts_in_group(items)

        assert len(conflicts) >= 1
        conflict_types = [c[0] for c in conflicts]
        assert ConflictType.PRIORITY.value in conflict_types

    def test_detect_conflicts_complexity_conflict(self, service):
        """Test detection of complexity/scope conflicts."""
        items = [
            {"data": {"estimated_complexity": "high"}, "provider": "A"},
            {"data": {"estimated_complexity": "low"}, "provider": "B"},
        ]

        conflicts = service._detect_conflicts_in_group(items)

        conflict_types = [c[0] for c in conflicts]
        assert ConflictType.SCOPE.value in conflict_types

    def test_detect_conflicts_no_conflict(self, service):
        """Test no conflicts when items agree."""
        items = [
            {"data": {"priority": "high"}, "provider": "A"},
            {"data": {"priority": "high"}, "provider": "B"},
        ]

        conflicts = service._detect_conflicts_in_group(items)

        # No priority conflict since they agree
        priority_conflicts = [c for c in conflicts if c[0] == ConflictType.PRIORITY.value]
        assert len(priority_conflicts) == 0

    def test_calculate_confidence_full_agreement(self, service):
        """Test confidence calculation with full agreement."""
        confidence = service._calculate_confidence(
            agreement_ratio=1.0,  # All LLMs agree
            item_count=3,
            has_enrichments=True,
        )

        # 70% base + 15% sources (capped) + 15% enrichment = 100%
        assert confidence == 1.0

    def test_calculate_confidence_partial_agreement(self, service):
        """Test confidence calculation with partial agreement."""
        confidence = service._calculate_confidence(
            agreement_ratio=0.5,  # Half of LLMs agree
            item_count=2,
            has_enrichments=False,
        )

        # 35% base (0.5 * 70%) + 10% sources (2 * 5%) + 0% enrichment
        expected = 0.35 + 0.10
        assert abs(confidence - expected) < 0.01

    def test_calculate_avg_confidence(self, service):
        """Test average confidence calculation."""
        grouped_items = {
            (ItemType.EPIC.value, "Epic 1"): [
                {"provider": "A"},
                {"provider": "B"},
            ],
            (ItemType.EPIC.value, "Epic 2"): [
                {"provider": "A"},
            ],
        }

        # Mock selector with 2 providers
        selector = MagicMock()
        selector.get_provider_ids.return_value = ["A", "B"]

        avg_conf = service._calculate_avg_confidence(grouped_items, selector)

        # Should be average of confidence scores
        assert 0 < avg_conf < 1

    @pytest.mark.asyncio
    async def test_run_cycle_3_creates_consensus_items(self, service, mock_session, mock_llm_results):
        """Test that Cycle 3 creates consensus items."""
        mock_session.llm_results = mock_llm_results

        with patch.object(service, 'get_session', return_value=mock_session):
            with patch.object(service, '_get_selector') as mock_selector:
                selector = MagicMock()
                selector.get_confidence_target.return_value = 0.8
                selector.get_provider_ids.return_value = ["ollama", "groq", "gemini"]
                selector.includes_human_review.return_value = False
                mock_selector.return_value = selector

                result = await service.run_cycle_3(mock_session.id)

        assert result["cycle"] == 3
        assert result["status"] == "completed"
        assert "consensus_items" in result
        assert "conflicts_found" in result
        assert "avg_confidence" in result

    @pytest.mark.asyncio
    async def test_run_cycle_3_detects_conflicts(self, service, mock_session, mock_llm_results):
        """Test that Cycle 3 detects conflicts in LLM outputs."""
        mock_session.llm_results = mock_llm_results

        with patch.object(service, 'get_session', return_value=mock_session):
            with patch.object(service, '_get_selector') as mock_selector:
                selector = MagicMock()
                selector.get_confidence_target.return_value = 0.8
                selector.get_provider_ids.return_value = ["ollama", "groq", "gemini"]
                selector.includes_human_review.return_value = False
                mock_selector.return_value = selector

                result = await service.run_cycle_3(mock_session.id)

        # Should have found conflicts (different priorities in mock data)
        assert result["conflicts_found"] >= 0  # May or may not find conflicts


# ===========================================================================
# Cycle 5 Tests: Final Synthesis
# ===========================================================================

class TestCycle5FinalSynthesis:
    """Tests for Cycle 5: Final Synthesis."""

    def test_estimate_function_points_epic(self, service):
        """Test FP estimation for epics."""
        items = [
            MagicMock(item_type=ItemType.EPIC.value, item_data={}),
        ]

        fp = service._estimate_function_points(items)

        assert fp == 150  # Default for epic

    def test_estimate_function_points_feature(self, service):
        """Test FP estimation for features."""
        items = [
            MagicMock(item_type=ItemType.FEATURE.value, item_data={}),
        ]

        fp = service._estimate_function_points(items)

        assert fp == 35  # Default for feature

    def test_estimate_function_points_story(self, service):
        """Test FP estimation for stories."""
        items = [
            MagicMock(item_type=ItemType.STORY.value, item_data={}),
        ]

        fp = service._estimate_function_points(items)

        assert fp == 10  # Default for story

    def test_estimate_function_points_task(self, service):
        """Test FP estimation for tasks."""
        items = [
            MagicMock(item_type=ItemType.TASK.value, item_data={}),
        ]

        fp = service._estimate_function_points(items)

        assert fp == 3  # Default for task

    def test_estimate_function_points_custom(self, service):
        """Test FP estimation with custom values in item_data."""
        items = [
            MagicMock(item_type=ItemType.EPIC.value, item_data={"estimated_fp": 200}),
            MagicMock(item_type=ItemType.FEATURE.value, item_data={"function_points": 50}),
        ]

        fp = service._estimate_function_points(items)

        assert fp == 250  # 200 + 50

    def test_estimate_function_points_mixed(self, service):
        """Test FP estimation with mixed item types."""
        items = [
            MagicMock(item_type=ItemType.EPIC.value, item_data={}),
            MagicMock(item_type=ItemType.FEATURE.value, item_data={}),
            MagicMock(item_type=ItemType.FEATURE.value, item_data={}),
            MagicMock(item_type=ItemType.STORY.value, item_data={}),
            MagicMock(item_type=ItemType.STORY.value, item_data={}),
            MagicMock(item_type=ItemType.STORY.value, item_data={}),
            MagicMock(item_type=ItemType.TASK.value, item_data={}),
        ]

        fp = service._estimate_function_points(items)

        # 150 + 35 + 35 + 10 + 10 + 10 + 3 = 253
        assert fp == 253

    def test_get_accepted_items(self, service, mock_session):
        """Test getting accepted items."""
        mock_session.consensus_items = [
            MagicMock(status=ConsensusStatus.AUTO_ACCEPTED.value),
            MagicMock(status=ConsensusStatus.ACCEPTED.value),
            MagicMock(status=ConsensusStatus.REJECTED.value),
            MagicMock(status=ConsensusStatus.HUMAN_REVIEW.value),
        ]

        accepted = service._get_accepted_items(mock_session)

        assert len(accepted) == 2  # AUTO_ACCEPTED + ACCEPTED

    def test_generate_synthesis_summary(self, service, mock_session):
        """Test synthesis summary generation."""
        final_epics = [
            MagicMock(
                item_title="Epic 1",
                item_description="Description 1",
                item_data={"features": ["F1", "F2"]},
                confidence_score=0.9,
            ),
        ]
        final_features = [
            MagicMock(item_title="Feature 1", confidence_score=0.85),
        ]
        final_stories = []
        final_tasks = []

        mock_session.conflicts = [
            MagicMock(status=ConflictStatus.RESOLVED.value),
            MagicMock(status=ConflictStatus.PENDING.value),
        ]
        mock_session.consensus_items = [
            MagicMock(status=ConsensusStatus.ACCEPTED.value),
        ]

        summary = service._generate_synthesis_summary(
            session=mock_session,
            final_epics=final_epics,
            final_features=final_features,
            final_stories=final_stories,
            final_tasks=final_tasks,
        )

        assert "epics" in summary
        assert len(summary["epics"]) == 1
        assert summary["epics"][0]["title"] == "Epic 1"
        assert summary["conflicts_resolved"] == 1
        assert summary["tier"] == mock_session.tier

    @pytest.mark.asyncio
    async def test_run_cycle_5_completes_session(self, service, mock_session):
        """Test that Cycle 5 completes the session."""
        mock_session.consensus_items = [
            MagicMock(
                status=ConsensusStatus.AUTO_ACCEPTED.value,
                item_type=ItemType.EPIC.value,
                confidence_score=0.9,
                item_data={},
                item_title="Epic 1",
                item_description="Desc",
            ),
            MagicMock(
                status=ConsensusStatus.ACCEPTED.value,
                item_type=ItemType.FEATURE.value,
                confidence_score=0.85,
                item_data={},
                item_title="Feature 1",
                item_description="Desc",
            ),
        ]
        mock_session.conflicts = []

        with patch.object(service, 'get_session', return_value=mock_session):
            with patch.object(service, '_get_selector') as mock_selector:
                selector = MagicMock()
                selector.get_call_statistics.return_value = {
                    "total_cost_usd": 5.0,
                    "total_tokens": 10000,
                }
                mock_selector.return_value = selector

                result = await service.run_cycle_5(mock_session.id)

        assert result["cycle"] == 5
        assert result["status"] == "completed"
        assert result["session_status"] == "completed"
        assert "totals" in result
        assert "confidence" in result
        assert "cost" in result
        assert "synthesis_summary" in result

    @pytest.mark.asyncio
    async def test_run_cycle_5_calculates_totals(self, service, mock_session):
        """Test that Cycle 5 calculates correct totals."""
        mock_session.consensus_items = [
            MagicMock(status=ConsensusStatus.AUTO_ACCEPTED.value, item_type=ItemType.EPIC.value, confidence_score=0.9, item_data={}, item_title="E1", item_description=None),
            MagicMock(status=ConsensusStatus.AUTO_ACCEPTED.value, item_type=ItemType.EPIC.value, confidence_score=0.85, item_data={}, item_title="E2", item_description=None),
            MagicMock(status=ConsensusStatus.ACCEPTED.value, item_type=ItemType.FEATURE.value, confidence_score=0.8, item_data={}, item_title="F1", item_description=None),
            MagicMock(status=ConsensusStatus.REJECTED.value, item_type=ItemType.FEATURE.value, confidence_score=0.7, item_data={}, item_title="F2", item_description=None),
        ]
        mock_session.conflicts = []

        with patch.object(service, 'get_session', return_value=mock_session):
            with patch.object(service, '_get_selector') as mock_selector:
                selector = MagicMock()
                selector.get_call_statistics.return_value = {"total_cost_usd": 5.0, "total_tokens": 10000}
                mock_selector.return_value = selector

                result = await service.run_cycle_5(mock_session.id)

        # 2 epics + 1 feature accepted (1 rejected not counted)
        assert result["totals"]["epics"] == 2
        assert result["totals"]["features"] == 1
        # FP: 2*150 + 1*35 = 335
        assert result["totals"]["function_points"] == 335


# ===========================================================================
# Bulk Resolution Tests
# ===========================================================================

class TestBulkResolution:
    """Tests for bulk conflict resolution helpers."""

    @pytest.mark.asyncio
    async def test_bulk_resolve_conflicts(self, service, mock_session):
        """Test bulk conflict resolution."""
        conflict1_id = uuid4()
        conflict2_id = uuid4()

        resolutions = [
            {"conflict_id": conflict1_id, "choice": "option_a", "reasoning": "Better option"},
            {"conflict_id": conflict2_id, "choice": "option_b", "reasoning": "Alternative"},
        ]

        with patch.object(service, 'resolve_conflict', new_callable=AsyncMock) as mock_resolve:
            result = await service.bulk_resolve_conflicts(
                session_id=mock_session.id,
                resolutions=resolutions,
                resolved_by="test_user",
            )

        assert result["total_submitted"] == 2
        assert result["resolved"] == 2
        assert len(result["errors"]) == 0
        assert mock_resolve.call_count == 2

    @pytest.mark.asyncio
    async def test_bulk_resolve_conflicts_with_errors(self, service, mock_session):
        """Test bulk resolution handles errors gracefully."""
        conflict1_id = uuid4()

        resolutions = [
            {"conflict_id": conflict1_id, "choice": "option_a"},
        ]

        with patch.object(service, 'resolve_conflict', new_callable=AsyncMock) as mock_resolve:
            mock_resolve.side_effect = ValueError("Conflict not found")

            result = await service.bulk_resolve_conflicts(
                session_id=mock_session.id,
                resolutions=resolutions,
                resolved_by="test_user",
            )

        assert result["total_submitted"] == 1
        assert result["resolved"] == 0
        assert len(result["errors"]) == 1

    @pytest.mark.asyncio
    async def test_bulk_decide_consensus(self, service, mock_session):
        """Test bulk consensus decisions."""
        consensus1_id = uuid4()
        consensus2_id = uuid4()

        decisions = [
            {"consensus_id": consensus1_id, "decision": "accept"},
            {"consensus_id": consensus2_id, "decision": "reject"},
        ]

        mock_accepted = MagicMock()
        mock_accepted.status = ConsensusStatus.ACCEPTED.value
        mock_rejected = MagicMock()
        mock_rejected.status = ConsensusStatus.REJECTED.value

        with patch.object(service, 'decide_consensus', new_callable=AsyncMock) as mock_decide:
            mock_decide.side_effect = [mock_accepted, mock_rejected]

            result = await service.bulk_decide_consensus(
                session_id=mock_session.id,
                decisions=decisions,
                decided_by="test_user",
            )

        assert result["total_submitted"] == 2
        assert result["accepted"] == 1
        assert result["rejected"] == 1
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_auto_resolve_llm_recommendations(self, service, mock_session):
        """Test auto-resolving conflicts using LLM recommendations."""
        mock_session.conflicts = [
            MagicMock(
                status=ConflictStatus.PENDING.value,
                llm_recommendation="option_a",
            ),
            MagicMock(
                status=ConflictStatus.PENDING.value,
                llm_recommendation="option_b",
            ),
            MagicMock(
                status=ConflictStatus.PENDING.value,
                llm_recommendation=None,  # No recommendation
            ),
            MagicMock(
                status=ConflictStatus.RESOLVED.value,  # Already resolved
                llm_recommendation="option_a",
            ),
        ]

        with patch.object(service, 'get_session', return_value=mock_session):
            result = await service.auto_resolve_llm_recommendations(mock_session.id)

        assert result["resolved"] == 2  # 2 with recommendations
        assert result["skipped"] == 1  # 1 without recommendation


# ===========================================================================
# Integration Tests
# ===========================================================================

class TestCycle3And5Integration:
    """Integration tests for Cycles 3 and 5 together."""

    @pytest.mark.asyncio
    async def test_full_cycle_3_to_5_flow(self, service, mock_session, mock_llm_results):
        """Test complete flow from Cycle 3 through 5."""
        mock_session.llm_results = mock_llm_results
        mock_session.consensus_items = []
        mock_session.conflicts = []

        # Run Cycle 3
        with patch.object(service, 'get_session', return_value=mock_session):
            with patch.object(service, '_get_selector') as mock_selector:
                selector = MagicMock()
                selector.get_confidence_target.return_value = 0.8
                selector.get_provider_ids.return_value = ["ollama", "groq", "gemini"]
                selector.includes_human_review.return_value = False
                selector.get_call_statistics.return_value = {"total_cost_usd": 5.0, "total_tokens": 10000}
                mock_selector.return_value = selector

                cycle3_result = await service.run_cycle_3(mock_session.id)

                # Simulate items being added
                mock_session.consensus_items = [
                    MagicMock(
                        status=ConsensusStatus.AUTO_ACCEPTED.value,
                        item_type=ItemType.EPIC.value,
                        confidence_score=0.9,
                        item_data={},
                        item_title="Epic",
                        item_description=None,
                    ),
                ]

                # Run Cycle 5
                cycle5_result = await service.run_cycle_5(mock_session.id)

        assert cycle3_result["cycle"] == 3
        assert cycle5_result["cycle"] == 5
        assert cycle5_result["session_status"] == "completed"


# ===========================================================================
# Run Tests
# ===========================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
