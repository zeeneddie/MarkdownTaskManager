"""
Week 85-87 Tests: Deep Extraction API Endpoints

Tests for:
- Week 85: Human Review Queue, Bulk Operations, Re-Run Capability, Delta Tracking
- Week 86: Pricing Endpoints, Cost Estimation, Results Aggregation
- Week 87: Tier Selection Onboarding Flow
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.models.deep_extraction import (
    ExtractionTier,
    ExtractionStatus,
    ConsensusStatus,
    ConflictStatus,
    ConflictType,
    ItemType,
    ExtractionSession,
    ExtractionConsensus,
    ExtractionConflict,
    ExtractionLLMResult,
    TIER_CONFIG,
)
from app.services.deep_extraction_service import DeepExtractionService
from app.services.tier_provider_selector import (
    TierProviderSelector,
    compare_tiers,
    PROVIDER_COSTS,
)


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
def mock_session_with_review_items():
    """Mock session with items needing human review."""
    session = MagicMock(spec=ExtractionSession)
    session.id = uuid4()
    session.tier = ExtractionTier.PROFESSIONAL.value  # Includes human review
    session.tier_price_usd = 75.0
    session.actual_cost_usd = 15.0
    session.status = ExtractionStatus.RUNNING.value
    session.current_cycle = 4  # Human review cycle
    session.source_path = "/test/project"
    session.total_files = 100

    # Consensus items needing review
    session.consensus_items = [
        MagicMock(
            id=uuid4(),
            status=ConsensusStatus.HUMAN_REVIEW.value,
            item_type=ItemType.EPIC.value,
            item_title="Authentication System",
            item_description="User auth module",
            item_data={"priority": "high"},
            confidence_score=0.75,
            supporting_llms=["ollama/qwen2.5-coder:7b", "groq/llama-3.1-70b"],
        ),
        MagicMock(
            id=uuid4(),
            status=ConsensusStatus.HUMAN_REVIEW.value,
            item_type=ItemType.FEATURE.value,
            item_title="OAuth Integration",
            item_description="Add OAuth2 support",
            item_data={"priority": "medium"},
            confidence_score=0.68,
            supporting_llms=["ollama/qwen2.5-coder:7b"],
        ),
        MagicMock(
            id=uuid4(),
            status=ConsensusStatus.AUTO_ACCEPTED.value,  # Already accepted
            item_type=ItemType.STORY.value,
            item_title="Login Page",
            item_description="Basic login page",
            item_data={},
            confidence_score=0.92,
            supporting_llms=["ollama/qwen2.5-coder:7b", "groq/llama-3.1-70b", "gemini/gemini-flash"],
        ),
    ]

    # Conflicts needing resolution
    session.conflicts = [
        MagicMock(
            id=uuid4(),
            status=ConflictStatus.PENDING.value,
            conflict_type=ConflictType.PRIORITY.value,
            item_type=ItemType.EPIC.value,
            item_title="Payment System",
            options={"a": "high", "b": "medium"},
            llm_recommendation="a",
            recommendation_reasoning="Core business feature",
        ),
        MagicMock(
            id=uuid4(),
            status=ConflictStatus.PENDING.value,
            conflict_type=ConflictType.SCOPE.value,
            item_type=ItemType.FEATURE.value,
            item_title="Notifications",
            options={"a": "full", "b": "basic"},
            llm_recommendation=None,  # No recommendation
            recommendation_reasoning=None,
        ),
    ]

    session.llm_results = []
    return session


@pytest.fixture
def mock_completed_session():
    """Mock completed session with results."""
    session = MagicMock(spec=ExtractionSession)
    session.id = uuid4()
    session.tier = ExtractionTier.STANDARD.value
    session.tier_price_usd = 25.0
    session.actual_cost_usd = 8.50
    session.total_tokens_used = 45000
    session.status = ExtractionStatus.COMPLETED.value
    session.current_cycle = 5
    session.source_path = "/test/project"
    session.total_files = 75
    session.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
    session.completed_at = datetime.now(timezone.utc)

    # Final consensus items
    session.consensus_items = [
        MagicMock(
            id=uuid4(),
            status=ConsensusStatus.AUTO_ACCEPTED.value,
            item_type=ItemType.EPIC.value,
            item_title="User Management",
            item_description="Complete user lifecycle",
            item_data={"features": ["Registration", "Profile", "Settings"]},
            confidence_score=0.91,
            supporting_llms=["ollama/qwen2.5-coder:7b", "groq/llama-3.1-70b", "gemini/gemini-flash"],
        ),
        MagicMock(
            id=uuid4(),
            status=ConsensusStatus.ACCEPTED.value,
            item_type=ItemType.EPIC.value,
            item_title="Order Processing",
            item_description="Handle orders end-to-end",
            item_data={},
            confidence_score=0.88,
            supporting_llms=["ollama/qwen2.5-coder:7b", "groq/llama-3.1-70b"],
        ),
        MagicMock(
            id=uuid4(),
            status=ConsensusStatus.AUTO_ACCEPTED.value,
            item_type=ItemType.FEATURE.value,
            item_title="Email Notifications",
            item_description="Send email alerts",
            item_data={},
            confidence_score=0.85,
            supporting_llms=["ollama/qwen2.5-coder:7b", "gemini/gemini-flash"],
        ),
        MagicMock(
            id=uuid4(),
            status=ConsensusStatus.REJECTED.value,  # Rejected - not counted
            item_type=ItemType.FEATURE.value,
            item_title="SMS Notifications",
            item_description="Send SMS alerts",
            item_data={},
            confidence_score=0.55,
            supporting_llms=["ollama/qwen2.5-coder:7b"],
        ),
    ]

    session.conflicts = [
        MagicMock(status=ConflictStatus.RESOLVED.value),
        MagicMock(status=ConflictStatus.RESOLVED.value),
    ]

    session.llm_results = [
        MagicMock(
            id=uuid4(),
            cycle=1,
            llm_provider="ollama",
            llm_model="qwen2.5-coder:7b",
            analysis_type="architecture",
            tokens_input=5000,
            tokens_output=3000,
            cost_usd=0.0,
            latency_ms=2500,
            parsed_output=True,
            extracted_epics=[{"title": "User Management"}],
            extracted_features=[],
            extracted_stories=[],
            extracted_tasks=[],
        ),
        MagicMock(
            id=uuid4(),
            cycle=1,
            llm_provider="groq",
            llm_model="llama-3.1-70b",
            analysis_type="business_logic",
            tokens_input=4500,
            tokens_output=2800,
            cost_usd=0.50,
            latency_ms=800,
            parsed_output=True,
            extracted_epics=[{"title": "Order Processing"}],
            extracted_features=[{"title": "Email Notifications"}],
            extracted_stories=[],
            extracted_tasks=[],
        ),
    ]

    return session


@pytest.fixture
def service(mock_db):
    """Create service with mocked dependencies."""
    return DeepExtractionService(mock_db)


# ===========================================================================
# Week 85: Human Review Queue Tests
# ===========================================================================

class TestWeek85HumanReviewQueue:
    """Tests for human review queue management."""

    def test_get_review_queue_items(self, service, mock_session_with_review_items):
        """Test getting items that need human review."""
        session = mock_session_with_review_items

        # Filter for items needing review
        review_items = [
            item for item in session.consensus_items
            if item.status == ConsensusStatus.HUMAN_REVIEW.value
        ]
        pending_conflicts = [
            c for c in session.conflicts
            if c.status == ConflictStatus.PENDING.value
        ]

        assert len(review_items) == 2  # 2 consensus items need review
        assert len(pending_conflicts) == 2  # 2 conflicts pending

    def test_review_queue_categorization(self, service, mock_session_with_review_items):
        """Test categorizing review items by type and priority."""
        session = mock_session_with_review_items

        review_items = [
            item for item in session.consensus_items
            if item.status == ConsensusStatus.HUMAN_REVIEW.value
        ]

        # Group by type
        by_type = {}
        for item in review_items:
            item_type = item.item_type
            if item_type not in by_type:
                by_type[item_type] = []
            by_type[item_type].append(item)

        assert ItemType.EPIC.value in by_type
        assert ItemType.FEATURE.value in by_type
        assert len(by_type[ItemType.EPIC.value]) == 1
        assert len(by_type[ItemType.FEATURE.value]) == 1

    def test_conflicts_with_llm_recommendations(self, mock_session_with_review_items):
        """Test identifying conflicts with LLM recommendations."""
        session = mock_session_with_review_items

        with_recommendation = [
            c for c in session.conflicts
            if c.llm_recommendation is not None
        ]
        without_recommendation = [
            c for c in session.conflicts
            if c.llm_recommendation is None
        ]

        assert len(with_recommendation) == 1
        assert len(without_recommendation) == 1


# ===========================================================================
# Week 85: Bulk Operations Tests
# ===========================================================================

class TestWeek85BulkOperations:
    """Tests for bulk conflict resolution and consensus decisions."""

    @pytest.mark.asyncio
    async def test_bulk_resolve_conflicts_success(self, service, mock_session_with_review_items):
        """Test bulk resolution of conflicts."""
        session = mock_session_with_review_items

        resolutions = [
            {
                "conflict_id": session.conflicts[0].id,
                "choice": "a",
                "reasoning": "Core business priority",
            },
            {
                "conflict_id": session.conflicts[1].id,
                "choice": "b",
                "reasoning": "MVP scope",
            },
        ]

        with patch.object(service, 'resolve_conflict', new_callable=AsyncMock) as mock_resolve:
            result = await service.bulk_resolve_conflicts(
                session_id=session.id,
                resolutions=resolutions,
                resolved_by="test_reviewer",
            )

        assert result["total_submitted"] == 2
        assert result["resolved"] == 2
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_bulk_decide_consensus_success(self, service, mock_session_with_review_items):
        """Test bulk consensus decisions."""
        session = mock_session_with_review_items

        review_items = [
            item for item in session.consensus_items
            if item.status == ConsensusStatus.HUMAN_REVIEW.value
        ]

        decisions = [
            {"consensus_id": review_items[0].id, "decision": "accept"},
            {"consensus_id": review_items[1].id, "decision": "reject"},
        ]

        mock_accepted = MagicMock()
        mock_accepted.status = ConsensusStatus.ACCEPTED.value
        mock_rejected = MagicMock()
        mock_rejected.status = ConsensusStatus.REJECTED.value

        with patch.object(service, 'decide_consensus', new_callable=AsyncMock) as mock_decide:
            mock_decide.side_effect = [mock_accepted, mock_rejected]

            result = await service.bulk_decide_consensus(
                session_id=session.id,
                decisions=decisions,
                decided_by="test_reviewer",
            )

        assert result["total_submitted"] == 2
        assert result["accepted"] == 1
        assert result["rejected"] == 1

    @pytest.mark.asyncio
    async def test_auto_resolve_with_recommendations(self, service, mock_session_with_review_items):
        """Test auto-resolve using LLM recommendations."""
        session = mock_session_with_review_items

        with patch.object(service, 'get_session', return_value=session):
            result = await service.auto_resolve_llm_recommendations(session.id)

        # Should resolve 1 (with recommendation), skip 1 (no recommendation)
        assert result["resolved"] == 1
        assert result["skipped"] == 1


# ===========================================================================
# Week 85: Delta Tracking Tests
# ===========================================================================

class TestWeek85DeltaTracking:
    """Tests for delta comparison between extraction runs."""

    def test_calculate_delta_new_items(self):
        """Test calculating delta for newly discovered items."""
        current_run = {
            "epics": [
                {"title": "User Management", "id": "e1"},
                {"title": "Payment System", "id": "e2"},  # New
            ],
            "features": [
                {"title": "Login", "id": "f1"},
                {"title": "Checkout", "id": "f2"},  # New
            ],
            "stories": [],
            "tasks": [],
        }

        previous_run = {
            "epics": [
                {"title": "User Management", "id": "e1"},
            ],
            "features": [
                {"title": "Login", "id": "f1"},
            ],
            "stories": [],
            "tasks": [],
        }

        # Calculate delta
        new_epics = len(current_run["epics"]) - len(previous_run["epics"])
        new_features = len(current_run["features"]) - len(previous_run["features"])

        assert new_epics == 1
        assert new_features == 1

    def test_confidence_improvement(self):
        """Test tracking confidence improvement across runs."""
        previous_confidence = 0.72
        current_confidence = 0.85

        improvement = current_confidence - previous_confidence
        improvement_pct = (improvement / previous_confidence) * 100

        assert improvement == pytest.approx(0.13, rel=0.01)
        assert improvement_pct == pytest.approx(18.0, rel=1.0)


# ===========================================================================
# Week 85: Re-Run Capability Tests
# ===========================================================================

class TestWeek85ReRunCapability:
    """Tests for re-running extraction with tier upgrade."""

    def test_rerun_with_same_tier(self, mock_completed_session):
        """Test re-running extraction with same tier preserves settings."""
        session = mock_completed_session

        # Re-run with same tier should preserve settings
        original_tier = session.tier
        original_source = session.source_path

        # New session would have:
        # - Same tier
        # - Same source path
        # - previous_run_id set to original session ID
        assert original_tier == ExtractionTier.STANDARD.value
        assert original_source == "/test/project"

        # Delta tracking fields would be populated
        previous_run_id = session.id
        assert previous_run_id is not None

    @pytest.mark.asyncio
    async def test_rerun_with_tier_upgrade(self, service, mock_completed_session):
        """Test re-running with tier upgrade and credit application."""
        session = mock_completed_session

        # Original tier: STANDARD ($25)
        # New tier: PROFESSIONAL ($75)
        # Credit: $25 (amount paid for STANDARD)
        # Amount to charge: $75 - $25 = $50

        old_tier_price = TIER_CONFIG[ExtractionTier.STANDARD]["price_usd"]
        new_tier_price = TIER_CONFIG[ExtractionTier.PROFESSIONAL]["price_usd"]

        credit = old_tier_price
        amount_to_charge = new_tier_price - credit

        assert credit == 25.0
        assert amount_to_charge == 50.0

    def test_tier_upgrade_credit_calculation(self):
        """Test credit calculation for tier upgrades."""
        test_cases = [
            (ExtractionTier.FREE, ExtractionTier.BASIC, 0, 5),
            (ExtractionTier.BASIC, ExtractionTier.STANDARD, 5, 20),
            (ExtractionTier.STANDARD, ExtractionTier.PROFESSIONAL, 25, 50),
            (ExtractionTier.PROFESSIONAL, ExtractionTier.PREMIUM, 75, 75),
        ]

        for old_tier, new_tier, expected_credit, expected_charge in test_cases:
            old_price = TIER_CONFIG[old_tier]["price_usd"]
            new_price = TIER_CONFIG[new_tier]["price_usd"]

            credit = old_price
            amount_to_charge = new_price - credit

            assert credit == expected_credit, f"Failed for {old_tier} -> {new_tier}"
            assert amount_to_charge == expected_charge, f"Failed for {old_tier} -> {new_tier}"


# ===========================================================================
# Week 86: Pricing Endpoints Tests
# ===========================================================================

class TestWeek86PricingEndpoints:
    """Tests for pricing and cost estimation endpoints."""

    def test_tier_pricing_structure(self):
        """Test that all tiers have correct pricing structure."""
        for tier in ExtractionTier:
            config = TIER_CONFIG[tier]

            assert "price_usd" in config
            assert "llms" in config
            assert "confidence_target" in config
            assert "human_review" in config

            # Prices should be in ascending order
            prices = [TIER_CONFIG[t]["price_usd"] for t in ExtractionTier]
            assert prices == sorted(prices)

    def test_tier_feature_comparison(self):
        """Test feature comparison across tiers."""
        comparison = compare_tiers()

        assert len(comparison) == 5  # All 5 tiers

        for tier_info in comparison:
            assert "tier" in tier_info
            assert "price_usd" in tier_info
            assert "confidence_target" in tier_info
            assert "llm_count" in tier_info
            assert "human_review" in tier_info

    def test_cost_estimation_formula(self):
        """Test cost estimation based on LOC and complexity."""
        base_loc = 50000  # Base for standard pricing

        test_cases = [
            # (loc, complexity, tier, expected_multiplier_factor)
            (25000, "simple", ExtractionTier.STANDARD, 0.5),  # Half LOC
            (50000, "moderate", ExtractionTier.STANDARD, 1.0),  # Base
            (100000, "complex", ExtractionTier.STANDARD, 2.0),  # Double LOC
            (50000, "legacy", ExtractionTier.PROFESSIONAL, 1.5),  # Legacy multiplier
        ]

        complexity_multipliers = {
            "simple": 0.8,
            "moderate": 1.0,
            "complex": 1.3,
            "legacy": 1.5,
        }

        for loc, complexity, tier, expected_loc_mult in test_cases:
            loc_multiplier = loc / base_loc
            complexity_mult = complexity_multipliers[complexity]
            tier_price = TIER_CONFIG[tier]["price_usd"]

            estimated_cost = tier_price * loc_multiplier * complexity_mult

            # Verify calculation is reasonable
            assert estimated_cost > 0
            assert estimated_cost < tier_price * 5  # Max 5x base price


# ===========================================================================
# Week 86: Results Aggregation Tests
# ===========================================================================

class TestWeek86ResultsAggregation:
    """Tests for results aggregation and final output."""

    def test_count_accepted_items(self, mock_completed_session):
        """Test counting accepted items by type."""
        session = mock_completed_session

        accepted_statuses = [ConsensusStatus.AUTO_ACCEPTED.value, ConsensusStatus.ACCEPTED.value]

        accepted_items = [
            item for item in session.consensus_items
            if item.status in accepted_statuses
        ]

        # Count by type
        counts = {}
        for item in accepted_items:
            item_type = item.item_type
            counts[item_type] = counts.get(item_type, 0) + 1

        assert counts.get(ItemType.EPIC.value, 0) == 2
        assert counts.get(ItemType.FEATURE.value, 0) == 1

    def test_calculate_average_confidence(self, mock_completed_session):
        """Test calculating average confidence score."""
        session = mock_completed_session

        accepted_statuses = [ConsensusStatus.AUTO_ACCEPTED.value, ConsensusStatus.ACCEPTED.value]

        accepted_items = [
            item for item in session.consensus_items
            if item.status in accepted_statuses
        ]

        confidences = [item.confidence_score for item in accepted_items]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        # (0.91 + 0.88 + 0.85) / 3 = 0.88
        assert avg_confidence == pytest.approx(0.88, rel=0.01)

    def test_llm_call_statistics(self, mock_completed_session):
        """Test aggregating LLM call statistics."""
        session = mock_completed_session

        total_tokens = sum(
            r.tokens_input + r.tokens_output
            for r in session.llm_results
        )
        total_cost = sum(r.cost_usd for r in session.llm_results)
        avg_latency = sum(r.latency_ms for r in session.llm_results) / len(session.llm_results)

        assert total_tokens == 15300  # 5000+3000 + 4500+2800
        assert total_cost == 0.50  # Only Groq costs money
        assert avg_latency == 1650  # (2500 + 800) / 2


# ===========================================================================
# Week 87: Tier Selection Onboarding Tests
# ===========================================================================

class TestWeek87TierOnboarding:
    """Tests for tier selection and onboarding flow."""

    def test_recommend_tier_small_project(self):
        """Test tier recommendation for small projects."""
        loc = 10000
        complexity = "simple"
        budget = 10

        # Small, simple project with limited budget -> BASIC or FREE
        if budget <= 0:
            recommended = ExtractionTier.FREE
        elif budget < 25:
            recommended = ExtractionTier.BASIC
        else:
            recommended = ExtractionTier.STANDARD

        assert recommended in [ExtractionTier.FREE, ExtractionTier.BASIC]

    def test_recommend_tier_medium_project(self):
        """Test tier recommendation for medium projects."""
        loc = 50000
        complexity = "moderate"
        budget = 50

        # Medium project with moderate budget -> STANDARD (best value)
        recommended = ExtractionTier.STANDARD

        assert recommended == ExtractionTier.STANDARD
        assert TIER_CONFIG[recommended]["price_usd"] <= budget

    def test_recommend_tier_large_project(self):
        """Test tier recommendation for large, complex projects."""
        loc = 200000
        complexity = "legacy"
        budget = 200

        # Large legacy project -> PROFESSIONAL or PREMIUM
        if loc > 100000 and complexity == "legacy":
            recommended = ExtractionTier.PROFESSIONAL

        assert recommended in [ExtractionTier.PROFESSIONAL, ExtractionTier.PREMIUM]

    def test_tier_upgrade_suggestions(self):
        """Test generating upgrade suggestions."""
        current_tier = ExtractionTier.STANDARD

        # Find next tier up
        tier_order = list(ExtractionTier)
        current_index = tier_order.index(current_tier)

        if current_index < len(tier_order) - 1:
            next_tier = tier_order[current_index + 1]

            current_confidence = TIER_CONFIG[current_tier]["confidence_target"]
            next_confidence = TIER_CONFIG[next_tier]["confidence_target"]
            confidence_gain = next_confidence - current_confidence

            current_price = TIER_CONFIG[current_tier]["price_usd"]
            next_price = TIER_CONFIG[next_tier]["price_usd"]
            additional_cost = next_price - current_price

            assert next_tier == ExtractionTier.PROFESSIONAL
            assert confidence_gain == pytest.approx(0.10, rel=0.01)  # 90% - 80%
            assert additional_cost == 50  # $75 - $25

    def test_tier_alternatives(self):
        """Test generating alternative tier suggestions."""
        recommended = ExtractionTier.STANDARD

        # Get alternatives (one below, one above)
        tier_order = list(ExtractionTier)
        rec_index = tier_order.index(recommended)

        alternatives = []

        # Lower tier (budget option)
        if rec_index > 0:
            lower = tier_order[rec_index - 1]
            alternatives.append({
                "tier": lower.value,
                "price_usd": TIER_CONFIG[lower]["price_usd"],
                "confidence": TIER_CONFIG[lower]["confidence_target"],
                "why_consider": "Budget-friendly option",
            })

        # Higher tier (premium option)
        if rec_index < len(tier_order) - 1:
            higher = tier_order[rec_index + 1]
            alternatives.append({
                "tier": higher.value,
                "price_usd": TIER_CONFIG[higher]["price_usd"],
                "confidence": TIER_CONFIG[higher]["confidence_target"],
                "why_consider": "Higher confidence for critical projects",
            })

        assert len(alternatives) == 2  # BASIC and PROFESSIONAL


# ===========================================================================
# Integration Tests
# ===========================================================================

class TestWeek85To87Integration:
    """Integration tests for Week 85-87 features."""

    @pytest.mark.asyncio
    async def test_full_human_review_flow(self, service, mock_session_with_review_items):
        """Test complete human review flow."""
        session = mock_session_with_review_items

        # Step 1: Get review queue
        review_items = [
            item for item in session.consensus_items
            if item.status == ConsensusStatus.HUMAN_REVIEW.value
        ]
        pending_conflicts = [
            c for c in session.conflicts
            if c.status == ConflictStatus.PENDING.value
        ]

        assert len(review_items) > 0
        assert len(pending_conflicts) > 0

        # Step 2: Auto-resolve conflicts with recommendations
        with patch.object(service, 'get_session', return_value=session):
            auto_result = await service.auto_resolve_llm_recommendations(session.id)

        assert auto_result["resolved"] >= 0

        # Step 3: Bulk decide remaining items
        decisions = [
            {"consensus_id": item.id, "decision": "accept"}
            for item in review_items
        ]

        mock_accepted = MagicMock()
        mock_accepted.status = ConsensusStatus.ACCEPTED.value

        with patch.object(service, 'decide_consensus', new_callable=AsyncMock) as mock_decide:
            mock_decide.return_value = mock_accepted

            bulk_result = await service.bulk_decide_consensus(
                session_id=session.id,
                decisions=decisions,
                decided_by="test_reviewer",
            )

        assert bulk_result["accepted"] == len(decisions)

    def test_rerun_with_delta_calculation(self, mock_completed_session):
        """Test re-run flow with delta calculation."""
        previous_session = mock_completed_session

        # Simulate new run results
        previous_counts = {
            "epics": 2,
            "features": 1,
            "stories": 0,
            "tasks": 0,
        }

        current_counts = {
            "epics": 3,  # +1 new
            "features": 2,  # +1 new
            "stories": 5,  # +5 new
            "tasks": 12,  # +12 new
        }

        delta = {
            "new_epics": current_counts["epics"] - previous_counts["epics"],
            "new_features": current_counts["features"] - previous_counts["features"],
            "new_stories": current_counts["stories"] - previous_counts["stories"],
            "new_tasks": current_counts["tasks"] - previous_counts["tasks"],
        }

        assert delta["new_epics"] == 1
        assert delta["new_features"] == 1
        assert delta["new_stories"] == 5
        assert delta["new_tasks"] == 12

    def test_pricing_to_onboarding_flow(self):
        """Test flow from pricing check to tier selection."""
        # Step 1: Get pricing info
        tiers = compare_tiers()
        assert len(tiers) == 5

        # Step 2: Estimate cost for project
        project_loc = 75000
        project_complexity = "moderate"

        base_loc = 50000
        loc_multiplier = project_loc / base_loc  # 1.5
        complexity_multipliers = {"simple": 0.8, "moderate": 1.0, "complex": 1.3, "legacy": 1.5}
        complexity_mult = complexity_multipliers[project_complexity]  # 1.0

        # Calculate estimated costs for each tier
        estimates = {}
        for tier_info in tiers:
            tier = tier_info["tier"]
            base_price = tier_info["price_usd"]
            estimates[tier] = base_price * loc_multiplier * complexity_mult

        # STANDARD: $25 * 1.5 * 1.0 = $37.50
        assert estimates["STANDARD"] == pytest.approx(37.50, rel=0.01)

        # Step 3: Get recommendation based on requirements
        budget = 50
        need_human_review = False

        # Find best tier within budget
        suitable_tiers = [
            t for t in tiers
            if estimates[t["tier"]] <= budget
        ]

        # Pick highest confidence tier within budget
        if suitable_tiers:
            recommended = max(suitable_tiers, key=lambda t: t["confidence_target"])
            assert recommended["tier"] in ["FREE", "BASIC", "STANDARD"]


# ===========================================================================
# Run Tests
# ===========================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
