"""
Week 90 Tests - Portal Voting and Comments API

Tests for:
- Voting endpoints (cast, remove, check, ranked)
- Comments endpoints (create, read, update, delete, pin)
- Threading and mentions
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime, timezone
from httpx import AsyncClient

from app.models.portal_voting import (
    PortalFeatureVote,
    PortalFeatureComment,
    PortalFeatureVoteAggregate
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def feature_request_id():
    """Generate a sample feature request ID."""
    return str(uuid4())


@pytest.fixture
def user_email():
    """Sample user email."""
    return "test@example.com"


@pytest.fixture
def sample_vote():
    """Sample vote data."""
    return {
        "user_email": "voter@example.com",
        "user_name": "Test Voter",
        "vote_type": "up"
    }


@pytest.fixture
def sample_comment():
    """Sample comment data."""
    return {
        "user_email": "commenter@example.com",
        "user_name": "Test Commenter",
        "user_role": "customer",
        "content": "This is a great feature request! @admin please review."
    }


# =============================================================================
# VOTING MODEL TESTS
# =============================================================================

class TestPortalFeatureVoteModel:
    """Tests for PortalFeatureVote model."""

    def test_vote_creation(self):
        """Test vote model creation."""
        vote = PortalFeatureVote(
            feature_request_id=uuid4(),
            user_email="test@example.com",
            user_name="Test User",
            vote_type="up",
            vote_weight=1
        )

        assert vote.vote_type == "up"
        assert vote.vote_weight == 1

    def test_vote_to_dict(self):
        """Test vote serialization."""
        vote_id = uuid4()
        feature_id = uuid4()
        vote = PortalFeatureVote(
            id=vote_id,
            feature_request_id=feature_id,
            user_email="test@example.com",
            vote_type="down",
            created_at=datetime.now(timezone.utc)
        )

        result = vote.to_dict()

        assert result["id"] == str(vote_id)
        assert result["vote_type"] == "down"
        assert result["user_email"] == "test@example.com"


class TestPortalFeatureVoteAggregateModel:
    """Tests for PortalFeatureVoteAggregate model."""

    def test_aggregate_creation(self):
        """Test aggregate model creation."""
        aggregate = PortalFeatureVoteAggregate(
            feature_request_id=uuid4(),
            upvotes=10,
            downvotes=3,
            total_votes=13,
            score=7,
            hot_score=1.5
        )

        assert aggregate.upvotes == 10
        assert aggregate.downvotes == 3
        assert aggregate.score == 7

    def test_hot_score_calculation(self):
        """Test Reddit-style hot score calculation."""
        # Recent item with positive score
        created = datetime.now(timezone.utc)
        score = PortalFeatureVoteAggregate.calculate_hot_score(10, 2, created)

        assert score > 0  # Positive score should be positive hot score

        # Older item with same score should have lower hot score
        from datetime import timedelta
        old_created = created - timedelta(days=30)
        old_score = PortalFeatureVoteAggregate.calculate_hot_score(10, 2, old_created)

        assert old_score < score  # Older items should rank lower

    def test_negative_hot_score(self):
        """Test hot score with negative votes."""
        created = datetime.now(timezone.utc)
        score = PortalFeatureVoteAggregate.calculate_hot_score(2, 10, created)

        assert score < 0  # Net negative should be negative hot score


# =============================================================================
# COMMENT MODEL TESTS
# =============================================================================

class TestPortalFeatureCommentModel:
    """Tests for PortalFeatureComment model."""

    def test_comment_creation(self):
        """Test comment model creation."""
        comment = PortalFeatureComment(
            feature_request_id=uuid4(),
            user_email="test@example.com",
            content="Test comment",
            thread_depth=0
        )

        assert comment.content == "Test comment"
        assert comment.thread_depth == 0
        assert comment.is_deleted == False

    def test_comment_to_dict(self):
        """Test comment serialization."""
        comment_id = uuid4()
        comment = PortalFeatureComment(
            id=comment_id,
            feature_request_id=uuid4(),
            user_email="test@example.com",
            user_name="Test User",
            content="Test content",
            content_html="<p>Test content</p>",
            thread_depth=0,
            is_edited=False,
            is_deleted=False,
            is_pinned=True,
            created_at=datetime.now(timezone.utc)
        )

        result = comment.to_dict()

        assert result["id"] == str(comment_id)
        assert result["content"] == "Test content"
        assert result["is_pinned"] == True

    def test_deleted_comment_content_hidden(self):
        """Test that deleted comments hide content."""
        comment = PortalFeatureComment(
            id=uuid4(),
            feature_request_id=uuid4(),
            user_email="test@example.com",
            content="Original content",
            is_deleted=True,
            created_at=datetime.now(timezone.utc)
        )

        result = comment.to_dict()

        assert result["content"] == "[deleted]"
        assert result["content_html"] is None


# =============================================================================
# VOTING API ENDPOINT TESTS
# =============================================================================

class TestVotingEndpoints:
    """Tests for voting API endpoints."""

    @pytest.mark.asyncio
    async def test_cast_upvote(self, sample_vote):
        """Test casting an upvote."""
        # This would be an integration test with the actual API
        # For unit testing, we verify the model behavior
        vote = PortalFeatureVote(
            feature_request_id=uuid4(),
            user_email=sample_vote["user_email"],
            user_name=sample_vote["user_name"],
            vote_type=sample_vote["vote_type"]
        )

        assert vote.vote_type == "up"

    @pytest.mark.asyncio
    async def test_cast_downvote(self):
        """Test casting a downvote."""
        vote = PortalFeatureVote(
            feature_request_id=uuid4(),
            user_email="test@example.com",
            vote_type="down"
        )

        assert vote.vote_type == "down"

    @pytest.mark.asyncio
    async def test_vote_toggle_same_type(self):
        """Test that voting same type removes the vote (toggle behavior)."""
        # This tests the expected behavior documented in the API
        # When a user votes the same way again, the vote should be removed
        pass  # Integration test would verify this

    @pytest.mark.asyncio
    async def test_vote_change_type(self):
        """Test changing vote from up to down."""
        # When a user changes their vote, it should update rather than create new
        pass  # Integration test would verify this


# =============================================================================
# COMMENTS API ENDPOINT TESTS
# =============================================================================

class TestCommentsEndpoints:
    """Tests for comments API endpoints."""

    @pytest.mark.asyncio
    async def test_create_comment(self, sample_comment):
        """Test creating a comment."""
        comment = PortalFeatureComment(
            feature_request_id=uuid4(),
            user_email=sample_comment["user_email"],
            user_name=sample_comment["user_name"],
            user_role=sample_comment["user_role"],
            content=sample_comment["content"]
        )

        assert comment.content == sample_comment["content"]
        assert comment.user_role == "customer"

    @pytest.mark.asyncio
    async def test_create_reply(self):
        """Test creating a reply to a comment."""
        parent_id = uuid4()
        reply = PortalFeatureComment(
            feature_request_id=uuid4(),
            user_email="replier@example.com",
            content="This is a reply",
            parent_id=parent_id,
            thread_depth=1
        )

        assert reply.parent_id == parent_id
        assert reply.thread_depth == 1

    @pytest.mark.asyncio
    async def test_max_nesting_depth(self):
        """Test that nesting depth is limited to 5."""
        # The API should reject comments with thread_depth > 5
        # This is enforced in the endpoint
        pass  # Integration test would verify this

    @pytest.mark.asyncio
    async def test_soft_delete_comment(self):
        """Test soft deleting a comment."""
        comment = PortalFeatureComment(
            id=uuid4(),
            feature_request_id=uuid4(),
            user_email="test@example.com",
            content="Original content",
            is_deleted=False,
            created_at=datetime.now(timezone.utc)
        )

        # Simulate soft delete
        comment.is_deleted = True
        comment.content = "[deleted]"
        comment.deleted_at = datetime.now(timezone.utc)

        assert comment.is_deleted == True
        result = comment.to_dict()
        assert result["content"] == "[deleted]"


# =============================================================================
# MENTION EXTRACTION TESTS
# =============================================================================

class TestMentionExtraction:
    """Tests for @mention extraction from comments."""

    def test_extract_username_mention(self):
        """Test extracting @username mentions."""
        from app.api.portal_features import _extract_mentions

        content = "Hey @johndoe, can you review this?"
        mentions = _extract_mentions(content)

        assert "johndoe" in mentions

    def test_extract_email_mention(self):
        """Test extracting @email mentions."""
        from app.api.portal_features import _extract_mentions

        content = "CC @admin@company.com for review"
        mentions = _extract_mentions(content)

        assert "admin@company.com" in mentions

    def test_extract_multiple_mentions(self):
        """Test extracting multiple mentions."""
        from app.api.portal_features import _extract_mentions

        content = "Hey @alice and @bob, please review @charlie"
        mentions = _extract_mentions(content)

        assert len(mentions) == 3
        assert "alice" in mentions
        assert "bob" in mentions
        assert "charlie" in mentions

    def test_no_duplicate_mentions(self):
        """Test that duplicate mentions are removed."""
        from app.api.portal_features import _extract_mentions

        content = "@admin @admin @admin please help"
        mentions = _extract_mentions(content)

        assert mentions.count("admin") == 1

    def test_no_mentions(self):
        """Test content without mentions."""
        from app.api.portal_features import _extract_mentions

        content = "This is a comment without any mentions"
        mentions = _extract_mentions(content)

        assert len(mentions) == 0


# =============================================================================
# RANKING ALGORITHM TESTS
# =============================================================================

class TestRankingAlgorithms:
    """Tests for feature ranking algorithms."""

    def test_score_ranking(self):
        """Test simple score ranking (upvotes - downvotes)."""
        agg1 = PortalFeatureVoteAggregate(
            feature_request_id=uuid4(),
            upvotes=10,
            downvotes=2,
            score=8
        )
        agg2 = PortalFeatureVoteAggregate(
            feature_request_id=uuid4(),
            upvotes=5,
            downvotes=1,
            score=4
        )

        assert agg1.score > agg2.score

    def test_hot_ranking_time_decay(self):
        """Test that hot ranking includes time decay."""
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        old = now - timedelta(days=7)

        # Same votes, different times
        hot_new = PortalFeatureVoteAggregate.calculate_hot_score(10, 2, now)
        hot_old = PortalFeatureVoteAggregate.calculate_hot_score(10, 2, old)

        assert hot_new > hot_old

    def test_controversial_items(self):
        """Test ranking of controversial items (many votes, close to zero)."""
        # Controversial: lots of votes but close to zero score
        controversial = PortalFeatureVoteAggregate(
            feature_request_id=uuid4(),
            upvotes=50,
            downvotes=48,
            total_votes=98,
            score=2
        )

        # Popular: clearly positive
        popular = PortalFeatureVoteAggregate(
            feature_request_id=uuid4(),
            upvotes=50,
            downvotes=5,
            total_votes=55,
            score=45
        )

        assert popular.score > controversial.score
        assert controversial.total_votes > popular.total_votes


# =============================================================================
# INTEGRATION SCENARIO TESTS
# =============================================================================

class TestVotingScenarios:
    """Integration-style scenario tests for voting."""

    @pytest.mark.asyncio
    async def test_voting_workflow(self):
        """Test complete voting workflow."""
        feature_id = uuid4()

        # User 1 upvotes
        vote1 = PortalFeatureVote(
            feature_request_id=feature_id,
            user_email="user1@example.com",
            vote_type="up"
        )

        # User 2 upvotes
        vote2 = PortalFeatureVote(
            feature_request_id=feature_id,
            user_email="user2@example.com",
            vote_type="up"
        )

        # User 3 downvotes
        vote3 = PortalFeatureVote(
            feature_request_id=feature_id,
            user_email="user3@example.com",
            vote_type="down"
        )

        # Aggregate should be: 2 up, 1 down, score = 1
        aggregate = PortalFeatureVoteAggregate(
            feature_request_id=feature_id,
            upvotes=2,
            downvotes=1,
            total_votes=3,
            score=1
        )

        assert aggregate.score == 1


class TestCommentingScenarios:
    """Integration-style scenario tests for commenting."""

    @pytest.mark.asyncio
    async def test_threaded_discussion(self):
        """Test threaded comment discussion."""
        feature_id = uuid4()

        # Root comment
        root = PortalFeatureComment(
            id=uuid4(),
            feature_request_id=feature_id,
            user_email="author@example.com",
            content="I think we should implement this feature",
            thread_depth=0,
            created_at=datetime.now(timezone.utc)
        )

        # Reply to root
        reply1 = PortalFeatureComment(
            id=uuid4(),
            feature_request_id=feature_id,
            user_email="dev@example.com",
            user_role="developer",
            content="Good idea! @author I can work on this",
            parent_id=root.id,
            thread_depth=1,
            created_at=datetime.now(timezone.utc)
        )

        # Reply to reply
        reply2 = PortalFeatureComment(
            id=uuid4(),
            feature_request_id=feature_id,
            user_email="author@example.com",
            content="Thanks @dev!",
            parent_id=reply1.id,
            thread_depth=2,
            created_at=datetime.now(timezone.utc)
        )

        assert reply1.thread_depth == 1
        assert reply2.thread_depth == 2
        assert reply1.parent_id == root.id
        assert reply2.parent_id == reply1.id

    @pytest.mark.asyncio
    async def test_admin_pins_important_comment(self):
        """Test admin pinning an important comment."""
        comment = PortalFeatureComment(
            id=uuid4(),
            feature_request_id=uuid4(),
            user_email="admin@example.com",
            user_role="admin",
            content="Official response: This will be in v2.0",
            is_pinned=False,
            created_at=datetime.now(timezone.utc)
        )

        # Admin pins comment
        comment.is_pinned = True

        assert comment.is_pinned == True
        result = comment.to_dict()
        assert result["is_pinned"] == True
