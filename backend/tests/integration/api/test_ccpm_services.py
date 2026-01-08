"""
Tests for Week 79 CCPM Services

Tests for:
- GitWorktreeService
- GitHubIssuesService
- CCPMOrchestrator
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.services.git_worktree_service import GitWorktreeService, WorktreeInfo, MergeResult
from app.services.github_issues_service import GitHubIssuesService, GitHubIssue, SyncResult
from app.services.ccpm_orchestrator import CCPMOrchestrator, DecompositionResult, TaskRecommendationResult
from app.models.ccpm import (
    GitWorktree, GitHubIssueSync, PRDDecomposition, TaskRecommendation,
    WorktreeStatus, MergeStatus, SyncDirection, SyncStatus, DecompositionStatus, RecommendationStatus
)


# =============================================================================
# GitWorktreeService Tests
# =============================================================================

class TestGitWorktreeService:
    """Tests for GitWorktreeService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mocked dependencies."""
        return GitWorktreeService(mock_db, repo_path="/tmp/test-repo")

    @pytest.mark.asyncio
    async def test_create_worktree_info_class(self):
        """Test WorktreeInfo container class."""
        info = WorktreeInfo(
            id=uuid4(),
            agent_id="felix",
            worktree_path="/tmp/worktrees/felix-123",
            base_branch="main",
            work_branch="agent/felix/20251216",
            status="active",
            commit_count=5,
            files_changed=10
        )

        assert info.agent_id == "felix"
        assert info.base_branch == "main"
        assert info.status == "active"
        assert info.commit_count == 5

    @pytest.mark.asyncio
    async def test_merge_result_success(self):
        """Test MergeResult for successful merge."""
        result = MergeResult(
            success=True,
            status="merged",
            merge_commit_sha="abc123",
            message="Successfully merged"
        )

        assert result.success is True
        assert result.status == "merged"
        assert result.conflicts == []

    @pytest.mark.asyncio
    async def test_merge_result_conflict(self):
        """Test MergeResult for conflict."""
        result = MergeResult(
            success=False,
            status="conflict",
            conflicts=["file1.py", "file2.py"],
            message="Merge conflicts detected"
        )

        assert result.success is False
        assert len(result.conflicts) == 2

    @pytest.mark.asyncio
    async def test_get_worktree(self, service, mock_db):
        """Test getting a worktree by ID."""
        worktree_id = uuid4()
        mock_worktree = GitWorktree(
            id=worktree_id,
            agent_id="felix",
            worktree_path="/tmp/worktrees/felix",
            base_branch="main",
            work_branch="agent/felix/123",
            status=WorktreeStatus.ACTIVE.value
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_worktree
        mock_db.execute.return_value = mock_result

        result = await service.get_worktree(worktree_id)

        assert result is not None
        assert result.agent_id == "felix"

    @pytest.mark.asyncio
    async def test_list_active_worktrees(self, service, mock_db):
        """Test listing active worktrees."""
        mock_worktrees = [
            GitWorktree(id=uuid4(), agent_id="felix", status=WorktreeStatus.ACTIVE.value),
            GitWorktree(id=uuid4(), agent_id="quinn", status=WorktreeStatus.ACTIVE.value)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_worktrees
        mock_db.execute.return_value = mock_result

        result = await service.list_active_worktrees()

        assert len(result) == 2
        assert result[0].agent_id == "felix"

    @pytest.mark.asyncio
    async def test_get_statistics(self, service, mock_db):
        """Test getting worktree statistics."""
        mock_data = [
            (WorktreeStatus.ACTIVE.value, uuid4()),
            (WorktreeStatus.ACTIVE.value, uuid4()),
            (WorktreeStatus.MERGED.value, uuid4()),
        ]

        mock_result = MagicMock()
        mock_result.all.return_value = mock_data
        mock_db.execute.return_value = mock_result

        stats = await service.get_statistics()

        assert "total_worktrees" in stats
        assert "status_counts" in stats
        assert stats["total_worktrees"] == 3


# =============================================================================
# GitHubIssuesService Tests
# =============================================================================

class TestGitHubIssuesService:
    """Tests for GitHubIssuesService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance."""
        return GitHubIssuesService(mock_db)

    @pytest.mark.asyncio
    async def test_github_issue_class(self):
        """Test GitHubIssue container class."""
        issue = GitHubIssue(
            number=42,
            title="Test Issue",
            body="Issue body",
            state="open",
            labels=["bug", "high-priority"],
            url="https://github.com/owner/repo/issues/42"
        )

        assert issue.number == 42
        assert issue.title == "Test Issue"
        assert "bug" in issue.labels

    @pytest.mark.asyncio
    async def test_sync_result_success(self):
        """Test SyncResult for successful sync."""
        result = SyncResult(
            success=True,
            created=5,
            updated=3,
            conflicts=0,
            message="Sync complete"
        )

        assert result.success is True
        assert result.created == 5
        assert result.updated == 3

    @pytest.mark.asyncio
    async def test_sync_without_token(self, service, mock_db):
        """Test sync fails without GitHub token."""
        # Ensure no token is set
        service.github_token = None

        result = await service.sync_issues("owner/repo")

        assert result.success is False
        assert "token not configured" in result.message.lower()

    @pytest.mark.asyncio
    async def test_get_synced_issues(self, service, mock_db):
        """Test getting synced issues."""
        mock_issues = [
            GitHubIssueSync(
                id=uuid4(),
                github_repo="owner/repo",
                github_issue_number=1,
                title="Issue 1",
                sync_status=SyncStatus.SYNCED.value
            ),
            GitHubIssueSync(
                id=uuid4(),
                github_repo="owner/repo",
                github_issue_number=2,
                title="Issue 2",
                sync_status=SyncStatus.SYNCED.value
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_issues
        mock_db.execute.return_value = mock_result

        result = await service.get_synced_issues(repo="owner/repo")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_statistics(self, service, mock_db):
        """Test getting sync statistics."""
        mock_records = [
            GitHubIssueSync(
                id=uuid4(),
                github_repo="owner/repo",
                sync_status=SyncStatus.SYNCED.value,
                local_task_type="feature"
            ),
            GitHubIssueSync(
                id=uuid4(),
                github_repo="owner/repo",
                sync_status=SyncStatus.PENDING.value,
                local_task_type="bug"
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_db.execute.return_value = mock_result

        stats = await service.get_statistics()

        assert "total_synced" in stats
        assert "status_counts" in stats
        assert stats["total_synced"] == 2

    @pytest.mark.asyncio
    async def test_label_to_type_mapping(self, service):
        """Test label to task type mapping."""
        assert service.LABEL_TO_TYPE["epic"] == "epic"
        assert service.LABEL_TO_TYPE["feature"] == "feature"
        assert service.LABEL_TO_TYPE["user-story"] == "story"
        assert service.LABEL_TO_TYPE["enhancement"] == "feature"


# =============================================================================
# CCPMOrchestrator Tests
# =============================================================================

class TestCCPMOrchestrator:
    """Tests for CCPMOrchestrator."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def orchestrator(self, mock_db):
        """Create orchestrator instance."""
        return CCPMOrchestrator(mock_db)

    @pytest.mark.asyncio
    async def test_decomposition_result_class(self):
        """Test DecompositionResult container class."""
        result = DecompositionResult(
            id=uuid4(),
            title="Test PRD",
            epics=[{"id": "E1", "title": "Epic 1"}],
            features=[{"id": "F1", "title": "Feature 1"}],
            stories=[{"id": "S1", "title": "Story 1"}],
            tasks=[{"id": "T1", "title": "Task 1"}],
            total_story_points=50,
            total_function_points=25.5,
            processing_time_ms=1500
        )

        assert result.title == "Test PRD"
        assert len(result.epics) == 1
        assert result.total_story_points == 50

    @pytest.mark.asyncio
    async def test_task_recommendation_result_class(self):
        """Test TaskRecommendationResult container class."""
        result = TaskRecommendationResult(
            id=uuid4(),
            task_id=uuid4(),
            task_title="Implement API",
            task_type="task",
            priority_score=85.5,
            reasoning="High impact, low complexity",
            recommended_agent="felix",
            estimated_hours=8,
            impact_score=90,
            urgency_score=70,
            complexity_score=40,
            dependencies_met=True,
            blocked_by=[]
        )

        assert result.priority_score == 85.5
        assert result.recommended_agent == "felix"
        assert result.dependencies_met is True

    @pytest.mark.asyncio
    async def test_agent_capabilities(self, orchestrator):
        """Test agent capability mapping."""
        assert "architecture" in orchestrator.AGENT_CAPABILITIES["felix"]
        assert "quality" in orchestrator.AGENT_CAPABILITIES["quinn"]
        assert "debug" in orchestrator.AGENT_CAPABILITIES["betty"]
        assert "test" in orchestrator.AGENT_CAPABILITIES["tessa"]

    @pytest.mark.asyncio
    async def test_recommend_agent_architecture(self, orchestrator):
        """Test agent recommendation for architecture tasks."""
        task = {
            "title": "Design system architecture",
            "keywords": ["architecture", "design", "api"]
        }

        agent = orchestrator._recommend_agent(task)
        assert agent == "felix"

    @pytest.mark.asyncio
    async def test_recommend_agent_testing(self, orchestrator):
        """Test agent recommendation for testing tasks."""
        task = {
            "title": "Write unit tests",
            "keywords": ["test", "testing", "coverage"]
        }

        agent = orchestrator._recommend_agent(task)
        assert agent == "tessa"

    @pytest.mark.asyncio
    async def test_recommend_agent_default(self, orchestrator):
        """Test default agent recommendation."""
        task = {
            "title": "Generic task",
            "keywords": []
        }

        agent = orchestrator._recommend_agent(task)
        assert agent == "felix"  # Default

    @pytest.mark.asyncio
    async def test_calculate_complexity_score_low(self, orchestrator):
        """Test complexity score for low complexity task."""
        task = {
            "complexity": "low",
            "keywords": ["simple", "basic"]
        }

        score = orchestrator._calculate_complexity_score(task)
        assert score < 30

    @pytest.mark.asyncio
    async def test_calculate_complexity_score_high(self, orchestrator):
        """Test complexity score for high complexity task."""
        task = {
            "complexity": "high",
            "keywords": ["complex", "distributed", "security"]
        }

        score = orchestrator._calculate_complexity_score(task)
        assert score > 70

    @pytest.mark.asyncio
    async def test_get_decomposition(self, orchestrator, mock_db):
        """Test getting a decomposition by ID."""
        decomposition_id = uuid4()
        mock_decomposition = PRDDecomposition(
            id=decomposition_id,
            title="Test PRD",
            prd_content="PRD content",
            status=DecompositionStatus.COMPLETED.value,
            decomposition_result={"epics": [], "features": [], "stories": [], "tasks": []}
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_decomposition
        mock_db.execute.return_value = mock_result

        result = await orchestrator.get_decomposition(decomposition_id)

        assert result is not None
        assert result.title == "Test PRD"

    @pytest.mark.asyncio
    async def test_list_decompositions(self, orchestrator, mock_db):
        """Test listing decompositions."""
        mock_decompositions = [
            PRDDecomposition(
                id=uuid4(),
                title="PRD 1",
                status=DecompositionStatus.COMPLETED.value
            ),
            PRDDecomposition(
                id=uuid4(),
                title="PRD 2",
                status=DecompositionStatus.PROCESSING.value
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_decompositions
        mock_db.execute.return_value = mock_result

        result = await orchestrator.list_decompositions()

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_statistics(self, orchestrator, mock_db):
        """Test getting orchestrator statistics."""
        mock_decompositions = [
            PRDDecomposition(
                id=uuid4(),
                status=DecompositionStatus.COMPLETED.value,
                total_story_points=50,
                total_function_points=25.0
            )
        ]

        mock_recommendations = [
            TaskRecommendation(
                id=uuid4(),
                status=RecommendationStatus.PENDING.value,
                recommended_agent="felix"
            )
        ]

        # Mock execute to return different results based on call
        mock_result1 = MagicMock()
        mock_result1.scalars.return_value.all.return_value = mock_decompositions

        mock_result2 = MagicMock()
        mock_result2.scalars.return_value.all.return_value = mock_recommendations

        mock_db.execute.side_effect = [mock_result1, mock_result2]

        stats = await orchestrator.get_statistics()

        assert "decompositions" in stats
        assert "recommendations" in stats
        assert stats["total_story_points"] == 50

    @pytest.mark.asyncio
    async def test_parse_decomposition_result_valid_json(self, orchestrator):
        """Test parsing valid JSON decomposition result."""
        llm_response = '''
        {
            "epics": [{"id": "E1", "title": "Epic 1"}],
            "features": [],
            "stories": [],
            "tasks": [],
            "total_story_points": 10,
            "total_function_points": 5.0
        }
        '''

        result = orchestrator._parse_decomposition_result(llm_response)

        assert len(result["epics"]) == 1
        assert result["total_story_points"] == 10

    @pytest.mark.asyncio
    async def test_parse_decomposition_result_with_markdown(self, orchestrator):
        """Test parsing JSON wrapped in markdown code blocks."""
        llm_response = '''```json
        {
            "epics": [],
            "features": [],
            "stories": [],
            "tasks": [],
            "total_story_points": 0,
            "total_function_points": 0
        }
        ```'''

        result = orchestrator._parse_decomposition_result(llm_response)

        assert "epics" in result

    @pytest.mark.asyncio
    async def test_parse_decomposition_result_invalid_json(self, orchestrator):
        """Test parsing invalid JSON returns empty structure."""
        llm_response = "This is not valid JSON"

        result = orchestrator._parse_decomposition_result(llm_response)

        assert "parse_error" in result
        assert result["epics"] == []


# =============================================================================
# Integration Tests
# =============================================================================

class TestCCPMIntegration:
    """Integration tests for CCPM components."""

    @pytest.mark.asyncio
    async def test_worktree_workflow(self):
        """Test complete worktree workflow."""
        # Create -> Commit -> Merge workflow
        info = WorktreeInfo(
            id=uuid4(),
            agent_id="felix",
            worktree_path="/tmp/worktrees/felix",
            base_branch="main",
            work_branch="agent/felix/123",
            status="active",
            commit_count=0,
            files_changed=0
        )

        # Simulate commit
        info.commit_count = 1
        info.files_changed = 5

        # Simulate merge
        merge_result = MergeResult(
            success=True,
            status="merged",
            merge_commit_sha="abc123"
        )

        assert info.commit_count == 1
        assert merge_result.success is True

    @pytest.mark.asyncio
    async def test_prd_to_recommendations_workflow(self):
        """Test PRD decomposition to recommendations workflow."""
        # Simulated decomposition result
        hierarchy = {
            "epics": [{"id": "E1", "title": "User Auth"}],
            "features": [{"id": "F1", "epic_id": "E1", "title": "Login"}],
            "stories": [{"id": "S1", "feature_id": "F1", "story_points": 5}],
            "tasks": [
                {
                    "id": "T1",
                    "story_id": "S1",
                    "title": "Implement API",
                    "complexity": "medium",
                    "keywords": ["api", "backend"],
                    "estimated_hours": 4,
                    "dependencies": []
                }
            ],
            "total_story_points": 5,
            "total_function_points": 3.0,
            "critical_path": ["T1"]
        }

        # Verify task can be converted to recommendation
        task = hierarchy["tasks"][0]
        assert task["title"] == "Implement API"
        assert task["complexity"] == "medium"

        # Simulated recommendation
        recommendation = TaskRecommendationResult(
            id=uuid4(),
            task_id=None,
            task_title=task["title"],
            task_type="task",
            priority_score=75.0,
            reasoning="Impact: 50, Urgency: 90, Complexity: 50",
            recommended_agent="felix",
            estimated_hours=task["estimated_hours"],
            impact_score=50,
            urgency_score=90,  # On critical path
            complexity_score=50,
            dependencies_met=True,
            blocked_by=[]
        )

        assert recommendation.urgency_score == 90  # High because on critical path
        assert recommendation.recommended_agent == "felix"
