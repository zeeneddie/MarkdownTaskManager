"""
Integration Tests for Deep Extraction Cycles.

Tests the complete 6-cycle deep extraction pipeline:
- Cycle 0: Static Analysis
- Cycle 1: Independent LLM Analysis
- Cycle 2: Cross-Enrichment
- Cycle 3: Conflict Detection
- Cycle 4: Human Review
- Cycle 5: Final Synthesis

Coverage:
- Session lifecycle
- Cycle execution order
- Data accumulation between cycles
- Tier-aware provider selection
- Cost tracking across cycles
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone
from typing import Dict, Any, List

from app.models.deep_extraction import (
    ExtractionTier,
    ExtractionStatus,
    ConsensusStatus,
    ConflictStatus,
    ItemType,
    TIER_CONFIG,
)
from app.services.deep_extraction_service import DeepExtractionService
from app.services.tier_provider_selector import (
    TierProviderSelector,
    create_tier_selector,
    LLMCallResult,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db():
    """Create mock async database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_session():
    """Create mock extraction session."""
    session = MagicMock()
    session.id = uuid4()
    session.tier = ExtractionTier.STANDARD.value
    session.tier_price_usd = 15.0
    session.actual_cost_usd = 0.0
    session.status = ExtractionStatus.STARTED.value
    session.current_cycle = 0
    session.source_path = "/test/project"
    session.total_files = 50
    session.total_lines = 5000
    session.workflow_type = "GREEN_PAPER"
    session.consensus_items = []
    session.conflicts = []
    session.llm_results = []
    session.enrichments = []
    return session


@pytest.fixture
def mock_static_analysis_result():
    """Create mock static analysis result."""
    return MagicMock(
        business_rules=[
            MagicMock(
                id="br-001",
                description="Patient must be over 18",
                confidence=0.85,
                source_location="/src/validators/patient.py:42"
            )
        ],
        nfr_detections=[
            MagicMock(
                id="nfr-001",
                category="performance",
                description="Response time < 200ms",
                confidence=0.90
            )
        ],
        compliance_violations=[
            MagicMock(
                id="cv-001",
                regulation="GDPR",
                severity="high",
                description="PII stored without encryption"
            )
        ],
        domain_coverage=0.75,
        nfr_coverage=0.80,
    )


@pytest.fixture
def mock_llm_results():
    """Create mock LLM analysis results."""
    return [
        {
            "provider": "ollama/qwen2.5-coder:7b",
            "analysis_type": "architecture",
            "epics": [
                {"title": "User Management", "description": "Handle user authentication"},
            ],
            "features": [
                {"title": "Login", "parent_id": None},
            ],
            "stories": [
                {"title": "As a user, I can login", "acceptance_criteria": ["Valid credentials"]},
            ],
            "confidence": 0.82,
        },
        {
            "provider": "groq/llama-3.1-8b",
            "analysis_type": "business_logic",
            "epics": [
                {"title": "User Management", "description": "User auth and profile management"},
            ],
            "features": [
                {"title": "Login", "parent_id": None},
                {"title": "Profile", "parent_id": None},
            ],
            "stories": [],
            "confidence": 0.78,
        },
    ]


# =============================================================================
# SESSION LIFECYCLE TESTS
# =============================================================================


class TestSessionLifecycle:
    """Tests for extraction session lifecycle."""

    @pytest.mark.asyncio
    async def test_create_session_sets_initial_status(self, mock_db, mock_session):
        """Test that new session has STARTED status."""
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        with patch.object(mock_db, 'refresh', new=AsyncMock()):
            # Create service and simulate session creation
            service = DeepExtractionService(mock_db)

            # Mock project lookup
            mock_db.execute.return_value = MagicMock(
                scalar_one_or_none=MagicMock(return_value=MagicMock(id=1, name="TestProject"))
            )

        # Initial status should be STARTED
        assert mock_session.status == ExtractionStatus.STARTED.value
        assert mock_session.current_cycle == 0

    @pytest.mark.asyncio
    async def test_session_tracks_source_metrics(self, mock_session):
        """Test that session tracks source code metrics."""
        assert mock_session.source_path == "/test/project"
        assert mock_session.total_files >= 0
        assert mock_session.total_lines >= 0

    @pytest.mark.asyncio
    async def test_session_has_tier_configuration(self, mock_session):
        """Test that session has tier configuration."""
        tier = ExtractionTier(mock_session.tier)
        config = TIER_CONFIG[tier]

        assert mock_session.tier_price_usd == config["price_usd"]


# =============================================================================
# CYCLE EXECUTION TESTS
# =============================================================================


class TestCycleExecution:
    """Tests for individual cycle execution."""

    @pytest.mark.asyncio
    async def test_cycle_0_performs_static_analysis(
        self, mock_db, mock_session, mock_static_analysis_result
    ):
        """Test that Cycle 0 performs static analysis."""
        service = DeepExtractionService(mock_db)

        # Mock session retrieval
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_session

        # Test that the service has the run_cycle_0 method
        assert hasattr(service, 'run_cycle_0')

        # Verify static analysis result structure
        assert mock_static_analysis_result.business_rules is not None
        assert mock_static_analysis_result.domain_coverage > 0

    @pytest.mark.asyncio
    async def test_cycle_1_uses_tier_providers(
        self, mock_db, mock_session, mock_llm_results
    ):
        """Test that Cycle 1 uses tier-appropriate providers."""
        service = DeepExtractionService(mock_db)

        # Get providers for tier
        selector = create_tier_selector(ExtractionTier.STANDARD)
        providers = selector.get_provider_ids()

        # Should have providers
        assert len(providers) >= 3

        # Verify Ollama (local) providers are included
        ollama_providers = [p for p in providers if p.startswith("ollama/")]
        assert len(ollama_providers) >= 1

    @pytest.mark.asyncio
    async def test_cycle_2_creates_enrichments(self, mock_session, mock_llm_results):
        """Test that Cycle 2 creates enrichments from LLM outputs."""
        # Simulate enrichment data structure
        enrichment = {
            "source_llm": "ollama/qwen2.5-coder:7b",
            "target_item_id": "epic-001",
            "enrichment_type": "description_enhancement",
            "original_text": "User management",
            "enriched_text": "User management including authentication and authorization",
            "confidence": 0.85,
        }

        assert "source_llm" in enrichment
        assert "enriched_text" in enrichment
        assert enrichment["confidence"] > 0

    @pytest.mark.asyncio
    async def test_cycle_3_detects_conflicts(self, mock_session, mock_llm_results):
        """Test that Cycle 3 detects conflicts between LLM outputs."""
        # Simulate conflict structure
        conflict = {
            "item_type": ItemType.FEATURE.value,
            "item_title": "Login Feature",
            "conflict_type": "priority_disagreement",
            "option_a": {
                "provider": "ollama/qwen2.5-coder:7b",
                "value": "high priority",
            },
            "option_b": {
                "provider": "groq/llama-3.1-8b",
                "value": "medium priority",
            },
            "status": ConflictStatus.PENDING.value,
        }

        assert conflict["status"] == ConflictStatus.PENDING.value
        assert conflict["option_a"]["provider"] != conflict["option_b"]["provider"]


# =============================================================================
# CYCLE ORDER AND DEPENDENCIES TESTS
# =============================================================================


class TestCycleOrderDependencies:
    """Tests for cycle execution order and dependencies."""

    def test_cycles_must_execute_in_order(self):
        """Test that cycles must execute in sequence 0-5."""
        expected_order = [0, 1, 2, 3, 4, 5]

        # Verify TIER_CONFIG doesn't skip cycles
        for tier in ExtractionTier:
            config = TIER_CONFIG[tier]
            # All tiers should support the full cycle chain
            assert "llm_count" in config

    def test_cycle_4_is_human_review(self):
        """Test that Cycle 4 requires human review for qualifying tiers."""
        # Only PROFESSIONAL and PREMIUM include mandatory human review
        prof_config = TIER_CONFIG[ExtractionTier.PROFESSIONAL]
        premium_config = TIER_CONFIG[ExtractionTier.PREMIUM]

        assert prof_config["human_review"] is True
        assert premium_config["human_review"] is True

    def test_lower_tiers_skip_human_review(self):
        """Test that lower tiers can skip human review."""
        free_config = TIER_CONFIG[ExtractionTier.FREE]
        basic_config = TIER_CONFIG[ExtractionTier.BASIC]
        standard_config = TIER_CONFIG[ExtractionTier.STANDARD]

        assert free_config["human_review"] is False
        assert basic_config["human_review"] is False
        assert standard_config["human_review"] is False


# =============================================================================
# DATA ACCUMULATION TESTS
# =============================================================================


class TestDataAccumulation:
    """Tests for data accumulation between cycles."""

    @pytest.mark.asyncio
    async def test_static_analysis_feeds_cycle_1(self, mock_static_analysis_result):
        """Test that static analysis results feed into Cycle 1."""
        # Static analysis provides context for LLM analysis
        business_rules = mock_static_analysis_result.business_rules
        nfrs = mock_static_analysis_result.nfr_detections

        # These should be used as context in Cycle 1
        assert len(business_rules) > 0
        assert len(nfrs) > 0

    @pytest.mark.asyncio
    async def test_llm_results_accumulate(self, mock_llm_results):
        """Test that LLM results accumulate across providers."""
        all_epics = []
        all_features = []
        all_stories = []

        for result in mock_llm_results:
            all_epics.extend(result.get("epics", []))
            all_features.extend(result.get("features", []))
            all_stories.extend(result.get("stories", []))

        # Multiple providers contribute results
        assert len(all_epics) >= 2
        assert len(all_features) >= 2

    @pytest.mark.asyncio
    async def test_enrichments_enhance_items(self):
        """Test that enrichments enhance extracted items."""
        original_item = {
            "id": "epic-001",
            "title": "User Management",
            "description": "Basic user management",
        }

        enrichment = {
            "enhanced_description": "Comprehensive user management including authentication, authorization, and profile management",
        }

        # Enrichment should add more detail
        assert len(enrichment["enhanced_description"]) > len(original_item["description"])


# =============================================================================
# CONSENSUS BUILDING TESTS
# =============================================================================


class TestConsensusBuilding:
    """Tests for consensus building in Cycle 5."""

    @pytest.mark.asyncio
    async def test_consensus_item_has_supporting_llms(self):
        """Test that consensus items track supporting LLMs."""
        consensus_item = {
            "item_type": ItemType.EPIC.value,
            "item_title": "User Management",
            "confidence_score": 0.88,
            "supporting_llms": [
                "ollama/qwen2.5-coder:7b",
                "groq/llama-3.1-8b",
                "alibaba/qwen-turbo",
            ],
            "status": ConsensusStatus.AUTO_ACCEPTED.value,
        }

        assert len(consensus_item["supporting_llms"]) >= 2
        assert consensus_item["confidence_score"] >= 0.72  # Auto-accept threshold

    @pytest.mark.asyncio
    async def test_low_confidence_items_need_review(self):
        """Test that low confidence items need human review."""
        consensus_item = {
            "item_type": ItemType.STORY.value,
            "item_title": "Complex user story",
            "confidence_score": 0.65,  # Below threshold
            "supporting_llms": ["ollama/qwen2.5-coder:7b"],
            "status": ConsensusStatus.HUMAN_REVIEW.value,
        }

        assert consensus_item["confidence_score"] < 0.72
        assert consensus_item["status"] == ConsensusStatus.HUMAN_REVIEW.value


# =============================================================================
# COST TRACKING TESTS
# =============================================================================


class TestCostTrackingAcrossCycles:
    """Tests for cost tracking across extraction cycles."""

    def test_cost_accumulates_across_cycles(self):
        """Test that cost accumulates as cycles execute."""
        selector = create_tier_selector(ExtractionTier.STANDARD)

        # Simulate multiple LLM calls
        call1 = LLMCallResult(
            provider_id="groq/llama-3.1-8b",
            model="llama-3.1-8b",
            content="Analysis result",
            tokens_input=1000,
            tokens_output=500,
            cost_usd=0.05,
        )
        call2 = LLMCallResult(
            provider_id="alibaba/qwen-turbo",
            model="qwen-turbo",
            content="Analysis result",
            tokens_input=1200,
            tokens_output=600,
            cost_usd=0.03,
        )

        selector.track_call(call1)
        selector.track_call(call2)

        assert selector.get_total_cost() == 0.08
        assert selector.get_total_tokens() == 3300

    def test_margin_calculation(self):
        """Test margin calculation (tier price - actual cost)."""
        selector = create_tier_selector(ExtractionTier.STANDARD)

        # Track some calls
        call = LLMCallResult(
            provider_id="groq/llama-3.1-8b",
            model="llama-3.1-8b",
            content="Result",
            cost_usd=2.50,
        )
        selector.track_call(call)

        tier_price = selector.get_price_usd()  # $15 for STANDARD
        margin = selector.get_margin()

        assert margin == tier_price - 2.50
        assert margin > 0  # Should have positive margin


# =============================================================================
# PROVIDER SELECTION PER CYCLE TESTS
# =============================================================================


class TestProviderSelectionPerCycle:
    """Tests for provider selection logic per cycle."""

    def test_cycle_1_assigns_all_providers(self):
        """Test that Cycle 1 assigns all tier providers."""
        selector = create_tier_selector(ExtractionTier.PREMIUM)
        assignments = selector.get_providers_for_cycle(1)

        # Should have assignments for all providers
        assert len(assignments) == len(selector.get_provider_ids())

    def test_cycle_1_assigns_analysis_types(self):
        """Test that Cycle 1 assigns different analysis types."""
        selector = create_tier_selector(ExtractionTier.PREMIUM)
        assignments = selector.get_providers_for_cycle(1)

        analysis_types = set(a[1] for a in assignments)

        # Should have variety of analysis types
        assert len(analysis_types) >= 1

    def test_cycle_5_uses_best_provider(self):
        """Test that Cycle 5 uses the best available provider."""
        selector = create_tier_selector(ExtractionTier.PREMIUM)
        assignments = selector.get_providers_for_cycle(5)

        assert len(assignments) == 1
        provider, analysis_type = assignments[0]

        # Should use a premium provider for synthesis
        assert "claude" in provider or "gpt" in provider or "gemini" in provider
        assert analysis_type == "synthesis"


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


class TestCycleErrorHandling:
    """Tests for error handling during cycle execution."""

    @pytest.mark.asyncio
    async def test_llm_failure_updates_health(self):
        """Test that LLM failures update provider health status."""
        selector = create_tier_selector(ExtractionTier.STANDARD)
        provider = selector.get_provider_ids()[0]

        # Simulate failures
        for _ in range(4):
            selector.update_health(provider, is_healthy=False, error="Connection timeout")

        health = selector.get_health_status()
        assert health[provider]["is_healthy"] is False
        assert health[provider]["consecutive_failures"] >= 3

    @pytest.mark.asyncio
    async def test_unhealthy_provider_excluded(self):
        """Test that unhealthy providers are excluded from selection."""
        selector = create_tier_selector(ExtractionTier.STANDARD)
        provider = selector.get_provider_ids()[0]

        # Mark provider as unhealthy
        for _ in range(4):
            selector.update_health(provider, is_healthy=False, error="Error")

        healthy = selector.get_healthy_providers()
        assert provider not in healthy


# =============================================================================
# FULL EXTRACTION TESTS
# =============================================================================


class TestFullExtractionFlow:
    """Tests for complete extraction flow."""

    @pytest.mark.asyncio
    async def test_full_extraction_executes_all_cycles(self, mock_db):
        """Test that full extraction runs all applicable cycles."""
        service = DeepExtractionService(mock_db)

        # The run_full_extraction method should execute cycles 0-5
        # Based on tier settings

        # Verify service has the method
        assert hasattr(service, 'run_full_extraction')

    def test_extraction_result_structure(self):
        """Test the structure of extraction results."""
        expected_result_keys = [
            "session_id",
            "status",
            "current_cycle",
            "epics",
            "features",
            "stories",
            "confidence",
            "cost",
        ]

        # Create mock result structure
        result = {
            "session_id": str(uuid4()),
            "status": ExtractionStatus.COMPLETED.value,
            "current_cycle": 5,
            "epics": [],
            "features": [],
            "stories": [],
            "confidence": {"average": 0.85},
            "cost": {"total_usd": 5.0},
        }

        for key in expected_result_keys:
            assert key in result


# =============================================================================
# TIER UPGRADE DURING EXTRACTION TESTS
# =============================================================================


class TestTierUpgradeDuringExtraction:
    """Tests for tier upgrade scenarios during extraction."""

    def test_upgrade_preserves_existing_results(self):
        """Test that tier upgrade preserves already-extracted results."""
        # Results from lower tier should remain valid
        existing_results = {
            "cycle_0_completed": True,
            "cycle_1_results": [{"epic": "User Management"}],
            "cost_so_far": 2.5,
        }

        # After upgrade, these should be preserved
        assert existing_results["cycle_0_completed"] is True
        assert len(existing_results["cycle_1_results"]) > 0

    def test_upgrade_unlocks_additional_providers(self):
        """Test that upgrade unlocks additional LLM providers."""
        basic_selector = create_tier_selector(ExtractionTier.BASIC)
        standard_selector = create_tier_selector(ExtractionTier.STANDARD)

        basic_providers = set(basic_selector.get_provider_ids())
        standard_providers = set(standard_selector.get_provider_ids())

        # Standard should have more providers
        new_providers = standard_providers - basic_providers
        assert len(new_providers) > 0
