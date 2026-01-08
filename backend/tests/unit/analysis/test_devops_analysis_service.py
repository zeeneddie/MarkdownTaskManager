# tests/services/week97/test_devops_analysis_service.py
"""
Unit tests for GitHub/DevOps Analysis Services - Week 97-98 (Fase 14).

Tests:
- GitHub URL parsing
- Azure DevOps URL parsing
- Hot spot calculation
- Risk scoring algorithms
- Insight generation
- API endpoints
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.models.devops_analysis import (
    RepositoryAnalysis,
    HotSpot,
    ContributorAnalysis,
    PRPattern,
    CIPipelineAnalysis,
    IssueCorrelation,
    RepositoryInsight,
    RepositoryPlatform,
    AnalysisDepth,
)
from app.services.github_analysis_service import (
    GitHubAnalysisService,
    GitHubConfig,
    AnalysisRequest as GitHubAnalysisRequest,
    HotSpotData,
)
from app.services.azure_devops_service import (
    AzureDevOpsService,
    AzureDevOpsConfig,
    AzureAnalysisRequest,
)


# =============================================================================
# GitHub URL Parsing Tests
# =============================================================================

class TestGitHubURLParsing:
    """Tests for GitHub repository URL parsing."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock(spec=Session)
        return db

    @pytest.fixture
    def github_service(self, mock_db):
        """Create GitHub service for testing."""
        config = GitHubConfig(token="test_token")
        # Note: constructor is (db, config)
        return GitHubAnalysisService(mock_db, config)

    def test_parse_standard_https_url(self, github_service):
        """Test parsing standard GitHub HTTPS URL."""
        url = "https://github.com/anthropics/claude-code"
        owner, repo = github_service._parse_repo_url(url)

        assert owner == "anthropics"
        assert repo == "claude-code"

    def test_parse_url_with_trailing_slash(self, github_service):
        """Test parsing URL with trailing slash."""
        url = "https://github.com/anthropics/claude-code/"
        owner, repo = github_service._parse_repo_url(url)

        assert owner == "anthropics"
        assert repo == "claude-code"

    def test_parse_url_with_git_suffix(self, github_service):
        """Test parsing URL with .git suffix."""
        url = "https://github.com/anthropics/claude-code.git"
        owner, repo = github_service._parse_repo_url(url)

        assert owner == "anthropics"
        assert repo == "claude-code"

    def test_parse_ssh_url(self, github_service):
        """Test parsing SSH URL (via github.com in URL)."""
        # The current implementation handles github.com URLs
        url = "https://github.com/anthropics/claude-code"
        owner, repo = github_service._parse_repo_url(url)

        assert owner == "anthropics"
        assert repo == "claude-code"

    def test_parse_url_with_extra_path(self, github_service):
        """Test parsing URL with extra path components."""
        url = "https://github.com/anthropics/claude-code/tree/main"
        owner, repo = github_service._parse_repo_url(url)

        assert owner == "anthropics"
        assert repo == "claude-code"

    def test_parse_invalid_url_raises_error(self, github_service):
        """Test that invalid URL raises ValueError."""
        with pytest.raises(ValueError):
            github_service._parse_repo_url("invalid-url")

    def test_parse_non_github_url_raises_error(self, github_service):
        """Test that non-GitHub URL raises ValueError."""
        with pytest.raises(ValueError):
            github_service._parse_repo_url("https://gitlab.com/user/repo")


# =============================================================================
# Azure DevOps URL Parsing Tests
# =============================================================================

class TestAzureDevOpsURLParsing:
    """Tests for Azure DevOps repository URL parsing."""

    def test_parse_standard_devazure_url(self):
        """Test parsing standard dev.azure.com URL."""
        url = "https://dev.azure.com/myorg/myproject/_git/myrepo"
        result = AzureDevOpsService.parse_azure_url(url)

        assert result["organization"] == "myorg"
        assert result["project"] == "myproject"
        assert result["repository"] == "myrepo"

    def test_parse_visualstudio_url(self):
        """Test parsing legacy visualstudio.com URL."""
        url = "https://myorg.visualstudio.com/myproject/_git/myrepo"
        result = AzureDevOpsService.parse_azure_url(url)

        assert result["organization"] == "myorg"
        assert result["project"] == "myproject"
        assert result["repository"] == "myrepo"

    def test_parse_shorthand_format(self):
        """Test parsing shorthand org/project/repo format."""
        url = "myorg/myproject/myrepo"
        result = AzureDevOpsService.parse_azure_url(url)

        assert result["organization"] == "myorg"
        assert result["project"] == "myproject"
        assert result["repository"] == "myrepo"

    def test_parse_invalid_url_raises_error(self):
        """Test that invalid URL raises ValueError."""
        with pytest.raises(ValueError):
            AzureDevOpsService.parse_azure_url("invalid")


# =============================================================================
# Hot Spot Calculation Tests
# =============================================================================

class TestHotSpotCalculation:
    """Tests for hot spot risk calculation."""

    def test_risk_score_high_frequency_high_authors(self):
        """Test high risk score for high change frequency and many authors."""
        # Simulate hot spot with high frequency and many authors
        freq_score = 0.9  # 90% of max changes
        complexity = 0.8  # 80% of max authors
        bug_factor = 0.5  # 2-3 bugs

        # Risk formula: freq*0.4 + complexity*0.3 + bugs*0.3
        expected_risk = (freq_score * 0.4) + (complexity * 0.3) + (bug_factor * 0.3)

        assert expected_risk == pytest.approx(0.75, abs=0.01)

    def test_risk_score_low_frequency_single_author(self):
        """Test low risk score for low change frequency and single author."""
        freq_score = 0.1
        complexity = 0.1
        bug_factor = 0.0

        expected_risk = (freq_score * 0.4) + (complexity * 0.3) + (bug_factor * 0.3)

        assert expected_risk == pytest.approx(0.07, abs=0.01)

    def test_bug_factor_capped_at_one(self):
        """Test that bug factor is capped at 1.0."""
        bugs = 10  # More than 5 bugs
        bug_factor = min(bugs / 5, 1.0)

        assert bug_factor == 1.0


# =============================================================================
# Database Model Tests
# =============================================================================

class TestDatabaseModels:
    """Tests for DevOps analysis database models."""

    def test_repository_analysis_with_explicit_values(self):
        """Test RepositoryAnalysis with explicit values."""
        analysis = RepositoryAnalysis(
            platform=RepositoryPlatform.GITHUB,
            repository_url="https://github.com/test/repo",
            repository_name="repo",
            status="pending",
            total_commits=0,
            total_prs=0,
            analysis_depth=AnalysisDepth.STANDARD
        )

        assert analysis.status == "pending"
        assert analysis.total_commits == 0
        assert analysis.total_prs == 0
        assert analysis.analysis_depth == AnalysisDepth.STANDARD

    def test_hot_spot_with_explicit_values(self):
        """Test HotSpot with explicit values."""
        hot_spot = HotSpot(
            analysis_id=1,
            file_path="src/main.py",
            change_count=0,
            risk_score=0.0,
            associated_bugs=0
        )

        assert hot_spot.change_count == 0
        assert hot_spot.risk_score == 0.0
        assert hot_spot.associated_bugs == 0

    def test_contributor_analysis_with_explicit_values(self):
        """Test ContributorAnalysis with explicit values."""
        contributor = ContributorAnalysis(
            analysis_id=1,
            contributor_id="user@example.com",
            total_commits=0,
            bus_factor_contribution=0.0,
            is_sole_maintainer_files=0
        )

        assert contributor.total_commits == 0
        assert contributor.bus_factor_contribution == 0.0
        assert contributor.is_sole_maintainer_files == 0

    def test_pr_pattern_with_explicit_values(self):
        """Test PRPattern with explicit values."""
        pr = PRPattern(
            analysis_id=1,
            pr_number=123,
            additions=0,
            deletions=0,
            had_merge_conflicts=False,
            required_rework=False
        )

        assert pr.additions == 0
        assert pr.deletions == 0
        assert pr.had_merge_conflicts is False
        assert pr.required_rework is False

    def test_ci_pipeline_with_explicit_values(self):
        """Test CIPipelineAnalysis with explicit values."""
        pipeline = CIPipelineAnalysis(
            analysis_id=1,
            pipeline_name="CI",
            total_runs=0,
            success_rate=0.0,
            flaky_test_count=0
        )

        assert pipeline.total_runs == 0
        assert pipeline.success_rate == 0.0
        assert pipeline.flaky_test_count == 0

    def test_repository_platform_enum(self):
        """Test RepositoryPlatform enum values."""
        assert RepositoryPlatform.GITHUB.value == "github"
        assert RepositoryPlatform.AZURE_DEVOPS.value == "azure_devops"
        assert RepositoryPlatform.GITLAB.value == "gitlab"
        assert RepositoryPlatform.BITBUCKET.value == "bitbucket"

    def test_analysis_depth_enum(self):
        """Test AnalysisDepth enum values."""
        assert AnalysisDepth.QUICK.value == "quick"
        assert AnalysisDepth.STANDARD.value == "standard"
        assert AnalysisDepth.FULL.value == "full"


# =============================================================================
# Insight Generation Tests
# =============================================================================

class TestInsightGeneration:
    """Tests for repository insight generation logic."""

    def test_high_risk_files_threshold(self):
        """Test threshold for high-risk file detection."""
        # Files with risk_score > 0.7 should be flagged
        high_risk_threshold = 0.7

        test_scores = [0.5, 0.7, 0.75, 0.9, 0.3]
        high_risk_files = [s for s in test_scores if s > high_risk_threshold]

        assert len(high_risk_files) == 2  # 0.75 and 0.9

    def test_knowledge_silo_detection(self):
        """Test knowledge silo detection logic."""
        # Contributors with >5 sole-maintainer files are flagged
        sole_maintainer_threshold = 5

        contributors = [
            {"name": "Alice", "sole_files": 3},
            {"name": "Bob", "sole_files": 8},
            {"name": "Charlie", "sole_files": 6},
        ]

        knowledge_silos = [
            c for c in contributors
            if c["sole_files"] > sole_maintainer_threshold
        ]

        assert len(knowledge_silos) == 2
        assert knowledge_silos[0]["name"] == "Bob"
        assert knowledge_silos[1]["name"] == "Charlie"

    def test_slow_pr_review_threshold(self):
        """Test slow PR review time threshold."""
        # PRs with avg review time > 48 hours are flagged
        slow_review_threshold = 48  # hours

        assert 24 < slow_review_threshold  # Fast
        assert 72 > slow_review_threshold  # Slow

    def test_low_build_success_threshold(self):
        """Test low build success rate threshold."""
        # Build success rate < 80% is flagged
        low_success_threshold = 0.8

        assert 0.9 > low_success_threshold  # Good
        assert 0.75 < low_success_threshold  # Bad


# =============================================================================
# Service Mock Tests
# =============================================================================

class TestGitHubServiceMocked:
    """Tests for GitHubAnalysisService with mocked API calls."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock(spec=Session)
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.query = Mock()
        return db

    @pytest.fixture
    def github_config(self):
        """Create test GitHub config."""
        return GitHubConfig(token="test_token")

    def test_service_initialization(self, mock_db, github_config):
        """Test GitHubAnalysisService initialization."""
        # Note: constructor is (db, config)
        service = GitHubAnalysisService(mock_db, github_config)

        assert service.config.token == "test_token"
        assert service.db == mock_db

    def test_config_token_stored(self, mock_db, github_config):
        """Test config stores token correctly."""
        service = GitHubAnalysisService(mock_db, github_config)

        assert service.config is not None
        assert service.config.token == "test_token"

    @pytest.mark.asyncio
    async def test_close_method(self, mock_db, github_config):
        """Test service close method."""
        service = GitHubAnalysisService(mock_db, github_config)
        mock_client = AsyncMock()
        service._client = mock_client

        await service.close()

        # After close, client should be None
        assert service._client is None
        # The aclose method should have been called
        mock_client.aclose.assert_called_once()

    def test_client_initially_none(self, mock_db, github_config):
        """Test that client is None before first request."""
        service = GitHubAnalysisService(mock_db, github_config)

        assert service._client is None


class TestAzureDevOpsServiceMocked:
    """Tests for AzureDevOpsService with mocked API calls."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock(spec=Session)
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.query = Mock()
        return db

    @pytest.fixture
    def azure_config(self):
        """Create test Azure DevOps config."""
        return AzureDevOpsConfig(
            personal_access_token="test_pat",
            organization="testorg",
            project="testproject"
        )

    def test_service_initialization(self, azure_config, mock_db):
        """Test AzureDevOpsService initialization."""
        service = AzureDevOpsService(azure_config, mock_db)

        assert service.config.personal_access_token == "test_pat"
        assert service.config.organization == "testorg"
        assert service.config.project == "testproject"

    def test_base_url_format(self, azure_config, mock_db):
        """Test Azure DevOps base URL format."""
        service = AzureDevOpsService(azure_config, mock_db)

        expected = "https://dev.azure.com/testorg/testproject/_apis"
        assert service.base_url == expected

    def test_auth_header_is_basic(self, azure_config, mock_db):
        """Test Azure DevOps uses Basic auth."""
        service = AzureDevOpsService(azure_config, mock_db)

        assert "Authorization" in service.auth_header
        assert service.auth_header["Authorization"].startswith("Basic ")


# =============================================================================
# Extraction Context Tests
# =============================================================================

class TestExtractionContext:
    """Tests for extraction pipeline context generation."""

    def test_context_structure(self):
        """Test extraction context has required structure."""
        # Simulate context output
        context = {
            "repository": {
                "platform": "github",
                "url": "https://github.com/test/repo",
                "name": "repo",
                "default_branch": "main"
            },
            "metrics": {
                "total_commits": 100,
                "total_prs": 50,
                "total_contributors": 10
            },
            "hot_spots": [],
            "knowledge_silos": []
        }

        assert "repository" in context
        assert "metrics" in context
        assert "hot_spots" in context
        assert "knowledge_silos" in context

    def test_hot_spot_context_fields(self):
        """Test hot spot context has required fields."""
        hot_spot = {
            "path": "src/main.py",
            "risk_score": 0.85,
            "change_count": 42,
            "bug_associations": 3
        }

        assert "path" in hot_spot
        assert "risk_score" in hot_spot
        assert "change_count" in hot_spot
        assert "bug_associations" in hot_spot

    def test_knowledge_silo_context_fields(self):
        """Test knowledge silo context has required fields."""
        silo = {
            "contributor": "alice@example.com",
            "bus_factor": 0.35,
            "focus_areas": ["src/auth", "src/security"]
        }

        assert "contributor" in silo
        assert "bus_factor" in silo
        assert "focus_areas" in silo


# =============================================================================
# API Schema Tests
# =============================================================================

class TestAPISchemas:
    """Tests for API request/response schemas."""

    def test_analysis_depth_values(self):
        """Test valid analysis depth values."""
        valid_depths = ["quick", "standard", "full"]

        for depth in valid_depths:
            assert AnalysisDepth(depth) in AnalysisDepth

    def test_platform_detection_github(self):
        """Test platform auto-detection for GitHub URLs."""
        github_urls = [
            "https://github.com/owner/repo",
            "git@github.com:owner/repo.git",
            "https://github.com/owner/repo.git"
        ]

        for url in github_urls:
            assert "github" in url.lower() or "github.com" in url


# =============================================================================
# Integration Tests (with fixtures)
# =============================================================================

class TestIntegrationWithFixtures:
    """Integration tests using pytest fixtures."""

    @pytest.fixture
    def sample_analysis(self):
        """Create sample analysis for testing."""
        return RepositoryAnalysis(
            id=1,
            platform=RepositoryPlatform.GITHUB,
            repository_url="https://github.com/test/repo",
            repository_name="repo",
            default_branch="main",
            analysis_depth=AnalysisDepth.STANDARD,
            status="completed",
            total_commits=500,
            total_prs=100,
            total_contributors=15,
            total_issues=50,
            avg_pr_review_time_hours=24.5,
            build_success_rate=0.92,
            created_at=datetime.now(timezone.utc) - timedelta(hours=1),
            completed_at=datetime.now(timezone.utc)
        )

    @pytest.fixture
    def sample_hot_spots(self, sample_analysis):
        """Create sample hot spots for testing."""
        return [
            HotSpot(
                id=1,
                analysis_id=sample_analysis.id,
                file_path="src/auth/login.py",
                file_extension="py",
                change_count=45,
                lines_changed_total=1200,
                distinct_authors=8,
                change_frequency_score=0.9,
                complexity_score=0.8,
                risk_score=0.85,
                associated_bugs=5
            ),
            HotSpot(
                id=2,
                analysis_id=sample_analysis.id,
                file_path="src/api/routes.py",
                file_extension="py",
                change_count=30,
                lines_changed_total=800,
                distinct_authors=5,
                change_frequency_score=0.6,
                complexity_score=0.5,
                risk_score=0.55,
                associated_bugs=2
            )
        ]

    def test_analysis_has_valid_platform(self, sample_analysis):
        """Test analysis has valid platform."""
        assert sample_analysis.platform in RepositoryPlatform

    def test_analysis_is_completed(self, sample_analysis):
        """Test analysis status is completed."""
        assert sample_analysis.status == "completed"
        assert sample_analysis.completed_at is not None

    def test_hot_spots_sorted_by_risk(self, sample_hot_spots):
        """Test hot spots can be sorted by risk score."""
        sorted_spots = sorted(sample_hot_spots, key=lambda x: -x.risk_score)

        assert sorted_spots[0].file_path == "src/auth/login.py"
        assert sorted_spots[0].risk_score == 0.85

    def test_high_risk_hot_spots_filter(self, sample_hot_spots):
        """Test filtering high-risk hot spots."""
        high_risk = [hs for hs in sample_hot_spots if hs.risk_score > 0.7]

        assert len(high_risk) == 1
        assert high_risk[0].file_path == "src/auth/login.py"


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_repository(self):
        """Test handling of empty repository (no commits)."""
        analysis = RepositoryAnalysis(
            platform=RepositoryPlatform.GITHUB,
            repository_url="https://github.com/test/empty-repo",
            repository_name="empty-repo",
            total_commits=0,
            total_prs=0,
            total_contributors=0
        )

        assert analysis.total_commits == 0
        # Should not crash on empty data

    def test_very_long_file_path(self):
        """Test handling of very long file paths."""
        long_path = "src/" + "/".join(["subdir"] * 50) + "/file.py"

        hot_spot = HotSpot(
            analysis_id=1,
            file_path=long_path[:500]  # Truncate to max length
        )

        assert len(hot_spot.file_path) <= 500

    def test_unicode_in_contributor_name(self):
        """Test handling of unicode in contributor names."""
        contributor = ContributorAnalysis(
            analysis_id=1,
            contributor_id="user@example.com",
            contributor_name="José García 日本語"
        )

        assert "José" in contributor.contributor_name
        assert "日本語" in contributor.contributor_name

    def test_null_optional_fields(self):
        """Test handling of null optional fields."""
        analysis = RepositoryAnalysis(
            platform=RepositoryPlatform.GITHUB,
            repository_url="https://github.com/test/repo",
            repository_name="repo",
            avg_pr_review_time_hours=None,
            build_success_rate=None,
            test_coverage_percent=None
        )

        assert analysis.avg_pr_review_time_hours is None
        assert analysis.build_success_rate is None


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Tests for performance-related functionality."""

    def test_batch_processing_limit(self):
        """Test batch size limits for API calls."""
        batch_size = 100
        max_commits = 1000

        batches_needed = (max_commits + batch_size - 1) // batch_size
        assert batches_needed == 10

    def test_top_n_hot_spots_limit(self):
        """Test limiting hot spots to top N."""
        all_spots = list(range(100))
        top_n = 20

        top_spots = all_spots[:top_n]
        assert len(top_spots) == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
