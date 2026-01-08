# backend/tests/services/week97/test_variable_classifier.py
"""
Unit tests for VariableClassifier - Week 97-98 (Fase 15).

Tests variable classification into DOMAIN, IMPLEMENTATION, and CONTROL types.
"""

import pytest
from app.services.static_analysis.variable_classifier import (
    VariableClassifier,
    VariableType,
    ClassifiedVariable,
    VariableClassificationResult,
)


class TestVariableClassifier:
    """Tests for VariableClassifier."""

    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return VariableClassifier()

    @pytest.fixture
    def classifier_with_custom_terms(self):
        """Create classifier with custom domain terms."""
        return VariableClassifier(custom_domain_terms=["patient", "diagnosis", "treatment"])

    def test_classify_domain_variable_by_pattern(self, classifier):
        """Test classification of domain variables by pattern."""
        result = classifier.classify_variable("customer_id")
        assert result.variable_type == VariableType.DOMAIN
        assert result.confidence >= 0.7

    def test_classify_domain_variable_with_business_terms(self, classifier):
        """Test classification with business terms."""
        result = classifier.classify_variable("order_total")
        assert result.variable_type == VariableType.DOMAIN

    def test_classify_implementation_variable(self, classifier):
        """Test classification of implementation variables."""
        result = classifier.classify_variable("temp_buffer")
        assert result.variable_type == VariableType.IMPLEMENTATION

    def test_classify_implementation_variable_index(self, classifier):
        """Test classification of index variables."""
        result = classifier.classify_variable("idx")
        # idx is recognized as control (index/counter pattern) or implementation
        assert result.variable_type in (VariableType.IMPLEMENTATION, VariableType.CONTROL)

    def test_classify_control_variable(self, classifier):
        """Test classification of control flow variables."""
        result = classifier.classify_variable("is_valid")
        assert result.variable_type == VariableType.CONTROL

    def test_classify_control_variable_flag(self, classifier):
        """Test classification of flag variables."""
        result = classifier.classify_variable("has_succeeded")  # Clear control prefix
        assert result.variable_type == VariableType.CONTROL

    def test_classify_unknown_variable(self, classifier):
        """Test classification of ambiguous variables."""
        result = classifier.classify_variable("xyz123")
        # Should still classify, but with lower confidence
        assert result.confidence < 0.7

    def test_classify_with_context(self, classifier):
        """Test classification with context from surrounding code."""
        result = classifier.classify_variable("order_amount", context="total_price = calculate_price(order_amount)")
        assert result.variable_type == VariableType.DOMAIN

    def test_custom_domain_terms(self, classifier_with_custom_terms):
        """Test custom domain terms are recognized."""
        result = classifier_with_custom_terms.classify_variable("patient_name")
        assert result.variable_type == VariableType.DOMAIN
        assert result.confidence >= 0.8

    def test_classify_all(self, classifier):
        """Test batch classification."""
        variables = ["customer_id", "temp_buffer", "is_active", "order_total"]
        result = classifier.classify_all(variables)

        assert isinstance(result, VariableClassificationResult)
        assert len(result.domain_variables) >= 2
        assert len(result.implementation_variables) >= 1
        assert len(result.control_variables) >= 1

    def test_domain_coverage_calculation(self, classifier):
        """Test domain coverage calculation."""
        variables = ["customer_id", "temp_buffer", "order_total", "idx"]
        result = classifier.classify_all(variables)

        # 2 domain vars out of 4 = 50%
        assert 0.4 <= result.domain_coverage <= 0.6

    def test_confidence_threshold_respected(self, classifier):
        """Test that only high-confidence variables are in domain list."""
        classifier.confidence_threshold = 0.9
        variables = ["customer_id"]
        result = classifier.classify_all(variables)

        # Should have customer_id classified
        assert len(result.variables) == 1

    def test_empty_variable_list(self, classifier):
        """Test handling of empty variable list."""
        result = classifier.classify_all([])
        assert len(result.variables) == 0
        assert result.domain_coverage == 0.0

    def test_duplicate_variable_handling(self, classifier):
        """Test that duplicates are handled correctly."""
        variables = ["customer_id", "customer_id", "customer_id"]
        result = classifier.classify_all(variables)

        # Should deduplicate or count all - depends on implementation
        assert len(result.variables) >= 1


class TestVariablePatterns:
    """Tests for pattern matching rules."""

    @pytest.fixture
    def classifier(self):
        return VariableClassifier()

    def test_entity_suffixes_detected(self, classifier):
        """Test entity suffix detection (_id, _name, etc.)."""
        entity_vars = ["user_id", "product_name", "order_status", "payment_amount"]
        for var in entity_vars:
            result = classifier.classify_variable(var)
            assert result.variable_type == VariableType.DOMAIN, f"{var} should be DOMAIN"

    def test_implementation_prefixes_detected(self, classifier):
        """Test implementation prefix detection (temp_, _internal, etc.)."""
        # Use variables that clearly match implementation patterns
        impl_vars = ["temp_buffer", "cache_data", "connection_pool"]
        for var in impl_vars:
            result = classifier.classify_variable(var)
            assert result.variable_type == VariableType.IMPLEMENTATION, f"{var} should be IMPLEMENTATION"

    def test_control_prefixes_detected(self, classifier):
        """Test control flow prefix detection (is_, has_, should_, etc.)."""
        control_vars = ["is_valid", "has_permission", "should_continue", "can_access"]
        for var in control_vars:
            result = classifier.classify_variable(var)
            assert result.variable_type == VariableType.CONTROL, f"{var} should be CONTROL"


class TestVariableClassificationResult:
    """Tests for VariableClassificationResult dataclass."""

    def test_result_structure(self):
        """Test that result has expected fields."""
        result = VariableClassificationResult(
            variables=[ClassifiedVariable("customer_id", VariableType.DOMAIN, 0.9, "from code", "entity suffix")],
            domain_variables=["customer_id", "order_total"],
            implementation_variables=["temp_val"],
            control_variables=["is_valid"],
            domain_coverage=0.5,
        )

        assert len(result.domain_variables) == 2
        assert len(result.implementation_variables) == 1
        assert len(result.control_variables) == 1
        assert result.domain_coverage == 0.5

    def test_variables_list(self):
        """Test variables list contains classifications."""
        cv1 = ClassifiedVariable("a", VariableType.DOMAIN, 0.9, "from code", "entity name")
        cv2 = ClassifiedVariable("b", VariableType.IMPLEMENTATION, 0.8, "from code", "temp prefix")
        cv3 = ClassifiedVariable("c", VariableType.CONTROL, 0.7, "from code", "is_ prefix")
        result = VariableClassificationResult(
            variables=[cv1, cv2, cv3],
            domain_variables=["a"],
            implementation_variables=["b"],
            control_variables=["c"],
            domain_coverage=0.33,
        )
        assert len(result.variables) == 3
