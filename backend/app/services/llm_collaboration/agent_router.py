"""
Agent Router Service - B12 (Fase 24)

Intelligently routes tasks to appropriate agents based on:
- Required capabilities
- Agent availability and load
- Specialization matching
- Historical reliability
- Collaboration patterns

Integrates with existing services:
- TaskchainService: For sequential task execution
- LLMCouncilService: For consensus-based decisions
- StackAgentFactory: For agent instantiation

Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from .collaboration_types import (
    AgentProfile,
    AgentCapabilityType,
    AgentStatus,
    CollaborationTask,
    CollaborationPattern,
    CollaborationSession,
    RoutingDecision,
    TaskPriority,
    PREDEFINED_PATTERNS
)

logger = logging.getLogger(__name__)


@dataclass
class RoutingScore:
    """Score breakdown for agent selection."""
    agent_id: str
    total_score: float
    capability_score: float
    availability_score: float
    specialization_score: float
    reliability_score: float
    latency_score: float
    breakdown: Dict[str, float] = field(default_factory=dict)


class AgentRouter:
    """
    Routes tasks to appropriate agents based on multiple factors.

    Scoring Factors (weighted):
    - Capability Match (0.35): Does agent have required capabilities?
    - Availability (0.25): Is agent available and not overloaded?
    - Specialization (0.20): Does agent specialize in this domain?
    - Reliability (0.15): Historical success rate
    - Latency (0.05): Expected response time

    Usage:
        router = AgentRouter()

        # Register agents
        router.register_agent(AgentProfile(
            agent_id="felix",
            name="Felix Code Analyzer",
            capabilities={AgentCapabilityType.CODE_ANALYSIS, AgentCapabilityType.CODE_REVIEW},
            specializations=["python", "typescript"]
        ))

        # Route a task
        decision = router.route_task(CollaborationTask(
            task_type="code_analysis",
            payload={"code": "..."},
            required_capabilities={AgentCapabilityType.CODE_ANALYSIS}
        ))
    """

    # Scoring weights
    WEIGHT_CAPABILITY = 0.35
    WEIGHT_AVAILABILITY = 0.25
    WEIGHT_SPECIALIZATION = 0.20
    WEIGHT_RELIABILITY = 0.15
    WEIGHT_LATENCY = 0.05

    def __init__(self):
        # Registry of available agents
        self._agents: Dict[str, AgentProfile] = {}

        # Active sessions
        self._sessions: Dict[UUID, CollaborationSession] = {}

        # Routing history for learning
        self._routing_history: List[Dict] = []

        # Initialize with known agents
        self._register_known_agents()

        logger.info("AgentRouter initialized")

    def _register_known_agents(self) -> None:
        """Register known agents from the system."""
        # These map to existing agents in the codebase
        known_agents = [
            AgentProfile(
                agent_id="felix",
                name="Felix Code Analyzer",
                capabilities={
                    AgentCapabilityType.CODE_ANALYSIS,
                    AgentCapabilityType.CODE_REVIEW,
                    AgentCapabilityType.DEBUGGING
                },
                specializations=["python", "typescript", "javascript"],
                reliability=0.92,
                avg_latency_ms=3000
            ),
            AgentProfile(
                agent_id="quinn",
                name="Quinn Quality Auditor",
                capabilities={
                    AgentCapabilityType.CODE_REVIEW,
                    AgentCapabilityType.TESTING,
                    AgentCapabilityType.CODE_ANALYSIS
                },
                specializations=["quality", "testing", "ci-cd"],
                reliability=0.94,
                avg_latency_ms=4000
            ),
            AgentProfile(
                agent_id="ghostcrew",
                name="GhostCrew Security Team",
                capabilities={
                    AgentCapabilityType.SECURITY_AUDIT,
                    AgentCapabilityType.CODE_ANALYSIS,
                    AgentCapabilityType.CODE_REVIEW
                },
                specializations=["security", "owasp", "cve", "vulnerability"],
                reliability=0.96,
                avg_latency_ms=5000
            ),
            AgentProfile(
                agent_id="kaiban_architect",
                name="KaibanJS Architect",
                capabilities={
                    AgentCapabilityType.ARCHITECTURE,
                    AgentCapabilityType.PLANNING,
                    AgentCapabilityType.CODE_GENERATION
                },
                specializations=["architecture", "design", "planning"],
                reliability=0.90,
                avg_latency_ms=6000
            ),
            AgentProfile(
                agent_id="kaiban_developer",
                name="KaibanJS Developer",
                capabilities={
                    AgentCapabilityType.CODE_GENERATION,
                    AgentCapabilityType.CODE_REFACTORING,
                    AgentCapabilityType.DEBUGGING
                },
                specializations=["implementation", "refactoring"],
                reliability=0.88,
                avg_latency_ms=4500
            ),
            AgentProfile(
                agent_id="llm_council",
                name="LLM Council (Multi-Model)",
                capabilities={
                    AgentCapabilityType.CODE_REVIEW,
                    AgentCapabilityType.ARCHITECTURE,
                    AgentCapabilityType.PLANNING
                },
                specializations=["consensus", "decision-making", "validation"],
                reliability=0.95,
                avg_latency_ms=15000,  # Slower due to multi-model
                max_concurrent=2
            ),
            AgentProfile(
                agent_id="migration_agent",
                name="Migration Specialist",
                capabilities={
                    AgentCapabilityType.MIGRATION,
                    AgentCapabilityType.CODE_ANALYSIS,
                    AgentCapabilityType.ARCHITECTURE
                },
                specializations=["migration", "legacy", "modernization", "database"],
                reliability=0.91,
                avg_latency_ms=8000
            ),
            AgentProfile(
                agent_id="doc_writer",
                name="Documentation Writer",
                capabilities={
                    AgentCapabilityType.DOCUMENTATION,
                    AgentCapabilityType.CODE_ANALYSIS
                },
                specializations=["documentation", "api-docs", "readme"],
                reliability=0.93,
                avg_latency_ms=3500
            ),
        ]

        for agent in known_agents:
            self.register_agent(agent)

    def register_agent(self, agent: AgentProfile) -> None:
        """Register an agent with the router."""
        self._agents[agent.agent_id] = agent
        logger.debug(f"Registered agent: {agent.agent_id} ({agent.name})")

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the router."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.debug(f"Unregistered agent: {agent_id}")
            return True
        return False

    def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
        """Get agent profile by ID."""
        return self._agents.get(agent_id)

    def list_agents(
        self,
        capability: Optional[AgentCapabilityType] = None,
        available_only: bool = False
    ) -> List[AgentProfile]:
        """List agents, optionally filtered."""
        agents = list(self._agents.values())

        if capability:
            agents = [a for a in agents if a.has_capability(capability)]

        if available_only:
            agents = [a for a in agents if a.is_available]

        return agents

    def update_agent_status(
        self,
        agent_id: str,
        status: Optional[AgentStatus] = None,
        current_load: Optional[int] = None
    ) -> bool:
        """Update agent status or load."""
        agent = self._agents.get(agent_id)
        if not agent:
            return False

        if status is not None:
            agent.status = status

        if current_load is not None:
            agent.current_load = current_load

        return True

    def _calculate_capability_score(
        self,
        agent: AgentProfile,
        required: Set[AgentCapabilityType]
    ) -> float:
        """
        Calculate capability match score.

        Returns 1.0 if agent has all required capabilities,
        0.0 if agent has none, proportional otherwise.
        """
        if not required:
            return 1.0

        matched = sum(1 for cap in required if agent.has_capability(cap))
        return matched / len(required)

    def _calculate_availability_score(self, agent: AgentProfile) -> float:
        """
        Calculate availability score.

        Factors in status and current load.
        """
        if agent.status != AgentStatus.AVAILABLE:
            return 0.0

        # Higher score for lower load
        return 1.0 - agent.load_factor

    def _calculate_latency_score(self, agent: AgentProfile) -> float:
        """
        Calculate latency score (normalized).

        Lower latency = higher score.
        Assumes max acceptable latency of 30 seconds.
        """
        max_latency = 30000  # 30 seconds
        if agent.avg_latency_ms >= max_latency:
            return 0.0
        return 1.0 - (agent.avg_latency_ms / max_latency)

    def _score_agent(
        self,
        agent: AgentProfile,
        task: CollaborationTask
    ) -> RoutingScore:
        """
        Calculate comprehensive routing score for an agent.

        Higher score = better match for the task.
        """
        capability_score = self._calculate_capability_score(
            agent, task.required_capabilities
        )
        availability_score = self._calculate_availability_score(agent)
        specialization_score = agent.matches_specialization(
            task.metadata.get("specializations", [])
        )
        reliability_score = agent.reliability
        latency_score = self._calculate_latency_score(agent)

        # Weighted total
        total_score = (
            capability_score * self.WEIGHT_CAPABILITY +
            availability_score * self.WEIGHT_AVAILABILITY +
            specialization_score * self.WEIGHT_SPECIALIZATION +
            reliability_score * self.WEIGHT_RELIABILITY +
            latency_score * self.WEIGHT_LATENCY
        )

        return RoutingScore(
            agent_id=agent.agent_id,
            total_score=total_score,
            capability_score=capability_score,
            availability_score=availability_score,
            specialization_score=specialization_score,
            reliability_score=reliability_score,
            latency_score=latency_score,
            breakdown={
                "capability": capability_score * self.WEIGHT_CAPABILITY,
                "availability": availability_score * self.WEIGHT_AVAILABILITY,
                "specialization": specialization_score * self.WEIGHT_SPECIALIZATION,
                "reliability": reliability_score * self.WEIGHT_RELIABILITY,
                "latency": latency_score * self.WEIGHT_LATENCY
            }
        )

    def _select_pattern(
        self,
        task: CollaborationTask,
        candidate_count: int
    ) -> CollaborationPattern:
        """
        Select appropriate collaboration pattern for the task.

        Based on task type and number of suitable agents.
        """
        # Check predefined patterns
        task_type = task.task_type.lower()
        if task_type in PREDEFINED_PATTERNS:
            return PREDEFINED_PATTERNS[task_type]["pattern"]

        # Default pattern selection based on context
        if candidate_count == 1:
            return CollaborationPattern.SPECIALIST

        if task.priority == TaskPriority.CRITICAL:
            return CollaborationPattern.PARALLEL  # Fastest results

        if "review" in task_type or "audit" in task_type:
            return CollaborationPattern.CONSENSUS

        if "generate" in task_type or "create" in task_type:
            return CollaborationPattern.ENSEMBLE

        return CollaborationPattern.PARALLEL

    def route_task(
        self,
        task: CollaborationTask,
        max_agents: int = 3,
        min_score: float = 0.4
    ) -> RoutingDecision:
        """
        Route a task to appropriate agents.

        Args:
            task: The task to route
            max_agents: Maximum number of agents to select
            min_score: Minimum score threshold for selection

        Returns:
            RoutingDecision with selected agents and pattern
        """
        # Score all agents
        scores: List[RoutingScore] = []
        for agent in self._agents.values():
            # Must have at least one required capability
            if task.required_capabilities:
                has_any = any(
                    agent.has_capability(cap)
                    for cap in task.required_capabilities
                )
                if not has_any:
                    continue

            score = self._score_agent(agent, task)
            if score.total_score >= min_score:
                scores.append(score)

        # Sort by score descending
        scores.sort(key=lambda s: s.total_score, reverse=True)

        # Handle preferred agents (boost them if valid)
        if task.preferred_agents:
            preferred_scores = [s for s in scores if s.agent_id in task.preferred_agents]
            other_scores = [s for s in scores if s.agent_id not in task.preferred_agents]
            scores = preferred_scores + other_scores

        # Select top agents
        selected = [s.agent_id for s in scores[:max_agents]]
        fallbacks = [s.agent_id for s in scores[max_agents:max_agents + 2]]

        # Determine collaboration pattern
        pattern = self._select_pattern(task, len(selected))

        # Generate reasoning
        reasoning = self._generate_reasoning(task, scores[:max_agents], pattern)

        decision = RoutingDecision(
            task=task,
            selected_agents=selected,
            pattern=pattern,
            reasoning=reasoning,
            fallback_agents=fallbacks
        )

        # Log for learning
        self._routing_history.append({
            "task_id": str(task.task_id),
            "task_type": task.task_type,
            "selected": selected,
            "pattern": pattern.value,
            "scores": [(s.agent_id, s.total_score) for s in scores[:5]],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        logger.info(
            f"Routed task {task.task_id} to agents {selected} "
            f"using {pattern.value} pattern"
        )

        return decision

    def _generate_reasoning(
        self,
        task: CollaborationTask,
        scores: List[RoutingScore],
        pattern: CollaborationPattern
    ) -> str:
        """Generate human-readable reasoning for routing decision."""
        if not scores:
            return "No suitable agents found for task requirements."

        parts = [
            f"Task type: {task.task_type}",
            f"Required capabilities: {[c.value for c in task.required_capabilities]}",
            f"Selected pattern: {pattern.value}",
            "",
            "Agent selection:"
        ]

        for score in scores:
            parts.append(
                f"  - {score.agent_id}: score={score.total_score:.2f} "
                f"(cap={score.capability_score:.2f}, "
                f"avail={score.availability_score:.2f}, "
                f"spec={score.specialization_score:.2f})"
            )

        return "\n".join(parts)

    def create_session(
        self,
        task: CollaborationTask,
        decision: RoutingDecision
    ) -> CollaborationSession:
        """
        Create a collaboration session from a routing decision.

        The session tracks the multi-agent collaboration.
        """
        session = CollaborationSession(
            pattern=decision.pattern,
            participating_agents=decision.selected_agents,
            tasks=[task],
            shared_context=task.context.copy(),
            metadata={
                "routing_reasoning": decision.reasoning,
                "fallback_agents": decision.fallback_agents
            }
        )

        self._sessions[session.session_id] = session

        # Update agent loads
        for agent_id in decision.selected_agents:
            if agent_id in self._agents:
                self._agents[agent_id].current_load += 1

        logger.info(f"Created collaboration session {session.session_id}")
        return session

    def complete_session(self, session_id: UUID) -> Optional[CollaborationSession]:
        """
        Mark a session as complete and release agent capacity.

        Returns the completed session or None if not found.
        """
        session = self._sessions.get(session_id)
        if not session:
            return None

        session.complete()

        # Release agent capacity
        for agent_id in session.participating_agents:
            if agent_id in self._agents:
                self._agents[agent_id].current_load = max(
                    0, self._agents[agent_id].current_load - 1
                )

        logger.info(f"Completed collaboration session {session_id}")
        return session

    def get_session(self, session_id: UUID) -> Optional[CollaborationSession]:
        """Get a collaboration session by ID."""
        return self._sessions.get(session_id)

    def get_routing_stats(self) -> Dict:
        """Get routing statistics for monitoring."""
        if not self._routing_history:
            return {"total_routings": 0}

        pattern_counts = {}
        agent_counts = {}

        for entry in self._routing_history:
            pattern = entry["pattern"]
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

            for agent_id in entry["selected"]:
                agent_counts[agent_id] = agent_counts.get(agent_id, 0) + 1

        return {
            "total_routings": len(self._routing_history),
            "pattern_distribution": pattern_counts,
            "agent_usage": agent_counts,
            "active_sessions": len([s for s in self._sessions.values() if s.status == "active"]),
            "agent_availability": {
                aid: agent.is_available
                for aid, agent in self._agents.items()
            }
        }


# Singleton instance for convenience
_router_instance: Optional[AgentRouter] = None


def get_agent_router() -> AgentRouter:
    """Get or create the singleton AgentRouter instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = AgentRouter()
    return _router_instance
