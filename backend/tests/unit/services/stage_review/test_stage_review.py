"""
Tests for Stage Review Service.

Fase 23.6 Phase 24.1: Tests for stage-based LLM council reviews.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.stage_review import (
    # Service
    StageReviewService,
    create_stage_review_service,
    # Types
    StageType,
    IssueSeverity,
    IssueCategory,
    ReviewStatus,
    ReviewDecision,
    ModelRole,
    ParsedIssue,
    ModelReviewResult,
    ConsolidatedIssue,
    ReviewRoundResult,
    ReviewResult,
    StageCouncilConfig,
    # Config functions
    get_stage_config,
    get_models_for_stage,
    get_provider_for_model,
    get_all_stage_types,
    STAGE_COUNCIL_CONFIGS,
)


# =============================================================================
# TEST TYPES
# =============================================================================


class TestTypes:
    """Tests for stage review types."""

    def test_stage_type_enum(self):
        """Test StageType enum values."""
        assert StageType.ARCHITECTURE.value == "architecture"
        assert StageType.DESIGN.value == "design"
        assert StageType.ANALYSIS.value == "analysis"
        assert StageType.PROGRAMMING.value == "programming"
        assert StageType.TESTING.value == "testing"
        assert StageType.INFRASTRUCTURE.value == "infrastructure"

    def test_issue_severity_enum(self):
        """Test IssueSeverity enum values."""
        assert IssueSeverity.CRITICAL.value == "critical"
        assert IssueSeverity.MAJOR.value == "major"
        assert IssueSeverity.MINOR.value == "minor"
        assert IssueSeverity.SUGGESTION.value == "suggestion"

    def test_issue_category_enum(self):
        """Test IssueCategory enum values."""
        assert IssueCategory.SECURITY.value == "security"
        assert IssueCategory.PERFORMANCE.value == "performance"
        assert IssueCategory.CORRECTNESS.value == "correctness"

    def test_review_decision_enum(self):
        """Test ReviewDecision enum values."""
        assert ReviewDecision.APPROVED.value == "approved"
        assert ReviewDecision.REJECTED.value == "rejected"
        assert ReviewDecision.NEEDS_REVISION.value == "needs_revision"

    def test_parsed_issue_to_dict(self):
        """Test ParsedIssue.to_dict() method."""
        issue = ParsedIssue(
            severity=IssueSeverity.MAJOR,
            category=IssueCategory.SECURITY,
            title="SQL Injection",
            description="User input directly used in query",
            suggested_fix="Use parameterized queries",
            line_start=42,
        )

        result = issue.to_dict()

        assert result["severity"] == "major"
        assert result["category"] == "security"
        assert result["title"] == "SQL Injection"
        assert result["line_start"] == 42

    def test_consolidated_issue_to_dict(self):
        """Test ConsolidatedIssue.to_dict() method."""
        issue = ConsolidatedIssue(
            severity=IssueSeverity.CRITICAL,
            category=IssueCategory.SECURITY,
            title="XSS Vulnerability",
            description="Unescaped output",
            suggested_fix="Escape HTML",
            line_start=10,
            line_end=15,
            code_snippet="print(user_input)",
            confirmed_by_models=["claude_opus", "deepseek_v3"],
            consensus_score=0.67,
        )

        result = issue.to_dict()

        assert result["severity"] == "critical"
        assert result["consensus_score"] == 0.67
        assert len(result["confirmed_by_models"]) == 2

    def test_stage_council_config_to_dict(self):
        """Test StageCouncilConfig.to_dict() method."""
        config = StageCouncilConfig(
            primary_models=["model1", "model2"],
            secondary_models=["model3"],
            critical_threshold=0,
            major_threshold=3,
            consensus_minimum=0.6,
        )

        result = config.to_dict()

        assert result["primary_models"] == ["model1", "model2"]
        assert result["critical_threshold"] == 0
        assert result["consensus_minimum"] == 0.6


# =============================================================================
# TEST CONFIGURATION
# =============================================================================


class TestStageCouncilConfig:
    """Tests for stage council configuration."""

    def test_get_stage_config_architecture(self):
        """Test getting architecture stage config."""
        config = get_stage_config("architecture")

        assert "claude_opus" in config.primary_models
        assert config.critical_threshold == 0
        assert config.consensus_minimum == 0.7  # Architecture is stricter

    def test_get_stage_config_programming(self):
        """Test getting programming stage config."""
        config = get_stage_config("programming")

        assert "qwen_coder" in config.primary_models
        assert "correctness" in config.criteria
        assert config.major_threshold == 2

    def test_get_stage_config_invalid(self):
        """Test getting config for invalid stage."""
        with pytest.raises(ValueError) as exc_info:
            get_stage_config("invalid_stage")

        assert "Unknown stage type" in str(exc_info.value)

    def test_get_models_for_stage(self):
        """Test getting models for a stage."""
        models = get_models_for_stage("architecture")

        # Should include both primary and secondary
        assert "claude_opus" in models
        assert len(models) >= 3

    def test_get_provider_for_model(self):
        """Test getting provider for a model."""
        assert get_provider_for_model("claude_opus") == "anthropic"
        assert get_provider_for_model("deepseek_v3") == "deepseek"
        assert get_provider_for_model("qwen_coder") == "ollama"
        assert get_provider_for_model("unknown_model") == "ollama"  # Default

    def test_get_all_stage_types(self):
        """Test getting all stage types."""
        stages = get_all_stage_types()

        assert "architecture" in stages
        assert "programming" in stages
        assert len(stages) == 6

    def test_all_configs_have_required_fields(self):
        """Test all configs have required fields."""
        for stage_type, config in STAGE_COUNCIL_CONFIGS.items():
            assert len(config.primary_models) >= 2, f"{stage_type} needs at least 2 primary models"
            assert config.critical_threshold >= 0
            assert config.major_threshold >= 0
            assert 0 < config.consensus_minimum <= 1


# =============================================================================
# TEST STAGE REVIEW SERVICE
# =============================================================================


class TestStageReviewService:
    """Tests for StageReviewService."""

    @pytest.fixture
    def service(self):
        """Create service with no LLM provider (uses mocks)."""
        return create_stage_review_service(llm_provider=None)

    def test_create_service(self, service):
        """Test service creation."""
        assert service is not None
        assert service.configs is not None
        assert len(service.configs) == 6

    def test_compute_hash(self, service):
        """Test content hashing."""
        content = "def hello(): pass"
        hash1 = service._compute_hash(content)
        hash2 = service._compute_hash(content)
        hash3 = service._compute_hash(content + " ")

        assert hash1 == hash2  # Same content = same hash
        assert hash1 != hash3  # Different content = different hash
        assert len(hash1) == 64  # SHA256 length

    def test_parse_single_issue_valid(self, service):
        """Test parsing a valid issue block."""
        issue_text = """
SEVERITY: critical
CATEGORY: security
TITLE: SQL Injection vulnerability
DESCRIPTION: User input is directly concatenated into SQL query
LINE: 42
SUGGESTED_FIX: Use parameterized queries
CODE_SNIPPET: f"SELECT * FROM users WHERE id = {user_id}"
"""
        result = service._parse_single_issue(issue_text)

        assert result is not None
        assert result.severity == IssueSeverity.CRITICAL
        assert result.category == IssueCategory.SECURITY
        assert result.title == "SQL Injection vulnerability"
        assert result.line_start == 42

    def test_parse_single_issue_line_range(self, service):
        """Test parsing issue with line range."""
        issue_text = """
SEVERITY: major
CATEGORY: performance
TITLE: N+1 Query
DESCRIPTION: Database called in loop
LINE: 10-25
SUGGESTED_FIX: Use bulk fetch
"""
        result = service._parse_single_issue(issue_text)

        assert result is not None
        assert result.line_start == 10
        assert result.line_end == 25

    def test_parse_single_issue_invalid_severity(self, service):
        """Test parsing issue with invalid severity (defaults to MINOR)."""
        issue_text = """
SEVERITY: unknown_severity
CATEGORY: security
TITLE: Test Issue
DESCRIPTION: Test description
"""
        result = service._parse_single_issue(issue_text)

        assert result is not None
        assert result.severity == IssueSeverity.MINOR  # Default

    def test_parse_single_issue_missing_required(self, service):
        """Test parsing issue with missing required fields."""
        issue_text = """
SEVERITY: critical
TITLE: Incomplete issue
"""
        result = service._parse_single_issue(issue_text)

        assert result is None  # Missing category and description

    def test_parse_review_response_multiple_issues(self, service):
        """Test parsing response with multiple issues."""
        response_text = """
[ISSUE]
SEVERITY: critical
CATEGORY: security
TITLE: Issue 1
DESCRIPTION: First issue
[/ISSUE]

[ISSUE]
SEVERITY: major
CATEGORY: performance
TITLE: Issue 2
DESCRIPTION: Second issue
[/ISSUE]

[SUMMARY]
Total issues: 2
[/SUMMARY]
"""
        issues = service._parse_review_response(response_text)

        assert len(issues) == 2
        assert issues[0].severity == IssueSeverity.CRITICAL
        assert issues[1].severity == IssueSeverity.MAJOR

    def test_parse_review_response_no_issues(self, service):
        """Test parsing response with no issues."""
        response_text = """
[NO_ISSUES]
The artifact passes all review criteria.
[/NO_ISSUES]

[SUMMARY]
Total issues: 0
Overall assessment: APPROVE
[/SUMMARY]
"""
        issues = service._parse_review_response(response_text)

        assert len(issues) == 0

    def test_consolidate_issues_deduplication(self, service):
        """Test issue consolidation with deduplication."""
        issues = [
            ParsedIssue(
                severity=IssueSeverity.CRITICAL,
                category=IssueCategory.SECURITY,
                title="SQL Injection",
                description="Desc 1",
                model_name="model1",
            ),
            ParsedIssue(
                severity=IssueSeverity.CRITICAL,
                category=IssueCategory.SECURITY,
                title="SQL Injection",  # Same issue from different model
                description="Desc 2",
                model_name="model2",
            ),
            ParsedIssue(
                severity=IssueSeverity.MAJOR,
                category=IssueCategory.PERFORMANCE,
                title="N+1 Query",
                description="Different issue",
                model_name="model1",
            ),
        ]

        result = service._consolidate_issues(issues, num_models=3)

        assert len(result) == 2  # Two unique issues
        # SQL Injection should have higher consensus
        sql_issue = next(i for i in result if "SQL" in i.title)
        assert sql_issue.consensus_score == 2/3
        assert len(sql_issue.confirmed_by_models) == 2

    def test_consolidate_issues_sorting(self, service):
        """Test that issues are sorted by severity then consensus."""
        issues = [
            ParsedIssue(
                severity=IssueSeverity.MINOR,
                category=IssueCategory.STYLE,
                title="Minor Issue",
                description="",
                model_name="model1",
            ),
            ParsedIssue(
                severity=IssueSeverity.CRITICAL,
                category=IssueCategory.SECURITY,
                title="Critical Issue",
                description="",
                model_name="model1",
            ),
        ]

        result = service._consolidate_issues(issues, num_models=2)

        # Critical should be first
        assert result[0].severity == IssueSeverity.CRITICAL
        assert result[1].severity == IssueSeverity.MINOR

    def test_calculate_consensus_full_agreement(self, service):
        """Test consensus calculation with full agreement."""
        reviews = [
            ModelReviewResult("m1", ModelRole.PRIMARY, [], "", 100),
            ModelReviewResult("m2", ModelRole.PRIMARY, [], "", 100),
        ]
        issues = []  # No issues = full consensus

        consensus = service._calculate_consensus(reviews, issues)

        assert consensus == 100.0

    def test_calculate_consensus_with_issues(self, service):
        """Test consensus calculation with issues."""
        reviews = [
            ModelReviewResult("m1", ModelRole.PRIMARY, [MagicMock()], "", 100),
            ModelReviewResult("m2", ModelRole.PRIMARY, [MagicMock()], "", 100),
        ]
        issues = [
            ConsolidatedIssue(
                severity=IssueSeverity.MAJOR,
                category=IssueCategory.SECURITY,
                title="Test",
                description="",
                suggested_fix=None,
                line_start=None,
                line_end=None,
                code_snippet=None,
                confirmed_by_models=["m1", "m2"],
                consensus_score=1.0,  # Both models agree
            )
        ]

        consensus = service._calculate_consensus(reviews, issues)

        assert consensus > 80  # High consensus with agreement

    def test_evaluate_threshold_under_limit(self, service):
        """Test threshold evaluation when under limit."""
        config = StageCouncilConfig(
            primary_models=["test"],
            critical_threshold=0,
            major_threshold=3,
        )
        issues = [
            ConsolidatedIssue(
                severity=IssueSeverity.MINOR,
                category=IssueCategory.STYLE,
                title="Test",
                description="",
                suggested_fix=None,
                line_start=None,
                line_end=None,
                code_snippet=None,
                confirmed_by_models=["m1"],
                consensus_score=0.8,
            )
        ]

        result = service._evaluate_threshold(issues, config)

        assert result is False  # Under threshold

    def test_evaluate_threshold_critical_exceeded(self, service):
        """Test threshold evaluation when critical exceeded."""
        config = StageCouncilConfig(
            primary_models=["test"],
            critical_threshold=0,
            major_threshold=3,
        )
        issues = [
            ConsolidatedIssue(
                severity=IssueSeverity.CRITICAL,
                category=IssueCategory.SECURITY,
                title="Test",
                description="",
                suggested_fix=None,
                line_start=None,
                line_end=None,
                code_snippet=None,
                confirmed_by_models=["m1", "m2"],
                consensus_score=0.67,  # Above 0.5 threshold
            )
        ]

        result = service._evaluate_threshold(issues, config)

        assert result is True  # Threshold exceeded

    def test_evaluate_threshold_low_consensus_ignored(self, service):
        """Test that low consensus issues are ignored in threshold."""
        config = StageCouncilConfig(
            primary_models=["test"],
            critical_threshold=0,
            major_threshold=3,
        )
        issues = [
            ConsolidatedIssue(
                severity=IssueSeverity.CRITICAL,
                category=IssueCategory.SECURITY,
                title="Test",
                description="",
                suggested_fix=None,
                line_start=None,
                line_end=None,
                code_snippet=None,
                confirmed_by_models=["m1"],
                consensus_score=0.3,  # Below 0.5, should be ignored
            )
        ]

        result = service._evaluate_threshold(issues, config)

        assert result is False  # Low consensus issue ignored

    def test_make_decision_approved(self, service):
        """Test decision making for approval."""
        config = StageCouncilConfig(
            primary_models=["test"],
            critical_threshold=0,
            major_threshold=3,
            consensus_minimum=0.6,
        )
        issues = [
            ConsolidatedIssue(
                severity=IssueSeverity.MINOR,
                category=IssueCategory.STYLE,
                title="Test",
                description="",
                suggested_fix=None,
                line_start=None,
                line_end=None,
                code_snippet=None,
                confirmed_by_models=["m1"],
                consensus_score=0.8,
            )
        ]

        result = service._make_decision(issues, consensus=75.0, config=config)

        assert result == ReviewDecision.APPROVED

    def test_make_decision_rejected_critical(self, service):
        """Test decision making when critical issues found."""
        config = StageCouncilConfig(
            primary_models=["test"],
            critical_threshold=0,
            major_threshold=3,
            consensus_minimum=0.6,
        )
        issues = [
            ConsolidatedIssue(
                severity=IssueSeverity.CRITICAL,
                category=IssueCategory.SECURITY,
                title="Test",
                description="",
                suggested_fix=None,
                line_start=None,
                line_end=None,
                code_snippet=None,
                confirmed_by_models=["m1", "m2"],
                consensus_score=0.67,
            )
        ]

        result = service._make_decision(issues, consensus=75.0, config=config)

        assert result == ReviewDecision.REJECTED

    def test_make_decision_needs_revision_major(self, service):
        """Test decision making when too many major issues."""
        config = StageCouncilConfig(
            primary_models=["test"],
            critical_threshold=0,
            major_threshold=1,
            consensus_minimum=0.6,
        )
        issues = [
            ConsolidatedIssue(
                severity=IssueSeverity.MAJOR,
                category=IssueCategory.PERFORMANCE,
                title="Issue 1",
                description="",
                suggested_fix=None,
                line_start=None,
                line_end=None,
                code_snippet=None,
                confirmed_by_models=["m1", "m2"],
                consensus_score=0.67,
            ),
            ConsolidatedIssue(
                severity=IssueSeverity.MAJOR,
                category=IssueCategory.CORRECTNESS,
                title="Issue 2",
                description="",
                suggested_fix=None,
                line_start=None,
                line_end=None,
                code_snippet=None,
                confirmed_by_models=["m1"],
                consensus_score=0.5,
            ),
        ]

        result = service._make_decision(issues, consensus=75.0, config=config)

        assert result == ReviewDecision.NEEDS_REVISION

    def test_make_decision_needs_revision_low_consensus(self, service):
        """Test decision making with low consensus."""
        config = StageCouncilConfig(
            primary_models=["test"],
            critical_threshold=0,
            major_threshold=3,
            consensus_minimum=0.7,
        )
        issues = []

        result = service._make_decision(issues, consensus=50.0, config=config)

        assert result == ReviewDecision.NEEDS_REVISION

    def test_extract_improved_artifact(self, service):
        """Test extracting improved artifact from response."""
        response = """
Some preamble text

[IMPROVED_ARTIFACT]
```python
def improved_function():
    return "fixed"
```
[/IMPROVED_ARTIFACT]

[CHANGES_MADE]
- Fixed the function
[/CHANGES_MADE]
"""
        result = service._extract_improved_artifact(response)

        assert "def improved_function():" in result
        assert "fixed" in result

    def test_extract_improved_artifact_fallback(self, service):
        """Test extracting artifact with fallback to code block."""
        response = """
```python
def fallback():
    pass
```
"""
        result = service._extract_improved_artifact(response)

        assert "def fallback():" in result

    def test_build_review_prompt_contains_stage_instructions(self, service):
        """Test review prompt contains stage-specific instructions."""
        prompt = service._build_review_prompt(
            stage_type="programming",
            artifact="def hello(): pass",
            artifact_type="code",
            context={},
            criteria={"correctness": 0.5, "security": 0.5},
        )

        assert "CODE REVIEW FOCUS:" in prompt
        assert "Correctness:" in prompt
        assert "Security:" in prompt
        assert "def hello():" in prompt

    def test_clear_cache(self, service):
        """Test clearing the review cache."""
        # Add something to cache
        service._review_cache["test_hash"] = MagicMock()
        assert len(service._review_cache) == 1

        service.clear_cache()

        assert len(service._review_cache) == 0


# =============================================================================
# TEST ASYNC REVIEW
# =============================================================================


class TestAsyncReview:
    """Async tests for review functionality."""

    @pytest.fixture
    def service(self):
        """Create service with no LLM provider (uses mocks)."""
        return create_stage_review_service(llm_provider=None)

    @pytest.mark.asyncio
    async def test_review_artifact_basic(self, service):
        """Test basic artifact review with mock responses."""
        code = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total
"""
        result = await service.review_artifact(
            stage_type="programming",
            artifact=code,
            artifact_type="code",
            context={"language": "python"},
        )

        assert result.session_id is not None
        assert result.stage_type == StageType.PROGRAMMING
        assert result.decision in [ReviewDecision.APPROVED, ReviewDecision.NEEDS_REVISION, ReviewDecision.REJECTED]
        assert isinstance(result.approved, bool)
        assert result.rounds_completed >= 1

    @pytest.mark.asyncio
    async def test_review_artifact_invalid_stage(self, service):
        """Test review with invalid stage type."""
        with pytest.raises(ValueError) as exc_info:
            await service.review_artifact(
                stage_type="invalid",
                artifact="test",
            )

        assert "Unknown stage type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_review_artifact_caching(self, service):
        """Test that reviews are cached."""
        code = "def test(): pass"

        result1 = await service.review_artifact(
            stage_type="programming",
            artifact=code,
        )

        result2 = await service.review_artifact(
            stage_type="programming",
            artifact=code,
        )

        # Should return same cached result
        assert result1.session_id == result2.session_id

    @pytest.mark.asyncio
    async def test_review_artifact_force_no_cache(self, service):
        """Test that force_review bypasses cache."""
        code = "def test(): pass"

        result1 = await service.review_artifact(
            stage_type="programming",
            artifact=code,
        )

        result2 = await service.review_artifact(
            stage_type="programming",
            artifact=code,
            force_review=True,
        )

        # Should have different session IDs
        assert result1.session_id != result2.session_id

    @pytest.mark.asyncio
    async def test_review_artifact_all_stages(self, service):
        """Test review for all stage types."""
        artifact = "sample artifact content"

        for stage_type in get_all_stage_types():
            result = await service.review_artifact(
                stage_type=stage_type,
                artifact=artifact,
                force_review=True,
            )

            assert result.session_id is not None
            assert result.stage_type.value == stage_type


# =============================================================================
# TEST INTEGRATION
# =============================================================================


class TestIntegration:
    """Integration tests for stage review system."""

    def test_review_result_serialization(self):
        """Test ReviewResult can be serialized to dict."""
        result = ReviewResult(
            session_id="test-123",
            stage_type=StageType.PROGRAMMING,
            decision=ReviewDecision.APPROVED,
            approved=True,
            issues=[],
            consensus_level=85.0,
            rounds_completed=1,
        )

        data = result.to_dict()

        assert data["session_id"] == "test-123"
        assert data["stage_type"] == "programming"
        assert data["decision"] == "approved"
        assert data["approved"] is True

    def test_full_config_validation(self):
        """Test all configs are properly configured."""
        for stage_type in get_all_stage_types():
            config = get_stage_config(stage_type)

            # Verify models exist
            assert len(config.primary_models) >= 2

            # Verify criteria sum to ~1.0
            criteria_sum = sum(config.criteria.values())
            assert 0.99 <= criteria_sum <= 1.01, f"{stage_type} criteria sum: {criteria_sum}"

            # Verify thresholds are reasonable
            assert config.critical_threshold >= 0
            assert config.major_threshold >= 0
            assert 0.5 <= config.consensus_minimum <= 1.0
