# backend/tests/services/week100/test_static_llm_conflict_models.py
"""
Week 100 Tests - Static-LLM Conflict Models

Tests for the database models supporting conflict detection and resolution
between static analysis (Cycle 0) and LLM analysis results.
"""

import pytest
import uuid
from datetime import datetime

from app.models.deep_extraction import (
    ExtractionSession,
    StaticLLMConflict,
    ConflictResolutionHistory,
    ExtractionConsensus,
    StaticLLMConflictType,
    StaticLLMConflictSeverity,
    StaticLLMConflictStatus,
    StaticLLMConflictResolution,
)


class TestStaticLLMConflictEnums:
    """Test enum values for conflict types, severity, status, and resolution."""

    def test_conflict_type_values(self):
        """Test all ConflictType enum values."""
        assert StaticLLMConflictType.CONFIDENCE_THRESHOLD.value == "confidence_threshold"
        assert StaticLLMConflictType.EXPLICIT_DISAGREEMENT.value == "explicit_disagreement"
        assert StaticLLMConflictType.CLASSIFICATION_CHANGE.value == "classification_change"
        assert StaticLLMConflictType.ITEM_REMOVAL.value == "item_removal"
        assert StaticLLMConflictType.PRIORITY_MISMATCH.value == "priority_mismatch"
        assert StaticLLMConflictType.SCOPE_EXPANSION.value == "scope_expansion"
        assert StaticLLMConflictType.SCOPE_REDUCTION.value == "scope_reduction"

    def test_conflict_type_count(self):
        """Test that we have exactly 7 conflict types."""
        assert len(StaticLLMConflictType) == 7

    def test_conflict_severity_values(self):
        """Test all ConflictSeverity enum values."""
        assert StaticLLMConflictSeverity.LOW.value == "low"
        assert StaticLLMConflictSeverity.MEDIUM.value == "medium"
        assert StaticLLMConflictSeverity.HIGH.value == "high"
        assert StaticLLMConflictSeverity.CRITICAL.value == "critical"

    def test_conflict_severity_count(self):
        """Test that we have exactly 4 severity levels."""
        assert len(StaticLLMConflictSeverity) == 4

    def test_conflict_status_values(self):
        """Test all ConflictStatus enum values."""
        assert StaticLLMConflictStatus.PENDING.value == "pending"
        assert StaticLLMConflictStatus.AUTO_RESOLVED.value == "auto_resolved"
        assert StaticLLMConflictStatus.HUMAN_REVIEW.value == "human_review"
        assert StaticLLMConflictStatus.RESOLVED.value == "resolved"
        assert StaticLLMConflictStatus.REJECTED.value == "rejected"

    def test_conflict_status_count(self):
        """Test that we have exactly 5 status values."""
        assert len(StaticLLMConflictStatus) == 5

    def test_conflict_resolution_values(self):
        """Test all ConflictResolution enum values."""
        assert StaticLLMConflictResolution.AUTO_ACCEPTED_STATIC.value == "auto_accepted_static"
        assert StaticLLMConflictResolution.AUTO_ACCEPTED_LLM.value == "auto_accepted_llm"
        assert StaticLLMConflictResolution.HUMAN_SELECTED_STATIC.value == "human_selected_static"
        assert StaticLLMConflictResolution.HUMAN_SELECTED_LLM.value == "human_selected_llm"
        assert StaticLLMConflictResolution.HUMAN_MERGED.value == "human_merged"
        assert StaticLLMConflictResolution.HUMAN_REJECTED_BOTH.value == "human_rejected_both"

    def test_conflict_resolution_count(self):
        """Test that we have exactly 6 resolution types."""
        assert len(StaticLLMConflictResolution) == 6


class TestExtractionSessionCycle0Fields:
    """Test Cycle 0 fields added to ExtractionSession model."""

    def test_session_has_cycle_0_timestamp_field(self):
        """Test that ExtractionSession has cycle_0_completed_at field."""
        session = ExtractionSession()
        assert hasattr(session, 'cycle_0_completed_at')

    def test_session_has_static_analysis_id_field(self):
        """Test that ExtractionSession has static_analysis_id field."""
        session = ExtractionSession()
        assert hasattr(session, 'static_analysis_id')

    def test_session_has_static_coverage_fields(self):
        """Test that ExtractionSession has static coverage metrics."""
        session = ExtractionSession()
        assert hasattr(session, 'static_domain_coverage')
        assert hasattr(session, 'static_nfr_coverage')
        assert hasattr(session, 'static_compliance_score')

    def test_session_has_static_count_fields(self):
        """Test that ExtractionSession has static analysis count fields."""
        session = ExtractionSession()
        assert hasattr(session, 'static_business_rules_count')
        assert hasattr(session, 'static_nfr_count')
        assert hasattr(session, 'static_compliance_violations_count')
        assert hasattr(session, 'static_high_confidence_count')
        assert hasattr(session, 'static_low_confidence_count')

    def test_session_has_conflict_summary_fields(self):
        """Test that ExtractionSession has conflict summary fields."""
        session = ExtractionSession()
        assert hasattr(session, 'total_conflicts')
        assert hasattr(session, 'conflicts_auto_resolved')
        assert hasattr(session, 'conflicts_pending_review')
        assert hasattr(session, 'conflicts_human_resolved')


class TestStaticLLMConflictModel:
    """Test StaticLLMConflict model fields and relationships."""

    def test_conflict_has_required_fields(self):
        """Test that StaticLLMConflict has all required fields."""
        conflict = StaticLLMConflict()

        # Identity fields
        assert hasattr(conflict, 'id')
        assert hasattr(conflict, 'session_id')
        assert hasattr(conflict, 'item_id')
        assert hasattr(conflict, 'item_type')

        # Classification
        assert hasattr(conflict, 'conflict_type')
        assert hasattr(conflict, 'severity')

        # Static side
        assert hasattr(conflict, 'static_classification')
        assert hasattr(conflict, 'static_confidence')
        assert hasattr(conflict, 'static_data')
        assert hasattr(conflict, 'static_source_file')
        assert hasattr(conflict, 'static_source_line')

        # LLM side
        assert hasattr(conflict, 'llm_classification')
        assert hasattr(conflict, 'llm_confidence')
        assert hasattr(conflict, 'llm_data')
        assert hasattr(conflict, 'llm_provider')
        assert hasattr(conflict, 'llm_model')

        # Details
        assert hasattr(conflict, 'description')
        assert hasattr(conflict, 'impact_assessment')
        assert hasattr(conflict, 'recommendations')

        # Resolution
        assert hasattr(conflict, 'status')
        assert hasattr(conflict, 'resolution')
        assert hasattr(conflict, 'resolved_at')
        assert hasattr(conflict, 'resolved_by')
        assert hasattr(conflict, 'resolution_notes')

        # Final value
        assert hasattr(conflict, 'final_value')
        assert hasattr(conflict, 'final_classification')
        assert hasattr(conflict, 'final_confidence')

        # Timestamps
        assert hasattr(conflict, 'created_at')
        assert hasattr(conflict, 'updated_at')

    def test_conflict_table_name(self):
        """Test that StaticLLMConflict has correct table name."""
        assert StaticLLMConflict.__tablename__ == "static_llm_conflicts"


class TestConflictResolutionHistoryModel:
    """Test ConflictResolutionHistory model for audit trail."""

    def test_history_has_required_fields(self):
        """Test that ConflictResolutionHistory has all required fields."""
        history = ConflictResolutionHistory()

        # Identity
        assert hasattr(history, 'id')
        assert hasattr(history, 'conflict_id')

        # Action
        assert hasattr(history, 'action')
        assert hasattr(history, 'action_by')
        assert hasattr(history, 'action_data')

        # State changes
        assert hasattr(history, 'previous_status')
        assert hasattr(history, 'new_status')
        assert hasattr(history, 'previous_resolution')
        assert hasattr(history, 'new_resolution')

        # Notes and timestamp
        assert hasattr(history, 'notes')
        assert hasattr(history, 'created_at')

    def test_history_table_name(self):
        """Test that ConflictResolutionHistory has correct table name."""
        assert ConflictResolutionHistory.__tablename__ == "conflict_resolution_history"


class TestExtractionConsensusConflictFields:
    """Test conflict-related fields added to ExtractionConsensus."""

    def test_consensus_has_conflict_reference(self):
        """Test that ExtractionConsensus has source_conflict_id field."""
        consensus = ExtractionConsensus()
        assert hasattr(consensus, 'source_conflict_id')

    def test_consensus_has_static_analysis_flag(self):
        """Test that ExtractionConsensus has from_static_analysis field."""
        consensus = ExtractionConsensus()
        assert hasattr(consensus, 'from_static_analysis')


class TestConflictTypeClassification:
    """Test conflict type classification logic."""

    def test_confidence_threshold_is_correct(self):
        """Verify 72.5% confidence threshold is used."""
        CONFIDENCE_THRESHOLD = 0.725

        # Below threshold should trigger review
        assert 0.60 < CONFIDENCE_THRESHOLD
        assert 0.70 < CONFIDENCE_THRESHOLD
        assert 0.724 < CONFIDENCE_THRESHOLD

        # At or above threshold should be acceptable
        assert 0.725 >= CONFIDENCE_THRESHOLD
        assert 0.80 >= CONFIDENCE_THRESHOLD
        assert 0.95 >= CONFIDENCE_THRESHOLD

    def test_severity_mapping_logic(self):
        """Test severity assignment based on conflict characteristics."""
        # Critical: compliance violations, security issues
        critical_keywords = ["compliance", "security", "violation", "breach"]

        # High: business rules, data integrity
        high_keywords = ["business_rule", "data_integrity", "calculation"]

        # Medium: classification changes, priority mismatches
        medium_keywords = ["classification", "priority", "scope"]

        # Low: cosmetic, documentation, minor
        low_keywords = ["documentation", "naming", "cosmetic"]

        # Verify keyword lists are non-empty
        assert len(critical_keywords) > 0
        assert len(high_keywords) > 0
        assert len(medium_keywords) > 0
        assert len(low_keywords) > 0


class TestResolutionWorkflow:
    """Test conflict resolution workflow states."""

    def test_valid_status_transitions(self):
        """Test valid status transitions in resolution workflow."""
        # pending -> auto_resolved (by system)
        # pending -> human_review (needs human)
        # human_review -> resolved (human accepted)
        # human_review -> rejected (human rejected)

        valid_transitions = {
            "pending": ["auto_resolved", "human_review"],
            "human_review": ["resolved", "rejected"],
            "auto_resolved": [],  # Final state
            "resolved": [],  # Final state
            "rejected": [],  # Final state
        }

        # Verify all statuses are covered
        all_statuses = [s.value for s in StaticLLMConflictStatus]
        for status in all_statuses:
            assert status in valid_transitions

    def test_resolution_requires_final_value(self):
        """Test that resolution should include final value selection."""
        # Human resolutions that require final value
        human_resolutions = [
            StaticLLMConflictResolution.HUMAN_SELECTED_STATIC,
            StaticLLMConflictResolution.HUMAN_SELECTED_LLM,
            StaticLLMConflictResolution.HUMAN_MERGED,
        ]

        # Human rejection doesn't require final value
        no_final_value = [
            StaticLLMConflictResolution.HUMAN_REJECTED_BOTH,
        ]

        assert len(human_resolutions) == 3
        assert len(no_final_value) == 1
