"""
Lane Progression Service - KaibanJS-Inspired Automatic Workflow

Week 80: Automatic lane progression when agents complete work.
Inspired by KaibanJS patterns:
- Task Result Chaining: Agent output → next agent input
- Team Auto-Flow: Pipeline controller for lane transitions
- Store Subscriptions: WebSocket broadcasts on state changes
- WorkflowDrivenAgent: Deterministic orchestration (no LLM for flow)

Flow: BACKLOG → ANALYSIS → PLANNED → BUILD → TEST → IN_REVIEW → DONE
      (manual)  (Quinn+    (sprint)  (Felix)  (Tessa) (Quinn)
                 Eliza)

Retry: BUILD ↔ TEST (max 3x) → HUMAN_NEEDED
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from enum import Enum
import logging
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.task_hierarchy import Story, Task, StoryStatus, TaskStatus
from app.models.bug import Bug, BugStatus
from app.api.websocket import manager, Channel, EventType

logger = logging.getLogger(__name__)


# =============================================================================
# LANE CONFIGURATION (KaibanJS-style workflow definition)
# =============================================================================

class LaneGate(str, Enum):
    """Quality gates for lane transitions"""
    ESTIMATION_COMPLETE = "estimation_complete"
    SPRINT_ASSIGNED = "sprint_assigned"
    CODE_COMPLETE = "code_complete"
    TESTS_PASS = "tests_pass"
    TESTS_FAIL = "tests_fail"
    REVIEW_APPROVED = "review_approved"
    REVIEW_REJECTED = "review_rejected"


class AgentResult(str, Enum):
    """Possible agent work results"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    NEEDS_HUMAN = "needs_human"


# KaibanJS-inspired lane flow configuration
# Each lane defines: agents, success gate, next lane, failure lane
LANE_FLOW_CONFIG: Dict[str, Dict[str, Any]] = {
    "analysis": {
        "agents": ["Quinn", "Eliza"],
        "description": "Estimation and analysis phase",
        "success_gate": LaneGate.ESTIMATION_COMPLETE,
        "gate_criteria": {
            "has_story_points": True,
            "has_description": True,
        },
        "next_lane": "planned",
        "failure_lane": "human_needed",
        "auto_trigger_next": True,
    },
    "planned": {
        "agents": [],  # No agents - waiting for sprint assignment
        "description": "Ready for sprint planning",
        "success_gate": LaneGate.SPRINT_ASSIGNED,
        "gate_criteria": {
            "assigned_to_sprint": True,
        },
        "next_lane": "build",
        "failure_lane": None,  # Stays in planned
        "auto_trigger_next": True,
    },
    "build": {
        "agents": ["Felix"],  # Or stack-specific agent
        "description": "Code implementation phase",
        "success_gate": LaneGate.CODE_COMPLETE,
        "gate_criteria": {
            "code_written": True,
            "no_syntax_errors": True,
        },
        "next_lane": "test",
        "failure_lane": "human_needed",
        "auto_trigger_next": True,
        "stack_aware": True,  # Uses project's stack agent
    },
    "test": {
        "agents": ["Tessa"],
        "description": "Testing and QA phase",
        "success_gate": LaneGate.TESTS_PASS,
        "failure_gate": LaneGate.TESTS_FAIL,
        "gate_criteria": {
            "unit_tests_pass": True,
            "coverage_adequate": True,
        },
        "next_lane": "in_review",
        "failure_lane": "build",  # Retry in build
        "auto_trigger_next": True,
        "max_retries": 3,
        "retry_escalation_lane": "human_needed",
    },
    "in_review": {
        "agents": ["Quinn"],
        "description": "Code review phase",
        "success_gate": LaneGate.REVIEW_APPROVED,
        "failure_gate": LaneGate.REVIEW_REJECTED,
        "gate_criteria": {
            "review_passed": True,
            "no_critical_issues": True,
        },
        "next_lane": "done",
        "failure_lane": "build",  # Back to build for fixes
        "auto_trigger_next": False,  # Done is final
    },
}

# Lane to status mapping for database updates
LANE_TO_STORY_STATUS = {
    "backlog": StoryStatus.DRAFT,
    "analysis": StoryStatus.DRAFT,  # Still being analyzed
    "planned": StoryStatus.READY,
    "build": StoryStatus.IN_PROGRESS,
    "test": StoryStatus.IN_PROGRESS,
    "in_review": StoryStatus.IN_REVIEW,
    "blocked": StoryStatus.BLOCKED,
    "human_needed": StoryStatus.BLOCKED,
    "done": StoryStatus.DONE,
}

LANE_TO_TASK_STATUS = {
    "backlog": TaskStatus.TODO,
    "analysis": TaskStatus.TODO,
    "planned": TaskStatus.TODO,
    "build": TaskStatus.IN_PROGRESS,
    "test": TaskStatus.IN_PROGRESS,
    "in_review": TaskStatus.IN_REVIEW,
    "blocked": TaskStatus.BLOCKED,
    "human_needed": TaskStatus.BLOCKED,
    "done": TaskStatus.DONE,
}


# =============================================================================
# LANE PROGRESSION SERVICE
# =============================================================================

class LaneProgressionService:
    """
    KaibanJS-inspired automatic lane progression.

    Features:
    - Automatic lane transitions when agents complete
    - Quality gate validation before progression
    - Retry tracking with escalation
    - WebSocket broadcasts for real-time dashboard
    - Task result chaining between lanes
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._retry_counts: Dict[str, int] = {}  # item_id -> retry count
        self._task_results: Dict[str, Dict[str, Any]] = {}  # KaibanJS-style memory

    # =========================================================================
    # CORE: Agent Completion Handler (KaibanJS Team Auto-Flow)
    # =========================================================================

    async def on_agent_complete(
        self,
        item_id: str,
        item_type: str,
        agent_name: str,
        result: AgentResult,
        work_output: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle agent work completion - KaibanJS-style auto-progression.

        This is the core method that makes the Kanban board "live":
        1. Agent completes work
        2. Check quality gate
        3. Auto-move to next lane
        4. Broadcast via WebSocket
        5. Trigger next agent (chaining)

        Args:
            item_id: Story/Task/Bug ID
            item_type: "story", "task", or "bug"
            agent_name: Name of completing agent
            result: Success/Failure/Partial
            work_output: Agent's work output (for chaining)
            metadata: Additional context

        Returns:
            Progression result with new lane and triggered agents
        """
        logger.info(f"Agent {agent_name} completed work on {item_type} {item_id}: {result}")

        # Get current lane
        current_lane = await self._get_item_lane(item_id, item_type)
        if not current_lane:
            logger.error(f"Could not determine lane for {item_type} {item_id}")
            return {"error": "Item not found", "success": False}

        # Store task result for chaining (KaibanJS memory pattern)
        self._store_task_result(item_id, agent_name, work_output)

        # Get flow configuration for current lane
        flow_config = LANE_FLOW_CONFIG.get(current_lane)
        if not flow_config:
            logger.info(f"No flow config for lane {current_lane}, no auto-progression")
            return {
                "success": True,
                "current_lane": current_lane,
                "progression": False,
                "reason": "No flow configuration for lane"
            }

        # Determine next lane based on result
        progression_result = await self._determine_progression(
            item_id=item_id,
            item_type=item_type,
            current_lane=current_lane,
            agent_result=result,
            flow_config=flow_config,
            work_output=work_output
        )

        if progression_result["should_progress"]:
            # Execute lane transition
            new_lane = progression_result["target_lane"]

            # Update database
            await self._update_item_lane(item_id, item_type, new_lane)

            # Broadcast via WebSocket (KaibanJS store subscription pattern)
            await self._broadcast_lane_change(
                item_id=item_id,
                item_type=item_type,
                from_lane=current_lane,
                to_lane=new_lane,
                agent_name=agent_name,
                result=result.value
            )

            # Auto-trigger next agents (KaibanJS task chaining)
            triggered_agents = []
            if flow_config.get("auto_trigger_next", False):
                next_flow = LANE_FLOW_CONFIG.get(new_lane)
                if next_flow and next_flow.get("agents"):
                    for next_agent in next_flow["agents"]:
                        trigger_result = await self._trigger_next_agent(
                            item_id=item_id,
                            item_type=item_type,
                            agent_name=next_agent,
                            previous_output=work_output
                        )
                        triggered_agents.append({
                            "agent": next_agent,
                            "triggered": trigger_result.get("success", False)
                        })

            logger.info(
                f"Auto-progressed {item_type} {item_id}: {current_lane} → {new_lane}, "
                f"triggered: {[a['agent'] for a in triggered_agents if a['triggered']]}"
            )

            return {
                "success": True,
                "progression": True,
                "from_lane": current_lane,
                "to_lane": new_lane,
                "triggered_agents": triggered_agents,
                "gate_result": progression_result.get("gate_result"),
            }
        else:
            # No progression - might be retry or escalation
            return {
                "success": True,
                "progression": False,
                "current_lane": current_lane,
                "reason": progression_result.get("reason"),
                "retry_count": progression_result.get("retry_count"),
                "escalated": progression_result.get("escalated", False),
            }

    # =========================================================================
    # QUALITY GATES (KaibanJS-style gate validation)
    # =========================================================================

    async def _determine_progression(
        self,
        item_id: str,
        item_type: str,
        current_lane: str,
        agent_result: AgentResult,
        flow_config: Dict[str, Any],
        work_output: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Determine if item should progress and to which lane.

        Implements KaibanJS branching logic:
        - Success → next_lane
        - Failure → failure_lane or retry
        - Max retries → escalation_lane
        """
        result = {
            "should_progress": False,
            "target_lane": None,
            "reason": None,
            "gate_result": None,
            "retry_count": 0,
            "escalated": False,
        }

        # Handle explicit failure
        if agent_result == AgentResult.FAILURE:
            failure_lane = flow_config.get("failure_lane")

            # Check for retry scenario (BUILD ↔ TEST)
            if failure_lane and flow_config.get("max_retries"):
                retry_key = f"{item_id}:{current_lane}:{failure_lane}"
                current_retries = self._retry_counts.get(retry_key, 0)

                if current_retries >= flow_config["max_retries"]:
                    # Escalate to human
                    escalation_lane = flow_config.get("retry_escalation_lane", "human_needed")
                    result["should_progress"] = True
                    result["target_lane"] = escalation_lane
                    result["reason"] = f"Max retries ({flow_config['max_retries']}) exceeded"
                    result["retry_count"] = current_retries
                    result["escalated"] = True

                    # Reset retry counter
                    self._retry_counts[retry_key] = 0

                    # Broadcast escalation
                    await self._broadcast_escalation(item_id, item_type, current_retries)
                else:
                    # Retry - go to failure lane
                    self._retry_counts[retry_key] = current_retries + 1
                    result["should_progress"] = True
                    result["target_lane"] = failure_lane
                    result["reason"] = f"Retry {current_retries + 1}/{flow_config['max_retries']}"
                    result["retry_count"] = current_retries + 1
            elif failure_lane:
                result["should_progress"] = True
                result["target_lane"] = failure_lane
                result["reason"] = "Agent reported failure"
            else:
                result["reason"] = "Failure with no failure_lane configured"

            return result

        # Handle needs human
        if agent_result == AgentResult.NEEDS_HUMAN:
            result["should_progress"] = True
            result["target_lane"] = "human_needed"
            result["reason"] = "Agent requested human intervention"
            return result

        # Handle success - check quality gate
        if agent_result in [AgentResult.SUCCESS, AgentResult.PARTIAL]:
            gate_criteria = flow_config.get("gate_criteria", {})
            gate_passed, gate_details = await self._check_quality_gate(
                item_id=item_id,
                item_type=item_type,
                criteria=gate_criteria,
                work_output=work_output
            )

            result["gate_result"] = gate_details

            if gate_passed:
                result["should_progress"] = True
                result["target_lane"] = flow_config["next_lane"]
                result["reason"] = "Quality gate passed"

                # Reset retry counter on success
                for key in list(self._retry_counts.keys()):
                    if key.startswith(f"{item_id}:"):
                        del self._retry_counts[key]
            else:
                # Gate failed but agent succeeded - partial success
                failure_lane = flow_config.get("failure_lane")
                if failure_lane:
                    result["should_progress"] = True
                    result["target_lane"] = failure_lane
                    result["reason"] = f"Quality gate failed: {gate_details}"
                else:
                    result["reason"] = f"Quality gate failed, no progression: {gate_details}"

        return result

    async def _check_quality_gate(
        self,
        item_id: str,
        item_type: str,
        criteria: Dict[str, Any],
        work_output: Optional[Dict[str, Any]]
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if item passes quality gate criteria.

        Returns (passed, details) tuple.
        """
        details = {"criteria_checked": [], "passed": [], "failed": []}

        # Get item data
        item_data = await self._get_item_data(item_id, item_type)
        if not item_data:
            return False, {"error": "Item not found"}

        # Merge with work output for comprehensive check
        check_data = {**item_data}
        if work_output:
            check_data.update(work_output)

        all_passed = True
        for criterion, required_value in criteria.items():
            details["criteria_checked"].append(criterion)

            actual_value = check_data.get(criterion)

            # Handle different criterion types
            if isinstance(required_value, bool):
                passed = bool(actual_value) == required_value
            elif required_value is None:
                passed = actual_value is not None
            else:
                passed = actual_value == required_value

            if passed:
                details["passed"].append(criterion)
            else:
                details["failed"].append({
                    "criterion": criterion,
                    "required": required_value,
                    "actual": actual_value
                })
                all_passed = False

        return all_passed, details

    # =========================================================================
    # DATABASE OPERATIONS
    # =========================================================================

    async def _get_item_lane(self, item_id: str, item_type: str) -> Optional[str]:
        """Get current lane for an item."""
        item_data = await self._get_item_data(item_id, item_type)
        if not item_data:
            return None

        status = item_data.get("status")
        is_blocked = item_data.get("is_blocked", False)

        # Convert status to lane
        if is_blocked:
            return "blocked"

        status_to_lane = {
            "draft": "backlog",
            "todo": "backlog",
            "ready": "planned",
            "planned": "planned",
            "in_progress": "build",
            "testing": "test",
            "in_review": "in_review",
            "done": "done",
            "blocked": "blocked",
            "analysis": "analysis",
        }

        return status_to_lane.get(status, "backlog")

    async def _get_item_data(self, item_id: str, item_type: str) -> Optional[Dict[str, Any]]:
        """Get item data from database."""
        try:
            if item_type == "story":
                result = await self.db.execute(
                    select(Story).where(Story.id == item_id)
                )
                item = result.scalar_one_or_none()
                if item:
                    return {
                        "id": str(item.id),
                        "status": item.status.value if item.status else "draft",
                        "story_points": item.story_points,
                        "is_blocked": item.is_blocked,
                        "has_story_points": item.story_points is not None,
                        "has_description": bool(item.description),
                        "assigned_to_sprint": item.sprint_id is not None,
                    }
            elif item_type == "task":
                result = await self.db.execute(
                    select(Task).where(Task.id == item_id)
                )
                item = result.scalar_one_or_none()
                if item:
                    return {
                        "id": str(item.id),
                        "status": item.status.value if item.status else "todo",
                        "story_points": item.estimated_hours,
                        "is_blocked": item.is_blocked,
                        "has_story_points": item.estimated_hours is not None,
                        "has_description": bool(item.description),
                    }
            elif item_type == "bug":
                result = await self.db.execute(
                    select(Bug).where(Bug.id == item_id)
                )
                item = result.scalar_one_or_none()
                if item:
                    return {
                        "id": str(item.id),
                        "status": item.status.value if item.status else "open",
                        "is_blocked": False,
                        "severity": item.severity.value if item.severity else "medium",
                    }
        except Exception as e:
            logger.error(f"Error getting item data: {e}")

        return None

    async def _update_item_lane(self, item_id: str, item_type: str, new_lane: str) -> bool:
        """Update item status in database based on lane."""
        try:
            if item_type == "story":
                new_status = LANE_TO_STORY_STATUS.get(new_lane, StoryStatus.DRAFT)
                await self.db.execute(
                    update(Story)
                    .where(Story.id == item_id)
                    .values(
                        status=new_status,
                        is_blocked=(new_lane in ["blocked", "human_needed"]),
                        updated_at=datetime.now(timezone.utc)
                    )
                )
            elif item_type == "task":
                new_status = LANE_TO_TASK_STATUS.get(new_lane, TaskStatus.TODO)
                await self.db.execute(
                    update(Task)
                    .where(Task.id == item_id)
                    .values(
                        status=new_status,
                        is_blocked=(new_lane in ["blocked", "human_needed"]),
                        updated_at=datetime.now(timezone.utc)
                    )
                )
            elif item_type == "bug":
                # Map lane to bug status
                lane_to_bug = {
                    "backlog": BugStatus.OPEN,
                    "analysis": BugStatus.CONFIRMED,
                    "build": BugStatus.IN_PROGRESS,
                    "test": BugStatus.TESTING,
                    "in_review": BugStatus.IN_REVIEW,
                    "done": BugStatus.RESOLVED,
                    "human_needed": BugStatus.OPEN,
                }
                new_status = lane_to_bug.get(new_lane, BugStatus.OPEN)
                await self.db.execute(
                    update(Bug)
                    .where(Bug.id == item_id)
                    .values(
                        status=new_status,
                        updated_at=datetime.now(timezone.utc)
                    )
                )

            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating item lane: {e}")
            await self.db.rollback()
            return False

    # =========================================================================
    # WEBSOCKET BROADCASTS (KaibanJS Store Subscription Pattern)
    # =========================================================================

    async def _broadcast_lane_change(
        self,
        item_id: str,
        item_type: str,
        from_lane: str,
        to_lane: str,
        agent_name: str,
        result: str
    ):
        """Broadcast lane change via WebSocket for real-time dashboard updates."""
        try:
            await manager.broadcast(
                channel=Channel.KANBAN,
                event_type=EventType.KANBAN_ITEM_MOVED,
                data={
                    "item_id": item_id,
                    "item_type": item_type,
                    "from_lane": from_lane,
                    "to_lane": to_lane,
                    "agent_name": agent_name,
                    "result": result,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "auto_progression": True,  # Flag for dashboard animation
                }
            )
            logger.debug(f"Broadcast lane change: {item_id} {from_lane} → {to_lane}")
        except Exception as e:
            logger.warning(f"Failed to broadcast lane change: {e}")

    async def _broadcast_escalation(
        self,
        item_id: str,
        item_type: str,
        retry_count: int
    ):
        """Broadcast escalation event for human attention."""
        try:
            await manager.broadcast(
                channel=Channel.KANBAN,
                event_type=EventType.ESCALATION_CREATED,
                data={
                    "item_id": item_id,
                    "item_type": item_type,
                    "retry_count": retry_count,
                    "reason": f"Max retries ({retry_count}) exceeded",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "requires_human": True,
                }
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast escalation: {e}")

    async def _broadcast_agent_triggered(
        self,
        item_id: str,
        item_type: str,
        agent_name: str,
        lane: str
    ):
        """Broadcast agent trigger for dashboard activity indicator."""
        try:
            await manager.broadcast(
                channel=Channel.KANBAN,
                event_type=EventType.AGENT_TRIGGERED,
                data={
                    "item_id": item_id,
                    "item_type": item_type,
                    "agent_name": agent_name,
                    "lane": lane,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast agent trigger: {e}")

    # =========================================================================
    # AGENT CHAINING (KaibanJS Task Result Passing)
    # =========================================================================

    def _store_task_result(
        self,
        item_id: str,
        agent_name: str,
        work_output: Optional[Dict[str, Any]]
    ):
        """Store task result for chaining to next agent (KaibanJS memory pattern)."""
        if item_id not in self._task_results:
            self._task_results[item_id] = {}

        self._task_results[item_id][agent_name] = {
            "output": work_output,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_previous_results(self, item_id: str) -> Dict[str, Any]:
        """Get all previous agent results for an item (for chaining)."""
        return self._task_results.get(item_id, {})

    async def _trigger_next_agent(
        self,
        item_id: str,
        item_type: str,
        agent_name: str,
        previous_output: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Trigger next agent in the chain.

        Passes previous agent's output as context (KaibanJS {taskResult:taskN} pattern).
        """
        try:
            # Import here to avoid circular imports
            from app.services.kanban_agent_service import KanbanAgentService

            agent_service = KanbanAgentService(self.db)

            # Get all previous results for context
            previous_results = self.get_previous_results(item_id)

            # Trigger with context
            result = await agent_service.trigger_agent_for_item(
                item_id=item_id,
                item_type=item_type,
                agent_name=agent_name,
                context={
                    "previous_results": previous_results,
                    "previous_output": previous_output,
                    "auto_triggered": True,
                }
            )

            # Broadcast trigger
            current_lane = await self._get_item_lane(item_id, item_type)
            await self._broadcast_agent_triggered(item_id, item_type, agent_name, current_lane)

            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Failed to trigger agent {agent_name}: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    async def get_item_journey(self, item_id: str) -> List[Dict[str, Any]]:
        """
        Get the complete journey of an item through lanes.

        Useful for dashboard timeline visualization.
        """
        journey = []

        results = self._task_results.get(item_id, {})
        for agent_name, data in results.items():
            journey.append({
                "agent": agent_name,
                "timestamp": data.get("timestamp"),
                "has_output": data.get("output") is not None,
            })

        return sorted(journey, key=lambda x: x.get("timestamp", ""))

    def get_retry_status(self, item_id: str) -> Dict[str, int]:
        """Get retry counts for an item."""
        return {
            key.split(":")[1]: count
            for key, count in self._retry_counts.items()
            if key.startswith(f"{item_id}:")
        }

    async def reset_item_state(self, item_id: str):
        """Reset all progression state for an item (for manual restart)."""
        # Clear retry counts
        keys_to_delete = [k for k in self._retry_counts if k.startswith(f"{item_id}:")]
        for key in keys_to_delete:
            del self._retry_counts[key]

        # Clear task results
        if item_id in self._task_results:
            del self._task_results[item_id]

        logger.info(f"Reset progression state for item {item_id}")
