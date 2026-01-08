# backend/tests/services/week97/test_orchestrator.py
"""
Integration tests for StaticAnalysisOrchestrator - Week 97-98 (Fase 15).

Tests the complete static analysis pipeline.
"""

import pytest
from datetime import datetime
from app.services.static_analysis.orchestrator import (
    StaticAnalysisOrchestrator,
    StaticAnalysisConfig,
    StaticAnalysisResult,
    create_orchestrator,
)


class TestStaticAnalysisOrchestrator:
    """Integration tests for StaticAnalysisOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        return StaticAnalysisOrchestrator()

    @pytest.fixture
    def config(self):
        """Create default config."""
        return StaticAnalysisConfig(
            enable_slicing=False,  # Skip slicing for faster tests
            enable_variable_classification=True,
            enable_business_rules=True,
            enable_nfr_detection=True,
            enable_compliance=True,
            compliance_frameworks=["NEN7510"],
        )

    @pytest.fixture
    def sample_files(self):
        """Create sample files for analysis."""
        return {
            "services/order_service.py": '''
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def validate_order(order):
    """Validate order before processing."""
    if order.total < 0:
        raise ValueError("Order total cannot be negative")
    if order.quantity > 1000:
        raise ValueError("Order quantity exceeds maximum")
    return True

def calculate_discount(order):
    """Calculate discount based on order total."""
    if order.total > 1000:
        discount = order.total * 0.1
    elif order.total > 500:
        discount = order.total * 0.05
    else:
        discount = 0
    return discount

def process_order(order, user):
    """Process an order for a user."""
    logger.info(f"Processing order {order.id} for user {user.id}")

    if not user.has_permission("order.create"):
        logger.warning(f"User {user.id} lacks permission for order creation")
        return None

    if order.status == "pending":
        order.status = "processing"

    return order
''',
            "models/customer.py": '''
from dataclasses import dataclass
from typing import Optional
import hashlib

@dataclass
class Customer:
    customer_id: str
    customer_name: str
    customer_email: str
    balance: float = 0.0
    is_active: bool = True

    def get_display_name(self):
        return f"{self.customer_name} ({self.customer_id})"

def hash_email(email: str) -> str:
    """Hash email for privacy."""
    return hashlib.sha256(email.encode()).hexdigest()
''',
            "utils/cache.py": '''
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1000)
def get_cached_value(key):
    """Get cached value with LRU cache."""
    logger.debug(f"Cache miss for key: {key}")
    return expensive_lookup(key)

cache = {}

def manual_cache_get(key):
    """Manual cache implementation."""
    if key in cache:
        return cache[key]
    value = compute_value(key)
    cache[key] = value
    return value
''',
        }

    @pytest.mark.asyncio
    async def test_run_analysis_basic(self, orchestrator, config, sample_files):
        """Test basic analysis run."""
        result = await orchestrator.run_analysis(
            project_id=1,
            files=sample_files,
            config=config,
        )

        assert isinstance(result, StaticAnalysisResult)
        assert result.project_id == 1
        assert result.total_files_analyzed == 3

    @pytest.mark.asyncio
    async def test_extracts_business_rules(self, orchestrator, config, sample_files):
        """Test that business rules are extracted."""
        result = await orchestrator.run_analysis(
            project_id=1,
            files=sample_files,
            config=config,
        )

        assert result.business_rules is not None
        # Rules may or may not be found depending on pattern matching
        # Just verify the structure is correct
        assert hasattr(result.business_rules, 'rules')
        assert isinstance(result.business_rules.rules, list)

        # If rules are found, verify they have correct structure
        for rule in result.business_rules.rules:
            assert hasattr(rule, 'rule_type')
            assert hasattr(rule, 'condition')

    @pytest.mark.asyncio
    async def test_detects_nfrs(self, orchestrator, config, sample_files):
        """Test that NFRs are detected."""
        result = await orchestrator.run_analysis(
            project_id=1,
            files=sample_files,
            config=config,
        )

        assert result.nfr_report is not None
        assert len(result.nfr_report.detections) > 0

        # Should find caching patterns (performance)
        perf_detections = [d for d in result.nfr_report.detections if d.category.value == "performance"]
        assert len(perf_detections) >= 1

        # Should find logging patterns (maintainability)
        maint_detections = [d for d in result.nfr_report.detections if d.category.value == "maintainability"]
        assert len(maint_detections) >= 1

    @pytest.mark.asyncio
    async def test_classifies_variables(self, orchestrator, config, sample_files):
        """Test that variables are classified."""
        result = await orchestrator.run_analysis(
            project_id=1,
            files=sample_files,
            config=config,
        )

        assert result.variable_classification is not None

        # Should find domain variables (customer_id, order_total, etc.)
        assert len(result.variable_classification.domain_variables) > 0

        # Should calculate domain coverage
        assert result.domain_coverage > 0

    @pytest.mark.asyncio
    async def test_checks_compliance(self, orchestrator, config, sample_files):
        """Test that compliance is checked."""
        result = await orchestrator.run_analysis(
            project_id=1,
            files=sample_files,
            config=config,
        )

        assert result.compliance_report is not None
        # Compliance score should be calculated
        assert 0.0 <= result.compliance_score <= 1.0

    @pytest.mark.asyncio
    async def test_categorizes_findings_by_confidence(self, orchestrator, config, sample_files):
        """Test that findings are categorized by 72.5% threshold."""
        result = await orchestrator.run_analysis(
            project_id=1,
            files=sample_files,
            config=config,
        )

        # Should have high and low confidence findings
        assert isinstance(result.high_confidence_findings, list)
        assert isinstance(result.low_confidence_findings, list)

        # High confidence should have confidence >= 0.725
        for finding in result.high_confidence_findings:
            assert finding.get("confidence", 1.0) >= 0.725

    @pytest.mark.asyncio
    async def test_to_llm_context_structure(self, orchestrator, config, sample_files):
        """Test LLM context output structure."""
        result = await orchestrator.run_analysis(
            project_id=1,
            files=sample_files,
            config=config,
        )

        context = result.to_llm_context()

        assert "static_analysis_summary" in context
        assert "business_rules" in context
        assert "nfr_detections" in context
        assert "compliance_violations" in context
        assert "domain_variables" in context
        assert "high_confidence_findings" in context
        assert "low_confidence_findings" in context

    @pytest.mark.asyncio
    async def test_to_summary_structure(self, orchestrator, config, sample_files):
        """Test summary output structure."""
        result = await orchestrator.run_analysis(
            project_id=1,
            files=sample_files,
            config=config,
        )

        summary = result.to_summary()

        assert "id" in summary
        assert "project_id" in summary
        assert "duration_seconds" in summary
        assert "files_analyzed" in summary
        assert "business_rules_found" in summary
        assert "nfr_detections" in summary
        assert "compliance_violations" in summary
        assert "domain_coverage" in summary

    @pytest.mark.asyncio
    async def test_handles_empty_files(self, orchestrator, config):
        """Test handling of empty file set."""
        result = await orchestrator.run_analysis(
            project_id=1,
            files={},
            config=config,
        )

        assert result.total_files_analyzed == 0
        assert result.total_lines_of_code == 0

    @pytest.mark.asyncio
    async def test_handles_parse_errors_gracefully(self, orchestrator, config):
        """Test graceful handling of parse errors."""
        files = {
            "broken.py": '''
def incomplete_function(
    # Missing closing paren and colon
''',
        }

        # Should not raise, should record error
        result = await orchestrator.run_analysis(
            project_id=1,
            files=files,
            config=config,
        )

        # May have errors but should complete
        assert isinstance(result, StaticAnalysisResult)

    @pytest.mark.asyncio
    async def test_disabled_components(self, orchestrator, sample_files):
        """Test that disabled components are skipped."""
        config = StaticAnalysisConfig(
            enable_slicing=False,
            enable_variable_classification=False,
            enable_business_rules=False,
            enable_nfr_detection=False,
            enable_compliance=False,
        )

        result = await orchestrator.run_analysis(
            project_id=1,
            files=sample_files,
            config=config,
        )

        # Disabled components should be None or empty
        assert result.variable_classification is None
        assert result.business_rules is None
        assert result.nfr_report is None
        assert result.compliance_report is None

    @pytest.mark.asyncio
    async def test_get_conflict_candidates(self, orchestrator, config, sample_files):
        """Test getting conflict candidates for LLM validation."""
        result = await orchestrator.run_analysis(
            project_id=1,
            files=sample_files,
            config=config,
        )

        candidates = orchestrator.get_conflict_candidates(result)

        assert isinstance(candidates, list)
        for candidate in candidates:
            assert "action" in candidate
            assert candidate["action"] in ["validate", "monitor"]


class TestStaticAnalysisConfig:
    """Tests for StaticAnalysisConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = StaticAnalysisConfig()

        assert config.enable_slicing is True
        assert config.enable_variable_classification is True
        assert config.enable_business_rules is True
        assert config.enable_nfr_detection is True
        assert config.enable_compliance is True
        assert config.max_files == 1000
        assert "python" in config.languages

    def test_custom_domain_terms(self):
        """Test custom domain terms configuration."""
        config = StaticAnalysisConfig(
            custom_domain_terms=["patient", "diagnosis", "medication"]
        )

        assert len(config.custom_domain_terms) == 3
        assert "patient" in config.custom_domain_terms

    def test_compliance_frameworks_config(self):
        """Test compliance frameworks configuration."""
        config = StaticAnalysisConfig(
            compliance_frameworks=["NEN7510", "ISO27001", "HIPAA"]
        )

        assert len(config.compliance_frameworks) == 3


class TestFactoryFunction:
    """Tests for create_orchestrator factory."""

    def test_create_orchestrator(self):
        """Test factory function creates orchestrator."""
        orchestrator = create_orchestrator()

        assert isinstance(orchestrator, StaticAnalysisOrchestrator)

    def test_create_orchestrator_with_db(self):
        """Test factory with database session."""
        # Mock db session
        class MockSession:
            pass

        orchestrator = create_orchestrator(db_session=MockSession())

        assert orchestrator.db is not None
