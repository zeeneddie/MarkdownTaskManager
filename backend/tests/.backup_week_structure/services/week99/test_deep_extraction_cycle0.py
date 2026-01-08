# backend/tests/services/week99/test_deep_extraction_cycle0.py
"""
Week 99 Tests - DeepExtractionService Cycle 0 Integration

Tests for static analysis integration in the extraction pipeline.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.services.deep_extraction_service import DeepExtractionService
from app.models.deep_extraction import (
    ExtractionTier,
    ExtractionStatus,
    TIER_CONFIG,
    tier_includes_static_analysis,
    is_tier_deprecated,
)


class TestCycle0Integration:
    """Test suite for Cycle 0 static analysis integration."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create DeepExtractionService instance."""
        return DeepExtractionService(mock_db)

    def test_service_has_static_results_cache(self, service):
        """Test that service has static results cache."""
        assert hasattr(service, '_static_results')
        assert isinstance(service._static_results, dict)

    def test_service_has_conflict_detector(self, service):
        """Test that service has conflict detector."""
        assert hasattr(service, '_conflict_detector')

    def test_format_static_context_for_llm(self, service):
        """Test formatting of static context for LLM prompts."""
        context = {
            "static_analysis_summary": {
                "files_analyzed": 100,
                "lines_of_code": 5000,
                "domain_coverage": 0.75,
                "nfr_coverage": 0.60,
            },
            "business_rules": [
                {
                    "type": "validation",
                    "natural_language": "User must be authenticated",
                    "confidence": 0.85,
                    "source_file": "auth.py",
                },
            ],
            "nfr_detections": [
                {
                    "category": "security",
                    "description": "Password hashing",
                    "confidence": 0.90,
                },
            ],
            "compliance_violations": [],
            "domain_variables": ["user_id", "order_total"],
        }

        result = service._format_static_context_for_llm(context)

        assert isinstance(result, str)
        assert "Static Analysis Results" in result
        assert "Files analyzed: 100" in result
        assert "Lines of code: 5000" in result
        assert "Business Rules Detected" in result
        assert "User must be authenticated" in result
        assert "Non-Functional Requirements Detected" in result
        assert "Password hashing" in result
        assert "Domain Variables" in result

    def test_format_static_context_empty(self, service):
        """Test formatting with empty context."""
        context = {
            "static_analysis_summary": {},
            "business_rules": [],
            "nfr_detections": [],
            "compliance_violations": [],
            "domain_variables": [],
        }

        result = service._format_static_context_for_llm(context)

        assert isinstance(result, str)
        assert "Static Analysis Results" in result
        # Should not contain sections for empty data
        assert "Business Rules Detected" not in result

    def test_get_compliance_frameworks_default(self, service):
        """Test default compliance frameworks."""
        mock_session = MagicMock()
        mock_session.project = None

        frameworks = service._get_compliance_frameworks(mock_session)

        assert isinstance(frameworks, list)
        assert "ISO27001" in frameworks
        assert "GDPR" in frameworks


class TestTierConfiguration:
    """Test tier configuration updates for Week 99."""

    def test_free_tier_deprecated(self):
        """Test that FREE tier is marked as deprecated."""
        assert is_tier_deprecated(ExtractionTier.FREE) is True

    def test_basic_tier_not_deprecated(self):
        """Test that BASIC tier is not deprecated."""
        assert is_tier_deprecated(ExtractionTier.BASIC) is False

    def test_all_paid_tiers_include_static_analysis(self):
        """Test that all paid tiers include static analysis."""
        paid_tiers = [
            ExtractionTier.BASIC,
            ExtractionTier.STANDARD,
            ExtractionTier.PROFESSIONAL,
            ExtractionTier.PREMIUM,
        ]

        for tier in paid_tiers:
            assert tier_includes_static_analysis(tier) is True, f"{tier} should include static analysis"

    def test_free_tier_no_static_analysis(self):
        """Test that FREE tier does not include static analysis."""
        assert tier_includes_static_analysis(ExtractionTier.FREE) is False

    def test_tier_prices_in_eur(self):
        """Test that tier prices include EUR values."""
        for tier in [ExtractionTier.BASIC, ExtractionTier.STANDARD, ExtractionTier.PROFESSIONAL, ExtractionTier.PREMIUM]:
            config = TIER_CONFIG[tier]
            assert "price_eur" in config
            assert config["price_eur"] > 0

    def test_basic_tier_price(self):
        """Test BASIC tier price is 5 EUR."""
        assert TIER_CONFIG[ExtractionTier.BASIC]["price_eur"] == 5.0

    def test_standard_tier_price(self):
        """Test STANDARD tier price is 15 EUR (Week 117: logarithmic pricing)."""
        assert TIER_CONFIG[ExtractionTier.STANDARD]["price_eur"] == 15.0

    def test_professional_tier_price(self):
        """Test PROFESSIONAL tier price is 45 EUR (Week 117: logarithmic pricing)."""
        assert TIER_CONFIG[ExtractionTier.PROFESSIONAL]["price_eur"] == 45.0

    def test_premium_tier_price(self):
        """Test PREMIUM tier price is 135 EUR (Week 117: logarithmic pricing)."""
        assert TIER_CONFIG[ExtractionTier.PREMIUM]["price_eur"] == 135.0

    def test_logarithmic_pricing_multiplier(self):
        """Test that tier pricing follows 3x logarithmic multiplier (Week 117)."""
        basic = TIER_CONFIG[ExtractionTier.BASIC]["price_eur"]
        standard = TIER_CONFIG[ExtractionTier.STANDARD]["price_eur"]
        professional = TIER_CONFIG[ExtractionTier.PROFESSIONAL]["price_eur"]
        premium = TIER_CONFIG[ExtractionTier.PREMIUM]["price_eur"]

        # Verify 3x multiplier between tiers
        assert standard == basic * 3  # €5 * 3 = €15
        assert professional == standard * 3  # €15 * 3 = €45
        assert premium == professional * 3  # €45 * 3 = €135

    def test_human_review_professional_and_premium(self):
        """Test that human review is included in PROFESSIONAL and PREMIUM."""
        assert TIER_CONFIG[ExtractionTier.PROFESSIONAL]["human_review"] is True
        assert TIER_CONFIG[ExtractionTier.PREMIUM]["human_review"] is True

    def test_no_human_review_basic_and_standard(self):
        """Test that human review is not included in BASIC and STANDARD."""
        assert TIER_CONFIG[ExtractionTier.BASIC]["human_review"] is False
        assert TIER_CONFIG[ExtractionTier.STANDARD]["human_review"] is False

    def test_llm_count_increases_with_tier(self):
        """Test that LLM count increases with tier level."""
        basic_llms = TIER_CONFIG[ExtractionTier.BASIC]["llm_count"]
        standard_llms = TIER_CONFIG[ExtractionTier.STANDARD]["llm_count"]
        professional_llms = TIER_CONFIG[ExtractionTier.PROFESSIONAL]["llm_count"]
        premium_llms = TIER_CONFIG[ExtractionTier.PREMIUM]["llm_count"]

        assert basic_llms <= standard_llms
        assert standard_llms <= professional_llms
        assert professional_llms <= premium_llms

    def test_confidence_target_increases_with_tier(self):
        """Test that confidence target increases with tier level."""
        basic_conf = TIER_CONFIG[ExtractionTier.BASIC]["confidence_target"]
        standard_conf = TIER_CONFIG[ExtractionTier.STANDARD]["confidence_target"]
        professional_conf = TIER_CONFIG[ExtractionTier.PROFESSIONAL]["confidence_target"]
        premium_conf = TIER_CONFIG[ExtractionTier.PREMIUM]["confidence_target"]

        assert basic_conf < standard_conf
        assert standard_conf < professional_conf
        assert professional_conf < premium_conf


class TestStartExtractionTierHandling:
    """Test start_extraction tier handling."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create DeepExtractionService instance."""
        return DeepExtractionService(mock_db)

    def test_default_tier_is_basic(self):
        """Test that default tier is now BASIC (not FREE)."""
        from app.services.deep_extraction_service import DeepExtractionService
        import inspect

        sig = inspect.signature(DeepExtractionService.start_extraction)
        tier_param = sig.parameters['tier']

        assert tier_param.default == ExtractionTier.BASIC


class TestSessionProgress:
    """Test session progress includes Cycle 0."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create DeepExtractionService instance."""
        return DeepExtractionService(mock_db)

    @pytest.mark.asyncio
    async def test_progress_includes_cycle_0(self, service, mock_db):
        """Test that progress report includes Cycle 0."""
        session_id = uuid4()

        # Mock session
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_session.status = ExtractionStatus.RUNNING.value
        mock_session.current_cycle = 1
        mock_session.tier = ExtractionTier.BASIC.value
        mock_session.cycle_0_completed_at = datetime.now(timezone.utc)
        mock_session.cycle_1_completed_at = None
        mock_session.cycle_2_completed_at = None
        mock_session.cycle_3_completed_at = None
        mock_session.cycle_4_completed_at = None
        mock_session.cycle_5_completed_at = None
        mock_session.total_epics = 0
        mock_session.total_features = 0
        mock_session.total_stories = 0
        mock_session.total_tasks = 0
        mock_session.total_function_points = 0
        mock_session.tier_confidence_target = 0.70
        mock_session.avg_confidence = 0.0
        mock_session.items_auto_accepted = 0
        mock_session.items_human_reviewed = 0
        mock_session.tier_price_usd = 5.0
        mock_session.actual_cost_usd = 0.0
        mock_session.margin_usd = 0.0
        mock_session.total_tokens_used = 0
        mock_session.static_analysis_id = "static-123"
        mock_session.static_domain_coverage = 0.75
        mock_session.static_nfr_coverage = 0.60
        mock_session.static_compliance_score = 0.85
        mock_session.runs = []
        mock_session.llm_results = []
        mock_session.consensus_items = []
        mock_session.conflicts = []

        # Patch get_session
        with patch.object(service, 'get_session', return_value=mock_session):
            progress = await service.get_session_progress(session_id)

        # Check Cycle 0 is included
        assert "cycle_0" in progress["cycles"]
        assert progress["cycles"]["cycle_0"]["name"] == "Static Analysis"
        assert progress["cycles"]["cycle_0"]["status"] == "completed"
        assert progress["cycles"]["cycle_0"]["metrics"] is not None
        assert progress["cycles"]["cycle_0"]["metrics"]["analysis_id"] == "static-123"

    def test_confidence_threshold_in_progress(self, service, mock_db):
        """Test that confidence threshold is included in progress."""
        # The threshold should be 0.725 (72.5%)
        from app.services.conflict_detector_service import ConflictDetectorService
        assert ConflictDetectorService.CONFIDENCE_THRESHOLD == 0.725
