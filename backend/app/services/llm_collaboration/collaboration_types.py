"""
LLM Agent Collaboration Types - B12 (Fase 24)

Defines collaboration patterns for agent-agent interaction.
Complements existing services:
- ActivePartnerService: Human-AI collaboration
- LLMCouncilService: Multi-model consensus
- TaskchainService: Sequential task execution

This module adds AGENT-AGENT collaboration patterns.

Version: 1.0.0
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from uuid import UUID, uuid4


class CollaborationPattern(str, Enum):
    """
    Patterns for multi-agent collaboration.

    Based on distributed systems and multi-agent research:
    - PIPELINE: Sequential processing (A → B → C)
    - PARALLEL: Concurrent processing with merge
    - CONSENSUS: Multiple agents vote/agree (like LLMCouncil)
    - SPECIALIST: Route to domain expert
    - ENSEMBLE: Combine multiple approaches
    - SUPERVISOR: One agent coordinates others
    - SWARM: Self-organizing agents
    """
    PIPELINE = "pipeline"           # Sequential: output of A → input of B
    PARALLEL = "parallel"           # Concurrent: same input, merge outputs
    CONSENSUS = "consensus"         # Voting/agreement pattern
    SPECIALIST = "specialist"       # Route to domain expert
    ENSEMBLE = "ensemble"           # Weighted combination of results
    SUPERVISOR = "supervisor"       # Coordinator pattern
    SWARM = "swarm"                 # Self-organizing pattern


class AgentCapabilityType(str, Enum):
    """
    Standardized agent capabilities for routing.

    Maps to existing agents:
    - CODE_ANALYSIS: Quinn, Felix, GhostCrew
    - CODE_GENERATION: KaibanJS agents, Codellama
    - SECURITY: GhostCrew, security scanners
    - DOCUMENTATION: Tech writers
    - TESTING: Test generators
    - PLANNING: Product/project agents
    - REVIEW: LLMCouncil, code review agents
    """
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    CODE_REFACTORING = "code_refactoring"
    SECURITY_AUDIT = "security_audit"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    PLANNING = "planning"
    ARCHITECTURE = "architecture"
    CODE_REVIEW = "code_review"
    DATA_ANALYSIS = "data_analysis"
    MIGRATION = "migration"
    DEBUGGING = "debugging"


class AgentStatus(str, Enum):
    """Current status of an agent."""
    AVAILABLE = "available"
    BUSY = "busy"
    PAUSED = "paused"
    ERROR = "error"
    OFFLINE = "offline"


class TaskPriority(str, Enum):
    """Priority levels for routed tasks."""
    CRITICAL = "critical"   # Immediate, blocking
    HIGH = "high"           # Next in queue
    MEDIUM = "medium"       # Normal processing
    LOW = "low"             # Background/batch


class AggregationStrategy(str, Enum):
    """
    Strategies for combining multi-agent results.

    - FIRST: Take first successful result
    - BEST: Select best by score/confidence
    - MERGE: Combine all results
    - VOTE: Majority voting
    - WEIGHTED: Weighted by agent reliability
    - CONSENSUS: Require agreement threshold
    """
    FIRST = "first"             # First successful result
    BEST = "best"               # Highest score/confidence
    MERGE = "merge"             # Combine all results
    VOTE = "vote"               # Majority voting
    WEIGHTED = "weighted"       # Weight by agent reliability
    CONSENSUS = "consensus"     # Require agreement threshold


@dataclass
class AgentProfile:
    """
    Profile of an agent for routing decisions.

    Attributes:
        agent_id: Unique agent identifier
        name: Human-readable name
        capabilities: Set of capabilities this agent provides
        reliability: Success rate (0.0 - 1.0)
        avg_latency_ms: Average response time
        max_concurrent: Max concurrent tasks
        current_load: Current task count
        specializations: Domain specializations (e.g., "python", "security")
        status: Current availability status
        metadata: Additional agent metadata
    """
    agent_id: str
    name: str
    capabilities: Set[AgentCapabilityType]
    reliability: float = 0.95
    avg_latency_ms: int = 5000
    max_concurrent: int = 5
    current_load: int = 0
    specializations: List[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.AVAILABLE
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_available(self) -> bool:
        """Check if agent can accept new tasks."""
        return (
            self.status == AgentStatus.AVAILABLE and
            self.current_load < self.max_concurrent
        )

    @property
    def load_factor(self) -> float:
        """Current load as percentage of capacity."""
        if self.max_concurrent == 0:
            return 1.0
        return self.current_load / self.max_concurrent

    def has_capability(self, capability: AgentCapabilityType) -> bool:
        """Check if agent has a specific capability."""
        return capability in self.capabilities

    def matches_specialization(self, required: List[str]) -> float:
        """
        Calculate specialization match score (0.0 - 1.0).

        Higher score = better match for the required specializations.
        """
        if not required:
            return 1.0
        if not self.specializations:
            return 0.5  # Neutral if no specializations

        matches = sum(1 for r in required if r.lower() in [s.lower() for s in self.specializations])
        return matches / len(required)


@dataclass
class CollaborationTask:
    """
    A task to be processed by collaborating agents.

    Attributes:
        task_id: Unique task identifier
        task_type: Type of task (maps to capability)
        payload: Task input data
        required_capabilities: Capabilities needed
        preferred_agents: Preferred agent IDs (optional)
        priority: Task priority
        timeout_ms: Max execution time
        context: Shared context from other agents
        metadata: Additional task metadata
    """
    task_id: UUID = field(default_factory=uuid4)
    task_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    required_capabilities: Set[AgentCapabilityType] = field(default_factory=set)
    preferred_agents: List[str] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.MEDIUM
    timeout_ms: int = 30000
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": str(self.task_id),
            "task_type": self.task_type,
            "payload": self.payload,
            "required_capabilities": [c.value for c in self.required_capabilities],
            "preferred_agents": self.preferred_agents,
            "priority": self.priority.value,
            "timeout_ms": self.timeout_ms,
            "context": self.context,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class AgentResult:
    """
    Result from a single agent execution.

    Attributes:
        agent_id: Which agent produced this result
        task_id: Which task this is for
        success: Whether execution succeeded
        output: Result data
        confidence: Agent's confidence in result (0.0 - 1.0)
        execution_time_ms: How long it took
        error: Error message if failed
        metadata: Additional result metadata
    """
    agent_id: str
    task_id: UUID
    success: bool
    output: Any = None
    confidence: float = 1.0
    execution_time_ms: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "agent_id": self.agent_id,
            "task_id": str(self.task_id),
            "success": self.success,
            "output": self.output,
            "confidence": self.confidence,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class CollaborationSession:
    """
    A collaboration session tracking multiple agents working together.

    Attributes:
        session_id: Unique session identifier
        pattern: Collaboration pattern being used
        participating_agents: Agents involved
        tasks: Tasks in this session
        results: Results collected
        shared_context: Context shared between agents
        status: Current session status
        started_at: When session started
        completed_at: When session ended
    """
    session_id: UUID = field(default_factory=uuid4)
    pattern: CollaborationPattern = CollaborationPattern.PARALLEL
    participating_agents: List[str] = field(default_factory=list)
    tasks: List[CollaborationTask] = field(default_factory=list)
    results: List[AgentResult] = field(default_factory=list)
    shared_context: Dict[str, Any] = field(default_factory=dict)
    status: str = "active"
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_result(self, result: AgentResult) -> None:
        """Add a result from an agent."""
        self.results.append(result)

    def get_successful_results(self) -> List[AgentResult]:
        """Get all successful results."""
        return [r for r in self.results if r.success]

    def get_failed_results(self) -> List[AgentResult]:
        """Get all failed results."""
        return [r for r in self.results if not r.success]

    def complete(self) -> None:
        """Mark session as complete."""
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": str(self.session_id),
            "pattern": self.pattern.value,
            "participating_agents": self.participating_agents,
            "tasks": [t.to_dict() for t in self.tasks],
            "results": [r.to_dict() for r in self.results],
            "shared_context": self.shared_context,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata
        }


@dataclass
class RoutingDecision:
    """
    Decision from the agent router.

    Attributes:
        task: The task being routed
        selected_agents: Agents selected for this task
        pattern: Collaboration pattern to use
        reasoning: Why these agents were selected
        fallback_agents: Alternative agents if primary fails
    """
    task: CollaborationTask
    selected_agents: List[str]
    pattern: CollaborationPattern
    reasoning: str
    fallback_agents: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AggregatedResult:
    """
    Combined result from multiple agents.

    Attributes:
        session_id: Which session this is from
        strategy: Aggregation strategy used
        final_output: Combined/selected output
        confidence: Overall confidence
        contributing_agents: Agents that contributed
        individual_results: All individual results
        aggregation_metadata: How aggregation was performed
    """
    session_id: UUID
    strategy: AggregationStrategy
    final_output: Any
    confidence: float
    contributing_agents: List[str]
    individual_results: List[AgentResult]
    aggregation_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": str(self.session_id),
            "strategy": self.strategy.value,
            "final_output": self.final_output,
            "confidence": self.confidence,
            "contributing_agents": self.contributing_agents,
            "individual_results": [r.to_dict() for r in self.individual_results],
            "aggregation_metadata": self.aggregation_metadata,
            "created_at": self.created_at.isoformat()
        }


# Pre-configured collaboration patterns for common scenarios
PREDEFINED_PATTERNS: Dict[str, Dict[str, Any]] = {
    "security_audit": {
        "pattern": CollaborationPattern.ENSEMBLE,
        "required_capabilities": {AgentCapabilityType.SECURITY_AUDIT, AgentCapabilityType.CODE_ANALYSIS},
        "aggregation_strategy": AggregationStrategy.MERGE,
        "description": "Multiple security agents analyze code, results merged"
    },
    "code_review": {
        "pattern": CollaborationPattern.CONSENSUS,
        "required_capabilities": {AgentCapabilityType.CODE_REVIEW},
        "aggregation_strategy": AggregationStrategy.CONSENSUS,
        "description": "Multiple reviewers must agree on findings"
    },
    "migration_planning": {
        "pattern": CollaborationPattern.PIPELINE,
        "required_capabilities": {
            AgentCapabilityType.CODE_ANALYSIS,
            AgentCapabilityType.ARCHITECTURE,
            AgentCapabilityType.MIGRATION
        },
        "aggregation_strategy": AggregationStrategy.MERGE,
        "description": "Sequential: analyze → design → plan migration"
    },
    "rapid_prototyping": {
        "pattern": CollaborationPattern.PARALLEL,
        "required_capabilities": {AgentCapabilityType.CODE_GENERATION},
        "aggregation_strategy": AggregationStrategy.BEST,
        "description": "Multiple agents generate, pick best solution"
    },
    "quality_gate": {
        "pattern": CollaborationPattern.SUPERVISOR,
        "required_capabilities": {
            AgentCapabilityType.CODE_REVIEW,
            AgentCapabilityType.TESTING,
            AgentCapabilityType.SECURITY_AUDIT
        },
        "aggregation_strategy": AggregationStrategy.CONSENSUS,
        "description": "Supervisor coordinates review, test, security checks"
    }
}
