"""
Kanban API - Task Board Management

9-lane Kanban board for Stories, Tasks, and Bugs:
- Backlog (draft, todo) - New items, not yet analyzed
- Analysis (analyzing) - Being estimated/analyzed
- Planned (ready for sprint) - Estimated and ready to plan
- Build (in_progress) - Code being written
- Test (testing) - Code being tested
- In Review (in_review) - Code review
- Blocked - Waiting on external dependency
- Human Needed - Agent needs human intervention
- Done - Completed

Flow: Backlog → Analysis → Planned → Build → Test → In Review → Done
       (new)    (estimate)  (sprint)  (code)  (qa)    (review)

Build ↔ Test allows 3 retries before escalating to Human Needed.
Items MUST have estimation (story_points) before moving to Planned.
Real-time updates via WebSocket.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
import logging

from app.database import get_db
from app.models.task_hierarchy import Story, Task, StoryStatus, TaskStatus, Epic, Feature
from app.models.bug import Bug, BugStatus, BugSeverity
from app.models.item import Item
from app.api.websocket import manager, Channel, EventType
from app.services.kanban_event_service import KanbanEventService
from app.services.kanban_agent_service import KanbanAgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kanban", tags=["kanban"])


# ============================================================================
# ENUMS AND SCHEMAS
# ============================================================================

class KanbanLane(str, Enum):
    """9 Kanban lanes - Flow: Backlog → Analysis → Planned → Build → Test → In Review → Done"""
    BACKLOG = "backlog"          # New items, not yet analyzed
    ANALYSIS = "analysis"        # Being estimated/analyzed (FP/SP)
    PLANNED = "planned"          # Estimated and ready for sprint
    BUILD = "build"              # Code being written (replaces IN_PROGRESS)
    TEST = "test"                # Code being tested (NEW)
    IN_REVIEW = "in_review"      # Code review
    BLOCKED = "blocked"          # Waiting on external dependency
    HUMAN_NEEDED = "human_needed"  # Agent needs human intervention
    DONE = "done"


class ItemType(str, Enum):
    """Kanban item types"""
    STORY = "story"
    TASK = "task"
    BUG = "bug"


class KanbanItem(BaseModel):
    """Kanban board item (Story, Task, or Bug)"""
    id: str
    type: ItemType
    title: str
    description: Optional[str] = None
    lane: KanbanLane
    priority: str = "medium"
    story_points: Optional[int] = None
    estimated_hours: Optional[float] = None
    assigned_to: Optional[str] = None
    parent_id: Optional[str] = None  # story_id for tasks, feature_id for stories
    parent_title: Optional[str] = None
    epic_title: Optional[str] = None
    project_name: Optional[str] = None  # Project this item belongs to
    is_blocked: bool = False
    blocked_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # Bug-specific fields
    bug_number: Optional[str] = None  # BUG-001
    severity: Optional[str] = None  # critical, high, medium, low

    model_config = ConfigDict(from_attributes=True)


class MoveItemRequest(BaseModel):
    """Request to move item between lanes"""
    item_id: str
    item_type: ItemType
    target_lane: KanbanLane
    blocked_reason: Optional[str] = None


class UpdateItemRequest(BaseModel):
    """Request to update item details"""
    assigned_to: Optional[str] = None
    priority: Optional[str] = None
    story_points: Optional[int] = None
    estimated_hours: Optional[float] = None
    blocked_reason: Optional[str] = None


class KanbanStats(BaseModel):
    """Kanban board statistics"""
    total_items: int
    by_lane: Dict[str, int]
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
    total_story_points: int
    total_estimated_hours: float
    blocked_count: int


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def status_to_lane(status: str, is_blocked: bool = False, item_type: str = None) -> KanbanLane:
    """Convert Story/Task/Bug status to Kanban lane"""
    if is_blocked:
        return KanbanLane.BLOCKED

    status_map = {
        # Story statuses
        "draft": KanbanLane.BACKLOG,
        "ready": KanbanLane.PLANNED,  # Ready for sprint → Planned lane
        "in_progress": KanbanLane.BUILD,  # In progress → Build lane
        "in_review": KanbanLane.IN_REVIEW,
        "done": KanbanLane.DONE,
        "blocked": KanbanLane.BLOCKED,
        # Task statuses
        "todo": KanbanLane.BACKLOG,
        "planned": KanbanLane.PLANNED,  # Explicit planned status
        # Bug statuses
        "confirmed": KanbanLane.BACKLOG,  # Confirmed bugs wait in backlog
        "analysis": KanbanLane.ANALYSIS,  # Being estimated/analyzed
        "testing": KanbanLane.TEST,  # QA validation → Test lane (NEW)
        "wont_fix": KanbanLane.DONE,  # Declined = done
        "duplicate": KanbanLane.DONE,  # Duplicate = done
    }
    return status_map.get(status, KanbanLane.BACKLOG)


def lane_to_status(lane: KanbanLane, item_type: ItemType) -> tuple[str, bool]:
    """Convert Kanban lane to Story/Task/Bug status and blocked flag"""
    is_blocked = lane == KanbanLane.BLOCKED or lane == KanbanLane.HUMAN_NEEDED

    if item_type == ItemType.STORY:
        lane_map = {
            KanbanLane.BACKLOG: "draft",
            KanbanLane.ANALYSIS: "draft",  # Stories being analyzed stay draft
            KanbanLane.PLANNED: "ready",  # Planned → ready for sprint
            KanbanLane.BUILD: "in_progress",  # Build lane → in_progress status
            KanbanLane.TEST: "in_progress",  # Test lane → still in_progress (testing phase)
            KanbanLane.IN_REVIEW: "in_review",
            KanbanLane.BLOCKED: "in_progress",
            KanbanLane.HUMAN_NEEDED: "in_progress",
            KanbanLane.DONE: "done",
        }
    elif item_type == ItemType.BUG:
        lane_map = {
            KanbanLane.BACKLOG: "confirmed",
            KanbanLane.ANALYSIS: "analysis",
            KanbanLane.PLANNED: "planned",
            KanbanLane.BUILD: "in_progress",  # Build lane → in_progress
            KanbanLane.TEST: "testing",  # Test lane → testing status
            KanbanLane.IN_REVIEW: "in_review",
            KanbanLane.BLOCKED: "in_progress",
            KanbanLane.HUMAN_NEEDED: "in_progress",
            KanbanLane.DONE: "done",
        }
    else:  # TASK
        lane_map = {
            KanbanLane.BACKLOG: "todo",
            KanbanLane.ANALYSIS: "todo",  # Tasks being analyzed stay todo
            KanbanLane.PLANNED: "todo",  # Tasks don't have planned status
            KanbanLane.BUILD: "in_progress",  # Build lane → in_progress
            KanbanLane.TEST: "in_progress",  # Test lane → still in_progress
            KanbanLane.IN_REVIEW: "in_review",
            KanbanLane.BLOCKED: "in_progress",
            KanbanLane.HUMAN_NEEDED: "in_progress",
            KanbanLane.DONE: "done",
        }

    return lane_map.get(lane, "todo"), is_blocked


def story_to_kanban_item(story: Story, feature_title: str = None, epic_title: str = None, project_name: str = None) -> KanbanItem:
    """Convert Story model to KanbanItem"""
    return KanbanItem(
        id=str(story.id),
        type=ItemType.STORY,
        title=story.title,
        description=story.description[:200] + "..." if story.description and len(story.description) > 200 else story.description,
        lane=status_to_lane(story.status, story.is_blocked),
        priority=story.priority,
        story_points=story.story_points,
        estimated_hours=story.estimated_hours,
        assigned_to=story.assigned_to,
        parent_id=str(story.feature_id) if story.feature_id else None,
        parent_title=feature_title,
        epic_title=epic_title,
        project_name=project_name,
        is_blocked=story.is_blocked,
        blocked_reason=story.blocked_reason,
        created_at=story.created_at,
        updated_at=story.updated_at,
    )


def task_to_kanban_item(task: Task, story_title: str = None, epic_title: str = None, project_name: str = None) -> KanbanItem:
    """Convert Task model to KanbanItem"""
    return KanbanItem(
        id=str(task.id),
        type=ItemType.TASK,
        title=task.title,
        description=task.description[:200] + "..." if task.description and len(task.description) > 200 else task.description,
        lane=status_to_lane(task.status, task.is_blocked),
        priority=task.priority,
        story_points=None,
        estimated_hours=task.estimated_hours,
        assigned_to=task.assigned_to,
        parent_id=str(task.story_id) if task.story_id else None,
        parent_title=story_title,
        epic_title=epic_title,
        project_name=project_name,
        is_blocked=task.is_blocked,
        blocked_reason=task.blocked_reason,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def bug_to_kanban_item(bug: Bug, epic_title: str = None, feature_title: str = None, project_name: str = None) -> KanbanItem:
    """Convert Bug model to KanbanItem"""
    return KanbanItem(
        id=str(bug.id),
        type=ItemType.BUG,
        title=bug.title,
        description=bug.description[:200] + "..." if bug.description and len(bug.description) > 200 else bug.description,
        lane=status_to_lane(bug.status, bug.is_blocked),
        priority=bug.priority,
        story_points=bug.story_points,
        estimated_hours=bug.estimated_hours,
        assigned_to=bug.assigned_to,
        parent_id=str(bug.feature_id) if bug.feature_id else None,
        parent_title=feature_title,
        epic_title=epic_title,
        project_name=project_name,
        is_blocked=bug.is_blocked,
        blocked_reason=bug.blocked_reason,
        created_at=bug.created_at,
        updated_at=bug.updated_at,
        # Bug-specific fields
        bug_number=bug.bug_number,
        severity=bug.severity,
    )


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get("/board", response_model=Dict[str, List[KanbanItem]])
async def get_kanban_board(
    project_id: Optional[str] = Query(None, description="Filter by project"),
    epic_id: Optional[str] = Query(None, description="Filter by epic"),
    feature_id: Optional[str] = Query(None, description="Filter by feature"),
    include_stories: bool = Query(True, description="Include stories"),
    include_tasks: bool = Query(True, description="Include tasks"),
    include_bugs: bool = Query(True, description="Include bugs"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get full Kanban board with items organized by lane.

    Returns a dictionary with 8 lanes, each containing a list of items.
    Flow: Backlog → Analysis → Planned → In Progress → In Review → Done
    """
    # Initialize lanes
    board = {lane.value: [] for lane in KanbanLane}

    # Cache for project names to avoid repeated queries
    project_name_cache: Dict[str, str] = {}

    async def get_project_name(pid: Optional[str]) -> Optional[str]:
        """Get project name from cache or database"""
        if not pid:
            return None
        if pid not in project_name_cache:
            project_result = await db.execute(select(Item).where(Item.id == pid))
            project = project_result.scalar_one_or_none()
            project_name_cache[pid] = project.title if project else None
        return project_name_cache.get(pid)

    # Build query for stories
    if include_stories:
        story_stmt = select(Story)

        if project_id:
            story_stmt = story_stmt.where(Story.project_id == project_id)
        if feature_id:
            story_stmt = story_stmt.where(Story.feature_id == feature_id)
        if epic_id:
            # Join through Feature to filter by Epic
            story_stmt = story_stmt.join(Feature).where(Feature.epic_id == epic_id)
        if assigned_to:
            story_stmt = story_stmt.where(Story.assigned_to == assigned_to)

        result = await db.execute(story_stmt)
        stories = result.scalars().all()

        # Get feature, epic titles and project name for context
        for story in stories:
            feature_result = await db.execute(select(Feature).where(Feature.id == story.feature_id))
            feature = feature_result.scalar_one_or_none()
            feature_title = feature.title if feature else None
            epic_title = None
            if feature:
                epic_result = await db.execute(select(Epic).where(Epic.id == feature.epic_id))
                epic = epic_result.scalar_one_or_none()
                epic_title = epic.title if epic else None

            # Get project name
            proj_name = await get_project_name(story.project_id)

            item = story_to_kanban_item(story, feature_title, epic_title, proj_name)
            board[item.lane.value].append(item)

    # Build query for tasks
    if include_tasks:
        task_stmt = select(Task)

        if project_id:
            task_stmt = task_stmt.where(Task.project_id == project_id)
        if feature_id:
            # Join through Story to filter by Feature
            task_stmt = task_stmt.join(Story).where(Story.feature_id == feature_id)
        if epic_id:
            # Join through Story and Feature to filter by Epic
            task_stmt = task_stmt.join(Story).join(Feature).where(Feature.epic_id == epic_id)
        if assigned_to:
            task_stmt = task_stmt.where(Task.assigned_to == assigned_to)

        result = await db.execute(task_stmt)
        tasks = result.scalars().all()

        # Get story, epic titles and project name for context
        for task in tasks:
            story_result = await db.execute(select(Story).where(Story.id == task.story_id))
            story = story_result.scalar_one_or_none()
            story_title = story.title if story else None
            epic_title = None
            if story:
                feature_result = await db.execute(select(Feature).where(Feature.id == story.feature_id))
                feature = feature_result.scalar_one_or_none()
                if feature:
                    epic_result = await db.execute(select(Epic).where(Epic.id == feature.epic_id))
                    epic = epic_result.scalar_one_or_none()
                    epic_title = epic.title if epic else None

            # Get project name
            proj_name = await get_project_name(task.project_id)

            item = task_to_kanban_item(task, story_title, epic_title, proj_name)
            board[item.lane.value].append(item)

    # Build query for bugs
    if include_bugs:
        bug_stmt = select(Bug)

        if project_id:
            bug_stmt = bug_stmt.where(Bug.project_id == project_id)
        if feature_id:
            bug_stmt = bug_stmt.where(Bug.feature_id == feature_id)
        if epic_id:
            bug_stmt = bug_stmt.where(Bug.epic_id == epic_id)
        if assigned_to:
            bug_stmt = bug_stmt.where(Bug.assigned_to == assigned_to)

        result = await db.execute(bug_stmt)
        bugs = result.scalars().all()

        # Get feature and epic titles for context
        for bug in bugs:
            feature_title = None
            epic_title = None
            if bug.feature_id:
                feature_result = await db.execute(select(Feature).where(Feature.id == bug.feature_id))
                feature = feature_result.scalar_one_or_none()
                feature_title = feature.title if feature else None
                if feature and feature.epic_id:
                    epic_result = await db.execute(select(Epic).where(Epic.id == feature.epic_id))
                    epic = epic_result.scalar_one_or_none()
                    epic_title = epic.title if epic else None
            elif bug.epic_id:
                epic_result = await db.execute(select(Epic).where(Epic.id == bug.epic_id))
                epic = epic_result.scalar_one_or_none()
                epic_title = epic.title if epic else None

            # Get project name for bug
            proj_name = await get_project_name(bug.project_id)
            item = bug_to_kanban_item(bug, epic_title, feature_title, proj_name)
            board[item.lane.value].append(item)

    # Sort items within each lane by priority (critical bugs first)
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    for lane in board:
        board[lane].sort(key=lambda x: (priority_order.get(x.priority, 2), x.created_at))

    return board


@router.post("/move")
async def move_item(
    request: MoveItemRequest,
    db: AsyncSession = Depends(get_db),
    skip_dod_validation: bool = Query(False, description="Skip DoD validation (for manual overrides)"),
    skip_quality_gates: bool = Query(False, description="Skip quality gate validation"),
    auto_trigger_agents: bool = Query(True, description="Auto-trigger suggested agents after move")
):
    """
    Move an item to a different lane (drag & drop).

    Updates the item's status and blocked flag based on target lane.
    Validates DoD criteria before allowing transition.
    Validates quality gates for IN_REVIEW transitions.
    Auto-triggers appropriate agents after successful transition.
    Broadcasts the change via WebSocket.
    """
    agent_service = KanbanAgentService(db)
    new_status, is_blocked = lane_to_status(request.target_lane, request.item_type)

    # =========================================================================
    # STEP 1: Fetch the item
    # =========================================================================
    if request.item_type == ItemType.STORY:
        result = await db.execute(select(Story).where(Story.id == request.item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Story not found")
    elif request.item_type == ItemType.BUG:
        result = await db.execute(select(Bug).where(Bug.id == request.item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Bug not found")
    else:  # TASK
        result = await db.execute(select(Task).where(Task.id == request.item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Task not found")

    old_lane = status_to_lane(item.status, item.is_blocked)

    # =========================================================================
    # STEP 2: Validate DoD for source lane (must be complete before leaving)
    # =========================================================================
    dod_result = None
    if not skip_dod_validation and old_lane and old_lane.value not in ["backlog", "blocked", "human_needed"]:
        # Build item data for validation
        item_data = {
            "id": str(item.id),
            "title": getattr(item, "title", getattr(item, "name", "")),
            "description": getattr(item, "description", ""),
            "story_points": getattr(item, "story_points", None),
            "estimated_hours": getattr(item, "estimated_hours", None),
            "acceptance_criteria": getattr(item, "acceptance_criteria", None),
            "tags": getattr(item, "tags", []),
            "assigned_to": getattr(item, "assigned_to", None),
            "status": item.status,
            "item_type": request.item_type.value,
        }

        dod_result = await agent_service.validate_dod(old_lane.value, item_data)

        # Check if DoD failed (status can be "passed", "partial", "failed", or "not_applicable")
        dod_status = dod_result.get("status", "passed")
        if dod_status == "failed":
            # DoD not met - block transition unless moving to blocked/human_needed
            if request.target_lane not in [KanbanLane.BLOCKED, KanbanLane.HUMAN_NEEDED]:
                return {
                    "success": False,
                    "item_id": request.item_id,
                    "from_lane": old_lane.value,
                    "to_lane": request.target_lane.value,
                    "blocked_by": "dod_validation",
                    "dod_result": dod_result,
                    "message": f"DoD criteria not met for {old_lane.value} lane: {dod_result.get('failed_criteria', [])}"
                }

    # =========================================================================
    # STEP 3: Validate Quality Gates for IN_REVIEW transitions
    # =========================================================================
    quality_result = None
    if not skip_quality_gates and request.target_lane == KanbanLane.IN_REVIEW:
        item_data = {
            "id": str(item.id),
            "title": getattr(item, "title", getattr(item, "name", "")),
            "description": getattr(item, "description", ""),
            "tags": getattr(item, "tags", []),
            "item_type": request.item_type.value,
        }

        # Get project_id as integer, or None if not available
        item_project_id = getattr(item, "project_id", None)
        if item_project_id is not None and not isinstance(item_project_id, int):
            # If project_id is not an integer (e.g., a string), set to None
            # This prevents type mismatch errors in the database query
            item_project_id = None

        quality_result = await agent_service.validate_lane_transition_quality(
            item_id=str(item.id),
            item_type=request.item_type.value,
            from_lane=old_lane.value if old_lane else "backlog",
            to_lane=request.target_lane.value,
            item_data=item_data,
            project_id=item_project_id
        )

        # Check if quality gates failed (can_proceed or validation_passed)
        if not quality_result.get("can_proceed", quality_result.get("validation_passed", True)):
            blocking_failures = quality_result.get("blocking_failures", [])
            if blocking_failures:
                return {
                    "success": False,
                    "item_id": request.item_id,
                    "from_lane": old_lane.value if old_lane else "backlog",
                    "to_lane": request.target_lane.value,
                    "blocked_by": "quality_gates",
                    "quality_result": quality_result,
                    "message": f"Quality gates failed: {len(blocking_failures)} blocking issues found"
                }

    # =========================================================================
    # STEP 4: Apply the status update
    # =========================================================================
    item.status = new_status
    item.is_blocked = is_blocked
    if request.blocked_reason:
        item.blocked_reason = request.blocked_reason
    elif not is_blocked:
        item.blocked_reason = None
    item.updated_at = datetime.now(timezone.utc)

    # Item-type specific updates
    if request.item_type == ItemType.STORY:
        if request.target_lane == KanbanLane.DONE:
            item.completed_at = datetime.now(timezone.utc)

    elif request.item_type == ItemType.BUG:
        # Bug-specific timestamps based on status
        if new_status == "analysis":
            item.analysis_started_at = datetime.now(timezone.utc)
        elif new_status == "in_progress":
            item.fix_started_at = datetime.now(timezone.utc)
        elif new_status == "testing":
            item.fixed_at = datetime.now(timezone.utc)
        elif request.target_lane == KanbanLane.DONE:
            item.verified_at = datetime.now(timezone.utc)

    else:  # TASK
        if request.target_lane == KanbanLane.DONE:
            item.completed_at = datetime.now(timezone.utc)

    await db.commit()

    # Trigger lane entry event (for agent automation)
    event_service = KanbanEventService(db)
    event_result = await event_service.on_lane_entry(
        item_id=request.item_id,
        item_type=request.item_type.value,
        old_lane=old_lane.value if old_lane else None,
        new_lane=request.target_lane.value,
        metadata={"tags": getattr(item, "tags", []), "assigned_to": getattr(item, "assigned_to", None)}
    )

    # Handle escalation if triggered
    actual_target_lane = request.target_lane.value
    if event_result.get("escalate"):
        actual_target_lane = event_result.get("to_lane", request.target_lane.value)
        # Update item to Human Needed lane if escalated
        item.status = "human_needed"
        item.is_blocked = True
        item.blocked_reason = event_result.get("analysis_summary", "Escalated after max retries")
        await db.commit()

    # Broadcast WebSocket event
    await manager.broadcast(
        Channel.ALL,
        EventType.AGENT_STATUS,  # Reuse existing event type
        {
            "event": "kanban_item_moved",
            "item_id": request.item_id,
            "item_type": request.item_type.value,
            "from_lane": old_lane.value,
            "to_lane": actual_target_lane,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "suggested_agents": event_result.get("suggested_agents", []),
            "retry_count": event_result.get("retry_count", 0),
            "escalated": event_result.get("escalate", False)
        }
    )

    # =========================================================================
    # STEP 5: Auto-trigger suggested agents (if enabled)
    # =========================================================================
    triggered_agents = []
    if auto_trigger_agents and not event_result.get("escalate"):
        suggested_agents = event_result.get("suggested_agents", [])
        for agent_name in suggested_agents[:2]:  # Limit to top 2 agents
            try:
                trigger_result = await agent_service.trigger_agent_for_item(
                    item_id=str(request.item_id),
                    item_type=request.item_type.value,
                    lane=actual_target_lane,
                    agent_name=agent_name,
                    task_description=f"Auto-triggered for {actual_target_lane} lane entry"
                )
                triggered_agents.append({
                    "agent": agent_name,
                    "status": "triggered",
                    "result": trigger_result
                })
                logger.info(f"Auto-triggered agent {agent_name} for item {request.item_id}")
            except Exception as e:
                logger.warning(f"Failed to auto-trigger agent {agent_name}: {str(e)}")
                triggered_agents.append({
                    "agent": agent_name,
                    "status": "failed",
                    "error": str(e)
                })

    return {
        "success": True,
        "item_id": request.item_id,
        "from_lane": old_lane.value,
        "to_lane": actual_target_lane,
        "new_status": new_status,
        "is_blocked": is_blocked,
        "event": event_result,
        "dod_result": dod_result,
        "quality_result": quality_result,
        "triggered_agents": triggered_agents
    }


@router.patch("/{item_type}/{item_id}")
async def update_item(
    item_type: ItemType,
    item_id: str,
    request: UpdateItemRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update item details (assignee, priority, etc.)
    """
    if item_type == ItemType.STORY:
        result = await db.execute(select(Story).where(Story.id == item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Story not found")

        if request.assigned_to is not None:
            item.assigned_to = request.assigned_to
        if request.priority is not None:
            item.priority = request.priority
        if request.story_points is not None:
            item.story_points = request.story_points
        if request.estimated_hours is not None:
            item.estimated_hours = request.estimated_hours
        if request.blocked_reason is not None:
            item.blocked_reason = request.blocked_reason
            item.is_blocked = bool(request.blocked_reason)

    elif item_type == ItemType.BUG:
        result = await db.execute(select(Bug).where(Bug.id == item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Bug not found")

        if request.assigned_to is not None:
            item.assigned_to = request.assigned_to
        if request.priority is not None:
            item.priority = request.priority
        if request.story_points is not None:
            item.story_points = request.story_points
        if request.estimated_hours is not None:
            item.estimated_hours = request.estimated_hours
        if request.blocked_reason is not None:
            item.blocked_reason = request.blocked_reason
            item.is_blocked = bool(request.blocked_reason)

    else:  # TASK
        result = await db.execute(select(Task).where(Task.id == item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Task not found")

        if request.assigned_to is not None:
            item.assigned_to = request.assigned_to
        if request.priority is not None:
            item.priority = request.priority
        if request.estimated_hours is not None:
            item.estimated_hours = request.estimated_hours
        if request.blocked_reason is not None:
            item.blocked_reason = request.blocked_reason
            item.is_blocked = bool(request.blocked_reason)

    item.updated_at = datetime.now(timezone.utc)
    await db.commit()

    # Broadcast update
    await manager.broadcast(
        Channel.ALL,
        EventType.AGENT_STATUS,
        {
            "event": "kanban_item_updated",
            "item_id": item_id,
            "item_type": item_type.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

    return {"success": True, "item_id": item_id}


@router.get("/stats", response_model=KanbanStats)
async def get_kanban_stats(
    project_id: Optional[str] = Query(None),
    epic_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get Kanban board statistics.
    """
    # Get all stories
    story_stmt = select(Story)
    if project_id:
        story_stmt = story_stmt.where(Story.project_id == project_id)
    if epic_id:
        story_stmt = story_stmt.join(Feature).where(Feature.epic_id == epic_id)
    result = await db.execute(story_stmt)
    stories = result.scalars().all()

    # Get all tasks
    task_stmt = select(Task)
    if project_id:
        task_stmt = task_stmt.where(Task.project_id == project_id)
    if epic_id:
        task_stmt = task_stmt.join(Story).join(Feature).where(Feature.epic_id == epic_id)
    result = await db.execute(task_stmt)
    tasks = result.scalars().all()

    # Get all bugs
    bug_stmt = select(Bug)
    if project_id:
        bug_stmt = bug_stmt.where(Bug.project_id == project_id)
    if epic_id:
        bug_stmt = bug_stmt.where(Bug.epic_id == epic_id)
    result = await db.execute(bug_stmt)
    bugs = result.scalars().all()

    # Calculate stats
    by_lane = {lane.value: 0 for lane in KanbanLane}
    by_type = {"story": len(stories), "task": len(tasks), "bug": len(bugs)}
    by_priority = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    total_story_points = 0
    total_estimated_hours = 0.0
    blocked_count = 0

    for story in stories:
        lane = status_to_lane(story.status, story.is_blocked)
        by_lane[lane.value] += 1
        by_priority[story.priority] = by_priority.get(story.priority, 0) + 1
        if story.story_points:
            total_story_points += story.story_points
        if story.estimated_hours:
            total_estimated_hours += story.estimated_hours
        if story.is_blocked:
            blocked_count += 1

    for task in tasks:
        lane = status_to_lane(task.status, task.is_blocked)
        by_lane[lane.value] += 1
        by_priority[task.priority] = by_priority.get(task.priority, 0) + 1
        if task.estimated_hours:
            total_estimated_hours += task.estimated_hours
        if task.is_blocked:
            blocked_count += 1

    for bug in bugs:
        lane = status_to_lane(bug.status, bug.is_blocked)
        by_lane[lane.value] += 1
        by_priority[bug.priority] = by_priority.get(bug.priority, 0) + 1
        if bug.story_points:
            total_story_points += bug.story_points
        if bug.estimated_hours:
            total_estimated_hours += bug.estimated_hours
        if bug.is_blocked:
            blocked_count += 1

    return KanbanStats(
        total_items=len(stories) + len(tasks) + len(bugs),
        by_lane=by_lane,
        by_type=by_type,
        by_priority=by_priority,
        total_story_points=total_story_points,
        total_estimated_hours=total_estimated_hours,
        blocked_count=blocked_count
    )


@router.get("/epics")
async def get_epics_for_filter(
    project_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of epics for filter dropdown.
    """
    stmt = select(Epic).order_by(Epic.sequence_number)
    if project_id:
        stmt = stmt.where(Epic.project_id == project_id)

    result = await db.execute(stmt)
    epics = result.scalars().all()

    # Build response with feature counts via separate queries to avoid lazy loading issues
    response = []
    for epic in epics:
        count_result = await db.execute(select(func.count(Feature.id)).where(Feature.epic_id == epic.id))
        features_count = count_result.scalar() or 0
        response.append({
            "id": str(epic.id),
            "title": epic.title,
            "status": epic.status,
            "features_count": features_count
        })

    return response


@router.get("/projects")
async def get_projects_for_filter(
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of projects that have items in the Kanban board.
    Returns projects with item counts.
    """
    # Get unique project IDs from stories, tasks, and bugs
    project_ids = set()

    # From stories
    story_result = await db.execute(
        select(Story.project_id).where(Story.project_id.isnot(None)).distinct()
    )
    for row in story_result:
        if row[0]:
            project_ids.add(row[0])

    # From tasks
    task_result = await db.execute(
        select(Task.project_id).where(Task.project_id.isnot(None)).distinct()
    )
    for row in task_result:
        if row[0]:
            project_ids.add(row[0])

    # From bugs
    bug_result = await db.execute(
        select(Bug.project_id).where(Bug.project_id.isnot(None)).distinct()
    )
    for row in bug_result:
        if row[0]:
            project_ids.add(row[0])

    # Get project details from Item table
    projects = []
    for pid in project_ids:
        item_result = await db.execute(select(Item).where(Item.id == pid))
        item = item_result.scalar_one_or_none()
        if item:
            # Count items for this project
            story_count = await db.execute(
                select(func.count(Story.id)).where(Story.project_id == pid)
            )
            task_count = await db.execute(
                select(func.count(Task.id)).where(Task.project_id == pid)
            )
            bug_count = await db.execute(
                select(func.count(Bug.id)).where(Bug.project_id == pid)
            )

            total_items = (story_count.scalar() or 0) + (task_count.scalar() or 0) + (bug_count.scalar() or 0)

            projects.append({
                "id": str(pid),
                "name": item.title,
                "item_count": total_items
            })

    # Sort by name
    projects.sort(key=lambda p: p["name"].lower())

    return projects


@router.get("/features")
async def get_features_for_filter(
    epic_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of features for filter dropdown.
    """
    stmt = select(Feature).order_by(Feature.sequence_number)
    if epic_id:
        stmt = stmt.where(Feature.epic_id == epic_id)
    if project_id:
        stmt = stmt.where(Feature.project_id == project_id)

    result = await db.execute(stmt)
    features = result.scalars().all()

    # Build response with explicit count queries to avoid lazy loading
    response = []
    for feature in features:
        # Explicit count query instead of accessing relationship
        count_result = await db.execute(
            select(func.count(Story.id)).where(Story.feature_id == feature.id)
        )
        stories_count = count_result.scalar() or 0

        response.append({
            "id": str(feature.id),
            "title": feature.title,
            "status": feature.status,
            "epic_id": str(feature.epic_id),
            "stories_count": stories_count
        })

    return response


@router.get("/assignees")
async def get_assignees(
    project_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of unique assignees from stories and tasks.
    """
    story_stmt = select(Story.assigned_to).where(Story.assigned_to.isnot(None)).distinct()
    task_stmt = select(Task.assigned_to).where(Task.assigned_to.isnot(None)).distinct()

    if project_id:
        story_stmt = story_stmt.where(Story.project_id == project_id)
        task_stmt = task_stmt.where(Task.project_id == project_id)

    story_result = await db.execute(story_stmt)
    task_result = await db.execute(task_stmt)

    story_assignees = [r[0] for r in story_result.all()]
    task_assignees = [r[0] for r in task_result.all()]

    all_assignees = sorted(set(story_assignees + task_assignees))

    return {"assignees": all_assignees}


# ============================================================================
# BUG MANAGEMENT ENDPOINTS
# ============================================================================

class CreateBugRequest(BaseModel):
    """Request to create a new bug"""
    title: str
    description: str
    severity: str = "medium"
    priority: str = "medium"
    category: Optional[str] = None
    component: Optional[str] = None
    reproduction_steps: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    story_points: Optional[int] = None
    function_points: Optional[int] = None
    estimated_hours: Optional[float] = None
    project_id: Optional[str] = None
    application_id: Optional[int] = None
    epic_id: Optional[str] = None
    feature_id: Optional[str] = None
    reporter: Optional[str] = None
    assigned_to: Optional[str] = None
    source: Optional[str] = None
    source_reference: Optional[str] = None
    tags: Optional[List[str]] = None
    acceptance_criteria: Optional[List[Dict[str, Any]]] = None


async def get_next_bug_number(db: AsyncSession) -> str:
    """Generate the next bug number (BUG-001, BUG-002, etc.)"""
    result = await db.execute(
        select(func.max(Bug.bug_number)).where(Bug.bug_number.like("BUG-%"))
    )
    max_number = result.scalar()
    if max_number:
        try:
            num = int(max_number.replace("BUG-", ""))
            return f"BUG-{num + 1:03d}"
        except ValueError:
            pass
    return "BUG-001"


@router.post("/bugs")
async def create_bug(
    request: CreateBugRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new bug.

    Bugs start in 'draft' status and appear in the Backlog lane.
    """
    import uuid

    bug_number = await get_next_bug_number(db)

    bug = Bug(
        id=uuid.uuid4(),
        bug_number=bug_number,
        title=request.title,
        description=request.description,
        status=BugStatus.DRAFT,
        severity=request.severity,
        priority=request.priority,
        category=request.category,
        component=request.component,
        reproduction_steps=request.reproduction_steps,
        expected_behavior=request.expected_behavior,
        actual_behavior=request.actual_behavior,
        story_points=request.story_points,
        function_points=request.function_points,
        estimated_hours=request.estimated_hours,
        project_id=request.project_id,
        application_id=request.application_id,
        epic_id=request.epic_id if request.epic_id else None,
        feature_id=request.feature_id if request.feature_id else None,
        reporter=request.reporter,
        assigned_to=request.assigned_to,
        source=request.source,
        source_reference=request.source_reference,
        tags=request.tags,
        acceptance_criteria=request.acceptance_criteria,
        reported_at=datetime.now(timezone.utc),
    )

    db.add(bug)
    await db.commit()
    await db.refresh(bug)

    # Broadcast creation
    await manager.broadcast(
        Channel.ALL,
        EventType.AGENT_STATUS,
        {
            "event": "kanban_bug_created",
            "bug_id": str(bug.id),
            "bug_number": bug.bug_number,
            "title": bug.title,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

    return {
        "id": str(bug.id),
        "bug_number": bug.bug_number,
        "title": bug.title,
        "status": bug.status,
        "severity": bug.severity,
        "lane": status_to_lane(bug.status, bug.is_blocked).value
    }


@router.get("/bugs")
async def list_bugs(
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    List all bugs with optional filters.
    """
    stmt = select(Bug).order_by(Bug.created_at.desc())

    if project_id:
        stmt = stmt.where(Bug.project_id == project_id)
    if status:
        stmt = stmt.where(Bug.status == status)
    if severity:
        stmt = stmt.where(Bug.severity == severity)
    if assigned_to:
        stmt = stmt.where(Bug.assigned_to == assigned_to)

    result = await db.execute(stmt)
    bugs = result.scalars().all()

    return [
        {
            "id": str(bug.id),
            "bug_number": bug.bug_number,
            "title": bug.title,
            "status": bug.status,
            "severity": bug.severity,
            "priority": bug.priority,
            "category": bug.category,
            "assigned_to": bug.assigned_to,
            "story_points": bug.story_points,
            "lane": status_to_lane(bug.status, bug.is_blocked).value,
            "created_at": bug.created_at.isoformat() if bug.created_at else None,
        }
        for bug in bugs
    ]


@router.get("/bugs/{bug_id}")
async def get_bug(
    bug_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed bug information.
    """
    result = await db.execute(select(Bug).where(Bug.id == bug_id))
    bug = result.scalar_one_or_none()

    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")

    return {
        "id": str(bug.id),
        "bug_number": bug.bug_number,
        "title": bug.title,
        "description": bug.description,
        "status": bug.status,
        "severity": bug.severity,
        "priority": bug.priority,
        "category": bug.category,
        "component": bug.component,
        "tags": bug.tags,
        "reproduction_steps": bug.reproduction_steps,
        "expected_behavior": bug.expected_behavior,
        "actual_behavior": bug.actual_behavior,
        "root_cause": bug.root_cause,
        "affected_files": bug.affected_files,
        "related_bugs": bug.related_bugs,
        "story_points": bug.story_points,
        "function_points": bug.function_points,
        "estimated_hours": bug.estimated_hours,
        "actual_hours": bug.actual_hours,
        "acceptance_criteria": bug.acceptance_criteria,
        "project_id": bug.project_id,
        "application_id": bug.application_id,
        "epic_id": str(bug.epic_id) if bug.epic_id else None,
        "feature_id": str(bug.feature_id) if bug.feature_id else None,
        "reporter": bug.reporter,
        "assigned_to": bug.assigned_to,
        "reviewer": bug.reviewer,
        "is_blocked": bug.is_blocked,
        "blocked_reason": bug.blocked_reason,
        "branch_name": bug.branch_name,
        "commit_sha": bug.commit_sha,
        "pull_request_url": bug.pull_request_url,
        "source": bug.source,
        "source_reference": bug.source_reference,
        "reported_at": bug.reported_at.isoformat() if bug.reported_at else None,
        "confirmed_at": bug.confirmed_at.isoformat() if bug.confirmed_at else None,
        "analysis_started_at": bug.analysis_started_at.isoformat() if bug.analysis_started_at else None,
        "analysis_completed_at": bug.analysis_completed_at.isoformat() if bug.analysis_completed_at else None,
        "fix_started_at": bug.fix_started_at.isoformat() if bug.fix_started_at else None,
        "fixed_at": bug.fixed_at.isoformat() if bug.fixed_at else None,
        "verified_at": bug.verified_at.isoformat() if bug.verified_at else None,
        "due_date": bug.due_date.isoformat() if bug.due_date else None,
        "created_at": bug.created_at.isoformat() if bug.created_at else None,
        "updated_at": bug.updated_at.isoformat() if bug.updated_at else None,
        "lane": status_to_lane(bug.status, bug.is_blocked).value,
    }


# ============================================================================
# EVENT & RETRY TRACKING ENDPOINTS
# ============================================================================

@router.get("/events/history/{item_id}")
async def get_item_event_history(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get event and retry history for an item.

    Returns all retry attempts and agent actions for debugging and learning.
    """
    event_service = KanbanEventService(db)
    history = await event_service.get_item_history(item_id)

    return {
        "item_id": item_id,
        "history": history,
        "total_events": len(history)
    }


@router.get("/events/escalations")
async def get_escalation_queue(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all items currently in Human Needed lane with escalation analysis.

    Returns items that have been escalated after max retries,
    including the summary of what was tried.
    """
    event_service = KanbanEventService(db)
    escalations = await event_service.get_escalation_queue()

    return {
        "escalations": escalations,
        "total": len(escalations)
    }


# ============================================================================
# HUMAN NEEDED LANE ENDPOINTS
# ============================================================================

@router.get("/human-needed/detail/{item_id}")
async def get_escalation_detail(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed escalation information for a specific item.

    Returns comprehensive data for UI display including:
    - Full retry history timeline
    - Agent actions and results
    - Failure analysis
    - Resolution options with recommendations
    - Priority assessment
    """
    event_service = KanbanEventService(db)
    detail = await event_service.get_escalation_detail(item_id)

    if "error" in detail:
        raise HTTPException(status_code=404, detail=detail["error"])

    return detail


@router.post("/human-needed/resolve/{item_id}")
async def resolve_escalation(
    item_id: str,
    resolution_type: str = Body(..., description="Type: retry, manual_fix, reassign, cancel"),
    target_lane: str = Body(..., description="Lane to move item to after resolution"),
    notes: Optional[str] = Body(None, description="Human reviewer notes"),
    assign_agent: Optional[str] = Body(None, description="Agent to assign for retry"),
    db: AsyncSession = Depends(get_db)
):
    """
    Resolve an escalated item with human decision.

    Resolution types:
    - retry: Reset retry count and try with different agent
    - manual_fix: Human will manually implement/fix
    - reassign: Break down or reassign (usually for stories)
    - cancel: Remove from workflow
    """
    event_service = KanbanEventService(db)
    result = await event_service.resolve_escalation(
        item_id=item_id,
        resolution_type=resolution_type,
        target_lane=target_lane,
        notes=notes,
        assign_agent=assign_agent
    )

    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Resolution failed"))

    # Broadcast resolution to connected clients
    await manager.broadcast(
        Channel.KANBAN,
        EventType.ESCALATION_RESOLVED,
        {
            "item_id": item_id,
            "resolution": result
        }
    )

    return result


@router.get("/human-needed/stats")
async def get_human_needed_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics about Human Needed lane for dashboard.

    Returns:
    - Pending escalation count
    - Escalations by item type
    - Resolution statistics
    - Top failure lanes
    """
    event_service = KanbanEventService(db)
    stats = await event_service.get_human_needed_stats()
    return stats


@router.post("/events/agent-action")
async def record_agent_action(
    item_id: str,
    item_type: str,
    lane: str,
    agent_name: str,
    action: str,
    success: bool,
    details: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Record an agent action for tracking and learning.

    Called by agents after performing work on an item.
    """
    event_service = KanbanEventService(db)
    result = await event_service.record_agent_action(
        item_id=item_id,
        item_type=item_type,
        lane=lane,
        agent_name=agent_name,
        action=action,
        success=success,
        details=details
    )

    return result


# ============================================================================
# AGENT SERVICE ENDPOINTS
# ============================================================================

@router.get("/agents/select/{lane}")
async def select_agents_for_lane(
    lane: str,
    item_type: str = Query("task", description="Type of item (story, task, bug)"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    db: AsyncSession = Depends(get_db)
):
    """
    Select appropriate agents for a lane based on item context.

    Uses hybrid selection for BUILD lane:
    1. Tag-based selection (highest confidence)
    2. Item type defaults (medium confidence)
    3. Human Needed (if uncertain)
    """
    agent_service = KanbanAgentService(db)

    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    result = await agent_service.select_agents_for_lane(
        lane=lane,
        item_type=item_type,
        tags=tag_list,
        metadata={}
    )

    return result


@router.get("/agents/dod/{lane}")
async def get_lane_dod(lane: str):
    """
    Get Definition of Done criteria for a lane.
    """
    from app.services.kanban_agent_service import LANE_DOD

    lane_dod = LANE_DOD.get(lane)
    if not lane_dod:
        return {
            "lane": lane,
            "criteria": [],
            "message": f"No DoD defined for {lane} lane"
        }

    return {
        "lane": lane_dod.lane,
        "criteria": [
            {
                "name": c.name,
                "description": c.description,
                "required": c.required
            }
            for c in lane_dod.criteria
        ],
        "min_pass_percentage": lane_dod.min_pass_percentage
    }


@router.post("/agents/dod/validate")
async def validate_item_dod(
    lane: str = Body(...),
    item: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate Definition of Done for an item in a lane.
    """
    agent_service = KanbanAgentService(db)

    result = await agent_service.validate_dod(lane=lane, item=item)

    return result


@router.post("/agents/trigger")
async def trigger_agent(
    item_id: str = Body(...),
    item_type: str = Body(...),
    lane: str = Body(...),
    agent_name: str = Body(...),
    task_description: Optional[str] = Body(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger an agent to work on an item.
    """
    agent_service = KanbanAgentService(db)

    result = await agent_service.trigger_agent_for_item(
        item_id=item_id,
        item_type=item_type,
        lane=lane,
        agent_name=agent_name,
        task_description=task_description
    )

    return result


@router.post("/agents/complete")
async def complete_agent_work(
    item_id: str = Body(...),
    item_type: str = Body(...),
    lane: str = Body(...),
    agent_name: str = Body(...),
    success: bool = Body(...),
    work_result: Optional[Dict[str, Any]] = Body(None),
    error_message: Optional[str] = Body(None),
    auto_progress: bool = Body(True, description="KaibanJS-style: auto-move to next lane"),
    db: AsyncSession = Depends(get_db)
):
    """
    Record completion of agent work on an item.

    KaibanJS-style auto-progression:
    - When auto_progress=True (default), automatically moves item to next lane
    - Triggers next lane's agents automatically
    - Broadcasts via WebSocket for real-time dashboard updates
    - Handles retries and escalation to Human Needed

    Returns progression info including:
    - moved_to: New lane if progressed
    - triggered_agents: Agents triggered for next lane
    - escalated: True if escalated to Human Needed
    """
    agent_service = KanbanAgentService(db)

    result = await agent_service.complete_agent_work(
        item_id=item_id,
        item_type=item_type,
        lane=lane,
        agent_name=agent_name,
        success=success,
        work_result=work_result,
        error_message=error_message,
        auto_progress=auto_progress
    )

    return result


@router.get("/items/{item_id}/journey")
async def get_item_journey(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the complete journey of an item through lanes.

    KaibanJS-style: Shows all agent work and lane transitions.
    Useful for dashboard timeline visualization.
    """
    from app.services.lane_progression_service import LaneProgressionService

    progression_service = LaneProgressionService(db)
    journey = await progression_service.get_item_journey(item_id)
    retry_status = progression_service.get_retry_status(item_id)

    return {
        "item_id": item_id,
        "journey": journey,
        "retry_status": retry_status,
    }


@router.get("/items/{item_id}/previous-results")
async def get_previous_results(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all previous agent results for an item.

    KaibanJS-style {taskResult:taskN} pattern:
    Returns outputs from all agents that worked on this item,
    useful for chaining context to next agent.
    """
    from app.services.lane_progression_service import LaneProgressionService

    progression_service = LaneProgressionService(db)
    results = progression_service.get_previous_results(item_id)

    return {
        "item_id": item_id,
        "previous_results": results,
    }


@router.get("/agents/statistics")
async def get_agent_statistics(
    agent_name: Optional[str] = Query(None),
    lane: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get agent performance statistics.
    """
    agent_service = KanbanAgentService(db)

    result = await agent_service.get_agent_statistics(
        agent_name=agent_name,
        lane=lane
    )

    return result


# WebSocket endpoint for Kanban real-time updates
@router.websocket("/ws")
async def websocket_kanban(
    websocket,
    client_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for Kanban board real-time updates.

    Events:
    - kanban_item_moved: Item moved between lanes
    - kanban_item_updated: Item details changed
    - kanban_refresh: Full board refresh needed
    """
    from fastapi import WebSocket, WebSocketDisconnect

    await manager.connect(websocket, [Channel.ALL], client_id)

    try:
        while True:
            data = await websocket.receive_text()
            import json
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await manager.send_personal(websocket, {"type": "pong"})
            except json.JSONDecodeError:
                await manager.send_personal(websocket, {
                    "type": "error",
                    "data": {"message": "Invalid JSON"}
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============================================================================
# QUALITY GATE VALIDATION ENDPOINTS
# ============================================================================

@router.get("/quality/rules/{lane}")
async def get_lane_quality_rules(
    lane: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all quality validation rules applicable to a specific lane.

    For IN_REVIEW lane, returns all 42 validation rules across:
    - Architecture (7 rules)
    - Design (8 rules)
    - Security (10 rules)
    - Code Quality (9 rules)
    - Testing (8 rules)
    """
    agent_service = KanbanAgentService(db)
    rules = await agent_service.get_lane_quality_rules(lane)

    return {
        "lane": lane,
        "rules": rules,
        "total_rules": len(rules)
    }


@router.post("/quality/validate")
async def validate_lane_transition(
    item_id: str = Body(...),
    item_type: str = Body(...),
    from_lane: str = Body(...),
    to_lane: str = Body(...),
    item_data: Dict[str, Any] = Body(default={}),
    project_id: Optional[int] = Body(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate quality gates for a lane transition.

    This executes the 42 validation rules when transitioning to IN_REVIEW.

    For IN_REVIEW lane, runs all validation categories:
    - Architecture checks (layer separation, dependencies)
    - Design checks (SOLID principles, complexity)
    - Security checks (SQL injection, XSS, CSRF, etc.)
    - Code quality checks (documentation, naming)
    - Testing checks (coverage, assertions)
    """
    agent_service = KanbanAgentService(db)

    result = await agent_service.validate_lane_transition_quality(
        item_id=item_id,
        item_type=item_type,
        from_lane=from_lane,
        to_lane=to_lane,
        item_data=item_data,
        project_id=project_id
    )

    return result


@router.get("/quality/rules/all")
async def get_all_quality_rules():
    """
    Get all 42 quality validation rules.

    Returns the complete list of validation rules with their
    categories, severities, and blocking status.
    """
    from app.services.kanban_quality_gate_service import get_all_validation_rules

    rules = get_all_validation_rules()

    return {
        "rules": rules,
        "total": len(rules),
        "categories": {
            "architecture": len([r for r in rules if r["category"] == "architecture"]),
            "design": len([r for r in rules if r["category"] == "design"]),
            "security": len([r for r in rules if r["category"] == "security"]),
            "code_quality": len([r for r in rules if r["category"] == "code_quality"]),
            "testing": len([r for r in rules if r["category"] == "testing"]),
        }
    }


# ============================================================================
# PROJECT AGENT CONFIGURATION ENDPOINTS
# ============================================================================

@router.get("/project-config/templates")
async def get_stack_templates(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all available tech stack templates.

    Templates include pre-configured agent mappings for:
    - Python/FastAPI
    - Python/Django
    - JavaScript/Node
    - React Native Mobile
    - IoT/Embedded
    - Security-focused
    - Legacy Migration
    """
    agent_service = KanbanAgentService(db)
    templates = await agent_service.get_available_stack_templates()

    return {
        "templates": templates,
        "total": len(templates)
    }


@router.get("/project-config")
async def list_project_configs(
    project_id: Optional[int] = Query(None),
    tech_stack: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    List all project agent configurations.
    """
    from app.models.project_agent_config import ProjectAgentConfig

    stmt = select(ProjectAgentConfig).where(ProjectAgentConfig.is_active == True)

    if project_id:
        stmt = stmt.where(ProjectAgentConfig.project_id == project_id)
    if tech_stack:
        stmt = stmt.where(ProjectAgentConfig.tech_stack == tech_stack)

    result = await db.execute(stmt)
    configs = result.scalars().all()

    return {
        "configs": [config.to_dict() for config in configs],
        "total": len(configs)
    }


@router.get("/project-config/{config_id}")
async def get_project_config(
    config_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed project agent configuration.
    """
    from app.models.project_agent_config import ProjectAgentConfig
    from uuid import UUID

    result = await db.execute(
        select(ProjectAgentConfig).where(ProjectAgentConfig.id == UUID(config_id))
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Project config not found")

    return config.to_dict()


class CreateProjectConfigRequest(BaseModel):
    """Request to create a project agent configuration"""
    project_id: Optional[int] = None
    project_name: str
    tech_stack: str = "custom"
    description: Optional[str] = None
    lane_agents: Optional[Dict[str, List[str]]] = None
    tag_mappings: Optional[Dict[str, str]] = None
    item_type_agents: Optional[Dict[str, str]] = None
    specialist_agents: Optional[List[str]] = None
    model_preferences: Optional[Dict[str, str]] = None
    extra_dod_criteria: Optional[Dict[str, Any]] = None
    blocking_quality_checks: Optional[List[str]] = None
    quality_gate_config_id: Optional[str] = None
    apply_template: bool = False  # If True, populates fields from STACK_TEMPLATES

    model_config = ConfigDict(protected_namespaces=())


def _apply_stack_template(request: CreateProjectConfigRequest) -> Dict[str, Any]:
    """Apply tech stack template to populate configuration fields."""
    from app.models.project_agent_config import STACK_TEMPLATES

    tech_stack = request.tech_stack
    if tech_stack not in STACK_TEMPLATES:
        return {}

    template = STACK_TEMPLATES[tech_stack]
    return {
        "lane_agents": request.lane_agents or template.get("lane_agents"),
        "tag_mappings": request.tag_mappings or template.get("tag_mappings"),
        "item_type_agents": request.item_type_agents or template.get("item_type_agents"),
        "specialist_agents": request.specialist_agents or template.get("specialist_agents"),
        "model_preferences": request.model_preferences or template.get("model_preferences"),
        "extra_dod_criteria": request.extra_dod_criteria or template.get("extra_dod_criteria"),
        "blocking_quality_checks": request.blocking_quality_checks or template.get("blocking_quality_checks"),
        "description": request.description or template.get("description"),
    }


@router.post("/project-config")
async def create_project_config(
    request: CreateProjectConfigRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new project agent configuration.

    Use a tech_stack template (e.g., 'iot_embedded', 'security_focused')
    to get pre-configured agent mappings, or use 'custom' for manual setup.
    Set apply_template=True to auto-populate fields from the stack template.
    """
    from app.models.project_agent_config import ProjectAgentConfig
    from uuid import uuid4, UUID

    # Apply template if requested
    template_data = {}
    if request.apply_template:
        template_data = _apply_stack_template(request)

    config = ProjectAgentConfig(
        id=uuid4(),
        project_id=request.project_id,
        project_name=request.project_name,
        tech_stack=request.tech_stack,
        description=template_data.get("description") or request.description,
        lane_agents=template_data.get("lane_agents") or request.lane_agents,
        tag_mappings=template_data.get("tag_mappings") or request.tag_mappings,
        item_type_agents=template_data.get("item_type_agents") or request.item_type_agents,
        specialist_agents=template_data.get("specialist_agents") or request.specialist_agents,
        model_preferences=template_data.get("model_preferences") or request.model_preferences,
        extra_dod_criteria=template_data.get("extra_dod_criteria") or request.extra_dod_criteria,
        blocking_quality_checks=template_data.get("blocking_quality_checks") or request.blocking_quality_checks,
        quality_gate_config_id=UUID(request.quality_gate_config_id) if request.quality_gate_config_id else None,
    )

    db.add(config)
    await db.commit()
    await db.refresh(config)

    return {
        "id": str(config.id),
        "project_name": config.project_name,
        "tech_stack": config.tech_stack,
        "template_applied": request.apply_template,
        "message": "Project agent configuration created successfully"
    }


@router.put("/project-config/{config_id}")
async def update_project_config(
    config_id: str,
    request: CreateProjectConfigRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a project agent configuration.

    If apply_template is True and tech_stack is changed, template values will
    be applied to any fields not explicitly provided in the request.
    """
    from app.models.project_agent_config import ProjectAgentConfig
    from uuid import UUID

    result = await db.execute(
        select(ProjectAgentConfig).where(ProjectAgentConfig.id == UUID(config_id))
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Project config not found")

    # Apply template if requested
    template_values = {}
    if request.apply_template:
        template_values = _apply_stack_template(request)

    # Update fields - use template values as fallback when apply_template is True
    if request.project_name:
        config.project_name = request.project_name
    if request.tech_stack:
        config.tech_stack = request.tech_stack
    if request.description is not None:
        config.description = request.description
    elif template_values.get("description"):
        config.description = template_values["description"]
    if request.lane_agents is not None:
        config.lane_agents = request.lane_agents
    elif template_values.get("lane_agents"):
        config.lane_agents = template_values["lane_agents"]
    if request.tag_mappings is not None:
        config.tag_mappings = request.tag_mappings
    elif template_values.get("tag_mappings"):
        config.tag_mappings = template_values["tag_mappings"]
    if request.item_type_agents is not None:
        config.item_type_agents = request.item_type_agents
    elif template_values.get("item_type_agents"):
        config.item_type_agents = template_values["item_type_agents"]
    if request.specialist_agents is not None:
        config.specialist_agents = request.specialist_agents
    elif template_values.get("specialist_agents"):
        config.specialist_agents = template_values["specialist_agents"]
    if request.model_preferences is not None:
        config.model_preferences = request.model_preferences
    elif template_values.get("model_preferences"):
        config.model_preferences = template_values["model_preferences"]
    if request.extra_dod_criteria is not None:
        config.extra_dod_criteria = request.extra_dod_criteria
    elif template_values.get("extra_dod_criteria"):
        config.extra_dod_criteria = template_values["extra_dod_criteria"]
    if request.blocking_quality_checks is not None:
        config.blocking_quality_checks = request.blocking_quality_checks
    elif template_values.get("blocking_quality_checks"):
        config.blocking_quality_checks = template_values["blocking_quality_checks"]

    await db.commit()

    # Clear cache in agent service
    agent_service = KanbanAgentService(db)
    agent_service.clear_config_cache(config.project_id)

    return {
        "id": str(config.id),
        "message": "Project agent configuration updated successfully"
    }


@router.delete("/project-config/{config_id}")
async def delete_project_config(
    config_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete (deactivate) a project agent configuration.
    """
    from app.models.project_agent_config import ProjectAgentConfig
    from uuid import UUID

    result = await db.execute(
        select(ProjectAgentConfig).where(ProjectAgentConfig.id == UUID(config_id))
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Project config not found")

    config.is_active = False
    await db.commit()

    # Clear cache
    agent_service = KanbanAgentService(db)
    agent_service.clear_config_cache(config.project_id)

    return {
        "id": str(config.id),
        "message": "Project agent configuration deactivated"
    }


@router.get("/agents/select-for-project/{lane}")
async def select_agents_for_lane_with_project(
    lane: str,
    item_type: str = Query("task"),
    tags: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Select appropriate agents for a lane using project-specific configuration.

    If project_id is provided, uses project's tech stack template and custom
    agent mappings. Otherwise, falls back to default mappings.
    """
    agent_service = KanbanAgentService(db)

    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    result = await agent_service.select_agents_for_lane(
        lane=lane,
        item_type=item_type,
        tags=tag_list,
        metadata={},
        project_id=project_id
    )

    return result
