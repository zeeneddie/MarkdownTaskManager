"""
Test: Requirements Extraction using EXISTING Components
Uses the actual extraction services from the codebase.

This test demonstrates the real extraction pipeline:
1. BusinessRuleExtractor - static_analysis/business_rule_extractor.py
2. QuantitativeNFRDetector - extraction/quantitative_nfr_detector.py
3. INVESTValidatorService - invest_validator_service.py

Compare with: test_requirements_extraction.py (standalone implementation)

Usage:
    pytest tests/services/extraction/test_extraction_with_existing_components.py -v
    pytest tests/services/extraction/test_extraction_with_existing_components.py -v --capture=no
"""
import pytest
import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any

# Import EXISTING components from the codebase
# Note: We import directly from the module files to avoid __init__.py dependency issues
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import directly from module files (bypassing __init__.py)
import importlib.util

def load_module_direct(name: str, path: str):
    """Load a module directly from file path, bypassing __init__.py"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Load BusinessRuleExtractor
base_path = Path(__file__).parent.parent.parent.parent
business_rule_module = load_module_direct(
    "business_rule_extractor_direct",
    str(base_path / "app" / "services" / "static_analysis" / "business_rule_extractor.py")
)
BusinessRuleExtractor = business_rule_module.BusinessRuleExtractor
BusinessRule = business_rule_module.BusinessRule
RuleType = business_rule_module.RuleType
RuleExtractionResult = business_rule_module.RuleExtractionResult

# Load QuantitativeNFRDetector
nfr_module = load_module_direct(
    "quantitative_nfr_detector_direct",
    str(base_path / "app" / "services" / "extraction" / "quantitative_nfr_detector.py")
)
QuantitativeNFRDetector = nfr_module.QuantitativeNFRDetector
NFRCategory = nfr_module.NFRCategory
NFRDetectionResult = nfr_module.NFRDetectionResult
QuantitativeNFR = nfr_module.QuantitativeNFR


# ============================================================================
# COMPARISON DATA MODEL
# ============================================================================

@dataclass
class ComponentExtractionResult:
    """Result from existing component extraction."""
    source_file: str
    lines_of_code: int
    business_rules: List[BusinessRule]
    nfr_result: NFRDetectionResult
    rules_by_type: Dict[str, int]
    nfrs_by_category: Dict[str, int]


# ============================================================================
# EXTRACTION FUNCTIONS USING EXISTING COMPONENTS
# ============================================================================

async def extract_with_existing_components(source_path: str) -> ComponentExtractionResult:
    """
    Run extraction using the EXISTING codebase components.

    This uses:
    - BusinessRuleExtractor from static_analysis/
    - QuantitativeNFRDetector from extraction/
    """
    with open(source_path, 'r') as f:
        source = f.read()

    lines_of_code = len(source.split('\n'))

    # 1. Business Rule Extraction (existing component)
    rule_extractor = BusinessRuleExtractor()
    business_rules = await rule_extractor.extract_from_file(source_path, source)

    # 2. NFR Detection (existing component)
    # The NFR detector works on text/documentation, so we extract docstrings
    nfr_detector = QuantitativeNFRDetector()

    # Extract docstrings and comments for NFR analysis
    docstrings = extract_docstrings_for_nfr(source)
    nfr_result = nfr_detector.detect(docstrings)

    # Group results
    rules_by_type = {}
    for rule in business_rules:
        type_name = rule.rule_type.value
        rules_by_type[type_name] = rules_by_type.get(type_name, 0) + 1

    nfrs_by_category = {}
    for nfr in nfr_result.detected_nfrs:
        cat_name = nfr.category.value
        nfrs_by_category[cat_name] = nfrs_by_category.get(cat_name, 0) + 1

    return ComponentExtractionResult(
        source_file=source_path,
        lines_of_code=lines_of_code,
        business_rules=business_rules,
        nfr_result=nfr_result,
        rules_by_type=rules_by_type,
        nfrs_by_category=nfrs_by_category,
    )


def extract_docstrings_for_nfr(source: str) -> str:
    """
    Extract docstrings and comments from Python source for NFR analysis.
    The NFR detector works on natural language text.
    """
    import ast

    docstrings = []

    try:
        tree = ast.parse(source)

        # Get module docstring
        module_doc = ast.get_docstring(tree)
        if module_doc:
            docstrings.append(module_doc)

        # Get class and function docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node)
                if doc:
                    docstrings.append(doc)
    except SyntaxError:
        pass

    # Also extract comments
    for line in source.split('\n'):
        stripped = line.strip()
        if stripped.startswith('#'):
            docstrings.append(stripped[1:].strip())

    return '\n'.join(docstrings)


# ============================================================================
# PYTEST FIXTURES
# ============================================================================

@pytest.fixture
def invest_validator_path():
    """Path to invest_validator_service.py"""
    base_path = Path(__file__).parent.parent.parent.parent
    return str(base_path / "app" / "services" / "invest_validator_service.py")


@pytest.fixture
def sample_source_with_nfrs():
    """Sample source with explicit NFR patterns."""
    return '''
"""
Sample Service with NFR Requirements

Performance Requirements:
- API response time must be under 200ms
- System must support 1000 concurrent users
- Throughput should be at least 500 requests per second

Availability:
- Uptime must be 99.9% or higher

Security:
- All data must use AES-256 encryption
- Session timeout after 30 minutes
"""

import logging

logger = logging.getLogger(__name__)

# Maximum allowed response time: 200 milliseconds
MAX_RESPONSE_TIME_MS = 200

# Minimum availability target: 99.9%
MIN_AVAILABILITY = 99.9

class PerformanceService:
    """
    Handles performance-critical operations.

    Must respond within 100ms under normal load.
    Supports up to 500 concurrent connections.
    """

    def validate_response_time(self, time_ms: int) -> bool:
        """
        Validates that response time is within acceptable limits.

        Maximum allowed: 200 milliseconds
        Target: under 100ms for optimal performance
        """
        if time_ms > MAX_RESPONSE_TIME_MS:
            return False
        return True

    def check_capacity(self, current_users: int) -> bool:
        """
        Checks if system can handle more users.

        Maximum: 1000 concurrent users
        Warning threshold: 800 users
        """
        if current_users > 1000:
            return False
        if current_users > 800:
            logger.warning("Approaching capacity limit")
        return True
'''


# ============================================================================
# TESTS - EXISTING COMPONENTS
# ============================================================================

class TestBusinessRuleExtractor:
    """Test the EXISTING BusinessRuleExtractor."""

    @pytest.mark.asyncio
    async def test_extract_from_python_file(self, invest_validator_path):
        """Test extraction from invest_validator_service.py."""
        if not Path(invest_validator_path).exists():
            pytest.skip("File not found")

        with open(invest_validator_path, 'r') as f:
            source = f.read()

        extractor = BusinessRuleExtractor()
        rules = await extractor.extract_from_file(invest_validator_path, source)

        assert len(rules) > 0, "Should find business rules"

        # Check rule types
        rule_types = {r.rule_type for r in rules}
        print(f"\nFound {len(rules)} business rules")
        print(f"Rule types: {[rt.value for rt in rule_types]}")

        # Show sample rules
        for rule in rules[:5]:
            print(f"  {rule.id}: [{rule.rule_type.value}] {rule.natural_language[:60]}...")

    @pytest.mark.asyncio
    async def test_rule_confidence(self, invest_validator_path):
        """Test that rules have confidence scores."""
        if not Path(invest_validator_path).exists():
            pytest.skip("File not found")

        with open(invest_validator_path, 'r') as f:
            source = f.read()

        extractor = BusinessRuleExtractor()
        rules = await extractor.extract_from_file(invest_validator_path, source)

        for rule in rules:
            assert 0.0 <= rule.confidence <= 1.0

        high_confidence = [r for r in rules if r.confidence >= 0.8]
        print(f"\nHigh confidence rules: {len(high_confidence)} / {len(rules)}")


class TestQuantitativeNFRDetector:
    """Test the EXISTING QuantitativeNFRDetector."""

    def test_detect_performance_nfrs(self, sample_source_with_nfrs):
        """Test detection of performance NFRs."""
        docstrings = extract_docstrings_for_nfr(sample_source_with_nfrs)

        detector = QuantitativeNFRDetector()
        result = detector.detect(docstrings)

        assert len(result.detected_nfrs) > 0, "Should detect NFRs"

        print(f"\nDetected {len(result.detected_nfrs)} quantitative NFRs:")
        for nfr in result.detected_nfrs:
            print(f"  [{nfr.category.value}] {nfr.description[:50]}...")
            if nfr.metrics:
                for m in nfr.metrics:
                    print(f"    - {m.name}: {m.formatted_value()}")

    def test_detect_with_statistics(self, sample_source_with_nfrs):
        """Test that detector provides statistics."""
        docstrings = extract_docstrings_for_nfr(sample_source_with_nfrs)

        detector = QuantitativeNFRDetector()
        result = detector.detect(docstrings)

        assert result.statistics is not None
        print(f"\nStatistics: {result.statistics}")
        print(f"Suggestions: {result.suggestions}")


class TestFullPipelineWithExistingComponents:
    """Integration test using all existing components."""

    @pytest.mark.asyncio
    async def test_full_extraction(self, invest_validator_path):
        """Test complete extraction pipeline with existing components."""
        if not Path(invest_validator_path).exists():
            pytest.skip("File not found")

        result = await extract_with_existing_components(invest_validator_path)

        print("\n" + "=" * 70)
        print("EXTRACTION WITH EXISTING COMPONENTS")
        print("=" * 70)
        print(f"\nSource: {result.source_file}")
        print(f"Lines: {result.lines_of_code}")

        print(f"\n--- BUSINESS RULES ({len(result.business_rules)}) ---")
        print(f"By type: {result.rules_by_type}")

        for rule in result.business_rules[:5]:
            print(f"  {rule.id}: [{rule.rule_type.value}]")
            print(f"    Condition: {rule.condition[:50]}...")
            print(f"    Action: {rule.action[:50]}...")
            print(f"    Confidence: {rule.confidence:.0%}")

        if len(result.business_rules) > 5:
            print(f"  ... and {len(result.business_rules) - 5} more rules")

        print(f"\n--- NFRs ({len(result.nfr_result.detected_nfrs)}) ---")
        print(f"By category: {result.nfrs_by_category}")

        for nfr in result.nfr_result.detected_nfrs:
            print(f"  [{nfr.category.value}] {nfr.description[:60]}")

        if result.nfr_result.unquantified_nfrs:
            print(f"\nUnquantified NFRs: {len(result.nfr_result.unquantified_nfrs)}")

        print("\n" + "=" * 70)

        # Assertions
        assert result.lines_of_code > 500
        assert len(result.business_rules) >= 5


# ============================================================================
# COMPARISON TEST
# ============================================================================

class TestCompareImplementations:
    """Compare standalone vs existing component implementations."""

    @pytest.mark.asyncio
    async def test_compare_extraction_results(self, invest_validator_path):
        """
        Compare results from standalone vs existing components.

        This helps understand:
        - Coverage differences
        - Confidence score differences
        - Rule type detection differences
        """
        if not Path(invest_validator_path).exists():
            pytest.skip("File not found")

        # Import standalone implementation
        from tests.services.extraction.test_requirements_extraction import (
            run_extraction as standalone_extraction,
        )

        # Run both implementations
        standalone_result = standalone_extraction(invest_validator_path)
        component_result = await extract_with_existing_components(invest_validator_path)

        print("\n" + "=" * 70)
        print("COMPARISON: STANDALONE vs EXISTING COMPONENTS")
        print("=" * 70)

        print(f"\n{'Metric':<40} {'Standalone':>15} {'Components':>15}")
        print("-" * 70)
        print(f"{'Lines of code':<40} {standalone_result.lines_of_code:>15} {component_result.lines_of_code:>15}")
        print(f"{'Code symbols':<40} {len(standalone_result.symbols):>15} {'N/A':>15}")
        print(f"{'Functional requirements':<40} {len(standalone_result.functional_requirements):>15} {'N/A':>15}")
        print(f"{'Business rules':<40} {len(standalone_result.business_rules):>15} {len(component_result.business_rules):>15}")
        print(f"{'NFRs detected':<40} {len(standalone_result.nfrs):>15} {len(component_result.nfr_result.detected_nfrs):>15}")

        print("\n--- BUSINESS RULES BY TYPE ---")

        # Standalone breakdown
        standalone_by_type = {}
        for r in standalone_result.business_rules:
            standalone_by_type[r.rule_type] = standalone_by_type.get(r.rule_type, 0) + 1

        print(f"\nStandalone: {standalone_by_type}")
        print(f"Components: {component_result.rules_by_type}")

        print("\n--- KEY DIFFERENCES ---")
        print("Standalone: Uses regex patterns, simpler implementation")
        print("Components: Uses AST parsing, more sophisticated detection")
        print("Components: Variable classification, compliance tags")

        print("\n" + "=" * 70)


# ============================================================================
# CLI RUNNER
# ============================================================================

if __name__ == "__main__":
    import sys

    base_path = Path(__file__).parent.parent.parent.parent
    source_path = base_path / "app" / "services" / "invest_validator_service.py"

    if not source_path.exists():
        print(f"Error: {source_path} not found")
        sys.exit(1)

    print("=" * 70)
    print("EXTRACTION WITH EXISTING COMPONENTS")
    print(f"Source: {source_path}")
    print("=" * 70)

    async def main():
        result = await extract_with_existing_components(str(source_path))

        print(f"\nExtracted from {result.lines_of_code} lines:")
        print(f"  - {len(result.business_rules)} business rules")
        print(f"  - {len(result.nfr_result.detected_nfrs)} quantitative NFRs")

        print("\n--- SAMPLE BUSINESS RULES ---")
        for rule in result.business_rules[:10]:
            print(f"  [{rule.rule_type.value}] {rule.natural_language[:70]}...")

    asyncio.run(main())
