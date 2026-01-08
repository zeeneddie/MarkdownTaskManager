# backend/tests/services/week118/test_impact_preview_service.py
"""
Tests for ImpactPreviewService - Week 118 Client Portal 2.0 Phase 2
Felix agent impact analysis for feature requests.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.impact_preview_service import ImpactPreviewService
from app.models.portal_enhancements import FeatureImpactPreview, ImpactLevel, RiskLevel


class TestImpactPreviewService:
    """Test suite for ImpactPreviewService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mock db."""
        return ImpactPreviewService(mock_db)

    # ============== Cache Tests ==============

    @pytest.mark.asyncio
    async def test_analyze_feature_uses_cache(self, service, mock_db):
        """Test that cached preview is returned if not stale."""
        cached_preview = FeatureImpactPreview(
            id=uuid4(),
            feature_request_id=42,
            analyzer_agent="felix",
            architecture_impact=ImpactLevel.MEDIUM.value,
            security_impact=ImpactLevel.LOW.value,
            performance_impact=ImpactLevel.LOW.value,
            ux_impact=ImpactLevel.MEDIUM.value,
            data_impact=ImpactLevel.LOW.value,
            overall_impact=ImpactLevel.MEDIUM.value,
            risk_level=RiskLevel.LOW.value,
            complexity_score=5,
            affected_components=[],
            affected_apis=[],
            dependencies=[],
            breaking_changes=[],
            warnings=[],
            is_stale=False,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            created_at=datetime.now(timezone.utc),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = cached_preview
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.analyze_feature(
            feature_request_id=42,
            title="Test Feature",
            description="Test description",
            force_refresh=False,
        )

        assert result["success"] is True
        assert result["cached"] is True
        assert result["preview_id"] == str(cached_preview.id)

    @pytest.mark.asyncio
    async def test_analyze_feature_force_refresh_ignores_cache(self, service, mock_db):
        """Test that force_refresh bypasses cache."""
        # Mock no cached preview for this test path
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock LLM provider failure for simpler test
        with patch.object(service, 'provider_registry') as mock_registry:
            mock_registry.get_provider.return_value = None

            result = await service.analyze_feature(
                feature_request_id=42,
                title="Test Feature",
                description="Test description",
                force_refresh=True,
            )

            # Should fall back to heuristic analysis
            assert result["success"] is False
            assert "fallback_analysis" in result

    # ============== Fallback Analysis Tests ==============

    def test_fallback_analysis_security_keywords(self, service):
        """Test fallback analysis detects security keywords."""
        analysis = service._get_fallback_analysis(
            "Add authentication",
            "Need to implement login with password protection"
        )

        assert analysis["security_impact"] == ImpactLevel.MEDIUM.value

    def test_fallback_analysis_performance_keywords(self, service):
        """Test fallback analysis detects performance keywords."""
        analysis = service._get_fallback_analysis(
            "Optimize database",
            "Need to add caching for better performance"
        )

        assert analysis["performance_impact"] == ImpactLevel.MEDIUM.value

    def test_fallback_analysis_data_keywords(self, service):
        """Test fallback analysis detects data keywords."""
        analysis = service._get_fallback_analysis(
            "Database migration",
            "Need to add new columns to user table"
        )

        assert analysis["data_impact"] == ImpactLevel.MEDIUM.value

    def test_fallback_analysis_ui_keywords(self, service):
        """Test fallback analysis detects UI keywords."""
        analysis = service._get_fallback_analysis(
            "New dashboard",
            "Add a button to the form for filtering"
        )

        assert analysis["ux_impact"] == ImpactLevel.MEDIUM.value

    def test_fallback_analysis_no_keywords(self, service):
        """Test fallback analysis with no special keywords."""
        analysis = service._get_fallback_analysis(
            "Simple change",
            "Just a small update"
        )

        assert analysis["security_impact"] == ImpactLevel.LOW.value
        assert analysis["performance_impact"] == ImpactLevel.LOW.value
        assert analysis["data_impact"] == ImpactLevel.LOW.value
        assert analysis["ux_impact"] == ImpactLevel.LOW.value

    # ============== Response Parsing Tests ==============

    def test_parse_felix_response_valid_json(self, service):
        """Test parsing valid JSON response."""
        response = '''Here is my analysis:
        {
            "architecture_impact": "high",
            "security_impact": "medium",
            "performance_impact": "low",
            "ux_impact": "low",
            "data_impact": "none",
            "overall_impact": "medium",
            "risk_level": "medium",
            "complexity_score": 7,
            "affected_components": ["auth", "users"],
            "affected_apis": ["/api/login"],
            "dependencies": [],
            "breaking_changes": [],
            "implementation_approach": "Add OAuth2 provider",
            "recommended_priority": "P1",
            "estimated_effort_hours": 40,
            "warnings": [],
            "notes": "Standard OAuth implementation"
        }'''

        analysis = service._parse_felix_response(response)

        assert analysis["architecture_impact"] == "high"
        assert analysis["security_impact"] == "medium"
        assert analysis["complexity_score"] == 7
        assert len(analysis["affected_components"]) == 2

    def test_parse_felix_response_invalid_json(self, service):
        """Test parsing invalid JSON falls back to heuristics."""
        response = "This is not valid JSON at all"

        analysis = service._parse_felix_response(response)

        # Should return fallback analysis
        assert analysis["overall_impact"] == ImpactLevel.MEDIUM.value

    # ============== Cache Invalidation Tests ==============

    @pytest.mark.asyncio
    async def test_invalidate_cache(self, service, mock_db):
        """Test cache invalidation."""
        previews = [
            FeatureImpactPreview(id=uuid4(), is_stale=False),
            FeatureImpactPreview(id=uuid4(), is_stale=False),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = previews
        mock_db.execute = AsyncMock(return_value=mock_result)

        success = await service.invalidate_cache(42)

        assert success is True
        assert all(p.is_stale for p in previews)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_cache_no_previews(self, service, mock_db):
        """Test cache invalidation with no existing previews."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        success = await service.invalidate_cache(42)

        assert success is False

    # ============== Summary Tests ==============

    @pytest.mark.asyncio
    async def test_get_impact_summary(self, service, mock_db):
        """Test getting impact summary statistics."""
        previews = [
            FeatureImpactPreview(
                id=uuid4(),
                feature_request_id=1,
                overall_impact=ImpactLevel.HIGH.value,
                risk_level=RiskLevel.HIGH.value,
                complexity_score=8,
                breaking_changes=["API change"],
                created_at=datetime.now(timezone.utc),
            ),
            FeatureImpactPreview(
                id=uuid4(),
                feature_request_id=2,
                overall_impact=ImpactLevel.LOW.value,
                risk_level=RiskLevel.LOW.value,
                complexity_score=3,
                breaking_changes=[],
                created_at=datetime.now(timezone.utc),
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = previews
        mock_db.execute = AsyncMock(return_value=mock_result)

        summary = await service.get_impact_summary()

        assert summary["total_analyzed"] == 2
        assert summary["high_risk_count"] == 1
        assert summary["breaking_changes_count"] == 1
        assert summary["average_complexity"] == 5.5

    # ============== Model Helper Tests ==============

    def test_feature_impact_preview_has_breaking_changes(self):
        """Test has_breaking_changes helper."""
        preview_with = FeatureImpactPreview(breaking_changes=["API v1 deprecated"])
        preview_without = FeatureImpactPreview(breaking_changes=[])

        assert preview_with.has_breaking_changes() is True
        assert preview_without.has_breaking_changes() is False

    def test_feature_impact_preview_is_high_risk(self):
        """Test is_high_risk helper."""
        high_risk = FeatureImpactPreview(
            risk_level=RiskLevel.HIGH.value,
            overall_impact=ImpactLevel.MEDIUM.value,
        )
        high_impact = FeatureImpactPreview(
            risk_level=RiskLevel.LOW.value,
            overall_impact=ImpactLevel.CRITICAL.value,
        )
        low_risk = FeatureImpactPreview(
            risk_level=RiskLevel.LOW.value,
            overall_impact=ImpactLevel.LOW.value,
        )

        assert high_risk.is_high_risk() is True
        assert high_impact.is_high_risk() is True
        assert low_risk.is_high_risk() is False
