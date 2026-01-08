"""
Kanban Event Service - Event-driven lane transitions with agent triggers

Week 58: Event system for automatic agent activation on lane entry/exit.
Includes retry tracking and escalation to Human Needed lane.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

logger = logging.getLogger(__name__)


class KanbanLane(str, Enum):
    """9 Kanban lanes - matches kanban.py enum"""
    BACKLOG = "backlog"
    ANALYSIS = "analysis"
    PLANNED = "planned"
    BUILD = "build"
    TEST = "test"
    IN_REVIEW = "in_review"
    BLOCKED = "blocked"
    HUMAN_NEEDED = "human_needed"
    DONE = "done"


class EventType(str, Enum):
    """Types of kanban events"""
    LANE_ENTRY = "lane_entry"
    LANE_EXIT = "lane_exit"
    RETRY_FAILED = "retry_failed"
    ESCALATED = "escalated"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"


# Lane-to-Agent mapping: which agents should activate on lane entry
LANE_AGENT_MAPPING: Dict[str, List[str]] = {
    KanbanLane.ANALYSIS: ["Quinn", "Eliza"],       # Analysis + Estimation
    KanbanLane.BUILD: [],                           # Hybrid selection - determined at runtime
    KanbanLane.TEST: ["Tessa"],                     # Test engineer
    KanbanLane.IN_REVIEW: ["Quinn"],                # Quality review
    KanbanLane.BLOCKED: [],                         # No auto-agent, needs investigation
    KanbanLane.HUMAN_NEEDED: [],                    # Human intervention required
}

# Maximum retries before escalation to Human Needed
MAX_RETRIES = 3


class KanbanEventService:
    """
    Service for handling Kanban lane events.

    Features:
    - Lane entry/exit event handlers
    - Retry tracking for Build ↔ Test transitions
    - Automatic escalation after MAX_RETRIES
    - Agent trigger integration
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def on_lane_entry(
        self,
        item_id: str,
        item_type: str,
        old_lane: Optional[str],
        new_lane: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle item entering a lane.

        Args:
            item_id: The item's ID (story/task/bug)
            item_type: Type of item (story, task, bug)
            old_lane: Previous lane (None if new item)
            new_lane: Target lane
            metadata: Additional context (tags, assigned_to, etc.)

        Returns:
            Event result with suggested agents and actions
        """
        from app.models.kanban_retry import KanbanRetryLog

        event_time = datetime.utcnow()
        result = {
            "event": EventType.LANE_ENTRY,
            "item_id": item_id,
            "item_type": item_type,
            "from_lane": old_lane,
            "to_lane": new_lane,
            "timestamp": event_time.isoformat(),
            "suggested_agents": [],
            "should_trigger_agent": False,
            "retry_count": 0,
            "escalate": False,
            "analysis_summary": None,
        }

        # Check for Build ↔ Test retry scenario
        is_retry_transition = self._is_retry_transition(old_lane, new_lane)

        if is_retry_transition:
            retry_count = await self._get_retry_count(item_id, old_lane, new_lane)
            result["retry_count"] = retry_count + 1

            if retry_count >= MAX_RETRIES:
                # Escalate to Human Needed
                result["escalate"] = True
                result["to_lane"] = KanbanLane.HUMAN_NEEDED
                result["analysis_summary"] = await self._generate_escalation_summary(item_id)

                # Log escalation
                await self._log_retry(
                    item_id=item_id,
                    item_type=item_type,
                    from_lane=old_lane,
                    to_lane=KanbanLane.HUMAN_NEEDED,
                    attempt=retry_count + 1,
                    result="escalated",
                    agent_used=None,
                    analysis=result["analysis_summary"]
                )

                logger.warning(
                    f"Item {item_id} escalated to Human Needed after {MAX_RETRIES} retries"
                )
                return result

        # Get suggested agents for the lane
        suggested_agents = self._get_suggested_agents(new_lane, item_type, metadata)
        result["suggested_agents"] = suggested_agents
        result["should_trigger_agent"] = len(suggested_agents) > 0

        # Log the lane entry event
        if is_retry_transition:
            await self._log_retry(
                item_id=item_id,
                item_type=item_type,
                from_lane=old_lane,
                to_lane=new_lane,
                attempt=result["retry_count"],
                result="pending",
                agent_used=suggested_agents[0] if suggested_agents else None,
                analysis=None
            )

        logger.info(
            f"Lane entry: {item_id} ({item_type}) moved from {old_lane} to {new_lane}, "
            f"agents: {suggested_agents}"
        )

        return result

    async def on_lane_exit(
        self,
        item_id: str,
        item_type: str,
        lane: str,
        success: bool,
        agent_used: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle item exiting a lane.

        Args:
            item_id: The item's ID
            item_type: Type of item
            lane: Lane being exited
            success: Whether the work in this lane was successful
            agent_used: Which agent processed this item
            error_message: Error details if not successful

        Returns:
            Event result
        """
        event_time = datetime.utcnow()
        result = {
            "event": EventType.LANE_EXIT,
            "item_id": item_id,
            "item_type": item_type,
            "lane": lane,
            "success": success,
            "agent_used": agent_used,
            "timestamp": event_time.isoformat(),
        }

        # Update retry log if this was a retry scenario
        if lane in [KanbanLane.BUILD, KanbanLane.TEST]:
            await self._update_retry_result(
                item_id=item_id,
                lane=lane,
                success=success,
                agent_used=agent_used,
                error_message=error_message
            )

        logger.info(
            f"Lane exit: {item_id} exiting {lane}, success={success}, agent={agent_used}"
        )

        return result

    async def record_agent_action(
        self,
        item_id: str,
        item_type: str,
        lane: str,
        agent_name: str,
        action: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record an agent action for tracking and learning.

        Args:
            item_id: The item's ID
            item_type: Type of item
            lane: Lane where action occurred
            agent_name: Name of the agent
            action: Action performed
            success: Whether action succeeded
            details: Additional action details

        Returns:
            Action record
        """
        from app.models.kanban_retry import KanbanAgentAction

        action_record = KanbanAgentAction(
            item_id=item_id,
            item_type=item_type,
            lane=lane,
            agent_name=agent_name,
            action=action,
            success=success,
            details=details or {},
            created_at=datetime.utcnow()
        )

        self.db.add(action_record)
        await self.db.commit()

        return {
            "id": str(action_record.id),
            "item_id": item_id,
            "agent_name": agent_name,
            "action": action,
            "success": success,
        }

    async def get_item_history(self, item_id: str) -> List[Dict[str, Any]]:
        """Get all retry/agent history for an item."""
        from app.models.kanban_retry import KanbanRetryLog, KanbanAgentAction

        # Get retry logs
        retry_result = await self.db.execute(
            select(KanbanRetryLog)
            .where(KanbanRetryLog.item_id == item_id)
            .order_by(KanbanRetryLog.created_at.desc())
        )
        retry_logs = retry_result.scalars().all()

        # Get agent actions
        action_result = await self.db.execute(
            select(KanbanAgentAction)
            .where(KanbanAgentAction.item_id == item_id)
            .order_by(KanbanAgentAction.created_at.desc())
        )
        agent_actions = action_result.scalars().all()

        history = []

        for log in retry_logs:
            history.append({
                "type": "retry",
                "from_lane": log.from_lane,
                "to_lane": log.to_lane,
                "attempt": log.attempt,
                "result": log.result,
                "agent_used": log.agent_used,
                "analysis": log.analysis,
                "created_at": log.created_at.isoformat(),
            })

        for action in agent_actions:
            history.append({
                "type": "agent_action",
                "lane": action.lane,
                "agent_name": action.agent_name,
                "action": action.action,
                "success": action.success,
                "details": action.details,
                "created_at": action.created_at.isoformat(),
            })

        # Sort by timestamp
        history.sort(key=lambda x: x["created_at"], reverse=True)

        return history

    async def get_escalation_queue(self) -> List[Dict[str, Any]]:
        """Get all items currently in Human Needed lane with their analysis."""
        from app.models.kanban_retry import KanbanRetryLog

        result = await self.db.execute(
            select(KanbanRetryLog)
            .where(KanbanRetryLog.to_lane == KanbanLane.HUMAN_NEEDED)
            .where(KanbanRetryLog.result == "escalated")
            .order_by(KanbanRetryLog.created_at.desc())
        )
        escalations = result.scalars().all()

        return [
            {
                "item_id": e.item_id,
                "item_type": e.item_type,
                "from_lane": e.from_lane,
                "attempts": e.attempt,
                "analysis": e.analysis,
                "escalated_at": e.created_at.isoformat(),
            }
            for e in escalations
        ]

    async def get_escalation_detail(self, item_id: str) -> Dict[str, Any]:
        """
        Get detailed escalation information for UI display.

        Returns comprehensive data for the Human Needed lane including:
        - Full retry history with timestamps
        - Agent actions and their results
        - Parsed analysis summary
        - Resolution options
        - Suggested next actions
        """
        from app.models.kanban_retry import KanbanRetryLog, KanbanAgentAction

        # Get the escalation record
        escalation_result = await self.db.execute(
            select(KanbanRetryLog)
            .where(KanbanRetryLog.item_id == item_id)
            .where(KanbanRetryLog.result == "escalated")
            .order_by(KanbanRetryLog.created_at.desc())
            .limit(1)
        )
        escalation = escalation_result.scalar_one_or_none()

        if not escalation:
            return {"error": "No escalation found for item", "item_id": item_id}

        # Get all retry logs for this item
        retry_result = await self.db.execute(
            select(KanbanRetryLog)
            .where(KanbanRetryLog.item_id == item_id)
            .order_by(KanbanRetryLog.created_at.asc())
        )
        retry_logs = retry_result.scalars().all()

        # Get all agent actions for this item
        action_result = await self.db.execute(
            select(KanbanAgentAction)
            .where(KanbanAgentAction.item_id == item_id)
            .order_by(KanbanAgentAction.created_at.asc())
        )
        agent_actions = action_result.scalars().all()

        # Build timeline
        timeline = []
        for log in retry_logs:
            timeline.append({
                "timestamp": log.created_at.isoformat(),
                "type": "retry_attempt",
                "data": {
                    "attempt": log.attempt,
                    "from_lane": log.from_lane,
                    "to_lane": log.to_lane,
                    "result": log.result,
                    "agent_used": log.agent_used,
                }
            })

        for action in agent_actions:
            timeline.append({
                "timestamp": action.created_at.isoformat(),
                "type": "agent_action",
                "data": {
                    "agent_name": action.agent_name,
                    "action": action.action,
                    "lane": action.lane,
                    "success": action.success,
                    "details": action.details,
                    "duration_ms": action.duration_ms,
                }
            })

        # Sort timeline by timestamp
        timeline.sort(key=lambda x: x["timestamp"])

        # Analyze failure patterns
        failure_analysis = self._analyze_failures(retry_logs, agent_actions)

        # Generate resolution options
        resolution_options = self._get_resolution_options(
            escalation.item_type,
            escalation.from_lane,
            failure_analysis
        )

        return {
            "item_id": item_id,
            "item_type": escalation.item_type,
            "escalated_at": escalation.created_at.isoformat(),
            "from_lane": escalation.from_lane,
            "total_attempts": escalation.attempt,
            "analysis_summary": escalation.analysis,
            "timeline": timeline,
            "failure_analysis": failure_analysis,
            "resolution_options": resolution_options,
            "status": "awaiting_human",
            "priority": self._calculate_priority(escalation, len(retry_logs)),
        }

    async def resolve_escalation(
        self,
        item_id: str,
        resolution_type: str,
        target_lane: str,
        notes: Optional[str] = None,
        assign_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resolve an escalated item with human decision.

        Args:
            item_id: The escalated item ID
            resolution_type: Type of resolution (retry, manual_fix, reassign, cancel)
            target_lane: Lane to move item to
            notes: Optional notes from human reviewer
            assign_agent: Optional agent to assign for retry

        Returns:
            Resolution result
        """
        from app.models.kanban_retry import KanbanRetryLog, KanbanAgentAction

        # Get the escalation
        result = await self.db.execute(
            select(KanbanRetryLog)
            .where(KanbanRetryLog.item_id == item_id)
            .where(KanbanRetryLog.result == "escalated")
            .order_by(KanbanRetryLog.created_at.desc())
            .limit(1)
        )
        escalation = result.scalar_one_or_none()

        if not escalation:
            return {"success": False, "error": "No escalation found for item"}

        # Record the resolution action
        resolution_action = KanbanAgentAction(
            item_id=item_id,
            item_type=escalation.item_type,
            lane=KanbanLane.HUMAN_NEEDED,
            agent_name="HUMAN",
            action=f"resolution_{resolution_type}",
            success=True,
            details={
                "resolution_type": resolution_type,
                "target_lane": target_lane,
                "notes": notes,
                "assigned_agent": assign_agent,
            },
            created_at=datetime.utcnow()
        )
        self.db.add(resolution_action)

        # Update the escalation record
        escalation.result = f"resolved_{resolution_type}"
        if notes:
            escalation.analysis = (escalation.analysis or "") + f"\n\n## Human Resolution\n{notes}"

        await self.db.commit()

        logger.info(
            f"Escalation resolved: {item_id} via {resolution_type} to {target_lane}"
        )

        return {
            "success": True,
            "item_id": item_id,
            "resolution_type": resolution_type,
            "target_lane": target_lane,
            "message": f"Item {item_id} resolved via {resolution_type}, moving to {target_lane}",
            "reset_retry_count": resolution_type == "retry",
        }

    async def get_human_needed_stats(self) -> Dict[str, Any]:
        """Get statistics about Human Needed lane for dashboard."""
        from app.models.kanban_retry import KanbanRetryLog, KanbanAgentAction

        # Get escalation counts
        escalation_result = await self.db.execute(
            select(
                KanbanRetryLog.item_type,
                func.count(KanbanRetryLog.id).label("count")
            )
            .where(KanbanRetryLog.result == "escalated")
            .group_by(KanbanRetryLog.item_type)
        )
        escalations_by_type = {row.item_type: row.count for row in escalation_result.fetchall()}

        # Get resolution counts
        resolution_result = await self.db.execute(
            select(
                KanbanRetryLog.result,
                func.count(KanbanRetryLog.id).label("count")
            )
            .where(KanbanRetryLog.result.like("resolved_%"))
            .group_by(KanbanRetryLog.result)
        )
        resolutions = {row.result: row.count for row in resolution_result.fetchall()}

        # Get average time in Human Needed
        # For now, return pending count
        pending_result = await self.db.execute(
            select(func.count(KanbanRetryLog.id))
            .where(KanbanRetryLog.result == "escalated")
        )
        pending_count = pending_result.scalar() or 0

        # Get common failure lanes
        failure_lanes_result = await self.db.execute(
            select(
                KanbanRetryLog.from_lane,
                func.count(KanbanRetryLog.id).label("count")
            )
            .where(KanbanRetryLog.result == "escalated")
            .group_by(KanbanRetryLog.from_lane)
            .order_by(func.count(KanbanRetryLog.id).desc())
            .limit(3)
        )
        top_failure_lanes = [
            {"lane": row.from_lane, "count": row.count}
            for row in failure_lanes_result.fetchall()
        ]

        return {
            "pending_escalations": pending_count,
            "escalations_by_type": escalations_by_type,
            "resolutions": resolutions,
            "top_failure_lanes": top_failure_lanes,
            "max_retries": MAX_RETRIES,
        }

    def _analyze_failures(
        self,
        retry_logs: List,
        agent_actions: List
    ) -> Dict[str, Any]:
        """Analyze failure patterns from retry history."""
        failed_agents = {}
        failed_lanes = {}
        error_patterns = []

        for log in retry_logs:
            if log.result == "failed":
                if log.agent_used:
                    failed_agents[log.agent_used] = failed_agents.get(log.agent_used, 0) + 1
                failed_lanes[log.from_lane] = failed_lanes.get(log.from_lane, 0) + 1

        for action in agent_actions:
            if not action.success and action.details:
                error = action.details.get("error", "Unknown error")
                error_patterns.append({
                    "agent": action.agent_name,
                    "action": action.action,
                    "error": error[:100],
                })

        return {
            "failed_agents": failed_agents,
            "failed_lanes": failed_lanes,
            "error_patterns": error_patterns[:5],  # Top 5 patterns
            "total_failures": sum(failed_lanes.values()),
        }

    def _get_resolution_options(
        self,
        item_type: str,
        from_lane: str,
        failure_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate resolution options based on failure analysis."""
        options = []

        # Always offer retry with different agent
        failed_agents = failure_analysis.get("failed_agents", {})
        available_agents = self._get_alternative_agents(from_lane, failed_agents)

        options.append({
            "type": "retry",
            "label": "Retry with Different Agent",
            "description": "Reset retry count and try with a different agent",
            "target_lane": from_lane,
            "available_agents": available_agents,
            "recommended": len(available_agents) > 0,
        })

        # Manual fix option
        options.append({
            "type": "manual_fix",
            "label": "Manual Fix",
            "description": "Human will manually implement/fix the item",
            "target_lane": from_lane,
            "available_agents": [],
            "recommended": False,
        })

        # Reassign/split option for stories
        if item_type == "story":
            options.append({
                "type": "reassign",
                "label": "Split or Reassign",
                "description": "Break down into smaller tasks or reassign to different team",
                "target_lane": KanbanLane.ANALYSIS,
                "available_agents": ["Peter", "Felix"],  # PO and architect
                "recommended": failure_analysis.get("total_failures", 0) > 2,
            })

        # Cancel option
        options.append({
            "type": "cancel",
            "label": "Cancel Item",
            "description": "Remove item from workflow entirely",
            "target_lane": KanbanLane.BACKLOG,
            "available_agents": [],
            "recommended": False,
        })

        return options

    def _get_alternative_agents(
        self,
        lane: str,
        failed_agents: Dict[str, int]
    ) -> List[str]:
        """Get alternative agents that haven't failed for this lane."""
        # All possible agents for BUILD lane
        all_build_agents = [
            "FrontendDev", "BackendDev", "Betty", "Quinn",
            "Tessa", "Felix", "Marcus"
        ]

        if lane == KanbanLane.BUILD:
            return [a for a in all_build_agents if a not in failed_agents]
        elif lane == KanbanLane.TEST:
            return ["Tessa", "Quinn"] if "Tessa" in failed_agents else ["Tessa"]

        return []

    def _calculate_priority(self, escalation, retry_count: int) -> str:
        """Calculate priority for escalated item."""
        # Bugs are always high priority
        if escalation.item_type == "bug":
            return "high"

        # Many retries = higher priority
        if retry_count >= 5:
            return "high"
        elif retry_count >= 3:
            return "medium"

        return "low"

    # Private helper methods

    def _is_retry_transition(self, old_lane: Optional[str], new_lane: str) -> bool:
        """Check if this is a Build ↔ Test retry transition."""
        if old_lane is None:
            return False

        retry_pairs = [
            (KanbanLane.BUILD, KanbanLane.TEST),
            (KanbanLane.TEST, KanbanLane.BUILD),
        ]

        return (old_lane, new_lane) in retry_pairs

    async def _get_retry_count(
        self,
        item_id: str,
        from_lane: str,
        to_lane: str
    ) -> int:
        """Get current retry count for this transition."""
        from app.models.kanban_retry import KanbanRetryLog

        result = await self.db.execute(
            select(func.count(KanbanRetryLog.id))
            .where(KanbanRetryLog.item_id == item_id)
            .where(KanbanRetryLog.from_lane.in_([from_lane, to_lane]))
            .where(KanbanRetryLog.to_lane.in_([from_lane, to_lane]))
        )
        count = result.scalar() or 0
        return count

    async def _log_retry(
        self,
        item_id: str,
        item_type: str,
        from_lane: str,
        to_lane: str,
        attempt: int,
        result: str,
        agent_used: Optional[str],
        analysis: Optional[str]
    ) -> None:
        """Log a retry attempt."""
        from app.models.kanban_retry import KanbanRetryLog

        retry_log = KanbanRetryLog(
            item_id=item_id,
            item_type=item_type,
            from_lane=from_lane,
            to_lane=to_lane,
            attempt=attempt,
            result=result,
            agent_used=agent_used,
            analysis=analysis,
            created_at=datetime.utcnow()
        )

        self.db.add(retry_log)
        await self.db.commit()

    async def _update_retry_result(
        self,
        item_id: str,
        lane: str,
        success: bool,
        agent_used: Optional[str],
        error_message: Optional[str]
    ) -> None:
        """Update the result of a retry attempt."""
        from app.models.kanban_retry import KanbanRetryLog

        result = await self.db.execute(
            select(KanbanRetryLog)
            .where(KanbanRetryLog.item_id == item_id)
            .where(KanbanRetryLog.to_lane == lane)
            .where(KanbanRetryLog.result == "pending")
            .order_by(KanbanRetryLog.created_at.desc())
            .limit(1)
        )
        retry_log = result.scalar_one_or_none()

        if retry_log:
            retry_log.result = "success" if success else "failed"
            retry_log.agent_used = agent_used
            if error_message:
                retry_log.analysis = (retry_log.analysis or "") + f"\nError: {error_message}"
            await self.db.commit()

    async def _generate_escalation_summary(self, item_id: str) -> str:
        """Generate a summary of all retry attempts for human review."""
        from app.models.kanban_retry import KanbanRetryLog

        result = await self.db.execute(
            select(KanbanRetryLog)
            .where(KanbanRetryLog.item_id == item_id)
            .order_by(KanbanRetryLog.created_at.asc())
        )
        logs = result.scalars().all()

        summary_parts = [
            f"## Escalation Summary for Item {item_id}",
            f"Total attempts: {len(logs)}",
            "",
            "### Attempt History:",
        ]

        for log in logs:
            summary_parts.append(
                f"- Attempt {log.attempt}: {log.from_lane} → {log.to_lane} "
                f"[{log.result}] Agent: {log.agent_used or 'N/A'}"
            )
            if log.analysis:
                summary_parts.append(f"  Analysis: {log.analysis[:200]}...")

        summary_parts.extend([
            "",
            "### Recommended Actions:",
            "1. Review the item requirements for completeness",
            "2. Check if there are missing dependencies",
            "3. Consider manual intervention or re-assignment",
        ])

        return "\n".join(summary_parts)

    def _get_suggested_agents(
        self,
        lane: str,
        item_type: str,
        metadata: Optional[Dict[str, Any]]
    ) -> List[str]:
        """
        Get suggested agents for a lane.

        For BUILD lane, uses hybrid selection:
        1. Check tags first
        2. Fall back to item_type-based selection
        """
        if lane == KanbanLane.BUILD:
            return self._get_build_agents(item_type, metadata)

        return LANE_AGENT_MAPPING.get(lane, [])

    def _get_build_agents(
        self,
        item_type: str,
        metadata: Optional[Dict[str, Any]]
    ) -> List[str]:
        """
        Hybrid agent selection for BUILD lane.

        Priority:
        1. Tags (frontend, backend, database, security)
        2. Item type defaults
        3. Empty (needs human assignment)
        """
        tags = (metadata or {}).get("tags", [])

        # Tag-based selection
        if "frontend" in tags:
            return ["FrontendDev"]
        if "backend" in tags or "api" in tags:
            return ["BackendDev"]
        if "database" in tags or "db" in tags:
            return ["BackendDev"]  # Backend handles DB
        if "security" in tags:
            return ["Quinn"]  # Security expert
        if "test" in tags or "testing" in tags:
            return ["Tessa"]

        # Item type defaults
        if item_type == "bug":
            return ["Betty"]  # Bug hunter
        if item_type == "task":
            return ["BackendDev"]  # Default to backend for tasks
        if item_type == "story":
            return []  # Stories need human assignment

        return []
