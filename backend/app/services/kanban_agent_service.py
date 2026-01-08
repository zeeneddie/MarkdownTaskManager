"""
Kanban Agent Service - Lane-Specific Agent Triggers and Execution

Week 58: Service for triggering appropriate agents when items enter lanes.

Features:
- Lane-to-agent mapping (dynamic per project)
- Hybrid agent selection (tags → AI classification → Human Needed)
- Definition of Done (DoD) validation per lane
- Integration with event system for retry tracking
- Quality gate integration for IN_REVIEW lane
- Stack-specific agent templates (IoT, Mobile, Security)
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Integer, select, func

from app.services.kanban_event_service import KanbanLane, KanbanEventService
from app.services.lane_progression_service import LaneProgressionService, AgentResult

logger = logging.getLogger(__name__)


class AgentName(str, Enum):
    """Core agents from AGENTS.md."""
    FELIX = "Felix"          # Feature Architect
    MARCUS = "Marcus"        # Maintenance Specialist
    QUINN = "Quinn"          # Quality Inspector
    BETTY = "Betty"          # Bug Hunter
    ELIZA = "Eliza"          # Estimation Engine
    TESSA = "Tessa"          # Test Engineer
    MIGUEL = "Miguel"        # Migration Architect
    DIANA = "Diana"          # Documentation Writer
    PETER = "Peter"          # Product Owner
    PAUL = "Paul"            # Project Lead
    # Stack agents
    BACKEND_DEV = "BackendDev"
    FRONTEND_DEV = "FrontendDev"
    SECURITY_AUDIT = "SecurityAudit"


class DoDStatus(str, Enum):
    """Definition of Done status."""
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"


# ============================================================================
# LANE-TO-AGENT MAPPING
# ============================================================================

LANE_AGENTS: Dict[str, List[str]] = {
    KanbanLane.ANALYSIS: [AgentName.QUINN, AgentName.ELIZA],  # Analysis + Estimation
    KanbanLane.PLANNED: [],  # No automatic agent, human planning
    KanbanLane.BUILD: [],    # Hybrid selection - determined at runtime
    KanbanLane.TEST: [AgentName.TESSA],  # Test engineer
    KanbanLane.IN_REVIEW: [AgentName.QUINN],  # Quality review
    KanbanLane.BLOCKED: [],  # No auto-agent, needs investigation
    KanbanLane.HUMAN_NEEDED: [],  # Human intervention required
    KanbanLane.DONE: [],  # No agent needed
    KanbanLane.BACKLOG: [],  # No agent needed
}

# Tag-to-agent mapping for BUILD lane hybrid selection
TAG_AGENT_MAPPING: Dict[str, str] = {
    "frontend": AgentName.FRONTEND_DEV,
    "ui": AgentName.FRONTEND_DEV,
    "backend": AgentName.BACKEND_DEV,
    "api": AgentName.BACKEND_DEV,
    "database": AgentName.BACKEND_DEV,
    "db": AgentName.BACKEND_DEV,
    "security": AgentName.QUINN,
    "test": AgentName.TESSA,
    "testing": AgentName.TESSA,
    "bug": AgentName.BETTY,
    "bugfix": AgentName.BETTY,
    "docs": AgentName.DIANA,
    "documentation": AgentName.DIANA,
    "migration": AgentName.MIGUEL,
    "architecture": AgentName.FELIX,
    "design": AgentName.FELIX,
}

# Item type defaults (when no tags match)
ITEM_TYPE_AGENTS: Dict[str, str] = {
    "bug": AgentName.BETTY,
    "task": AgentName.BACKEND_DEV,  # Default to backend for generic tasks
    "story": None,  # Stories need human assignment
}


# ============================================================================
# DEFINITION OF DONE (DoD) PER LANE
# ============================================================================

@dataclass
class DoDCriterion:
    """Single DoD criterion."""
    name: str
    description: str
    required: bool = True
    validator: Optional[str] = None  # Function name to validate


@dataclass
class LaneDoD:
    """Definition of Done for a lane."""
    lane: str
    criteria: List[DoDCriterion]
    min_pass_percentage: float = 100.0  # All required criteria must pass


LANE_DOD: Dict[str, LaneDoD] = {
    KanbanLane.ANALYSIS: LaneDoD(
        lane=KanbanLane.ANALYSIS,
        criteria=[
            DoDCriterion("has_story_points", "Item has story point estimate", required=True),
            DoDCriterion("has_acceptance_criteria", "Item has acceptance criteria defined", required=True),
            DoDCriterion("has_description", "Item has clear description", required=True),
        ]
    ),
    KanbanLane.PLANNED: LaneDoD(
        lane=KanbanLane.PLANNED,
        criteria=[
            DoDCriterion("assigned_to_sprint", "Item is assigned to a sprint", required=True),
            DoDCriterion("dependencies_identified", "Dependencies are identified", required=False),
            DoDCriterion("has_assignee", "Item has assigned owner", required=False),
        ],
        min_pass_percentage=50.0  # More flexible for planning
    ),
    KanbanLane.BUILD: LaneDoD(
        lane=KanbanLane.BUILD,
        criteria=[
            DoDCriterion("code_written", "Implementation code is written", required=True),
            DoDCriterion("local_tests_pass", "Local tests pass", required=True),
            DoDCriterion("no_syntax_errors", "No syntax/lint errors", required=True),
        ]
    ),
    KanbanLane.TEST: LaneDoD(
        lane=KanbanLane.TEST,
        criteria=[
            DoDCriterion("unit_tests_pass", "All unit tests pass", required=True),
            DoDCriterion("coverage_adequate", "Test coverage >80%", required=False),
            DoDCriterion("integration_tests_pass", "Integration tests pass", required=True),
        ],
        min_pass_percentage=66.0  # 2 of 3 required
    ),
    KanbanLane.IN_REVIEW: LaneDoD(
        lane=KanbanLane.IN_REVIEW,
        criteria=[
            DoDCriterion("code_review_done", "Code review completed", required=True),
            DoDCriterion("security_check_passed", "Security scan passed", required=False),
            DoDCriterion("documentation_updated", "Documentation is current", required=False),
        ],
        min_pass_percentage=50.0
    ),
}


class KanbanAgentService:
    """
    Service for managing agent assignments and triggers on Kanban lanes.

    Features:
    - Select appropriate agents for lane entry (dynamic per project)
    - Validate Definition of Done criteria
    - Track agent assignments and performance
    - Integrate with retry/escalation system
    - Quality gate validation at IN_REVIEW lane
    - Support for IoT, Mobile, Security specialist stacks
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.event_service = KanbanEventService(db)
        self.progression_service = LaneProgressionService(db)  # KaibanJS-style auto-progression
        self._project_config_cache: Dict[int, Any] = {}

    async def get_project_config(self, project_id: Optional[int]) -> Optional[Any]:
        """Get project-specific agent configuration."""
        if not project_id:
            return None

        # Check cache first
        if project_id in self._project_config_cache:
            return self._project_config_cache[project_id]

        from app.models.project_agent_config import ProjectAgentConfig

        result = await self.db.execute(
            select(ProjectAgentConfig)
            .where(ProjectAgentConfig.project_id == project_id)
            .where(ProjectAgentConfig.is_active == True)
        )
        config = result.scalar_one_or_none()

        if config:
            self._project_config_cache[project_id] = config
        return config

    def clear_config_cache(self, project_id: Optional[int] = None):
        """Clear project config cache."""
        if project_id:
            self._project_config_cache.pop(project_id, None)
        else:
            self._project_config_cache.clear()

    async def select_agents_for_lane(
        self,
        lane: str,
        item_type: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Select appropriate agents for a lane based on context.

        Args:
            lane: Target lane
            item_type: Type of item (story, task, bug)
            tags: Item tags for hybrid selection
            metadata: Additional context
            project_id: Optional project ID for custom agent config

        Returns:
            Agent selection result with agents and reasoning
        """
        result = {
            "agents": [],
            "selection_method": "default",
            "confidence": 1.0,
            "reasoning": "",
            "needs_human": False,
            "project_config_used": False,
        }

        # Try to get project-specific configuration
        project_config = await self.get_project_config(project_id)

        # Special handling for BUILD lane (hybrid selection)
        if lane == KanbanLane.BUILD:
            return await self._select_build_agents(item_type, tags, metadata, project_config)

        # Check for project-specific lane agents first
        if project_config:
            lane_agents = project_config.get_effective_lane_agents(lane)
            if lane_agents:
                result["agents"] = lane_agents
                result["selection_method"] = "project_config"
                result["reasoning"] = f"Project-specific agents for {lane} lane (stack: {project_config.tech_stack})"
                result["project_config_used"] = True
                logger.info(f"Selected project-specific agents {lane_agents} for lane {lane}")
                return result

        # Fall back to default lane-to-agent mapping
        lane_agents = LANE_AGENTS.get(lane, [])

        if lane_agents:
            result["agents"] = lane_agents
            result["selection_method"] = "lane_mapping"
            result["reasoning"] = f"Standard agents for {lane} lane"
        else:
            result["reasoning"] = f"No automatic agents for {lane} lane"
            if lane in [KanbanLane.BLOCKED, KanbanLane.HUMAN_NEEDED]:
                result["needs_human"] = True
                result["reasoning"] = f"{lane} lane requires human intervention"

        logger.info(f"Selected agents {result['agents']} for lane {lane}")
        return result

    async def _select_build_agents(
        self,
        item_type: str,
        tags: Optional[List[str]],
        metadata: Optional[Dict[str, Any]],
        project_config: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Hybrid agent selection for BUILD lane.

        Priority:
        1. Project-specific tag mappings (if project_config available)
        2. Default tag-based selection (highest confidence)
        3. Item type defaults (medium confidence)
        4. Human Needed (if uncertain)
        """
        result = {
            "agents": [],
            "selection_method": "hybrid",
            "confidence": 0.0,
            "reasoning": "",
            "needs_human": False,
            "project_config_used": False,
        }

        # Get effective tag mappings (project-specific or default)
        tag_mappings = TAG_AGENT_MAPPING.copy()
        if project_config:
            project_mappings = project_config.get_effective_tag_mappings()
            tag_mappings.update(project_mappings)
            result["project_config_used"] = True

        # 1. Check tags first
        if tags:
            matched_agents = []
            matched_tags = []
            for tag in tags:
                tag_lower = tag.lower()
                if tag_lower in tag_mappings:
                    agent = tag_mappings[tag_lower]
                    if agent not in matched_agents:
                        matched_agents.append(agent)
                        matched_tags.append(tag)

            if matched_agents:
                result["agents"] = matched_agents
                result["selection_method"] = "tag_based" if not project_config else "project_tag_based"
                result["confidence"] = 0.95 if project_config else 0.9
                result["reasoning"] = f"Selected based on tags: {matched_tags}"
                if project_config:
                    result["reasoning"] += f" (stack: {project_config.tech_stack})"
                logger.info(f"BUILD lane: tag-based selection -> {matched_agents}")
                return result

        # 2. Fall back to project-specific or default item type agents
        item_type_agents = ITEM_TYPE_AGENTS.copy()
        if project_config and project_config.item_type_agents:
            item_type_agents.update(project_config.item_type_agents)

        item_agent = item_type_agents.get(item_type)
        if item_agent:
            result["agents"] = [item_agent]
            result["selection_method"] = "item_type"
            result["confidence"] = 0.7
            result["reasoning"] = f"Selected based on item type: {item_type}"
            logger.info(f"BUILD lane: item-type selection -> {item_agent}")
            return result

        # 3. Check for specialist agents in project config
        if project_config:
            specialists = project_config.get_effective_specialist_agents()
            if specialists:
                # Use first available specialist as default
                result["agents"] = [specialists[0]]
                result["selection_method"] = "project_specialist"
                result["confidence"] = 0.6
                result["reasoning"] = f"Using project specialist: {specialists[0]}"
                logger.info(f"BUILD lane: project specialist selection -> {specialists[0]}")
                return result

        # 4. Needs human assignment
        result["needs_human"] = True
        result["selection_method"] = "human_required"
        result["confidence"] = 0.0
        result["reasoning"] = "Unable to determine agent from tags or item type"
        logger.info(f"BUILD lane: needs human assignment")
        return result

    async def validate_dod(
        self,
        lane: str,
        item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate Definition of Done for an item in a lane.

        Args:
            lane: Lane to validate DoD for
            item: Item data to validate

        Returns:
            DoD validation result
        """
        lane_dod = LANE_DOD.get(lane)

        if not lane_dod:
            return {
                "status": DoDStatus.NOT_APPLICABLE,
                "passed_criteria": [],
                "failed_criteria": [],
                "message": f"No DoD defined for {lane} lane",
            }

        passed = []
        failed = []

        for criterion in lane_dod.criteria:
            # Simple field-based validation for now
            if self._check_criterion(criterion, item):
                passed.append(criterion.name)
            else:
                failed.append({
                    "name": criterion.name,
                    "description": criterion.description,
                    "required": criterion.required,
                })

        # Calculate pass percentage
        total = len(lane_dod.criteria)
        required_passed = sum(1 for c in lane_dod.criteria if c.required and c.name in passed)
        required_total = sum(1 for c in lane_dod.criteria if c.required)

        # Check if required criteria passed
        required_all_passed = required_passed == required_total
        pass_percentage = (len(passed) / total * 100) if total > 0 else 100

        if required_all_passed and pass_percentage >= lane_dod.min_pass_percentage:
            status = DoDStatus.PASSED
        elif required_passed > 0 or len(passed) > 0:
            status = DoDStatus.PARTIAL
        else:
            status = DoDStatus.FAILED

        result = {
            "status": status,
            "passed_criteria": passed,
            "failed_criteria": failed,
            "pass_percentage": pass_percentage,
            "required_passed": required_passed,
            "required_total": required_total,
            "message": self._generate_dod_message(status, passed, failed, lane),
        }

        logger.info(f"DoD validation for {lane}: {status} ({pass_percentage:.0f}%)")
        return result

    def _check_criterion(self, criterion: DoDCriterion, item: Dict[str, Any]) -> bool:
        """Check if a single DoD criterion is met."""
        # Map criterion names to item fields
        field_mapping = {
            "has_story_points": lambda i: i.get("story_points") is not None and i.get("story_points") > 0,
            "has_acceptance_criteria": lambda i: bool(i.get("acceptance_criteria")),
            "has_description": lambda i: bool(i.get("description") or i.get("content")),
            "assigned_to_sprint": lambda i: i.get("sprint_id") is not None,
            "dependencies_identified": lambda i: i.get("dependencies_checked", False),
            "has_assignee": lambda i: bool(i.get("assigned_to")),
            "code_written": lambda i: i.get("has_code", True),  # Default to True, needs real validation
            "local_tests_pass": lambda i: i.get("local_tests_passed", True),
            "no_syntax_errors": lambda i: i.get("no_syntax_errors", True),
            "unit_tests_pass": lambda i: i.get("unit_tests_passed", True),
            "coverage_adequate": lambda i: (i.get("test_coverage", 0) or 0) >= 80,
            "integration_tests_pass": lambda i: i.get("integration_tests_passed", True),
            "code_review_done": lambda i: i.get("code_review_completed", False),
            "security_check_passed": lambda i: i.get("security_check_passed", True),
            "documentation_updated": lambda i: i.get("documentation_updated", False),
        }

        checker = field_mapping.get(criterion.name)
        if checker:
            try:
                return checker(item)
            except Exception as e:
                logger.warning(f"Error checking criterion {criterion.name}: {e}")
                return False

        # Default: not applicable / pass
        return True

    def _generate_dod_message(
        self,
        status: DoDStatus,
        passed: List[str],
        failed: List[Dict],
        lane: str
    ) -> str:
        """Generate human-readable DoD message."""
        if status == DoDStatus.PASSED:
            return f"All Definition of Done criteria met for {lane} lane"
        elif status == DoDStatus.PARTIAL:
            failed_names = [f["name"] for f in failed if f["required"]]
            return f"Partial DoD: Missing required criteria: {', '.join(failed_names)}"
        else:
            return f"DoD failed: None of the criteria met for {lane} lane"

    async def trigger_agent_for_item(
        self,
        item_id: str,
        item_type: str,
        lane: str,
        agent_name: str,
        task_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger an agent to work on an item.

        Args:
            item_id: Item identifier
            item_type: Type of item
            lane: Current lane
            agent_name: Agent to trigger
            task_description: Optional task description

        Returns:
            Agent trigger result
        """
        # Record the agent action
        action_result = await self.event_service.record_agent_action(
            item_id=item_id,
            item_type=item_type,
            lane=lane,
            agent_name=agent_name,
            action=f"triggered_for_{lane}",
            success=True,  # Trigger is successful, execution tracked separately
            details={
                "task_description": task_description,
                "triggered_at": datetime.utcnow().isoformat(),
            }
        )

        logger.info(f"Triggered agent {agent_name} for item {item_id} in lane {lane}")

        return {
            "item_id": item_id,
            "agent": agent_name,
            "lane": lane,
            "status": "triggered",
            "action_id": action_result.get("id"),
            "message": f"Agent {agent_name} triggered for {item_type} {item_id}",
        }

    async def complete_agent_work(
        self,
        item_id: str,
        item_type: str,
        lane: str,
        agent_name: str,
        success: bool,
        work_result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        auto_progress: bool = True  # KaibanJS-style: auto-progress by default
    ) -> Dict[str, Any]:
        """
        Record completion of agent work on an item.

        KaibanJS-style: Automatically progresses to next lane when agent completes.
        This makes the Kanban board "live" with items moving automatically.

        Args:
            item_id: Item identifier
            item_type: Type of item
            lane: Current lane
            agent_name: Agent that completed work
            success: Whether work was successful
            work_result: Result details
            error_message: Error if not successful
            auto_progress: If True, auto-progress to next lane (KaibanJS pattern)

        Returns:
            Completion result with progression info
        """
        # Record the completion action
        await self.event_service.record_agent_action(
            item_id=item_id,
            item_type=item_type,
            lane=lane,
            agent_name=agent_name,
            action=f"completed_{lane}" if success else f"failed_{lane}",
            success=success,
            details={
                "work_result": work_result,
                "error_message": error_message,
                "completed_at": datetime.utcnow().isoformat(),
            }
        )

        # Trigger lane exit event (for retry tracking)
        exit_result = await self.event_service.on_lane_exit(
            item_id=item_id,
            item_type=item_type,
            lane=lane,
            success=success,
            agent_used=agent_name,
            error_message=error_message
        )

        result = {
            "item_id": item_id,
            "agent": agent_name,
            "lane": lane,
            "success": success,
            "message": f"Agent {agent_name} {'completed' if success else 'failed'} work on {item_id}",
        }

        # KaibanJS-STYLE: Automatic lane progression
        if auto_progress:
            agent_result = AgentResult.SUCCESS if success else AgentResult.FAILURE
            if error_message and "human" in error_message.lower():
                agent_result = AgentResult.NEEDS_HUMAN

            progression_result = await self.progression_service.on_agent_complete(
                item_id=item_id,
                item_type=item_type,
                agent_name=agent_name,
                result=agent_result,
                work_output=work_result,
                metadata={"original_lane": lane, "error_message": error_message}
            )

            result["auto_progression"] = progression_result

            if progression_result.get("progression"):
                result["moved_to"] = progression_result.get("to_lane")
                result["triggered_agents"] = progression_result.get("triggered_agents", [])
                result["message"] = (
                    f"Agent {agent_name} completed, auto-moved {item_id} "
                    f"from {lane} to {progression_result.get('to_lane')}"
                )
                logger.info(result["message"])
            elif progression_result.get("escalated"):
                result["escalated"] = True
                result["moved_to"] = "human_needed"
                result["message"] = f"Item {item_id} escalated to Human Needed after max retries"
                logger.warning(result["message"])
        else:
            # Legacy behavior: just suggest next lane
            if success:
                result["suggested_next_lane"] = self._get_next_lane(lane)
            else:
                result["error"] = error_message
                result["retry_info"] = exit_result

        return result

    def _get_next_lane(self, current_lane: str) -> Optional[str]:
        """Get the logical next lane in the workflow."""
        lane_flow = {
            KanbanLane.BACKLOG: KanbanLane.ANALYSIS,
            KanbanLane.ANALYSIS: KanbanLane.PLANNED,
            KanbanLane.PLANNED: KanbanLane.BUILD,
            KanbanLane.BUILD: KanbanLane.TEST,
            KanbanLane.TEST: KanbanLane.IN_REVIEW,
            KanbanLane.IN_REVIEW: KanbanLane.DONE,
        }
        return lane_flow.get(current_lane)

    async def get_agent_statistics(
        self,
        agent_name: Optional[str] = None,
        lane: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics for agent performance.

        Args:
            agent_name: Filter by specific agent
            lane: Filter by specific lane

        Returns:
            Agent performance statistics
        """
        from app.models.kanban_retry import KanbanAgentAction

        query = select(
            KanbanAgentAction.agent_name,
            KanbanAgentAction.lane,
            func.count(KanbanAgentAction.id).label("total_actions"),
            func.sum(func.cast(KanbanAgentAction.success, Integer)).label("successful_actions"),
        ).group_by(KanbanAgentAction.agent_name, KanbanAgentAction.lane)

        if agent_name:
            query = query.where(KanbanAgentAction.agent_name == agent_name)
        if lane:
            query = query.where(KanbanAgentAction.lane == lane)

        result = await self.db.execute(query)
        rows = result.fetchall()

        stats = []
        for row in rows:
            total = row.total_actions or 0
            success = row.successful_actions or 0
            stats.append({
                "agent": row.agent_name,
                "lane": row.lane,
                "total_actions": total,
                "successful_actions": success,
                "success_rate": (success / total * 100) if total > 0 else 0,
            })

        return {
            "statistics": stats,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def validate_lane_transition_quality(
        self,
        item_id: str,
        item_type: str,
        from_lane: str,
        to_lane: str,
        item_data: Dict[str, Any],
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validate quality gates for a lane transition.

        This executes the 42 validation rules when transitioning to IN_REVIEW.

        Args:
            item_id: Item identifier
            item_type: Type of item
            from_lane: Source lane
            to_lane: Target lane
            item_data: Item data for validation
            project_id: Optional project ID for custom rules

        Returns:
            Quality gate validation result
        """
        from app.services.kanban_quality_gate_service import KanbanQualityGateService

        quality_service = KanbanQualityGateService(self.db)

        result = await quality_service.validate_lane_transition(
            item_id=item_id,
            item_type=item_type,
            from_lane=from_lane,
            to_lane=to_lane,
            item_data=item_data,
            project_id=project_id
        )

        return {
            "item_id": item_id,
            "from_lane": from_lane,
            "to_lane": to_lane,
            "validation_passed": result.passed,
            "blocking_failures": [
                {
                    "rule_id": f.rule_id,
                    "rule_name": f.rule_name,
                    "category": f.category,
                    "severity": f.severity,
                    "message": f.message,
                }
                for f in result.blocking_failures
            ],
            "all_failures": [
                {
                    "rule_id": f.rule_id,
                    "rule_name": f.rule_name,
                    "category": f.category,
                    "severity": f.severity,
                    "message": f.message,
                }
                for f in result.all_failures
            ],
            "summary": result.summary,
            "can_proceed": result.passed,
        }

    async def get_lane_quality_rules(self, lane: str) -> List[Dict[str, Any]]:
        """
        Get all quality validation rules applicable to a specific lane.

        Args:
            lane: The lane to get rules for

        Returns:
            List of validation rules
        """
        from app.services.kanban_quality_gate_service import (
            VALIDATION_RULES,
            ValidationCategory
        )

        # Define lane-specific rule categories
        lane_categories = {
            KanbanLane.BUILD: [ValidationCategory.CODE_QUALITY],
            KanbanLane.TEST: [ValidationCategory.TESTING],
            KanbanLane.IN_REVIEW: [
                ValidationCategory.ARCHITECTURE,
                ValidationCategory.DESIGN,
                ValidationCategory.SECURITY,
                ValidationCategory.CODE_QUALITY,
                ValidationCategory.TESTING,
            ],
        }

        categories = lane_categories.get(lane, [])
        if not categories:
            return []

        return [
            {
                "id": rule.id,
                "name": rule.name,
                "category": rule.category.value,
                "description": rule.description,
                "severity": rule.severity.value,
                "blocking": rule.blocking,
                "threshold": rule.threshold,
            }
            for rule in VALIDATION_RULES
            if rule.category in categories
        ]

    async def get_available_stack_templates(self) -> List[Dict[str, Any]]:
        """Get all available tech stack templates."""
        from app.models.project_agent_config import STACK_TEMPLATES, TechStack

        templates = []
        for stack in TechStack:
            template_data = STACK_TEMPLATES.get(stack.value, {})
            templates.append({
                "stack_id": stack.value,
                "name": stack.name,
                "description": template_data.get("description", ""),
                "specialist_agents": template_data.get("specialist_agents", []),
                "has_extra_dod": "extra_dod_criteria" in template_data,
            })
        return templates
