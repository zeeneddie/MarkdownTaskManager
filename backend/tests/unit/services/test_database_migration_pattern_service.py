"""
Unit tests for DatabaseMigrationPatternService - D4 (Fase 24 GAP).

Tests cover:
- Pattern catalog initialization
- Pattern retrieval (get_pattern, list_patterns)
- Scenario-based pattern filtering
- Pattern recommendations
- Risk assessments
- Pattern summaries

Author: Claude Code (Week 159)
Date: 2026-01-24
"""

import pytest
from datetime import datetime

from app.services.database_migration_pattern_service import (
    DatabaseMigrationPatternService,
    MigrationPatternType,
    DataVolumeCategory,
    DowntimeRequirement,
    RiskLevel,
    MigrationPattern,
    PatternRecommendation,
    PatternRiskAssessment,
)


# ==================== Fixtures ====================

@pytest.fixture
def service():
    """Create a fresh DatabaseMigrationPatternService instance."""
    return DatabaseMigrationPatternService()


# ==================== Catalog Initialization Tests ====================

class TestCatalogInitialization:
    """Tests for pattern catalog initialization."""

    def test_service_initializes_with_patterns(self, service):
        """Service should initialize with all expected patterns."""
        patterns = service.list_patterns()
        assert len(patterns) == 8

        # Verify all expected pattern types exist
        pattern_types = {p.pattern_type for p in patterns}
        expected_types = {
            MigrationPatternType.DUAL_WRITE,
            MigrationPatternType.CDC_SYNC,
            MigrationPatternType.BULK_LOAD,
            MigrationPatternType.SHADOW_TABLE,
            MigrationPatternType.BLUE_GREEN,
            MigrationPatternType.TRICKLE_MIGRATION,
            MigrationPatternType.STRANGLER_FIG,
            MigrationPatternType.EXPAND_CONTRACT,
        }
        assert pattern_types == expected_types

    def test_all_patterns_have_required_fields(self, service):
        """All patterns should have all required fields populated."""
        for pattern in service.list_patterns():
            assert pattern.name, f"Pattern {pattern.pattern_type} missing name"
            assert pattern.description, f"Pattern {pattern.pattern_type} missing description"
            assert len(pattern.suitable_data_volumes) > 0
            assert len(pattern.suitable_downtime_requirements) > 0
            assert len(pattern.suitable_scenarios) > 0
            assert len(pattern.prerequisites) > 0
            assert len(pattern.phases) > 0
            assert len(pattern.risks) > 0
            assert 1 <= pattern.complexity_score <= 10
            assert pattern.recommended_team_size >= 1
            assert pattern.typical_duration_weeks > 0


# ==================== Pattern Retrieval Tests ====================

class TestPatternRetrieval:
    """Tests for pattern retrieval methods."""

    def test_get_pattern_by_type(self, service):
        """Should retrieve specific pattern by type."""
        pattern = service.get_pattern(MigrationPatternType.DUAL_WRITE)

        assert pattern is not None
        assert pattern.pattern_type == MigrationPatternType.DUAL_WRITE
        assert pattern.name == "Dual Write Pattern"
        assert "both" in pattern.description.lower() or "simultaneously" in pattern.description.lower()

    def test_get_nonexistent_pattern(self, service):
        """Should return None for invalid pattern type."""
        # Note: This can't actually happen with enum, but test the behavior
        result = service._patterns.get("nonexistent")
        assert result is None

    def test_list_patterns_returns_all(self, service):
        """list_patterns should return all catalog patterns."""
        patterns = service.list_patterns()

        assert len(patterns) == 8
        assert all(isinstance(p, MigrationPattern) for p in patterns)

    def test_cdc_pattern_details(self, service):
        """CDC pattern should have correct configuration."""
        pattern = service.get_pattern(MigrationPatternType.CDC_SYNC)

        assert pattern is not None
        assert "Change Data Capture" in pattern.name
        assert DataVolumeCategory.LARGE in pattern.suitable_data_volumes
        assert DataVolumeCategory.VERY_LARGE in pattern.suitable_data_volumes
        assert DowntimeRequirement.ZERO in pattern.suitable_downtime_requirements
        assert "Debezium" in pattern.tools_supported

    def test_bulk_load_pattern_details(self, service):
        """Bulk load pattern should have correct configuration."""
        pattern = service.get_pattern(MigrationPatternType.BULK_LOAD)

        assert pattern is not None
        assert pattern.complexity_score <= 5  # Should be simpler than others
        assert DowntimeRequirement.EXTENDED in pattern.suitable_downtime_requirements
        # Bulk load typically needs downtime
        assert DowntimeRequirement.ZERO not in pattern.suitable_downtime_requirements


# ==================== Scenario Filtering Tests ====================

class TestScenarioFiltering:
    """Tests for scenario-based pattern filtering."""

    def test_filter_by_data_volume_small(self, service):
        """Should return patterns suitable for small data volumes."""
        patterns = service.get_patterns_for_scenario(
            data_volume=DataVolumeCategory.SMALL,
            downtime_requirement=DowntimeRequirement.MINIMAL
        )

        assert len(patterns) > 0
        for p in patterns:
            assert DataVolumeCategory.SMALL in p.suitable_data_volumes

    def test_filter_by_data_volume_very_large(self, service):
        """Should return patterns suitable for very large data volumes."""
        patterns = service.get_patterns_for_scenario(
            data_volume=DataVolumeCategory.VERY_LARGE,
            downtime_requirement=DowntimeRequirement.ZERO
        )

        assert len(patterns) > 0
        for p in patterns:
            assert DataVolumeCategory.VERY_LARGE in p.suitable_data_volumes
            assert DowntimeRequirement.ZERO in p.suitable_downtime_requirements

    def test_filter_by_zero_downtime(self, service):
        """Should only return zero-downtime patterns when required."""
        patterns = service.get_patterns_for_scenario(
            data_volume=DataVolumeCategory.MEDIUM,
            downtime_requirement=DowntimeRequirement.ZERO
        )

        for p in patterns:
            assert DowntimeRequirement.ZERO in p.suitable_downtime_requirements

    def test_filter_with_keywords(self, service):
        """Should filter patterns by scenario keywords."""
        patterns = service.get_patterns_for_scenario(
            data_volume=DataVolumeCategory.MEDIUM,
            downtime_requirement=DowntimeRequirement.MINIMAL,
            scenario_keywords=["gradual", "rollback"]
        )

        # Should include patterns mentioning gradual migration or rollback
        assert len(patterns) > 0

    def test_filter_returns_sorted_by_complexity(self, service):
        """Returned patterns should be sorted by complexity (ascending)."""
        patterns = service.get_patterns_for_scenario(
            data_volume=DataVolumeCategory.MEDIUM,
            downtime_requirement=DowntimeRequirement.MINIMAL
        )

        complexities = [p.complexity_score for p in patterns]
        assert complexities == sorted(complexities)


# ==================== Recommendation Tests ====================

class TestPatternRecommendation:
    """Tests for pattern recommendation engine."""

    def test_recommend_returns_all_patterns_scored(self, service):
        """Recommend should return scored recommendations for all patterns."""
        recommendations = service.recommend_pattern(
            data_volume=DataVolumeCategory.MEDIUM,
            downtime_requirement=DowntimeRequirement.MINIMAL,
            scenario_description="Migrate legacy Oracle database to PostgreSQL"
        )

        assert len(recommendations) == 8
        assert all(isinstance(r, PatternRecommendation) for r in recommendations)
        assert all(0 <= r.score <= 100 for r in recommendations)

    def test_recommend_sorted_by_score_descending(self, service):
        """Recommendations should be sorted by score (highest first)."""
        recommendations = service.recommend_pattern(
            data_volume=DataVolumeCategory.MEDIUM,
            downtime_requirement=DowntimeRequirement.MINIMAL,
            scenario_description="Real-time data sync"
        )

        scores = [r.score for r in recommendations]
        assert scores == sorted(scores, reverse=True)

    def test_recommend_with_database_types(self, service):
        """Should consider database type compatibility."""
        recommendations = service.recommend_pattern(
            data_volume=DataVolumeCategory.LARGE,
            downtime_requirement=DowntimeRequirement.ZERO,
            scenario_description="Database migration",
            source_db_type="Oracle",
            target_db_type="PostgreSQL"
        )

        # CDC should score well for Oracle to PostgreSQL
        cdc_rec = next(
            r for r in recommendations
            if r.pattern.pattern_type == MigrationPatternType.CDC_SYNC
        )
        assert cdc_rec.score > 50  # Should have decent score

    def test_recommend_with_team_size(self, service):
        """Should consider team size in recommendations."""
        # Large team - complex patterns more viable
        large_team_recs = service.recommend_pattern(
            data_volume=DataVolumeCategory.LARGE,
            downtime_requirement=DowntimeRequirement.ZERO,
            scenario_description="Platform migration",
            team_size=10
        )

        # Small team - simpler patterns preferred
        small_team_recs = service.recommend_pattern(
            data_volume=DataVolumeCategory.LARGE,
            downtime_requirement=DowntimeRequirement.ZERO,
            scenario_description="Platform migration",
            team_size=2
        )

        # Verify recommendations include reasons about team size
        large_rec = large_team_recs[0]
        small_rec = small_team_recs[0]

        # At least one should mention team size
        all_reasons = large_rec.reasons + large_rec.warnings + small_rec.reasons + small_rec.warnings
        team_mentioned = any("team" in r.lower() for r in all_reasons)
        assert team_mentioned

    def test_recommend_with_duration_constraint(self, service):
        """Should warn when duration exceeds limit."""
        recommendations = service.recommend_pattern(
            data_volume=DataVolumeCategory.LARGE,
            downtime_requirement=DowntimeRequirement.ZERO,
            scenario_description="Quick migration needed",
            max_duration_weeks=2.0
        )

        # Strangler Fig takes 24 weeks, should have warning
        strangler_rec = next(
            r for r in recommendations
            if r.pattern.pattern_type == MigrationPatternType.STRANGLER_FIG
        )

        assert any("duration" in w.lower() or "weeks" in w.lower() for w in strangler_rec.warnings)

    def test_recommend_includes_reasons(self, service):
        """Recommendations should include explanatory reasons."""
        recommendations = service.recommend_pattern(
            data_volume=DataVolumeCategory.MEDIUM,
            downtime_requirement=DowntimeRequirement.MINIMAL,
            scenario_description="Migrate database with CDC"
        )

        # Top recommendation should have reasons
        top_rec = recommendations[0]
        assert len(top_rec.reasons) > 0

    def test_recommend_includes_alternatives(self, service):
        """Recommendations should include alternative patterns."""
        recommendations = service.recommend_pattern(
            data_volume=DataVolumeCategory.MEDIUM,
            downtime_requirement=DowntimeRequirement.ZERO,
            scenario_description="Database migration"
        )

        # Most patterns have related patterns as alternatives
        has_alternatives = any(len(r.alternatives) > 0 for r in recommendations)
        assert has_alternatives


# ==================== Risk Assessment Tests ====================

class TestRiskAssessment:
    """Tests for pattern risk assessment."""

    def test_assess_risk_returns_assessment(self, service):
        """Should return risk assessment for valid pattern."""
        assessment = service.assess_pattern_risk(
            pattern_type=MigrationPatternType.DUAL_WRITE,
            data_volume=DataVolumeCategory.MEDIUM,
            has_downtime_window=True,
            team_experience_level="senior"
        )

        assert assessment is not None
        assert isinstance(assessment, PatternRiskAssessment)
        assert assessment.pattern_type == MigrationPatternType.DUAL_WRITE
        assert 0 <= assessment.risk_score <= 100
        assert assessment.overall_risk_level in RiskLevel
        assert assessment.go_no_go_recommendation in ["GO", "GO_WITH_CAUTION", "NO_GO"]

    def test_assess_risk_higher_for_junior_team(self, service):
        """Junior team should have higher risk score."""
        junior_assessment = service.assess_pattern_risk(
            pattern_type=MigrationPatternType.BLUE_GREEN,
            data_volume=DataVolumeCategory.LARGE,
            has_downtime_window=False,
            team_experience_level="junior"
        )

        senior_assessment = service.assess_pattern_risk(
            pattern_type=MigrationPatternType.BLUE_GREEN,
            data_volume=DataVolumeCategory.LARGE,
            has_downtime_window=False,
            team_experience_level="senior"
        )

        assert junior_assessment.risk_score > senior_assessment.risk_score

    def test_assess_risk_higher_for_very_large_data(self, service):
        """Very large data should increase risk score."""
        small_data = service.assess_pattern_risk(
            pattern_type=MigrationPatternType.CDC_SYNC,
            data_volume=DataVolumeCategory.SMALL,
            has_downtime_window=True,
            team_experience_level="senior"
        )

        very_large_data = service.assess_pattern_risk(
            pattern_type=MigrationPatternType.CDC_SYNC,
            data_volume=DataVolumeCategory.VERY_LARGE,
            has_downtime_window=True,
            team_experience_level="senior"
        )

        assert very_large_data.risk_score > small_data.risk_score

    def test_assess_risk_critical_data_requires_mitigations(self, service):
        """Critical data should require additional mitigations."""
        assessment = service.assess_pattern_risk(
            pattern_type=MigrationPatternType.BULK_LOAD,
            data_volume=DataVolumeCategory.MEDIUM,
            has_downtime_window=True,
            team_experience_level="mid",
            critical_data=True
        )

        # Should require backup and dry-run mitigations
        mitigations_text = " ".join(assessment.mitigations_required).lower()
        assert "backup" in mitigations_text or "rollback" in mitigations_text

    def test_assess_risk_regulatory_requirements(self, service):
        """Regulatory requirements should require audit mitigations."""
        assessment = service.assess_pattern_risk(
            pattern_type=MigrationPatternType.TRICKLE_MIGRATION,
            data_volume=DataVolumeCategory.LARGE,
            has_downtime_window=False,
            team_experience_level="senior",
            regulatory_requirements=True
        )

        mitigations_text = " ".join(assessment.mitigations_required).lower()
        assert "audit" in mitigations_text or "compliance" in mitigations_text or "document" in mitigations_text

    def test_assess_risk_no_downtime_window_warns(self, service):
        """No downtime window should increase risk for patterns requiring it."""
        # Bulk load requires downtime
        assessment = service.assess_pattern_risk(
            pattern_type=MigrationPatternType.BULK_LOAD,
            data_volume=DataVolumeCategory.MEDIUM,
            has_downtime_window=False,
            team_experience_level="senior"
        )

        # Should have higher risk or warning about downtime
        assert assessment.risk_score >= 25 or len(assessment.mitigations_required) > 0

    def test_assess_risk_go_recommendation_for_low_risk(self, service):
        """Low risk scenarios should get GO recommendation."""
        assessment = service.assess_pattern_risk(
            pattern_type=MigrationPatternType.EXPAND_CONTRACT,
            data_volume=DataVolumeCategory.SMALL,
            has_downtime_window=True,
            team_experience_level="expert",
            critical_data=False,
            regulatory_requirements=False
        )

        assert assessment.go_no_go_recommendation == "GO"
        assert assessment.overall_risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]

    def test_assess_risk_includes_pattern_risks(self, service):
        """Assessment should include pattern's inherent risks."""
        assessment = service.assess_pattern_risk(
            pattern_type=MigrationPatternType.DUAL_WRITE,
            data_volume=DataVolumeCategory.MEDIUM,
            has_downtime_window=True,
            team_experience_level="senior"
        )

        # Dual write has data inconsistency risk
        risk_names = [r.name.lower() for r in assessment.identified_risks]
        assert any("inconsisten" in name or "complexity" in name for name in risk_names)


# ==================== Summary Tests ====================

class TestPatternSummary:
    """Tests for pattern summary generation."""

    def test_summary_contains_all_patterns(self, service):
        """Summary should include all patterns."""
        summary = service.get_pattern_summary()

        assert summary["total_patterns"] == 8
        assert len(summary["patterns"]) == 8

    def test_summary_includes_statistics(self, service):
        """Summary should include complexity statistics."""
        summary = service.get_pattern_summary()

        assert "complexity_range" in summary
        assert "min" in summary["complexity_range"]
        assert "max" in summary["complexity_range"]
        assert "avg" in summary["complexity_range"]

        # Verify range is sensible
        assert 1 <= summary["complexity_range"]["min"] <= 10
        assert 1 <= summary["complexity_range"]["max"] <= 10
        assert summary["complexity_range"]["min"] <= summary["complexity_range"]["avg"]
        assert summary["complexity_range"]["avg"] <= summary["complexity_range"]["max"]

    def test_summary_counts_zero_downtime_patterns(self, service):
        """Summary should count zero-downtime capable patterns."""
        summary = service.get_pattern_summary()

        assert "zero_downtime_patterns" in summary
        assert summary["zero_downtime_patterns"] > 0
        assert summary["zero_downtime_patterns"] <= summary["total_patterns"]

    def test_summary_pattern_info(self, service):
        """Each pattern summary should have key info."""
        summary = service.get_pattern_summary()

        for pattern_info in summary["patterns"]:
            assert "type" in pattern_info
            assert "name" in pattern_info
            assert "complexity" in pattern_info
            assert "typical_weeks" in pattern_info
            assert "team_size" in pattern_info
            assert "zero_downtime" in pattern_info
            assert "risk_count" in pattern_info


# ==================== Pattern Content Tests ====================

class TestPatternContent:
    """Tests for specific pattern content validation."""

    def test_dual_write_phases(self, service):
        """Dual write should have proper phase sequence."""
        pattern = service.get_pattern(MigrationPatternType.DUAL_WRITE)

        phase_names = [p.name.lower() for p in pattern.phases]
        assert "setup" in phase_names
        assert "cutover" in phase_names or "switch" in " ".join(phase_names)

    def test_cdc_supports_major_databases(self, service):
        """CDC should support major database types."""
        pattern = service.get_pattern(MigrationPatternType.CDC_SYNC)

        supported = " ".join(pattern.database_types_supported).lower()
        assert "postgresql" in supported
        assert "mysql" in supported
        assert "oracle" in supported

    def test_strangler_fig_longest_duration(self, service):
        """Strangler fig should have longest typical duration."""
        patterns = service.list_patterns()

        strangler = service.get_pattern(MigrationPatternType.STRANGLER_FIG)
        max_duration = max(p.typical_duration_weeks for p in patterns)

        assert strangler.typical_duration_weeks == max_duration

    def test_bulk_load_lowest_complexity(self, service):
        """Bulk load should have lowest/equal lowest complexity."""
        patterns = service.list_patterns()

        bulk = service.get_pattern(MigrationPatternType.BULK_LOAD)
        min_complexity = min(p.complexity_score for p in patterns)

        assert bulk.complexity_score == min_complexity

    def test_all_patterns_have_mitigations(self, service):
        """All pattern risks should have mitigations."""
        for pattern in service.list_patterns():
            for risk in pattern.risks:
                assert risk.mitigation, f"Risk '{risk.name}' in {pattern.name} lacks mitigation"
                assert len(risk.mitigation) > 10, f"Mitigation for '{risk.name}' too short"
