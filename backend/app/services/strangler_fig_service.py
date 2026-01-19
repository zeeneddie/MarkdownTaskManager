"""
Strangler Fig Service - Fase 26: Migration Execution

Week 140-141: Incremental migration using the Strangler Fig pattern.
Supports feature flags, traffic splitting, and gradual rollout.

Agent: Miguel (Migration Architect)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Union
from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)


def _to_uuid(session_id: Union[UUID, str]) -> UUID:
    """Convert session_id to UUID, handling both string and UUID inputs."""
    if isinstance(session_id, UUID):
        return session_id
    try:
        return UUID(session_id)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid session_id: {session_id}")


# ==================== Enums ====================

class FeatureFlagStatus(Enum):
    """Feature flag states"""
    OFF = "off"
    CANARY = "canary"  # Small % of traffic
    GRADUAL = "gradual"  # Increasing rollout
    FULL = "full"  # 100% new system
    ROLLBACK = "rollback"  # Emergency rollback


class TrafficSplitStrategy(Enum):
    """Traffic splitting strategies"""
    PERCENTAGE = "percentage"  # Random % based
    USER_SEGMENT = "user_segment"  # Based on user attributes
    GEOGRAPHIC = "geographic"  # Region-based
    TIME_BASED = "time_based"  # Time windows
    HEADER_BASED = "header_based"  # Request headers


class MigrationPhase(Enum):
    """Strangler Fig migration phases"""
    IDENTIFY = "identify"  # Identify bounded contexts
    EXTRACT = "extract"  # Extract functionality
    REDIRECT = "redirect"  # Route traffic to new
    DEPRECATE = "deprecate"  # Mark legacy for removal
    RETIRE = "retire"  # Remove legacy code


class HealthStatus(Enum):
    """Component health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


# ==================== Data Classes ====================

@dataclass
class FeatureFlag:
    """Feature flag configuration"""
    id: str
    name: str
    description: str
    status: FeatureFlagStatus
    legacy_endpoint: str
    new_endpoint: str
    rollout_percentage: float = 0.0
    user_segments: List[str] = field(default_factory=list)
    geographic_regions: List[str] = field(default_factory=list)
    enabled_since: Optional[datetime] = None
    last_modified: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    tags: List[str] = field(default_factory=list)


@dataclass
class TrafficRule:
    """Traffic routing rule"""
    id: str
    feature_flag_id: str
    strategy: TrafficSplitStrategy
    condition: str  # Expression for routing decision
    weight: float  # 0.0 to 1.0
    target: str  # "legacy" or "new"
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MigrationComponent:
    """Component being migrated"""
    id: str
    name: str
    legacy_path: str
    new_path: Optional[str]
    phase: MigrationPhase
    feature_flag_id: Optional[str]
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    lines_of_code: int = 0
    complexity_score: float = 0.0
    migration_effort_hours: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    health_status: HealthStatus = HealthStatus.UNKNOWN


@dataclass
class RolloutStep:
    """Gradual rollout step configuration"""
    step_number: int
    percentage: float
    duration_hours: int
    success_criteria: Dict[str, Any]
    rollback_criteria: Dict[str, Any]
    notifications: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, active, completed, failed


@dataclass
class RolloutPlan:
    """Complete rollout plan for a migration"""
    id: str
    component_id: str
    name: str
    steps: List[RolloutStep]
    current_step: int = 0
    status: str = "draft"  # draft, active, paused, completed, aborted
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    rollback_count: int = 0


@dataclass
class HealthCheck:
    """Health check result"""
    component_id: str
    timestamp: datetime
    status: HealthStatus
    latency_ms: float
    error_rate: float
    success_rate: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)


@dataclass
class StranglerSession:
    """Active strangler fig migration session"""
    id: UUID
    project_id: str
    name: str
    components: List[MigrationComponent]
    feature_flags: List[FeatureFlag]
    rollout_plans: List[RolloutPlan]
    traffic_rules: List[TrafficRule]
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# ==================== Service ====================

class StranglerFigService:
    """
    Strangler Fig Pattern implementation for incremental migration.

    Features:
    - Feature flag management
    - Traffic splitting configuration
    - Gradual rollout planning
    - Health monitoring integration
    - Automatic rollback support
    """

    def __init__(self):
        self.sessions: Dict[UUID, StranglerSession] = {}
        self.health_history: Dict[str, List[HealthCheck]] = {}

    # ==================== Session Management ====================

    async def create_session(
        self,
        project_id: str,
        name: str,
        components: Optional[List[Dict[str, Any]]] = None
    ) -> StranglerSession:
        """Create a new strangler fig migration session."""
        session_id = uuid4()

        migration_components = []
        if components:
            for i, comp in enumerate(components):
                migration_components.append(MigrationComponent(
                    id=f"comp-{i+1:03d}",
                    name=comp.get("name", f"Component-{i+1}"),
                    legacy_path=comp.get("legacy_path", ""),
                    new_path=comp.get("new_path"),
                    phase=MigrationPhase.IDENTIFY,
                    feature_flag_id=None,
                    dependencies=comp.get("dependencies", []),
                    lines_of_code=comp.get("loc", 0),
                    complexity_score=comp.get("complexity", 0.0),
                ))

        session = StranglerSession(
            id=session_id,
            project_id=project_id,
            name=name,
            components=migration_components,
            feature_flags=[],
            rollout_plans=[],
            traffic_rules=[],
        )

        self.sessions[session_id] = session
        logger.info(f"Created strangler fig session: {session_id}")

        return session

    async def get_session(self, session_id: Union[UUID, str]) -> Optional[StranglerSession]:
        """Get session by ID."""
        uuid_id = _to_uuid(session_id)
        return self.sessions.get(uuid_id)

    # ==================== Feature Flags ====================

    async def create_feature_flag(
        self,
        session_id: Union[UUID, str],
        name: str,
        legacy_endpoint: str,
        new_endpoint: str,
        description: str = "",
        initial_status: FeatureFlagStatus = FeatureFlagStatus.OFF
    ) -> Optional[FeatureFlag]:
        """Create a new feature flag for traffic routing."""
        uuid_id = _to_uuid(session_id)
        session = self.sessions.get(uuid_id)
        if not session:
            return None

        flag_id = f"ff-{len(session.feature_flags)+1:03d}"

        flag = FeatureFlag(
            id=flag_id,
            name=name,
            description=description,
            status=initial_status,
            legacy_endpoint=legacy_endpoint,
            new_endpoint=new_endpoint,
        )

        session.feature_flags.append(flag)
        session.updated_at = datetime.now()

        logger.info(f"Created feature flag: {flag_id} for session {session_id}")
        return flag

    async def update_feature_flag_status(
        self,
        session_id: Union[UUID, str],
        flag_id: str,
        status: FeatureFlagStatus,
        rollout_percentage: Optional[float] = None
    ) -> Optional[FeatureFlag]:
        """Update feature flag status and rollout percentage."""
        uuid_id = _to_uuid(session_id)
        session = self.sessions.get(uuid_id)
        if not session:
            return None

        for flag in session.feature_flags:
            if flag.id == flag_id:
                flag.status = status
                if rollout_percentage is not None:
                    flag.rollout_percentage = min(100.0, max(0.0, rollout_percentage))
                flag.last_modified = datetime.now()

                if status == FeatureFlagStatus.CANARY and not flag.enabled_since:
                    flag.enabled_since = datetime.now()

                logger.info(f"Updated flag {flag_id}: status={status.value}, rollout={flag.rollout_percentage}%")
                return flag

        return None

    # ==================== Traffic Rules ====================

    async def create_traffic_rule(
        self,
        session_id: Union[UUID, str],
        feature_flag_id: str,
        strategy: TrafficSplitStrategy,
        condition: str,
        weight: float,
        target: str
    ) -> Optional[TrafficRule]:
        """Create a traffic routing rule."""
        uuid_id = _to_uuid(session_id)
        session = self.sessions.get(uuid_id)
        if not session:
            return None

        rule = TrafficRule(
            id=f"tr-{len(session.traffic_rules)+1:03d}",
            feature_flag_id=feature_flag_id,
            strategy=strategy,
            condition=condition,
            weight=weight,
            target=target,
            priority=len(session.traffic_rules),
        )

        session.traffic_rules.append(rule)
        return rule

    async def evaluate_traffic_routing(
        self,
        session_id: Union[UUID, str],
        flag_id: str,
        request_context: Dict[str, Any]
    ) -> str:
        """
        Evaluate which endpoint to route to based on flag and rules.

        Returns: "legacy" or "new"
        """
        uuid_id = _to_uuid(session_id)
        session = self.sessions.get(uuid_id)
        if not session:
            return "legacy"

        # Find the flag
        flag = next((f for f in session.feature_flags if f.id == flag_id), None)
        if not flag:
            return "legacy"

        # Check flag status
        if flag.status == FeatureFlagStatus.OFF:
            return "legacy"
        elif flag.status == FeatureFlagStatus.FULL:
            return "new"
        elif flag.status == FeatureFlagStatus.ROLLBACK:
            return "legacy"

        # Get applicable rules
        applicable_rules = [
            r for r in session.traffic_rules
            if r.feature_flag_id == flag_id
        ]
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)

        # Evaluate rules
        for rule in applicable_rules:
            if self._evaluate_rule_condition(rule, request_context):
                return rule.target

        # Default: percentage-based
        import random
        if random.random() * 100 < flag.rollout_percentage:
            return "new"

        return "legacy"

    def _evaluate_rule_condition(
        self,
        rule: TrafficRule,
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate a single traffic rule condition."""
        try:
            if rule.strategy == TrafficSplitStrategy.PERCENTAGE:
                import random
                return random.random() < rule.weight

            elif rule.strategy == TrafficSplitStrategy.USER_SEGMENT:
                user_segment = context.get("user_segment", "default")
                return user_segment in rule.condition.split(",")

            elif rule.strategy == TrafficSplitStrategy.GEOGRAPHIC:
                region = context.get("region", "unknown")
                return region in rule.condition.split(",")

            elif rule.strategy == TrafficSplitStrategy.HEADER_BASED:
                header_name, expected = rule.condition.split("=", 1)
                return context.get("headers", {}).get(header_name) == expected

            elif rule.strategy == TrafficSplitStrategy.TIME_BASED:
                # Format: "HH:MM-HH:MM"
                now = datetime.now()
                start_str, end_str = rule.condition.split("-")
                start_hour, start_min = map(int, start_str.split(":"))
                end_hour, end_min = map(int, end_str.split(":"))

                current_minutes = now.hour * 60 + now.minute
                start_minutes = start_hour * 60 + start_min
                end_minutes = end_hour * 60 + end_min

                return start_minutes <= current_minutes <= end_minutes

        except Exception as e:
            logger.warning(f"Rule evaluation failed: {e}")
            return False

        return False

    # ==================== Rollout Planning ====================

    async def create_rollout_plan(
        self,
        session_id: Union[UUID, str],
        component_id: str,
        name: str,
        steps: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[RolloutPlan]:
        """Create a gradual rollout plan."""
        uuid_id = _to_uuid(session_id)
        session = self.sessions.get(uuid_id)
        if not session:
            return None

        rollout_steps = []

        if steps:
            for i, step in enumerate(steps):
                rollout_steps.append(RolloutStep(
                    step_number=i + 1,
                    percentage=step.get("percentage", (i + 1) * 25),
                    duration_hours=step.get("duration_hours", 24),
                    success_criteria=step.get("success_criteria", {
                        "error_rate_max": 0.01,
                        "latency_p99_ms": 500,
                    }),
                    rollback_criteria=step.get("rollback_criteria", {
                        "error_rate_threshold": 0.05,
                        "latency_p99_threshold_ms": 2000,
                    }),
                ))
        else:
            # Default 4-step rollout
            rollout_steps = [
                RolloutStep(
                    step_number=1,
                    percentage=5.0,
                    duration_hours=24,
                    success_criteria={"error_rate_max": 0.01, "latency_p99_ms": 500},
                    rollback_criteria={"error_rate_threshold": 0.05},
                ),
                RolloutStep(
                    step_number=2,
                    percentage=25.0,
                    duration_hours=48,
                    success_criteria={"error_rate_max": 0.01, "latency_p99_ms": 500},
                    rollback_criteria={"error_rate_threshold": 0.03},
                ),
                RolloutStep(
                    step_number=3,
                    percentage=50.0,
                    duration_hours=72,
                    success_criteria={"error_rate_max": 0.005, "latency_p99_ms": 400},
                    rollback_criteria={"error_rate_threshold": 0.02},
                ),
                RolloutStep(
                    step_number=4,
                    percentage=100.0,
                    duration_hours=168,  # 1 week
                    success_criteria={"error_rate_max": 0.001, "latency_p99_ms": 300},
                    rollback_criteria={"error_rate_threshold": 0.01},
                ),
            ]

        plan = RolloutPlan(
            id=f"rp-{len(session.rollout_plans)+1:03d}",
            component_id=component_id,
            name=name,
            steps=rollout_steps,
        )

        session.rollout_plans.append(plan)
        logger.info(f"Created rollout plan: {plan.id} with {len(rollout_steps)} steps")

        return plan

    async def advance_rollout(
        self,
        session_id: Union[UUID, str],
        plan_id: str
    ) -> Optional[Dict[str, Any]]:
        """Advance to next rollout step if criteria met."""
        uuid_id = _to_uuid(session_id)
        session = self.sessions.get(uuid_id)
        if not session:
            return None

        plan = next((p for p in session.rollout_plans if p.id == plan_id), None)
        if not plan:
            return None

        if plan.current_step >= len(plan.steps):
            return {"status": "completed", "message": "Rollout already complete"}

        current_step = plan.steps[plan.current_step]

        # Check health before advancing
        component_health = self.health_history.get(plan.component_id, [])
        if component_health:
            latest_health = component_health[-1]
            if latest_health.status != HealthStatus.HEALTHY:
                return {
                    "status": "blocked",
                    "reason": f"Component unhealthy: {latest_health.status.value}",
                    "health": latest_health.metrics,
                }

        # Mark current step complete
        current_step.status = "completed"
        plan.current_step += 1

        if plan.current_step >= len(plan.steps):
            plan.status = "completed"
            plan.completed_at = datetime.now()
            return {"status": "completed", "message": "Rollout complete"}

        # Activate next step
        next_step = plan.steps[plan.current_step]
        next_step.status = "active"

        return {
            "status": "advanced",
            "current_step": plan.current_step + 1,
            "percentage": next_step.percentage,
            "duration_hours": next_step.duration_hours,
        }

    async def rollback_plan(
        self,
        session_id: Union[UUID, str],
        plan_id: str,
        reason: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Rollback to previous step or disable entirely."""
        uuid_id = _to_uuid(session_id)
        session = self.sessions.get(uuid_id)
        if not session:
            return None

        plan = next((p for p in session.rollout_plans if p.id == plan_id), None)
        if not plan:
            return None

        previous_step = plan.current_step

        if plan.current_step > 0:
            plan.steps[plan.current_step].status = "failed"
            plan.current_step -= 1
            plan.steps[plan.current_step].status = "active"
        else:
            plan.status = "aborted"

        plan.rollback_count += 1

        # Also set feature flag to rollback
        component = next((c for c in session.components if c.id == plan.component_id), None)
        if component and component.feature_flag_id:
            await self.update_feature_flag_status(
                session_id,
                component.feature_flag_id,
                FeatureFlagStatus.ROLLBACK
            )

        logger.warning(f"Rollback plan {plan_id}: step {previous_step} -> {plan.current_step}. Reason: {reason}")

        return {
            "status": "rolled_back",
            "from_step": previous_step + 1,
            "to_step": plan.current_step + 1,
            "rollback_count": plan.rollback_count,
            "reason": reason,
        }

    # ==================== Health Monitoring ====================

    async def record_health_check(
        self,
        component_id: str,
        status: HealthStatus,
        latency_ms: float,
        error_rate: float,
        metrics: Optional[Dict[str, Any]] = None
    ) -> HealthCheck:
        """Record a health check for monitoring."""
        health = HealthCheck(
            component_id=component_id,
            timestamp=datetime.now(),
            status=status,
            latency_ms=latency_ms,
            error_rate=error_rate,
            success_rate=1.0 - error_rate,
            metrics=metrics or {},
        )

        # Generate alerts if unhealthy
        if status == HealthStatus.UNHEALTHY:
            health.alerts.append(f"Component {component_id} is UNHEALTHY")
        if error_rate > 0.05:
            health.alerts.append(f"High error rate: {error_rate*100:.1f}%")
        if latency_ms > 1000:
            health.alerts.append(f"High latency: {latency_ms:.0f}ms")

        # Store in history
        if component_id not in self.health_history:
            self.health_history[component_id] = []
        self.health_history[component_id].append(health)

        # Keep last 1000 checks
        if len(self.health_history[component_id]) > 1000:
            self.health_history[component_id] = self.health_history[component_id][-1000:]

        return health

    async def check_rollback_needed(
        self,
        session_id: Union[UUID, str],
        plan_id: str
    ) -> Optional[Dict[str, Any]]:
        """Check if automatic rollback is needed based on health."""
        uuid_id = _to_uuid(session_id)
        session = self.sessions.get(uuid_id)
        if not session:
            return None

        plan = next((p for p in session.rollout_plans if p.id == plan_id), None)
        if not plan or plan.status != "active":
            return None

        current_step = plan.steps[plan.current_step]
        rollback_criteria = current_step.rollback_criteria

        # Get recent health checks
        component_health = self.health_history.get(plan.component_id, [])
        recent_health = component_health[-10:] if component_health else []

        if not recent_health:
            return {"needs_rollback": False, "reason": "No health data"}

        # Calculate averages
        avg_error_rate = sum(h.error_rate for h in recent_health) / len(recent_health)
        avg_latency = sum(h.latency_ms for h in recent_health) / len(recent_health)
        unhealthy_count = sum(1 for h in recent_health if h.status == HealthStatus.UNHEALTHY)

        # Check criteria
        reasons = []
        needs_rollback = False

        error_threshold = rollback_criteria.get("error_rate_threshold", 0.05)
        if avg_error_rate > error_threshold:
            reasons.append(f"Error rate {avg_error_rate*100:.1f}% > {error_threshold*100:.1f}%")
            needs_rollback = True

        latency_threshold = rollback_criteria.get("latency_p99_threshold_ms", 2000)
        if avg_latency > latency_threshold:
            reasons.append(f"Latency {avg_latency:.0f}ms > {latency_threshold}ms")
            needs_rollback = True

        if unhealthy_count > len(recent_health) * 0.5:
            reasons.append(f"{unhealthy_count}/{len(recent_health)} checks unhealthy")
            needs_rollback = True

        return {
            "needs_rollback": needs_rollback,
            "reasons": reasons,
            "metrics": {
                "avg_error_rate": avg_error_rate,
                "avg_latency_ms": avg_latency,
                "unhealthy_checks": unhealthy_count,
                "total_checks": len(recent_health),
            }
        }

    # ==================== Component Progress ====================

    async def update_component_phase(
        self,
        session_id: Union[UUID, str],
        component_id: str,
        phase: MigrationPhase
    ) -> Optional[MigrationComponent]:
        """Update component migration phase."""
        uuid_id = _to_uuid(session_id)
        session = self.sessions.get(uuid_id)
        if not session:
            return None

        component = next((c for c in session.components if c.id == component_id), None)
        if not component:
            return None

        old_phase = component.phase
        component.phase = phase
        session.updated_at = datetime.now()

        if phase == MigrationPhase.EXTRACT and not component.started_at:
            component.started_at = datetime.now()
        elif phase == MigrationPhase.RETIRE:
            component.completed_at = datetime.now()

        logger.info(f"Component {component_id}: {old_phase.value} -> {phase.value}")
        return component

    async def get_migration_progress(
        self,
        session_id: Union[UUID, str]
    ) -> Optional[Dict[str, Any]]:
        """Get overall migration progress summary."""
        uuid_id = _to_uuid(session_id)
        session = self.sessions.get(uuid_id)
        if not session:
            return None

        phase_counts = {}
        for phase in MigrationPhase:
            phase_counts[phase.value] = sum(
                1 for c in session.components if c.phase == phase
            )

        total = len(session.components)
        completed = phase_counts.get("retire", 0)
        in_progress = total - phase_counts.get("identify", 0) - completed

        return {
            "session_id": str(session.id),
            "name": session.name,
            "total_components": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": phase_counts.get("identify", 0),
            "progress_percentage": (completed / total * 100) if total > 0 else 0,
            "phase_breakdown": phase_counts,
            "feature_flags_active": sum(
                1 for f in session.feature_flags
                if f.status not in [FeatureFlagStatus.OFF, FeatureFlagStatus.ROLLBACK]
            ),
            "rollout_plans": len(session.rollout_plans),
            "status": session.status,
        }

    # ==================== Export ====================

    def to_mermaid_diagram(self, session: StranglerSession) -> str:
        """Generate Mermaid diagram of migration state."""
        lines = ["graph LR"]

        # Group by phase
        for phase in MigrationPhase:
            phase_components = [c for c in session.components if c.phase == phase]
            if phase_components:
                lines.append(f"    subgraph {phase.value.upper()}")
                for comp in phase_components:
                    lines.append(f"        {comp.id}[{comp.name}]")
                lines.append("    end")

        # Add arrows for dependencies
        for comp in session.components:
            for dep in comp.dependencies:
                lines.append(f"    {dep} --> {comp.id}")

        # Add feature flag connections
        for flag in session.feature_flags:
            lines.append(f"    {flag.id}{{{{FF: {flag.name}}}}}")
            lines.append(f"    {flag.id} -.-> {flag.legacy_endpoint}")
            lines.append(f"    {flag.id} -.-> {flag.new_endpoint}")

        return "\n".join(lines)

    def to_markdown_report(self, session: StranglerSession) -> str:
        """Generate markdown progress report."""
        lines = [
            f"# Strangler Fig Migration Report",
            f"",
            f"**Session:** {session.name}",
            f"**ID:** {session.id}",
            f"**Status:** {session.status}",
            f"**Created:** {session.created_at.isoformat()}",
            f"",
            f"## Component Summary",
            f"",
            f"| Component | Phase | LOC | Complexity | Started | Completed |",
            f"|-----------|-------|-----|------------|---------|-----------|",
        ]

        for comp in session.components:
            started = comp.started_at.strftime("%Y-%m-%d") if comp.started_at else "-"
            completed = comp.completed_at.strftime("%Y-%m-%d") if comp.completed_at else "-"
            lines.append(
                f"| {comp.name} | {comp.phase.value} | {comp.lines_of_code} | "
                f"{comp.complexity_score:.1f} | {started} | {completed} |"
            )

        lines.extend([
            f"",
            f"## Feature Flags",
            f"",
            f"| Flag | Status | Rollout % | Legacy | New |",
            f"|------|--------|-----------|--------|-----|",
        ])

        for flag in session.feature_flags:
            lines.append(
                f"| {flag.name} | {flag.status.value} | {flag.rollout_percentage:.1f}% | "
                f"`{flag.legacy_endpoint}` | `{flag.new_endpoint}` |"
            )

        if session.rollout_plans:
            lines.extend([
                f"",
                f"## Rollout Plans",
                f"",
            ])
            for plan in session.rollout_plans:
                lines.append(f"### {plan.name}")
                lines.append(f"- Status: {plan.status}")
                lines.append(f"- Current Step: {plan.current_step + 1}/{len(plan.steps)}")
                if plan.rollback_count > 0:
                    lines.append(f"- Rollbacks: {plan.rollback_count}")

        return "\n".join(lines)
