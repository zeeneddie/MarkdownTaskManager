"""
MarQed Native Context Manager

3-layer structured context management:
1. System (static): Role, rules, ethics - always included
2. Task (dynamic): Current task context - TTL-based
3. Memory (compressed): History - truncatable

Integrates with existing ClaudeMemService for persistence.
"""

import uuid
import hashlib
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from app.harness.core.protocols import (
    ContextManagerProtocol,
    ContextLayer,
    ResolvedContext,
    BaseAdapter,
)

logger = logging.getLogger(__name__)


# Default system contexts for agents
DEFAULT_SYSTEM_CONTEXTS = {
    "felix": {
        "role": "Feature Architect",
        "capabilities": ["System design", "API design", "Work breakdown", "Architecture decisions"],
        "rules": [
            "Always consider scalability and maintainability",
            "Follow SOLID principles",
            "Document design decisions",
            "Consider security implications",
        ],
        "ethics": [
            "Never introduce security vulnerabilities intentionally",
            "Respect data privacy in designs",
            "Consider accessibility in all designs",
        ],
        "llm": "qwen2.5-coder:7b",
    },
    "marcus": {
        "role": "Maintenance Specialist",
        "capabilities": ["Refactoring", "Dependency updates", "Technical debt management"],
        "rules": [
            "Preserve existing functionality during refactoring",
            "Test changes thoroughly",
            "Document breaking changes",
            "Follow boy scout rule: leave code better than found",
        ],
        "ethics": [
            "Never remove safety checks without explicit approval",
            "Maintain backwards compatibility when possible",
        ],
        "llm": "qwen2.5-coder:7b",
    },
    "quinn": {
        "role": "Quality Inspector",
        "capabilities": ["Code review", "Security audits", "Quality gates"],
        "rules": [
            "Be thorough but constructive in reviews",
            "Prioritize security issues",
            "Check for test coverage",
            "Verify documentation completeness",
        ],
        "ethics": [
            "Report all security issues immediately",
            "Never approve code you don't understand",
        ],
        "llm": "deepseek-r1",
    },
    "betty": {
        "role": "Bug Hunter",
        "capabilities": ["Debugging", "Root cause analysis", "Bug reproduction"],
        "rules": [
            "Always reproduce bugs before fixing",
            "Document root cause",
            "Add regression tests for fixed bugs",
            "Check for similar bugs elsewhere",
        ],
        "ethics": [
            "Never hide bugs or their severity",
            "Report security bugs through proper channels",
        ],
        "llm": "codellama",
    },
    "eliza": {
        "role": "Estimation Engine",
        "capabilities": ["Function points", "Story points", "ML-based estimation"],
        "rules": [
            "Use IFPUG standard for function points",
            "Consider complexity factors",
            "Provide confidence intervals",
            "Document estimation assumptions",
        ],
        "ethics": [
            "Never inflate or deflate estimates for political reasons",
            "Be honest about uncertainty",
        ],
        "llm": "deepseek-r1",
    },
    "diana": {
        "role": "Documentation Writer",
        "capabilities": ["API documentation", "Architecture docs", "User guides"],
        "rules": [
            "Write for the target audience",
            "Keep documentation up to date with code",
            "Include examples",
            "Use consistent terminology",
        ],
        "ethics": [
            "Never document features that don't exist",
            "Credit sources appropriately",
        ],
        "llm": "mistral",
    },
    "tessa": {
        "role": "Test Engineer",
        "capabilities": ["Unit tests", "E2E tests", "Test strategy"],
        "rules": [
            "Aim for meaningful coverage, not just numbers",
            "Test edge cases and error paths",
            "Write maintainable tests",
            "Use appropriate test levels (unit/integration/e2e)",
        ],
        "ethics": [
            "Never skip tests to meet deadlines",
            "Report flaky tests immediately",
        ],
        "llm": "qwen2.5-coder:7b",
    },
    "miguel": {
        "role": "Migration Architect",
        "capabilities": ["Tech stack migrations", "Data migrations", "Legacy analysis"],
        "rules": [
            "Plan migrations incrementally",
            "Maintain data integrity",
            "Create rollback plans",
            "Document migration paths",
        ],
        "ethics": [
            "Never migrate without data backups",
            "Be honest about migration risks",
        ],
        "llm": "qwen2.5-coder:7b",
    },
    "peter": {
        "role": "Product Owner",
        "capabilities": ["User stories", "Business analysis", "Prioritization"],
        "rules": [
            "Write INVEST-compliant user stories",
            "Consider business value",
            "Maintain clear acceptance criteria",
            "Balance stakeholder needs",
        ],
        "ethics": [
            "Represent user needs honestly",
            "Be transparent about priorities and trade-offs",
        ],
        "llm": "deepseek-r1",
    },
    "paul": {
        "role": "Project Lead",
        "capabilities": ["Resource allocation", "Sprint planning", "Risk management"],
        "rules": [
            "Balance team capacity with commitments",
            "Track and communicate risks",
            "Facilitate rather than dictate",
            "Maintain sustainable pace",
        ],
        "ethics": [
            "Never sacrifice team wellbeing for deadlines",
            "Be transparent about project status",
        ],
        "llm": "qwen2.5:7b",
    },
}


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: str
    content: str
    tags: List[str]
    priority: int
    token_count: int
    created_at: datetime
    compressed: bool = False


class MarQedContextManager(BaseAdapter, ContextManagerProtocol):
    """
    MarQed native implementation of ContextManagerProtocol.

    Features:
    - 3-layer context (system/task/memory)
    - Token budget management
    - Priority-based truncation
    - Memory compression via summarization
    - Session isolation

    Usage:
        manager = MarQedContextManager()

        # Set static system context
        await manager.set_system_context("felix", {
            "role": "Feature Architect",
            "rules": ["Follow SOLID principles"]
        })

        # Add task context
        await manager.set_task_context("session-123", {
            "task": "Design user authentication",
            "requirements": ["OAuth2", "MFA support"]
        })

        # Add memory
        await manager.add_memory("session-123", "User prefers JWT tokens")

        # Resolve for agent
        context = await manager.resolve_context("felix", "session-123", token_budget=4000)
    """

    def __init__(
        self,
        default_token_budget: int = 4000,
        use_default_contexts: bool = True,
        **kwargs
    ):
        """
        Initialize context manager.

        Args:
            default_token_budget: Default token budget for context resolution
            use_default_contexts: Load default system contexts for known agents
        """
        super().__init__(**kwargs)

        self._system_contexts: Dict[str, ContextLayer] = {}
        self._task_contexts: Dict[str, ContextLayer] = {}  # session_id -> context
        self._memories: Dict[str, List[MemoryEntry]] = {}  # session_id -> memories
        self._default_token_budget = default_token_budget

        if use_default_contexts:
            self._load_default_contexts()

        self._initialized = True
        logger.info(f"MarQedContextManager initialized with {len(self._system_contexts)} agent contexts")

    def _load_default_contexts(self) -> None:
        """Load default system contexts for known agents."""
        for agent_id, context_data in DEFAULT_SYSTEM_CONTEXTS.items():
            self._system_contexts[agent_id] = ContextLayer(
                name=f"system_{agent_id}",
                content=context_data,
                token_count=self._estimate_tokens(str(context_data)),
                priority=100,  # Highest priority - never truncated
                ttl_seconds=None,  # Permanent
                tags=["system", "static"],
            )

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: 4 chars per token)."""
        return len(text) // 4

    def _render_context_layer(self, layer: ContextLayer) -> str:
        """Render a context layer to string."""
        content = layer.content
        if isinstance(content, dict):
            lines = []
            for key, value in content.items():
                if isinstance(value, list):
                    lines.append(f"{key}:")
                    for item in value:
                        lines.append(f"  - {item}")
                else:
                    lines.append(f"{key}: {value}")
            return "\n".join(lines)
        return str(content)

    async def set_system_context(
        self,
        agent_id: str,
        context: Dict[str, Any]
    ) -> None:
        """Set static system context for an agent."""
        content_str = str(context)
        self._system_contexts[agent_id] = ContextLayer(
            name=f"system_{agent_id}",
            content=context,
            token_count=self._estimate_tokens(content_str),
            priority=100,
            ttl_seconds=None,
            tags=["system", "static"],
        )
        logger.info(f"Set system context for {agent_id}")

    async def get_system_context(self, agent_id: str) -> Optional[ContextLayer]:
        """Get system context for an agent."""
        return self._system_contexts.get(agent_id)

    async def set_task_context(
        self,
        session_id: str,
        context: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Set dynamic task context for a session."""
        content_str = str(context)
        self._task_contexts[session_id] = ContextLayer(
            name=f"task_{session_id}",
            content=context,
            token_count=self._estimate_tokens(content_str),
            priority=80,  # High priority, but can be truncated if needed
            ttl_seconds=ttl_seconds,
            tags=["task", "dynamic"],
        )
        logger.debug(f"Set task context for session {session_id}")

    async def add_memory(
        self,
        session_id: str,
        observation: str,
        tags: Optional[List[str]] = None,
        priority: int = 5
    ) -> str:
        """Add observation to memory layer."""
        memory_id = str(uuid.uuid4())[:8]

        if session_id not in self._memories:
            self._memories[session_id] = []

        entry = MemoryEntry(
            id=memory_id,
            content=observation,
            tags=tags or [],
            priority=priority,
            token_count=self._estimate_tokens(observation),
            created_at=datetime.utcnow(),
        )
        self._memories[session_id].append(entry)

        logger.debug(f"Added memory {memory_id} to session {session_id}")
        return memory_id

    async def resolve_context(
        self,
        agent_id: str,
        session_id: str,
        token_budget: int = 4000
    ) -> ResolvedContext:
        """
        Resolve all context layers to agent-ready format.

        Priority order:
        1. System context (always included, never truncated)
        2. Task context (current task)
        3. Memory (compressed history, truncatable)
        """
        layers_used: List[str] = []
        truncated = False
        remaining_budget = token_budget

        # 1. System context (always included)
        system_layer = self._system_contexts.get(agent_id)
        if system_layer:
            system_str = self._render_context_layer(system_layer)
            remaining_budget -= system_layer.token_count
            layers_used.append("system")
        else:
            system_str = f"Agent: {agent_id}"
            remaining_budget -= self._estimate_tokens(system_str)
            layers_used.append("system_default")

        # 2. Task context
        task_layer = self._task_contexts.get(session_id)
        task_str = ""
        if task_layer:
            # Check TTL
            if task_layer.ttl_seconds:
                age = (datetime.utcnow() - task_layer.created_at).total_seconds()
                if age > task_layer.ttl_seconds:
                    # Expired, clear it
                    del self._task_contexts[session_id]
                    task_layer = None

        if task_layer:
            task_str = self._render_context_layer(task_layer)
            if task_layer.token_count <= remaining_budget:
                remaining_budget -= task_layer.token_count
                layers_used.append("task")
            else:
                # Truncate task context
                truncated = True
                char_limit = remaining_budget * 4  # rough estimate
                task_str = task_str[:char_limit] + "... [truncated]"
                remaining_budget = 0
                layers_used.append("task_truncated")

        # 3. Memory (lowest priority, most truncatable)
        memory_str = ""
        memories = self._memories.get(session_id, [])
        if memories and remaining_budget > 100:
            # Sort by priority (highest first) and recency
            sorted_memories = sorted(
                memories,
                key=lambda m: (m.priority, m.created_at.timestamp()),
                reverse=True
            )

            memory_parts = []
            tokens_used = 0

            for mem in sorted_memories:
                if tokens_used + mem.token_count <= remaining_budget:
                    memory_parts.append(f"- {mem.content}")
                    tokens_used += mem.token_count
                else:
                    truncated = True
                    break

            if memory_parts:
                memory_str = "Memory:\n" + "\n".join(memory_parts)
                remaining_budget -= tokens_used
                layers_used.append(f"memory({len(memory_parts)} entries)")

        # Calculate context hash
        full_content = f"{system_str}\n\n{task_str}\n\n{memory_str}"
        context_hash = hashlib.sha256(full_content.encode()).hexdigest()[:16]

        return ResolvedContext(
            system=system_str,
            task=task_str,
            memory=memory_str,
            total_tokens=token_budget - remaining_budget,
            layers_used=layers_used,
            truncated=truncated,
            context_hash=context_hash,
        )

    async def compress_memory(
        self,
        session_id: str,
        compression_ratio: float = 0.1
    ) -> int:
        """
        Compress older memories.

        In a full implementation, this would use LLM summarization.
        For now, it removes low-priority and old memories.

        Returns:
            Number of tokens saved
        """
        if session_id not in self._memories:
            return 0

        memories = self._memories[session_id]
        if len(memories) < 10:
            return 0  # Not enough to compress

        original_tokens = sum(m.token_count for m in memories)

        # Keep top priority and recent memories
        cutoff = datetime.utcnow() - timedelta(hours=1)
        keep_count = max(5, int(len(memories) * compression_ratio))

        # Sort by priority and recency
        sorted_memories = sorted(
            memories,
            key=lambda m: (m.priority, m.created_at.timestamp()),
            reverse=True
        )

        # Keep top entries
        self._memories[session_id] = sorted_memories[:keep_count]

        new_tokens = sum(m.token_count for m in self._memories[session_id])
        tokens_saved = original_tokens - new_tokens

        logger.info(f"Compressed memory for {session_id}: saved {tokens_saved} tokens")
        return tokens_saved

    async def clear_task_context(self, session_id: str) -> None:
        """Clear task context for a session."""
        if session_id in self._task_contexts:
            del self._task_contexts[session_id]
            logger.debug(f"Cleared task context for {session_id}")

    async def clear_session(self, session_id: str) -> None:
        """Clear all context for a session."""
        if session_id in self._task_contexts:
            del self._task_contexts[session_id]
        if session_id in self._memories:
            del self._memories[session_id]
        logger.info(f"Cleared all context for session {session_id}")

    def health_check(self) -> bool:
        """Check if context manager is operational."""
        return self._initialized

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about context usage."""
        return {
            "system_contexts": len(self._system_contexts),
            "active_sessions": len(self._task_contexts),
            "total_memories": sum(len(m) for m in self._memories.values()),
            "total_memory_tokens": sum(
                sum(e.token_count for e in memories)
                for memories in self._memories.values()
            ),
            "initialized": self._initialized,
        }

    def get_agent_context_summary(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of agent's system context."""
        layer = self._system_contexts.get(agent_id)
        if not layer:
            return None

        return {
            "agent_id": agent_id,
            "role": layer.content.get("role", "Unknown"),
            "capabilities": layer.content.get("capabilities", []),
            "token_count": layer.token_count,
            "llm": layer.content.get("llm", "unknown"),
        }

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents with system contexts."""
        return [
            self.get_agent_context_summary(agent_id)
            for agent_id in self._system_contexts.keys()
        ]
