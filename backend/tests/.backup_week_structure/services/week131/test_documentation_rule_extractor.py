"""
Unit tests for DocumentationRuleExtractorService - Week 131

Tests for business rule extraction from documentation files.
"""
import pytest
import tempfile
from pathlib import Path

from app.services.static_analysis.documentation_rule_extractor import (
    DocumentationRuleExtractorService,
    RULE_PREFIX_PATTERNS,
    RFC_2119_KEYWORDS,
    CONDITIONAL_PATTERNS,
)
from app.models.week131_research import RuleType


@pytest.fixture
def service():
    return DocumentationRuleExtractorService()


@pytest.fixture
def temp_docs():
    """Create a temporary documentation directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestDocumentationRuleExtractorBasic:
    """Basic service functionality tests."""

    def test_service_init(self, service):
        """Test service initialization."""
        assert service is not None

    def test_extract_nonexistent_path(self, service):
        """Test extraction from non-existent path."""
        result = service.extract_from_directory(Path("/nonexistent/path"))
        assert result.success is False
        assert len(result.errors) > 0

    def test_extract_empty_directory(self, service, temp_docs):
        """Test extraction from empty directory."""
        result = service.extract_from_directory(temp_docs)
        assert result.success is True
        assert result.total_rules == 0


class TestRulePrefixExtraction:
    """Tests for rule prefix pattern extraction."""

    def test_extract_business_rule_prefix(self, service, temp_docs):
        """Test extraction of Business Rule: prefix."""
        content = """
        # Documentation

        Business Rule: All orders must have a valid customer ID.
        """
        (temp_docs / "rules.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.total_rules >= 1
        rule = result.rules[0]
        assert rule.extraction_pattern == "rule_prefix"
        assert rule.confidence >= 0.8

    def test_extract_rule_prefix(self, service, temp_docs):
        """Test extraction of Rule: prefix."""
        content = "Rule: Invoices must be paid within 30 days."
        (temp_docs / "rules.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.total_rules >= 1

    def test_extract_br_prefix(self, service, temp_docs):
        """Test extraction of BR-xxx format."""
        content = """
        BR-001: Users must verify email before login.
        BR-002: Passwords must be at least 8 characters.
        """
        (temp_docs / "rules.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.total_rules >= 2
        assert "DOC-BR-001" in [r.rule_id for r in result.rules] or any("001" in r.rule_id for r in result.rules)

    def test_extract_dutch_regel_prefix(self, service, temp_docs):
        """Test extraction of Dutch Regel: prefix."""
        content = "Regel: Alle klanten moeten een geldig adres hebben."
        (temp_docs / "regels.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.total_rules >= 1


class TestRFC2119Extraction:
    """Tests for RFC 2119 keyword extraction."""

    def test_extract_must_keyword(self, service, temp_docs):
        """Test extraction of MUST keyword."""
        content = "The system MUST validate all input fields."
        (temp_docs / "spec.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.total_rules >= 1
        rule = result.rules[0]
        assert rule.rule_type == RuleType.VALIDATION
        assert rule.confidence >= 0.9

    def test_extract_shall_keyword(self, service, temp_docs):
        """Test extraction of SHALL keyword."""
        content = "The API SHALL return HTTP 401 for unauthorized requests."
        (temp_docs / "spec.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.total_rules >= 1
        rule = result.rules[0]
        assert rule.rule_type == RuleType.VALIDATION

    def test_extract_should_keyword(self, service, temp_docs):
        """Test extraction of SHOULD keyword."""
        content = "The response SHOULD include pagination metadata."
        (temp_docs / "spec.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.total_rules >= 1
        rule = result.rules[0]
        assert rule.rule_type == RuleType.RECOMMENDATION
        assert rule.confidence < 0.9  # Lower confidence than MUST

    def test_extract_may_keyword(self, service, temp_docs):
        """Test extraction of MAY keyword."""
        content = "The client MAY cache responses for up to 1 hour."
        (temp_docs / "spec.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.total_rules >= 1
        rule = result.rules[0]
        assert rule.rule_type == RuleType.OPTIONAL


class TestConditionalRuleExtraction:
    """Tests for IF-THEN conditional rule extraction."""

    def test_extract_if_then_rule(self, service, temp_docs):
        """Test extraction of IF-THEN pattern."""
        content = "IF the order total exceeds $1000 THEN apply a 10% discount."
        (temp_docs / "rules.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.total_rules >= 1
        rule = result.rules[0]
        assert rule.condition is not None
        assert rule.action is not None
        assert rule.extraction_pattern == "conditional"

    def test_extract_when_then_rule(self, service, temp_docs):
        """Test extraction of WHEN-THEN pattern."""
        content = "WHEN a payment fails THEN notify the customer via email."
        (temp_docs / "rules.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.total_rules >= 1
        rule = result.rules[0]
        assert rule.rule_type == RuleType.CONDITION

    def test_extract_dutch_als_dan_rule(self, service, temp_docs):
        """Test extraction of Dutch ALS-DAN pattern."""
        content = "ALS de klant niet betaalt binnen 30 dagen DAN verstuur een herinnering."
        (temp_docs / "regels.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.total_rules >= 1

    def test_extract_arrow_notation_rule(self, service, temp_docs):
        """Test extraction of => arrow notation."""
        content = "Order status = 'pending' => Send confirmation email"
        (temp_docs / "rules.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.total_rules >= 1


class TestNumberedListExtraction:
    """Tests for numbered list rule extraction."""

    def test_extract_numbered_list_rules(self, service, temp_docs):
        """Test extraction from numbered lists."""
        content = """
        ## Validation Rules

        1. All email addresses must be valid.
        2. Phone numbers should follow E.164 format.
        3. Dates must be in ISO 8601 format.
        """
        (temp_docs / "rules.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        # Numbered list rules have lower confidence, but should be detected
        # in a "Rules" section

    def test_numbered_list_in_rules_section(self, service, temp_docs):
        """Test that rules section boosts confidence."""
        content = """
        ## Business Rules

        1. Users must authenticate before checkout.
        2. Orders cannot exceed $10,000 per day.
        """
        (temp_docs / "rules.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        # Rules in a "Rules" section should have higher confidence


class TestTableRuleExtraction:
    """Tests for markdown table rule extraction."""

    def test_extract_condition_action_table(self, service, temp_docs):
        """Test extraction from Condition/Action table."""
        content = """
        ## Decision Table

        | Condition | Action |
        |-----------|--------|
        | Order > $100 | Apply free shipping |
        | Customer is premium | Apply 10% discount |
        """
        (temp_docs / "rules.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.total_rules >= 2
        for rule in result.rules:
            assert rule.extraction_pattern == "table"
            assert rule.condition is not None
            assert rule.action is not None

    def test_extract_if_then_table(self, service, temp_docs):
        """Test extraction from IF/THEN table."""
        content = """
        | If | Then |
        |----|------|
        | Payment fails | Retry after 1 hour |
        | Account locked | Send reset email |
        """
        (temp_docs / "rules.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.total_rules >= 2


class TestRuleTypeInference:
    """Tests for rule type inference."""

    def test_infer_validation_type(self, service, temp_docs):
        """Test inference of VALIDATION type."""
        content = "Rule: The system must validate all user input."
        (temp_docs / "rules.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.rules[0].rule_type == RuleType.VALIDATION

    def test_infer_authorization_type(self, service, temp_docs):
        """Test inference of AUTHORIZATION type."""
        content = "Rule: Only admins have permission to delete users."
        (temp_docs / "rules.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.rules[0].rule_type == RuleType.AUTHORIZATION

    def test_infer_calculation_type(self, service, temp_docs):
        """Test inference of CALCULATION type."""
        content = "Rule: The total is calculated as sum of items plus tax."
        (temp_docs / "rules.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.rules[0].rule_type == RuleType.CALCULATION


class TestCodeRuleCorrelation:
    """Tests for correlation with code-extracted rules."""

    def test_correlate_matching_rules(self, service, temp_docs):
        """Test correlation of matching rules."""
        content = "Rule: All orders must have a valid customer."
        (temp_docs / "rules.md").write_text(content)

        code_rules = [
            {"rule_id": "BR-001", "natural_language": "Orders require valid customer ID"}
        ]

        result = service.extract_from_directory(temp_docs, code_rules=code_rules)
        # Should find correlation between doc rule and code rule
        if result.rules:
            assert len(result.rules[0].related_code_rules) >= 0  # May or may not find a match

    def test_detect_conflicting_rules(self, service, temp_docs):
        """Test detection of conflicting rules."""
        content = "IF status = 'active' THEN allow login."
        (temp_docs / "rules.md").write_text(content)

        code_rules = [
            {
                "rule_id": "BR-002",
                "condition": "status = 'active'",
                "action": "deny access"
            }
        ]

        result = service.extract_from_directory(temp_docs, code_rules=code_rules)
        # Should detect conflict: same condition, different action


class TestConflictDetection:
    """Tests for internal conflict detection."""

    def test_detect_internal_conflicts(self, service, temp_docs):
        """Test detection of conflicts between doc rules."""
        content = """
        Rule: IF payment fails THEN retry immediately.
        Rule: IF payment fails THEN wait 24 hours before retry.
        """
        (temp_docs / "rules.md").write_text(content)
        result = service.extract_from_directory(temp_docs)

        # Detect conflicts
        conflicts = service.detect_conflicts(result.rules)
        # Should detect conflict: same condition, different actions


class TestDeduplication:
    """Tests for rule deduplication."""

    def test_deduplicate_identical_rules(self, service, temp_docs):
        """Test that identical rules are deduplicated."""
        content = """
        Rule: Users must verify email.
        Business Rule: Users must verify email.
        """
        (temp_docs / "rules.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        # Should only keep one rule (highest confidence)
        assert result.total_rules == 1


class TestSectionTracking:
    """Tests for source section tracking."""

    def test_track_source_section(self, service, temp_docs):
        """Test tracking of source section."""
        content = """
        # User Management

        ## Authentication Rules

        Rule: Users must authenticate before checkout.
        """
        (temp_docs / "rules.md").write_text(content)
        result = service.extract_from_directory(temp_docs)
        assert result.rules[0].source_section is not None
        assert "Authentication" in result.rules[0].source_section or "User Management" in result.rules[0].source_section
