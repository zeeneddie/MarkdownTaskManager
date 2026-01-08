# backend/tests/services/week111/test_llm_extraction.py
"""
Unit tests for Phase 2.5: LLM-Assisted Business Rule Extraction.

Tests the following components:
- LLMRuleClassifier: Validates ambiguous regex matches
- LLMRuleExtractor: Extracts rules from comments/messages
- MultiLLMValidator: Cross-validates with multiple LLMs
- TierOrchestrator: Coordinates hybrid extraction pipeline
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.static_analysis.extraction_models import (
    BusinessRule,
    RuleType,
    ExtractionTier,
    ExtractionMethod,
    Language,
)
from app.services.static_analysis.llm_classifier import (
    LLMRuleClassifier,
    ClassificationResponse,
    ClassificationResult,
    TIER_CLASSIFICATION_PROVIDERS,
)
from app.services.static_analysis.llm_extractor import (
    LLMRuleExtractor,
    ExtractedRule,
    LLMExtractionResult,
)
from app.services.static_analysis.multi_llm_validator import (
    MultiLLMValidator,
    ValidationVote,
    ConsensusResult,
    CONSENSUS_THRESHOLD,
)
from app.services.static_analysis.tier_orchestrator import (
    TierOrchestrator,
    OrchestrationResult,
    OrchestrationMetrics,
)


# =============================================================================
# Sample Data
# =============================================================================

def create_sample_rule(
    confidence: float = 0.7,
    rule_type: RuleType = RuleType.VALIDATION,
) -> BusinessRule:
    """Create a sample BusinessRule for testing."""
    return BusinessRule(
        id="BR-TEST-001",
        rule_type=rule_type,
        condition="If intCanView = 0 Then",
        action="Response.Redirect 'NoAccess.asp'",
        source_file="test.asp",
        source_lines=(100, 102),
        confidence=confidence,
        natural_language="Check if user has view permission",
        variables_involved=["intCanView"],
        related_entities=["User", "Permission"],
        language=Language.CLASSIC_ASP,
        extraction_method=ExtractionMethod.REGEX,
        code_snippet="If intCanView = 0 Then\n    Response.Redirect 'NoAccess.asp'\nEnd If",
    )


SAMPLE_VBSCRIPT_CODE = """
' Authorization check for agenda access
' User must have view permission to see agenda
If intCanView = 0 Then
    MsgBox "U heeft geen rechten om deze gegevens te bekijken"
    Response.Redirect "NoAccess.asp"
End If

' Validate appointment times
' Start time must be before end time
If StartTime > EndTime Then
    MsgBox "Eindtijd moet na starttijd liggen"
    Exit Sub
End If

' Check availability
' REM: Slot must not overlap with existing appointments
rst.Execute("SELECT COUNT(*) FROM taAfspraak WHERE overlap = 1")
"""

SAMPLE_TSQL_CODE = """
-- Authorization check for user permissions
-- Must have edit rights to modify data
IF @intCanEdit = 0
BEGIN
    RAISERROR('U heeft geen wijzigingsrechten', 16, 1)
    RETURN
END

-- Validate date range
-- Start date cannot be after end date
IF @StartDate > @EndDate
BEGIN
    RAISERROR('Begindatum moet voor einddatum liggen', 16, 1)
    RETURN
END
"""


# =============================================================================
# LLMRuleClassifier Tests
# =============================================================================

class TestLLMRuleClassifier:
    """Tests for LLMRuleClassifier."""

    def test_init_with_tier(self):
        """Test classifier initialization with different tiers."""
        for tier in ExtractionTier:
            classifier = LLMRuleClassifier(extraction_tier=tier)
            assert classifier.extraction_tier == tier

    def test_get_available_providers_free_tier(self):
        """FREE tier should have no LLM providers."""
        classifier = LLMRuleClassifier(extraction_tier=ExtractionTier.FREE)
        providers = classifier.get_available_providers()
        assert providers == []

    def test_get_available_providers_basic_tier(self):
        """BASIC tier should have Ollama only."""
        classifier = LLMRuleClassifier(extraction_tier=ExtractionTier.BASIC)
        providers = classifier.get_available_providers()
        assert "ollama" in providers

    def test_get_available_providers_premium_tier(self):
        """PREMIUM tier should have all providers."""
        classifier = LLMRuleClassifier(extraction_tier=ExtractionTier.PREMIUM)
        providers = classifier.get_available_providers()
        assert "ollama" in providers
        assert "anthropic" in providers

    @pytest.mark.asyncio
    async def test_classify_rule_no_providers(self):
        """Classify rule with no providers returns uncertain."""
        classifier = LLMRuleClassifier(extraction_tier=ExtractionTier.FREE)
        rule = create_sample_rule(confidence=0.5)

        result = await classifier.classify_rule(rule)

        assert result.result == ClassificationResult.UNCERTAIN
        assert result.is_business_rule is True
        assert result.confidence_boost == 0.0

    def test_build_classification_prompt(self):
        """Test prompt building includes all context."""
        classifier = LLMRuleClassifier(extraction_tier=ExtractionTier.BASIC)
        rule = create_sample_rule()
        rule.parent_function = "CheckPermissions"
        rule.parent_class = "AgendaHandler"

        prompt = classifier._build_classification_prompt(rule)

        assert "Language: asp" in prompt
        assert "test.asp" in prompt
        assert "100-102" in prompt
        assert "intCanView" in prompt
        assert "validation" in prompt
        assert "CheckPermissions" in prompt
        assert "AgendaHandler" in prompt

    def test_parse_classification_response_valid(self):
        """Test parsing valid JSON response."""
        classifier = LLMRuleClassifier(extraction_tier=ExtractionTier.BASIC)

        response_json = '''
        {
            "is_business_rule": true,
            "rule_type": "authorization",
            "confidence_boost": 0.10,
            "natural_language": "User must have view permission",
            "reasoning": "This checks user authorization"
        }
        '''

        result = classifier._parse_classification_response(
            response_json,
            "ollama",
            100,
            0.0,
        )

        assert result.result == ClassificationResult.CONFIRMED_RULE
        assert result.is_business_rule is True
        assert result.suggested_type == RuleType.AUTHORIZATION
        assert result.confidence_boost == 0.10
        assert result.natural_language == "User must have view permission"
        assert result.provider_used == "ollama"

    def test_parse_classification_response_rejected(self):
        """Test parsing response that rejects the rule."""
        classifier = LLMRuleClassifier(extraction_tier=ExtractionTier.BASIC)

        response_json = '''
        {
            "is_business_rule": false,
            "reasoning": "This is just a logging statement"
        }
        '''

        result = classifier._parse_classification_response(
            response_json,
            "ollama",
            50,
            0.0,
        )

        assert result.result == ClassificationResult.REJECTED
        assert result.is_business_rule is False

    def test_parse_classification_response_invalid(self):
        """Test parsing invalid response."""
        classifier = LLMRuleClassifier(extraction_tier=ExtractionTier.BASIC)

        result = classifier._parse_classification_response(
            "Not a valid JSON response",
            "ollama",
            10,
            0.0,
        )

        assert result.result == ClassificationResult.ERROR

    def test_filter_rejected_rules(self):
        """Test filtering out rejected rules."""
        classifier = LLMRuleClassifier(extraction_tier=ExtractionTier.BASIC)

        rules = [
            create_sample_rule(confidence=0.5),
            create_sample_rule(confidence=0.6),
            create_sample_rule(confidence=0.7),
        ]
        rules[0].id = "BR-001"
        rules[1].id = "BR-002"
        rules[2].id = "BR-003"

        classifications = [
            (rules[0], ClassificationResponse(
                result=ClassificationResult.CONFIRMED_RULE,
                is_business_rule=True,
            )),
            (rules[1], ClassificationResponse(
                result=ClassificationResult.REJECTED,
                is_business_rule=False,
            )),
        ]

        filtered = classifier.filter_rejected_rules(rules, classifications)

        assert len(filtered) == 2
        assert all(r.id != "BR-002" for r in filtered)


# =============================================================================
# LLMRuleExtractor Tests
# =============================================================================

class TestLLMRuleExtractor:
    """Tests for LLMRuleExtractor."""

    def test_init_with_tier(self):
        """Test extractor initialization with different tiers."""
        extractor = LLMRuleExtractor(extraction_tier=ExtractionTier.STANDARD)
        assert extractor.extraction_tier == ExtractionTier.STANDARD

    def test_extract_comments_vbscript(self):
        """Test comment extraction from VBScript."""
        extractor = LLMRuleExtractor(extraction_tier=ExtractionTier.STANDARD)

        comments = extractor.extract_comments(
            SAMPLE_VBSCRIPT_CODE,
            Language.CLASSIC_ASP,
        )

        assert len(comments) >= 3
        assert any("Authorization" in c["text"] for c in comments)
        assert any("permission" in c["text"] for c in comments)
        assert all("line" in c for c in comments)

    def test_extract_comments_tsql(self):
        """Test comment extraction from T-SQL."""
        extractor = LLMRuleExtractor(extraction_tier=ExtractionTier.STANDARD)

        comments = extractor.extract_comments(
            SAMPLE_TSQL_CODE,
            Language.TSQL,
        )

        assert len(comments) >= 2
        assert any("Authorization" in c["text"] for c in comments)
        assert any("date" in c["text"].lower() for c in comments)

    def test_extract_messages_vbscript(self):
        """Test message extraction from VBScript."""
        extractor = LLMRuleExtractor(extraction_tier=ExtractionTier.STANDARD)

        messages = extractor.extract_messages(
            SAMPLE_VBSCRIPT_CODE,
            Language.CLASSIC_ASP,
        )

        assert len(messages) >= 2
        assert any("rechten" in m["text"] for m in messages)
        assert any("Eindtijd" in m["text"] for m in messages)

    def test_extract_messages_tsql(self):
        """Test message extraction from T-SQL (RAISERROR)."""
        extractor = LLMRuleExtractor(extraction_tier=ExtractionTier.STANDARD)

        messages = extractor.extract_messages(
            SAMPLE_TSQL_CODE,
            Language.TSQL,
        )

        assert len(messages) >= 2
        assert any("wijzigingsrechten" in m["text"] for m in messages)

    def test_convert_to_business_rules(self):
        """Test conversion of ExtractedRules to BusinessRules."""
        extractor = LLMRuleExtractor(extraction_tier=ExtractionTier.STANDARD)

        extracted = [
            ExtractedRule(
                rule_type=RuleType.AUTHORIZATION,
                condition="User lacks permission",
                action="Deny access",
                natural_language="User must have view permission",
                confidence=0.85,
                source_text="' Check user permission",
                line_number=10,
                variables=["intCanView"],
                entities=["User"],
            ),
        ]

        rules = extractor.convert_to_business_rules(
            extracted,
            "test.asp",
            Language.CLASSIC_ASP,
        )

        assert len(rules) == 1
        assert rules[0].rule_type == RuleType.AUTHORIZATION
        assert rules[0].confidence == 0.85
        assert rules[0].extraction_method == ExtractionMethod.LLM
        assert rules[0].language == Language.CLASSIC_ASP


# =============================================================================
# MultiLLMValidator Tests
# =============================================================================

class TestMultiLLMValidator:
    """Tests for MultiLLMValidator."""

    def test_init_with_tier(self):
        """Test validator initialization."""
        validator = MultiLLMValidator(
            extraction_tier=ExtractionTier.PROFESSIONAL,
            min_providers=2,
        )
        assert validator.extraction_tier == ExtractionTier.PROFESSIONAL
        assert validator.min_providers == 2

    def test_get_available_providers(self):
        """Test provider availability by tier."""
        validator = MultiLLMValidator(
            extraction_tier=ExtractionTier.PROFESSIONAL,
            max_providers=3,
        )
        providers = validator.get_available_providers()

        assert len(providers) <= 3
        assert "ollama" in providers

    def test_calculate_consensus_all_agree(self):
        """Test consensus calculation when all LLMs agree."""
        validator = MultiLLMValidator(extraction_tier=ExtractionTier.PROFESSIONAL)

        votes = [
            ValidationVote(
                provider="ollama",
                is_business_rule=True,
                suggested_type=RuleType.AUTHORIZATION,
                confidence_boost=0.10,
            ),
            ValidationVote(
                provider="groq",
                is_business_rule=True,
                suggested_type=RuleType.AUTHORIZATION,
                confidence_boost=0.08,
            ),
            ValidationVote(
                provider="gemini",
                is_business_rule=True,
                suggested_type=RuleType.AUTHORIZATION,
                confidence_boost=0.12,
            ),
        ]

        result = validator._calculate_consensus(
            votes,
            ["ollama", "groq", "gemini"],
            300,
            0.05,
        )

        assert result.is_business_rule is True
        assert result.consensus_reached is True
        assert result.agreement_ratio == 1.0
        assert result.final_type == RuleType.AUTHORIZATION
        assert result.final_confidence_boost > 0

    def test_calculate_consensus_split_vote(self):
        """Test consensus calculation when LLMs disagree."""
        validator = MultiLLMValidator(extraction_tier=ExtractionTier.PROFESSIONAL)

        votes = [
            ValidationVote(
                provider="ollama",
                is_business_rule=True,
                confidence_boost=0.10,
            ),
            ValidationVote(
                provider="groq",
                is_business_rule=False,
                confidence_boost=0.0,
            ),
            ValidationVote(
                provider="gemini",
                is_business_rule=False,
                confidence_boost=0.0,
            ),
        ]

        result = validator._calculate_consensus(
            votes,
            ["ollama", "groq", "gemini"],
            300,
            0.05,
        )

        # Majority says not a business rule (2/3 = 0.666... < 0.67 threshold)
        assert result.is_business_rule is False
        # Note: 2/3 = 0.6666... is just below the 0.67 threshold
        assert result.consensus_reached is False  # 0.666 < 0.67
        assert result.agreement_ratio == pytest.approx(0.67, 0.02)

    def test_calculate_consensus_no_votes(self):
        """Test consensus with no votes."""
        validator = MultiLLMValidator(extraction_tier=ExtractionTier.PROFESSIONAL)

        result = validator._calculate_consensus([], [], 0, 0.0)

        assert result.is_business_rule is True
        assert result.consensus_reached is False
        assert result.agreement_ratio == 0.0

    def test_calculate_consensus_type_voting(self):
        """Test that rule type is determined by majority vote."""
        validator = MultiLLMValidator(extraction_tier=ExtractionTier.PROFESSIONAL)

        votes = [
            ValidationVote(
                provider="ollama",
                is_business_rule=True,
                suggested_type=RuleType.VALIDATION,
            ),
            ValidationVote(
                provider="groq",
                is_business_rule=True,
                suggested_type=RuleType.AUTHORIZATION,
            ),
            ValidationVote(
                provider="gemini",
                is_business_rule=True,
                suggested_type=RuleType.AUTHORIZATION,
            ),
        ]

        result = validator._calculate_consensus(
            votes,
            ["ollama", "groq", "gemini"],
            300,
            0.05,
        )

        # Authorization wins 2-1
        assert result.final_type == RuleType.AUTHORIZATION


# =============================================================================
# TierOrchestrator Tests
# =============================================================================

class TestTierOrchestrator:
    """Tests for TierOrchestrator."""

    def test_init_creates_components(self):
        """Test orchestrator creates all required components."""
        orchestrator = TierOrchestrator(
            extraction_tier=ExtractionTier.STANDARD,
            project_id=123,
        )

        assert orchestrator.extraction_tier == ExtractionTier.STANDARD
        assert orchestrator.project_id == 123
        assert orchestrator.factory is not None
        assert orchestrator.classifier is not None
        assert orchestrator.extractor is not None
        assert orchestrator.validator is not None
        assert orchestrator.synthesizer is not None

    def test_tier_determines_pipeline_steps(self):
        """Test that tier affects which pipeline steps run."""
        # FREE tier should skip LLM steps
        free_orchestrator = TierOrchestrator(
            extraction_tier=ExtractionTier.FREE,
        )
        assert free_orchestrator.classifier.get_available_providers() == []

        # PREMIUM tier should have all steps
        premium_orchestrator = TierOrchestrator(
            extraction_tier=ExtractionTier.PREMIUM,
        )
        assert "anthropic" in premium_orchestrator.classifier.get_available_providers()


class TestOrchestrationMetrics:
    """Tests for OrchestrationMetrics."""

    def test_default_values(self):
        """Test default metric values."""
        metrics = OrchestrationMetrics()

        assert metrics.static_rules_extracted == 0
        assert metrics.llm_rules_extracted == 0
        assert metrics.total_rules == 0
        assert metrics.average_confidence == 0.0
        assert metrics.total_cost_cents == 0.0

    def test_can_aggregate_metrics(self):
        """Test that metrics can be aggregated."""
        m1 = OrchestrationMetrics(static_rules_extracted=10, total_tokens=100)
        m2 = OrchestrationMetrics(static_rules_extracted=5, total_tokens=50)

        total = m1.static_rules_extracted + m2.static_rules_extracted
        assert total == 15

        total_tokens = m1.total_tokens + m2.total_tokens
        assert total_tokens == 150


# =============================================================================
# Integration Tests
# =============================================================================

class TestTierBasedBehavior:
    """Tests for tier-based behavior across components."""

    @pytest.mark.parametrize("tier,expected_providers", [
        (ExtractionTier.FREE, []),
        (ExtractionTier.BASIC, ["ollama"]),
        (ExtractionTier.STANDARD, ["ollama", "groq"]),  # classifier has ollama+groq at STANDARD
    ])
    def test_classifier_providers_by_tier(self, tier, expected_providers):
        """Test classifier provider availability by tier."""
        classifier = LLMRuleClassifier(extraction_tier=tier)
        providers = classifier.get_available_providers()

        for expected in expected_providers:
            assert expected in providers

    def test_free_tier_static_only(self):
        """FREE tier should only use static extraction."""
        classifier = LLMRuleClassifier(extraction_tier=ExtractionTier.FREE)
        extractor = LLMRuleExtractor(extraction_tier=ExtractionTier.FREE)
        validator = MultiLLMValidator(extraction_tier=ExtractionTier.FREE)

        assert classifier.get_available_providers() == []
        assert extractor.get_available_providers() == []
        assert validator.get_available_providers() == []

    def test_premium_tier_full_pipeline(self):
        """PREMIUM tier should have access to all features."""
        orchestrator = TierOrchestrator(extraction_tier=ExtractionTier.PREMIUM)

        # All providers available
        assert "anthropic" in orchestrator.classifier.get_available_providers()
        assert "anthropic" in orchestrator.validator.get_available_providers()

        # Synthesizer available
        assert orchestrator.synthesizer is not None


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_source_code(self):
        """Test handling of empty source code."""
        extractor = LLMRuleExtractor(extraction_tier=ExtractionTier.STANDARD)

        comments = extractor.extract_comments("", Language.VBNET)
        messages = extractor.extract_messages("", Language.VBNET)

        assert comments == []
        assert messages == []

    def test_malformed_json_response(self):
        """Test handling of malformed JSON from LLM."""
        classifier = LLMRuleClassifier(extraction_tier=ExtractionTier.BASIC)

        result = classifier._parse_classification_response(
            "{ invalid json }",
            "ollama",
            10,
            0.0,
        )

        assert result.result == ClassificationResult.ERROR
        assert result.is_business_rule is True  # Fail-safe default

    def test_confidence_boost_capped(self):
        """Test that confidence boost is capped at 0.15."""
        classifier = LLMRuleClassifier(extraction_tier=ExtractionTier.BASIC)

        response_json = '''
        {
            "is_business_rule": true,
            "confidence_boost": 0.50
        }
        '''

        result = classifier._parse_classification_response(
            response_json,
            "ollama",
            100,
            0.0,
        )

        assert result.confidence_boost <= 0.15

    def test_unknown_rule_type(self):
        """Test handling of unknown rule type from LLM."""
        classifier = LLMRuleClassifier(extraction_tier=ExtractionTier.BASIC)

        response_json = '''
        {
            "is_business_rule": true,
            "rule_type": "unknown_type"
        }
        '''

        result = classifier._parse_classification_response(
            response_json,
            "ollama",
            100,
            0.0,
        )

        # Should still work, just no type suggestion
        assert result.result == ClassificationResult.CONFIRMED_RULE
        assert result.suggested_type is None
