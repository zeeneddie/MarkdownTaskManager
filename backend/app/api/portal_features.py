"""
Week 88-90: Portal Feature Request API

API endpoints for customer portal feature requests:
- Feature submission from external portal
- Classification with Peter agent
- Epic/feature mapping
- Status tracking and reporting
- Week 90: Voting and Comments systems
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
import logging
import re
import markdown

from app.database import get_db
from app.services.portal_feature_request_service import PortalFeatureRequestService
from app.models.portal_voting import (
    PortalFeatureVote,
    PortalFeatureComment,
    PortalFeatureVoteAggregate
)
from app.models.graph_workflow import PortalFeatureRequest

router = APIRouter(prefix="/api/portal/features", tags=["Portal Features"])
logger = logging.getLogger(__name__)


# =============================================================================
# Request/Response Models
# =============================================================================

class FeatureRequestSubmit(BaseModel):
    """Request model for submitting a feature request."""
    user_email: EmailStr
    title: str = Field(..., min_length=5, max_length=500)
    description: Optional[str] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    category: Optional[str] = None
    user_name: Optional[str] = None
    organization: Optional[str] = None
    external_id: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class FeatureRequestUpdate(BaseModel):
    """Request model for updating a feature request."""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None


class MappingConfirmation(BaseModel):
    """Request model for confirming epic mapping."""
    epic_id: str
    feature_id: Optional[str] = None


class SprintAssignment(BaseModel):
    """Request model for sprint assignment."""
    sprint_id: int


class ClassificationRequest(BaseModel):
    """Request model for classification options."""
    use_llm: bool = True


# =============================================================================
# Feature Request CRUD Endpoints
# =============================================================================

@router.post("/submit")
async def submit_feature_request(
    request: FeatureRequestSubmit,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a new feature request from the customer portal.

    Returns the created request with status 'submitted'.
    """
    service = PortalFeatureRequestService(db)
    result = await service.submit_feature_request(
        user_email=request.user_email,
        title=request.title,
        description=request.description,
        priority=request.priority,
        category=request.category,
        user_name=request.user_name,
        organization=request.organization,
        external_id=request.external_id,
        attachments=request.attachments,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.get("/{request_id}")
async def get_feature_request(
    request_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a feature request by ID."""
    service = PortalFeatureRequestService(db)
    result = await service.get_feature_request(request_id)

    if not result:
        raise HTTPException(status_code=404, detail="Feature request not found")

    return result


@router.get("")
async def list_feature_requests(
    status: Optional[str] = Query(None),
    user_email: Optional[str] = Query(None),
    organization: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None),
    work_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List feature requests with optional filters."""
    service = PortalFeatureRequestService(db)
    return await service.list_feature_requests(
        status=status,
        user_email=user_email,
        organization=organization,
        project_id=project_id,
        work_type=work_type,
        limit=limit,
        offset=offset,
    )


@router.patch("/{request_id}")
async def update_feature_request(
    request_id: str,
    updates: FeatureRequestUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a feature request."""
    service = PortalFeatureRequestService(db)
    update_dict = updates.model_dump(exclude_unset=True)
    result = await service.update_feature_request(request_id, update_dict)

    if not result.get("success"):
        raise HTTPException(
            status_code=404 if "not found" in result.get("error", "").lower() else 400,
            detail=result.get("error"),
        )

    return result


# =============================================================================
# Classification Endpoints
# =============================================================================

@router.post("/{request_id}/classify")
async def classify_feature_request(
    request_id: str,
    options: ClassificationRequest = ClassificationRequest(),
    db: AsyncSession = Depends(get_db),
):
    """
    Classify a feature request using Peter agent.

    Determines work type (BUG, NEW_FEATURE, ENHANCEMENT, etc.)
    and provides classification confidence and reasoning.
    """
    service = PortalFeatureRequestService(db)
    result = await service.classify_feature_request(
        request_id,
        use_llm=options.use_llm,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=404 if "not found" in result.get("error", "").lower() else 400,
            detail=result.get("error"),
        )

    return result


# =============================================================================
# Mapping Endpoints
# =============================================================================

@router.post("/{request_id}/map/{project_id}")
async def map_to_epic(
    request_id: str,
    project_id: int,
    auto_suggest: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """
    Map a feature request to an epic in a project.

    Returns mapping suggestions based on title/description similarity.
    """
    service = PortalFeatureRequestService(db)
    result = await service.map_to_epic(
        request_id,
        project_id,
        auto_suggest=auto_suggest,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=404 if "not found" in result.get("error", "").lower() else 400,
            detail=result.get("error"),
        )

    return result


@router.post("/{request_id}/confirm-mapping")
async def confirm_mapping(
    request_id: str,
    mapping: MappingConfirmation,
    db: AsyncSession = Depends(get_db),
):
    """Confirm the epic/feature mapping for a feature request."""
    service = PortalFeatureRequestService(db)
    result = await service.confirm_mapping(
        request_id,
        epic_id=mapping.epic_id,
        feature_id=mapping.feature_id,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=404 if "not found" in result.get("error", "").lower() else 400,
            detail=result.get("error"),
        )

    return result


# =============================================================================
# Sprint/Kanban Endpoints
# =============================================================================

@router.post("/{request_id}/assign-sprint")
async def assign_to_sprint(
    request_id: str,
    assignment: SprintAssignment,
    db: AsyncSession = Depends(get_db),
):
    """Assign a feature request to a sprint."""
    service = PortalFeatureRequestService(db)
    result = await service.assign_to_sprint(
        request_id,
        sprint_id=assignment.sprint_id,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=404 if "not found" in result.get("error", "").lower() else 400,
            detail=result.get("error"),
        )

    return result


@router.post("/{request_id}/create-kanban")
async def create_kanban_item(
    request_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Create a kanban item from a feature request."""
    service = PortalFeatureRequestService(db)
    result = await service.create_kanban_item(request_id)

    if not result.get("success"):
        raise HTTPException(
            status_code=404 if "not found" in result.get("error", "").lower() else 400,
            detail=result.get("error"),
        )

    return result


# =============================================================================
# Full Processing Pipeline
# =============================================================================

@router.post("/{request_id}/process")
async def process_feature_request(
    request_id: str,
    project_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Process a feature request through the full pipeline.

    Steps:
    1. Classify with Peter agent
    2. Map to epic (if project_id provided)
    3. Return recommended next actions
    """
    service = PortalFeatureRequestService(db)
    result = await service.process_feature_request(
        request_id,
        project_id=project_id,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=404 if "not found" in result.get("error", "").lower() else 400,
            detail=result.get("error"),
        )

    return result


# =============================================================================
# Statistics Endpoints
# =============================================================================

@router.get("/stats/overview")
async def get_statistics(
    organization: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get feature request statistics."""
    service = PortalFeatureRequestService(db)
    return await service.get_statistics(
        organization=organization,
        project_id=project_id,
        days=days,
    )


@router.get("/user/{user_email}")
async def get_user_requests(
    user_email: str,
    include_completed: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """Get all feature requests for a specific user."""
    service = PortalFeatureRequestService(db)
    return await service.get_user_requests(
        user_email=user_email,
        include_completed=include_completed,
    )


# =============================================================================
# WEEK 90: VOTING SYSTEM
# =============================================================================

class VoteRequest(BaseModel):
    """Request model for casting a vote."""
    user_email: EmailStr
    user_name: Optional[str] = None
    vote_type: str = Field(..., pattern="^(up|down)$")


class VoteResponse(BaseModel):
    """Response model for vote operations."""
    success: bool
    vote_id: Optional[str] = None
    action: str  # created, updated, removed
    new_score: int
    upvotes: int
    downvotes: int


@router.post("/{request_id}/votes")
async def cast_vote(
    request_id: str,
    vote: VoteRequest,
    db: AsyncSession = Depends(get_db),
) -> VoteResponse:
    """
    Cast a vote on a feature request.

    If the user has already voted, updates their vote.
    Returns the new aggregate score.
    """
    try:
        request_uuid = UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")

    # Check if feature request exists
    result = await db.execute(
        select(PortalFeatureRequest).where(PortalFeatureRequest.id == request_uuid)
    )
    feature_request = result.scalar_one_or_none()
    if not feature_request:
        raise HTTPException(status_code=404, detail="Feature request not found")

    # Check for existing vote
    result = await db.execute(
        select(PortalFeatureVote).where(
            and_(
                PortalFeatureVote.feature_request_id == request_uuid,
                PortalFeatureVote.user_email == vote.user_email
            )
        )
    )
    existing_vote = result.scalar_one_or_none()

    action = "created"
    if existing_vote:
        if existing_vote.vote_type == vote.vote_type:
            # Same vote type - remove vote (toggle off)
            await db.delete(existing_vote)
            action = "removed"
            vote_id = None
        else:
            # Different vote type - update vote
            existing_vote.vote_type = vote.vote_type
            existing_vote.updated_at = datetime.utcnow()
            action = "updated"
            vote_id = str(existing_vote.id)
    else:
        # New vote
        new_vote = PortalFeatureVote(
            feature_request_id=request_uuid,
            user_email=vote.user_email,
            user_name=vote.user_name,
            vote_type=vote.vote_type,
        )
        db.add(new_vote)
        vote_id = str(new_vote.id)

    await db.commit()

    # Update aggregates
    aggregates = await _update_vote_aggregates(db, request_uuid)

    # Update feature request vote_score
    await db.execute(
        update(PortalFeatureRequest)
        .where(PortalFeatureRequest.id == request_uuid)
        .values(vote_score=aggregates["score"])
    )
    await db.commit()

    return VoteResponse(
        success=True,
        vote_id=vote_id,
        action=action,
        new_score=aggregates["score"],
        upvotes=aggregates["upvotes"],
        downvotes=aggregates["downvotes"],
    )


@router.delete("/{request_id}/votes")
async def remove_vote(
    request_id: str,
    user_email: EmailStr = Query(...),
    db: AsyncSession = Depends(get_db),
) -> VoteResponse:
    """Remove a user's vote from a feature request."""
    try:
        request_uuid = UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")

    # Find and delete the vote
    result = await db.execute(
        select(PortalFeatureVote).where(
            and_(
                PortalFeatureVote.feature_request_id == request_uuid,
                PortalFeatureVote.user_email == user_email
            )
        )
    )
    vote = result.scalar_one_or_none()

    if not vote:
        raise HTTPException(status_code=404, detail="Vote not found")

    await db.delete(vote)
    await db.commit()

    # Update aggregates
    aggregates = await _update_vote_aggregates(db, request_uuid)

    # Update feature request vote_score
    await db.execute(
        update(PortalFeatureRequest)
        .where(PortalFeatureRequest.id == request_uuid)
        .values(vote_score=aggregates["score"])
    )
    await db.commit()

    return VoteResponse(
        success=True,
        vote_id=None,
        action="removed",
        new_score=aggregates["score"],
        upvotes=aggregates["upvotes"],
        downvotes=aggregates["downvotes"],
    )


@router.get("/{request_id}/votes")
async def get_votes(
    request_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get vote information for a feature request."""
    try:
        request_uuid = UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")

    # Get aggregate
    result = await db.execute(
        select(PortalFeatureVoteAggregate)
        .where(PortalFeatureVoteAggregate.feature_request_id == request_uuid)
    )
    aggregate = result.scalar_one_or_none()

    if not aggregate:
        return {
            "feature_request_id": request_id,
            "upvotes": 0,
            "downvotes": 0,
            "score": 0,
            "total_votes": 0,
            "hot_score": 0.0,
        }

    return aggregate.to_dict()


@router.get("/{request_id}/votes/check")
async def check_user_vote(
    request_id: str,
    user_email: EmailStr = Query(...),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Check if a user has voted on a feature request."""
    try:
        request_uuid = UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")

    result = await db.execute(
        select(PortalFeatureVote).where(
            and_(
                PortalFeatureVote.feature_request_id == request_uuid,
                PortalFeatureVote.user_email == user_email
            )
        )
    )
    vote = result.scalar_one_or_none()

    return {
        "has_voted": vote is not None,
        "vote_type": vote.vote_type if vote else None,
        "vote_id": str(vote.id) if vote else None,
    }


@router.get("/ranked")
async def get_ranked_features(
    sort_by: str = Query("score", pattern="^(score|hot|recent|votes)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get feature requests ranked by votes.

    Sort options:
    - score: Simple upvotes - downvotes
    - hot: Reddit-style hot ranking (includes time decay)
    - recent: Most recently voted
    - votes: Total vote count
    """
    # Build base query
    query = (
        select(PortalFeatureRequest, PortalFeatureVoteAggregate)
        .outerjoin(
            PortalFeatureVoteAggregate,
            PortalFeatureRequest.id == PortalFeatureVoteAggregate.feature_request_id
        )
    )

    if status:
        query = query.where(PortalFeatureRequest.status == status)

    # Apply sorting
    if sort_by == "score":
        query = query.order_by(
            func.coalesce(PortalFeatureVoteAggregate.score, 0).desc()
        )
    elif sort_by == "hot":
        query = query.order_by(
            func.coalesce(PortalFeatureVoteAggregate.hot_score, 0).desc()
        )
    elif sort_by == "recent":
        query = query.order_by(
            func.coalesce(PortalFeatureVoteAggregate.last_vote_at, PortalFeatureRequest.created_at).desc()
        )
    elif sort_by == "votes":
        query = query.order_by(
            func.coalesce(PortalFeatureVoteAggregate.total_votes, 0).desc()
        )

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    features = []
    for feature, aggregate in rows:
        feature_dict = {
            "id": str(feature.id),
            "title": feature.title,
            "description": feature.description,
            "status": feature.status,
            "priority": feature.priority,
            "work_type": feature.work_type,
            "created_at": feature.created_at.isoformat() if feature.created_at else None,
            "vote_score": feature.vote_score or 0,
            "comment_count": feature.comment_count or 0,
        }
        if aggregate:
            feature_dict["votes"] = aggregate.to_dict()
        else:
            feature_dict["votes"] = {
                "upvotes": 0,
                "downvotes": 0,
                "score": 0,
                "total_votes": 0,
            }
        features.append(feature_dict)

    # Get total count
    count_query = select(func.count(PortalFeatureRequest.id))
    if status:
        count_query = count_query.where(PortalFeatureRequest.status == status)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return {
        "features": features,
        "total": total,
        "limit": limit,
        "offset": offset,
        "sort_by": sort_by,
    }


async def _update_vote_aggregates(
    db: AsyncSession,
    feature_request_id: UUID
) -> Dict[str, Any]:
    """
    Update vote aggregates for a feature request.

    Recalculates upvotes, downvotes, score, and hot score.
    """
    # Count votes
    upvote_result = await db.execute(
        select(func.count(PortalFeatureVote.id))
        .where(
            and_(
                PortalFeatureVote.feature_request_id == feature_request_id,
                PortalFeatureVote.vote_type == "up"
            )
        )
    )
    upvotes = upvote_result.scalar() or 0

    downvote_result = await db.execute(
        select(func.count(PortalFeatureVote.id))
        .where(
            and_(
                PortalFeatureVote.feature_request_id == feature_request_id,
                PortalFeatureVote.vote_type == "down"
            )
        )
    )
    downvotes = downvote_result.scalar() or 0

    total_votes = upvotes + downvotes
    score = upvotes - downvotes

    # Get feature request creation time for hot score
    result = await db.execute(
        select(PortalFeatureRequest.created_at)
        .where(PortalFeatureRequest.id == feature_request_id)
    )
    created_at = result.scalar()

    # Calculate hot score
    hot_score = PortalFeatureVoteAggregate.calculate_hot_score(
        upvotes, downvotes, created_at or datetime.utcnow()
    )

    # Upsert aggregate
    result = await db.execute(
        select(PortalFeatureVoteAggregate)
        .where(PortalFeatureVoteAggregate.feature_request_id == feature_request_id)
    )
    aggregate = result.scalar_one_or_none()

    if aggregate:
        aggregate.upvotes = upvotes
        aggregate.downvotes = downvotes
        aggregate.total_votes = total_votes
        aggregate.score = score
        aggregate.hot_score = hot_score
        aggregate.last_vote_at = datetime.utcnow()
        aggregate.computed_at = datetime.utcnow()
    else:
        aggregate = PortalFeatureVoteAggregate(
            feature_request_id=feature_request_id,
            upvotes=upvotes,
            downvotes=downvotes,
            total_votes=total_votes,
            score=score,
            hot_score=hot_score,
            last_vote_at=datetime.utcnow(),
        )
        db.add(aggregate)

    await db.commit()

    return {
        "upvotes": upvotes,
        "downvotes": downvotes,
        "total_votes": total_votes,
        "score": score,
        "hot_score": hot_score,
    }


# =============================================================================
# WEEK 90: COMMENTS SYSTEM
# =============================================================================

class CommentCreate(BaseModel):
    """Request model for creating a comment."""
    user_email: EmailStr
    user_name: Optional[str] = None
    user_role: Optional[str] = Field(None, pattern="^(customer|developer|admin)$")
    content: str = Field(..., min_length=1, max_length=10000)
    parent_id: Optional[str] = None  # For replies


class CommentUpdate(BaseModel):
    """Request model for updating a comment."""
    content: str = Field(..., min_length=1, max_length=10000)


class CommentResponse(BaseModel):
    """Response model for comment operations."""
    success: bool
    comment_id: str
    message: str


@router.post("/{request_id}/comments")
async def create_comment(
    request_id: str,
    comment: CommentCreate,
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    """
    Create a comment on a feature request.

    Supports threading via parent_id.
    Automatically extracts @mentions from content.
    """
    try:
        request_uuid = UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")

    # Check if feature request exists
    result = await db.execute(
        select(PortalFeatureRequest).where(PortalFeatureRequest.id == request_uuid)
    )
    feature_request = result.scalar_one_or_none()
    if not feature_request:
        raise HTTPException(status_code=404, detail="Feature request not found")

    # Process parent_id if provided
    parent_uuid = None
    thread_depth = 0
    if comment.parent_id:
        try:
            parent_uuid = UUID(comment.parent_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parent ID format")

        # Check parent exists
        result = await db.execute(
            select(PortalFeatureComment).where(PortalFeatureComment.id == parent_uuid)
        )
        parent_comment = result.scalar_one_or_none()
        if not parent_comment:
            raise HTTPException(status_code=404, detail="Parent comment not found")

        thread_depth = parent_comment.thread_depth + 1
        if thread_depth > 5:
            raise HTTPException(status_code=400, detail="Maximum nesting depth exceeded")

    # Extract mentions (@username or @email)
    mentions = _extract_mentions(comment.content)

    # Render markdown to HTML
    content_html = markdown.markdown(
        comment.content,
        extensions=['fenced_code', 'tables', 'nl2br']
    )

    # Create comment
    new_comment = PortalFeatureComment(
        feature_request_id=request_uuid,
        user_email=comment.user_email,
        user_name=comment.user_name,
        user_role=comment.user_role,
        content=comment.content,
        content_html=content_html,
        parent_id=parent_uuid,
        thread_depth=thread_depth,
        mentions=mentions if mentions else None,
    )
    db.add(new_comment)

    # Update comment count
    await db.execute(
        update(PortalFeatureRequest)
        .where(PortalFeatureRequest.id == request_uuid)
        .values(comment_count=PortalFeatureRequest.comment_count + 1)
    )

    await db.commit()
    await db.refresh(new_comment)

    return CommentResponse(
        success=True,
        comment_id=str(new_comment.id),
        message="Comment created successfully",
    )


@router.get("/{request_id}/comments")
async def get_comments(
    request_id: str,
    include_deleted: bool = Query(False),
    threaded: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get comments for a feature request.

    If threaded=True, returns nested comment structure.
    If threaded=False, returns flat list ordered by creation time.
    """
    try:
        request_uuid = UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")

    # Build query
    query = (
        select(PortalFeatureComment)
        .where(PortalFeatureComment.feature_request_id == request_uuid)
    )

    if not include_deleted:
        query = query.where(PortalFeatureComment.is_deleted == False)

    query = query.order_by(PortalFeatureComment.created_at.asc())

    result = await db.execute(query)
    comments = result.scalars().all()

    if threaded:
        # Build threaded structure
        comment_dict = {str(c.id): c.to_dict() for c in comments}
        root_comments = []

        for c in comments:
            c_dict = comment_dict[str(c.id)]
            c_dict["replies"] = []

            if c.parent_id:
                parent_key = str(c.parent_id)
                if parent_key in comment_dict:
                    comment_dict[parent_key]["replies"].append(c_dict)
            else:
                root_comments.append(c_dict)

        return {
            "feature_request_id": request_id,
            "comments": root_comments,
            "total_count": len(comments),
            "threaded": True,
        }
    else:
        return {
            "feature_request_id": request_id,
            "comments": [c.to_dict() for c in comments],
            "total_count": len(comments),
            "threaded": False,
        }


@router.get("/{request_id}/comments/{comment_id}")
async def get_comment(
    request_id: str,
    comment_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get a specific comment by ID."""
    try:
        comment_uuid = UUID(comment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid comment ID format")

    result = await db.execute(
        select(PortalFeatureComment).where(PortalFeatureComment.id == comment_uuid)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    return comment.to_dict(include_replies=True)


@router.patch("/{request_id}/comments/{comment_id}")
async def update_comment(
    request_id: str,
    comment_id: str,
    update_data: CommentUpdate,
    user_email: EmailStr = Query(...),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    """
    Update a comment.

    Only the comment author can edit their comment.
    """
    try:
        comment_uuid = UUID(comment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid comment ID format")

    result = await db.execute(
        select(PortalFeatureComment).where(PortalFeatureComment.id == comment_uuid)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_email != user_email:
        raise HTTPException(status_code=403, detail="Only the author can edit this comment")

    if comment.is_deleted:
        raise HTTPException(status_code=400, detail="Cannot edit a deleted comment")

    # Update content
    comment.content = update_data.content
    comment.content_html = markdown.markdown(
        update_data.content,
        extensions=['fenced_code', 'tables', 'nl2br']
    )
    comment.mentions = _extract_mentions(update_data.content) or None
    comment.is_edited = True
    comment.updated_at = datetime.utcnow()

    await db.commit()

    return CommentResponse(
        success=True,
        comment_id=str(comment.id),
        message="Comment updated successfully",
    )


@router.delete("/{request_id}/comments/{comment_id}")
async def delete_comment(
    request_id: str,
    comment_id: str,
    user_email: EmailStr = Query(...),
    hard_delete: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    """
    Delete a comment.

    By default, soft-deletes (marks as deleted but preserves for thread integrity).
    Use hard_delete=True to permanently remove.
    """
    try:
        request_uuid = UUID(request_id)
        comment_uuid = UUID(comment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    result = await db.execute(
        select(PortalFeatureComment).where(PortalFeatureComment.id == comment_uuid)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_email != user_email:
        raise HTTPException(status_code=403, detail="Only the author can delete this comment")

    if hard_delete:
        await db.delete(comment)
    else:
        comment.is_deleted = True
        comment.deleted_at = datetime.utcnow()
        comment.content = "[deleted]"
        comment.content_html = "<p>[deleted]</p>"

    # Update comment count
    await db.execute(
        update(PortalFeatureRequest)
        .where(PortalFeatureRequest.id == request_uuid)
        .values(comment_count=func.greatest(PortalFeatureRequest.comment_count - 1, 0))
    )

    await db.commit()

    return CommentResponse(
        success=True,
        comment_id=comment_id,
        message="Comment deleted successfully",
    )


@router.post("/{request_id}/comments/{comment_id}/pin")
async def pin_comment(
    request_id: str,
    comment_id: str,
    user_email: EmailStr = Query(...),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    """Pin a comment (admin only in production)."""
    try:
        comment_uuid = UUID(comment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid comment ID format")

    result = await db.execute(
        select(PortalFeatureComment).where(PortalFeatureComment.id == comment_uuid)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment.is_pinned = not comment.is_pinned
    await db.commit()

    action = "pinned" if comment.is_pinned else "unpinned"
    return CommentResponse(
        success=True,
        comment_id=str(comment.id),
        message=f"Comment {action} successfully",
    )


def _extract_mentions(content: str) -> List[str]:
    """Extract @mentions from comment content."""
    # Match @username or @email patterns
    pattern = r'@([\w.+-]+@[\w.-]+\.\w+|[\w.-]+)'
    matches = re.findall(pattern, content)
    return list(set(matches))
