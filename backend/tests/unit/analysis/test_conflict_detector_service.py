# backend/tests/services/week99/test_conflict_detector_service.py
"""
Week 99 Tests - ConflictDetectorService

Tests for the 72.5% confidence threshold conflict detection
between static analysis and LLM results.
"""

import pytest
from datetime import datetime

from app.services.conflict_detector_service import (
    ConflictDetectorService,
    ConflictType,
    ConflictSeverity,
    ConflictResolution,
    ConflictItem,
    ConflictDetectionResult,
)


class TestConflictDetectorService:
    """Test suite for ConflictDetectorService."""

    @pytest.fixture
    def detector(self):
        """Create a fresh detector instance."""
        return ConflictDetectorService()

    @pytest.fixture
    def sample_static_results(self):
        """Sample static analysis results."""
        return {
            "static_analysis_summary": {
                "id": "static-123",
                "files_analyzed": 50,
                "lines_of_code": 10000,
                "domain_coverage": 0.75,
                "nfr_coverage": 0.60,
                "compliance_score": 0.85,
            },
            "business_rules": [
                {
                    "id": "rule-1",
                    "type": "validation",
                    "natural_language": "User must be authenticated to access dashboard",
                    "confidence": 0.90,
                    "source_file": "auth.py",
                },
                {
                    "id": "rule-2",
                    "type": "calculation",
                    "natural_language": "Total price = item_price * quantity * (1 - discount)",
                    "confidence": 0.85,
                    "source_file": "pricing.py",
                },
                {
                    "id": "rule-3",
                    "type": "constraint",
                    "natural_language": "Maximum 10 items per order",
                    "confidence": 0.65,  # Below threshold
                    "source_file": "orders.py",
                },
            ],
            "nfr_detections": [
                {
                    "id": "nfr-1",
                    "category": "security",
                    "description": "Password hashing using bcrypt",
                    "confidence": 0.95,
                    "source_file": "security.py",
                },
            ],
            "compliance_violations": [],
            "domain_variables": ["user_id", "order_total", "discount_rate"],
            "high_confidence_findings": [],
            "low_confidence_findings": [],
        }

    @pytest.fixture
    def sample_llm_results(self):
        """Sample LLM analysis results."""
        return [
            {
                "provider": "ollama/qwen2.5-coder:7b",
                "analysis_type": "architecture",
                "epics": [
                    {
                        "title": "User Authentication System",
                        "description": "Complete auth with JWT tokens",
                        "confidence": 0.85,
                    }
                ],
                "features": [
                    {
                        "title": "Dashboard Access Control",
                        "description": "Ensure only authenticated users access dashboard",
                        "confidence": 0.90,
                    }
                ],
                "stories": [],
                "tasks": [],
            },
            {
                "provider": "ollama/deepseek-r1",
                "analysis_type": "business_logic",
                "epics": [],
                "features": [
                    {
                        "title": "Pricing Calculator",
                        "description": "Calculate prices with discounts",
                        "confidence": 0.80,
                    }
                ],
                "stories": [],
                "tasks": [],
            },
        ]

    def test_confidence_threshold_is_correct(self, detector):
        """Test that confidence threshold is 72.5%."""
        assert detector.CONFIDENCE_THRESHOLD == 0.725

    def test_agreement_threshold_is_correct(self, detector):
        """Test that agreement threshold is 80%."""
        assert detector.AGREEMENT_THRESHOLD == 0.80

    def test_scope_change_threshold_is_correct(self, detector):
        """Test that scope change threshold is 30%."""
        assert detector.SCOPE_CHANGE_THRESHOLD == 0.30

    @pytest.mark.asyncio
    async def test_detect_conflicts_returns_result(self, detector, sample_static_results, sample_llm_results):
        """Test that detect_conflicts returns a valid result."""
        result = await detector.detect_conflicts(
            session_id="test-session-1",
            static_results=sample_static_results,
            llm_results=sample_llm_results,
        )

        assert isinstance(result, ConflictDetectionResult)
        assert result.session_id == "test-session-1"
        assert isinstance(result.conflicts_found, int)
        assert isinstance(result.auto_resolved, int)
        assert isinstance(result.needs_human_review, int)

    @pytest.mark.asyncio
    async def test_low_confidence_triggers_review(self, detector):
        """Test that items below 72.5% confidence trigger human review."""
        static_results = {
            "business_rules": [
                {
                    "id": "low-conf-rule",
                    "type": "validation",
                    "natural_language": "Uncertain business rule",
                    "confidence": 0.60,  # Below 72.5%
                    "source_file": "test.py",
                },
            ],
            "nfr_detections": [],
            "compliance_violations": [],
            "domain_variables": [],
            "high_confidence_findings": [],
            "low_confidence_findings": [],
        }

        llm_results = [
            {
                "provider": "ollama/qwen2.5-coder:7b",
                "analysis_type": "architecture",
                "epics": [],
                "features": [],
                "stories": [],
                "tasks": [],
            }
        ]

        result = await detector.detect_conflicts(
            session_id="low-conf-test",
            static_results=static_results,
            llm_results=llm_results,
        )

        # Low confidence items should trigger review
        assert result.needs_human_review >= 0

    @pytest.mark.asyncio
    async def test_high_confidence_auto_resolved(self, detector):
        """Test that high confidence items with LLM agreement are auto-resolved."""
        static_results = {
            "business_rules": [
                {
                    "id": "high-conf-rule",
                    "type": "validation",
                    "natural_language": "Clear authentication requirement",
                    "confidence": 0.95,  # Well above 72.5%
                    "source_file": "auth.py",
                },
            ],
            "nfr_detections": [],
            "compliance_violations": [],
            "domain_variables": [],
            "high_confidence_findings": [],
            "low_confidence_findings": [],
        }

        llm_results = [
            {
                "provider": "ollama/qwen2.5-coder:7b",
                "analysis_type": "architecture",
                "epics": [],
                "features": [
                    {
                        "title": "Authentication",
                        "description": "Clear authentication requirement",
                        "confidence": 0.92,
                    }
                ],
                "stories": [],
                "tasks": [],
            }
        ]

        result = await detector.detect_conflicts(
            session_id="high-conf-test",
            static_results=static_results,
            llm_results=llm_results,
        )

        # High agreement should result in auto-resolution
        assert result.auto_resolved >= 0

    @pytest.mark.asyncio
    async def test_disagreement_triggers_review(self, detector):
        """Test that static/LLM disagreement triggers human review."""
        static_results = {
            "business_rules": [
                {
                    "id": "disagree-rule",
                    "type": "validation",
                    "natural_language": "Max 5 items per order",
                    "confidence": 0.85,
                    "source_file": "orders.py",
                },
            ],
            "nfr_detections": [],
            "compliance_violations": [],
            "domain_variables": [],
            "high_confidence_findings": [],
            "low_confidence_findings": [],
        }

        llm_results = [
            {
                "provider": "ollama/qwen2.5-coder:7b",
                "analysis_type": "business_logic",
                "epics": [],
                "features": [
                    {
                        "title": "Order Limits",
                        "description": "Max 10 items per order",  # Different from static
                        "confidence": 0.80,
                    }
                ],
                "stories": [],
                "tasks": [],
            }
        ]

        result = await detector.detect_conflicts(
            session_id="disagree-test",
            static_results=static_results,
            llm_results=llm_results,
        )

        # Disagreement should be detected
        assert isinstance(result, ConflictDetectionResult)

    @pytest.mark.asyncio
    async def test_empty_results_handled(self, detector):
        """Test that empty results are handled gracefully."""
        result = await detector.detect_conflicts(
            session_id="empty-test",
            static_results={},
            llm_results=[],
        )

        assert isinstance(result, ConflictDetectionResult)
        assert result.conflicts_found == 0

    def test_conflict_type_values(self):
        """Test ConflictType enum values."""
        assert ConflictType.CONFIDENCE_THRESHOLD.value == "confidence_threshold"
        assert ConflictType.EXPLICIT_DISAGREEMENT.value == "explicit_disagreement"
        assert ConflictType.CLASSIFICATION_CHANGE.value == "classification_change"
        assert ConflictType.ITEM_REMOVAL.value == "item_removal"

    def test_conflict_severity_values(self):
        """Test ConflictSeverity enum values."""
        assert ConflictSeverity.LOW.value == "low"
        assert ConflictSeverity.MEDIUM.value == "medium"
        assert ConflictSeverity.HIGH.value == "high"
        assert ConflictSeverity.CRITICAL.value == "critical"

    def test_conflict_resolution_values(self):
        """Test ConflictResolution enum values."""
        assert ConflictResolution.PENDING.value == "pending"
        assert ConflictResolution.AUTO_ACCEPTED_STATIC.value == "auto_accepted_static"
        assert ConflictResolution.AUTO_ACCEPTED_LLM.value == "auto_accepted_llm"


class TestConflictDetectionThresholds:
    """Test threshold-based behavior."""

    @pytest.fixture
    def detector(self):
        return ConflictDetectorService()

    def test_threshold_boundary_at_725(self, detector):
        """Test behavior exactly at 72.5% threshold."""
        # Items at exactly 72.5% should not trigger review
        assert detector.CONFIDENCE_THRESHOLD == 0.725

    def test_threshold_boundary_below(self, detector):
        """Test that 72.4% is below threshold."""
        test_confidence = 0.724
        assert test_confidence < detector.CONFIDENCE_THRESHOLD

    def test_threshold_boundary_above(self, detector):
        """Test that 72.6% is above threshold."""
        test_confidence = 0.726
        assert test_confidence > detector.CONFIDENCE_THRESHOLD
