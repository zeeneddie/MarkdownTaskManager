"""
Harness Protocol Definitions - Abstract Interfaces for Pluggable Modules

These protocols define the contracts that any adapter must implement.
This enables plug-and-play mounting of:
- Native MarQed implementations
- LangChain adapters
- Mem0 adapters
- MCP (Model Context Protocol) adapters
- Custom enterprise implementations
"""

from typing import Protocol, Dict, Any, List, Optional, Callable, Awaitable, runtime_checkable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


# =============================================================================
# MODULE 1: AGENT CONSTRAINTS
# =============================================================================

class ConstraintSeverity(str, Enum):
    """Severity levels for constraint violations."""
    BLOCK = "block"        # Prevent action completely
    WARN = "warn"          # Log warning, allow action
    AUDIT = "audit"        # Log for review, allow action
    APPROVE = "approve"    # Requires human approval


@dataclass
class ConstraintResult:
    """Result of a constraint check."""
    allowed: bool
    severity: ConstraintSeverity
    reason: Optional[str] = None
    requires_approval: bool = False
    audit_id: Optional[str] = None
    matched_rules: List[str] = field(default_factory=list)


@runtime_checkable
class ConstraintManagerProtocol(Protocol):
    """
    Abstract interface for Agent Constraint Management.

    Implementations can be:
    - MarQed native (YAML-driven)
    - LangChain GuardrailsAdapter
    - NeMo Guardrails Adapter
    - Custom enterprise rules engine
    """

    async def check_action(
        self,
        agent_id: str,
        action_type: str,
        action_params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ConstraintResult:
        """
        Check if an action is allowed for an agent.

        Args:
            agent_id: The agent attempting the action
            action_type: Type of action (e.g., "file_write", "code_execute")
            action_params: Parameters of the action
            context: Optional context for conditional rules

        Returns:
            ConstraintResult with allowed status and details
        """
        ...

    async def get_constraints(
        self,
        agent_id: str
    ) -> List[Dict[str, Any]]:
        """Get all constraints configured for an agent."""
        ...

    async def add_constraint(
        self,
        agent_id: str,
        constraint: Dict[str, Any]
    ) -> bool:
        """Add a new constraint for an agent."""
        ...

    async def remove_constraint(
        self,
        agent_id: str,
        constraint_id: str
    ) -> bool:
        """Remove a constraint by ID."""
        ...

    async def validate_output(
        self,
        agent_id: str,
        output: str,
        output_type: str
    ) -> ConstraintResult:
        """
        Validate agent output against output constraints.

        Checks for:
        - Forbidden patterns (SQL injection, shell commands)
        - Length limits
        - Format requirements
        """
        ...

    def health_check(self) -> bool:
        """Check if the constraint manager is operational."""
        ...


# =============================================================================
# MODULE 2: STRUCTURED CONTEXT MANAGER
# =============================================================================

@dataclass
class ContextLayer:
    """A layer in the context stack."""
    name: str
    content: Dict[str, Any]
    token_count: int
    priority: int  # Higher priority = retained during truncation
    ttl_seconds: Optional[int] = None  # None = permanent
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = field(default_factory=list)


@dataclass
class ResolvedContext:
    """Resolved context ready for agent consumption."""
    system: str          # Rendered system prompt (role, rules, ethics)
    task: str            # Current task context
    memory: str          # Compressed history
    total_tokens: int
    layers_used: List[str]
    truncated: bool
    context_hash: str    # For versioning


@runtime_checkable
class ContextManagerProtocol(Protocol):
    """
    Abstract interface for Structured Context Management.

    Manages 3-layer context:
    1. System (static): Role, rules, ethics - always included
    2. Task (dynamic): Current task - TTL-based
    3. Memory (compressed): History - truncatable

    Implementations can be:
    - MarQed native (extends ClaudeMemService)
    - LangChain Memory Adapter
    - Mem0 Adapter
    - MemGPT Adapter
    """

    async def set_system_context(
        self,
        agent_id: str,
        context: Dict[str, Any]
    ) -> None:
        """
        Set static system context (role, rules, ethics).

        This context is:
        - Always included in resolved context
        - Never truncated
        - Persisted across sessions
        """
        ...

    async def get_system_context(
        self,
        agent_id: str
    ) -> Optional[ContextLayer]:
        """Get the system context for an agent."""
        ...

    async def set_task_context(
        self,
        session_id: str,
        context: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Set dynamic task context.

        Args:
            session_id: Current session
            context: Task-specific context (document, requirements, etc.)
            ttl_seconds: Time-to-live, None for session lifetime
        """
        ...

    async def add_memory(
        self,
        session_id: str,
        observation: str,
        tags: Optional[List[str]] = None,
        priority: int = 5
    ) -> str:
        """
        Add observation to memory layer.

        Returns:
            Memory entry ID
        """
        ...

    async def resolve_context(
        self,
        agent_id: str,
        session_id: str,
        token_budget: int = 4000
    ) -> ResolvedContext:
        """
        Resolve all context layers to agent-ready format.

        Resolution order (priority):
        1. System context (always first, never truncated)
        2. Task context (current task)
        3. Memory (compressed history, truncatable)

        Fits within token budget via prioritized truncation.
        """
        ...

    async def compress_memory(
        self,
        session_id: str,
        compression_ratio: float = 0.1
    ) -> int:
        """
        Compress older memories using LLM summarization.

        Returns:
            Number of tokens saved
        """
        ...

    async def clear_task_context(
        self,
        session_id: str
    ) -> None:
        """Clear task context for a session."""
        ...

    def health_check(self) -> bool:
        """Check if the context manager is operational."""
        ...


# =============================================================================
# MODULE 3: TOOL PERMISSION REGISTRY
# =============================================================================

class ToolCategory(str, Enum):
    """Categories of tools for permission grouping."""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    CODE_EXECUTE = "code_execute"
    CODE_GENERATE = "code_generate"
    API_INTERNAL = "api_internal"
    API_EXTERNAL = "api_external"
    DATABASE_READ = "database_read"
    DATABASE_WRITE = "database_write"
    SECURITY = "security"
    SYSTEM = "system"


@dataclass
class ToolDefinition:
    """Definition of a tool available to agents."""
    name: str
    category: ToolCategory
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    handler: str  # Module path to handler function
    requires_approval: bool = False
    rate_limit: Optional[int] = None  # Calls per minute
    sandbox_required: bool = False
    timeout_seconds: int = 30
    enabled: bool = True


@dataclass
class ToolCallRequest:
    """Request to execute a tool."""
    tool_name: str
    agent_id: str
    session_id: str
    parameters: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


@dataclass
class ToolCallResult:
    """Result of a tool execution."""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: int = 0
    tokens_used: int = 0
    audit_id: Optional[str] = None
    sandbox_used: bool = False


@runtime_checkable
class ToolRegistryProtocol(Protocol):
    """
    Abstract interface for Tool Permission Registry.

    Manages:
    - Available tools and their definitions
    - Agent-specific permissions
    - Rate limiting
    - Sandbox execution

    Implementations can be:
    - MarQed native (YAML-driven)
    - LangChain Tools Adapter
    - OpenAI Function Calling Adapter
    - MCP (Model Context Protocol) Adapter
    """

    def register_tool(
        self,
        tool: ToolDefinition
    ) -> bool:
        """Register a new tool in the registry."""
        ...

    def unregister_tool(
        self,
        tool_name: str
    ) -> bool:
        """Remove a tool from the registry."""
        ...

    def get_tool(
        self,
        tool_name: str
    ) -> Optional[ToolDefinition]:
        """Get a tool definition by name."""
        ...

    def get_tools_for_agent(
        self,
        agent_id: str
    ) -> List[ToolDefinition]:
        """Get all tools available to an agent (based on permissions)."""
        ...

    async def can_use_tool(
        self,
        agent_id: str,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if an agent can use a specific tool.

        Checks:
        - Permission configuration
        - Rate limits
        - Parameter constraints
        """
        ...

    async def execute_tool(
        self,
        request: ToolCallRequest
    ) -> ToolCallResult:
        """
        Execute a tool with full permission pipeline.

        Pipeline:
        1. Check constraint manager
        2. Check rate limits
        3. Execute in sandbox if required
        4. Log to observability
        """
        ...

    def get_tool_schema(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Generate OpenAI-compatible function schema
        for all permitted tools of an agent.

        Returns:
            JSON Schema for function calling
        """
        ...

    def set_agent_permissions(
        self,
        agent_id: str,
        allowed: List[str],
        denied: List[str],
        requires_approval: Optional[List[str]] = None
    ) -> None:
        """Configure tool permissions for an agent."""
        ...

    def health_check(self) -> bool:
        """Check if the tool registry is operational."""
        ...


# =============================================================================
# MODULE 4: CONTEXT VERSION TRACKER
# =============================================================================

@dataclass
class ContextSnapshot:
    """Immutable snapshot of context at a point in time."""
    version_id: str           # Unique identifier (UUID)
    content_hash: str         # SHA256 of content for deduplication
    agent_id: str
    session_id: str
    timestamp: datetime
    layers: Dict[str, Any]    # {system, task, memory}
    token_count: int
    parent_version: Optional[str] = None  # For history chain
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextDiff:
    """Difference between two context versions."""
    from_version: str
    to_version: str
    added: Dict[str, Any]
    removed: Dict[str, Any]
    modified: Dict[str, Any]
    token_delta: int


@runtime_checkable
class ContextVersionTrackerProtocol(Protocol):
    """
    Abstract interface for Context Version Tracking.

    Provides:
    - Immutable snapshots of context state
    - Content-addressed deduplication
    - History chain for audit
    - Links to observability actions

    Implementations can be:
    - MarQed native (PostgreSQL-based)
    - Git-based versioning
    - IPFS content-addressed storage
    - MLflow Tracking Adapter
    """

    async def snapshot(
        self,
        agent_id: str,
        session_id: str,
        context: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextSnapshot:
        """
        Create an immutable snapshot of current context.

        Features:
        - Content-addressed hashing for deduplication
        - Parent linking for history chain
        - Metadata attachment for audit
        """
        ...

    async def get_snapshot(
        self,
        version_id: str
    ) -> Optional[ContextSnapshot]:
        """Get a specific snapshot by version ID."""
        ...

    async def get_by_hash(
        self,
        content_hash: str
    ) -> Optional[ContextSnapshot]:
        """Get snapshot by content hash (deduplication lookup)."""
        ...

    async def get_history(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[ContextSnapshot]:
        """Get snapshot history for a session, newest first."""
        ...

    async def get_agent_history(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[ContextSnapshot]:
        """Get snapshot history for an agent across sessions."""
        ...

    async def diff(
        self,
        from_version: str,
        to_version: str
    ) -> ContextDiff:
        """Calculate difference between two versions."""
        ...

    async def restore(
        self,
        version_id: str
    ) -> Dict[str, Any]:
        """Restore context to a specific version."""
        ...

    async def link_to_action(
        self,
        version_id: str,
        action_id: str
    ) -> None:
        """
        Link context snapshot to an agent action.

        Enables:
        - Audit: "What context did the agent have?"
        - Reproducibility: "Replay with same context"
        - Debugging: "Why did agent do X?"
        """
        ...

    async def get_actions_for_snapshot(
        self,
        version_id: str
    ) -> List[str]:
        """Get all action IDs linked to a snapshot."""
        ...

    async def cleanup_old_snapshots(
        self,
        retention_days: int = 90
    ) -> int:
        """
        Remove snapshots older than retention period.

        Returns:
            Number of snapshots removed
        """
        ...

    def health_check(self) -> bool:
        """Check if the version tracker is operational."""
        ...


# =============================================================================
# BASE ADAPTER CLASS
# =============================================================================

class BaseAdapter:
    """
    Base class for all harness adapters.

    Provides common functionality for:
    - Configuration loading
    - Health checking
    - Cleanup on unmount
    """

    def __init__(self, **config):
        """Initialize with configuration."""
        self.config = config
        self._initialized = False

    def health_check(self) -> bool:
        """Default health check - override for specific checks."""
        return self._initialized

    def cleanup(self) -> None:
        """Cleanup resources on unmount. Override as needed."""
        self._initialized = False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(initialized={self._initialized})"
