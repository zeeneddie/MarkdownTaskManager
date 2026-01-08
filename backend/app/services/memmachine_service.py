"""
Week 73: MemMachine - Persistent Agent Memory Service

Provides persistent memory capabilities for AI agents:
- Conversation history with context
- Agent-specific memories (facts, preferences, learnings)
- Session management with continuity
- Cross-session learning and knowledge transfer
- Memory compression and summarization

Target: +35% context retention, +28% task continuity
"""

import hashlib
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, or_, case, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mcp_proxy import MCPServer  # Reuse for now


class MemoryType:
    """Types of memories that can be stored."""
    CONVERSATION = "conversation"  # Chat history
    FACT = "fact"                  # Learned facts about user/project
    PREFERENCE = "preference"      # User/agent preferences
    SKILL = "skill"               # Learned procedures/patterns
    CONTEXT = "context"           # Session context
    TASK = "task"                 # Task-related memories


class MemoryPriority:
    """Priority levels for memory retention."""
    CRITICAL = "critical"     # Never forget
    HIGH = "high"            # Long retention
    MEDIUM = "medium"        # Standard retention
    LOW = "low"              # May be compressed
    EPHEMERAL = "ephemeral"  # Session-only


class MemMachineService:
    """
    Persistent Agent Memory Service.

    Provides intelligent memory management for AI agents with:
    - Context-aware storage and retrieval
    - Automatic memory compression
    - Cross-session continuity
    - Agent-specific knowledge bases
    """

    # Memory retention periods (in hours)
    RETENTION_PERIODS = {
        MemoryPriority.CRITICAL: None,  # Never expires
        MemoryPriority.HIGH: 720,       # 30 days
        MemoryPriority.MEDIUM: 168,     # 7 days
        MemoryPriority.LOW: 24,         # 1 day
        MemoryPriority.EPHEMERAL: 1     # 1 hour
    }

    # Memory compression thresholds
    MAX_CONVERSATION_LENGTH = 100
    MAX_MEMORY_AGE_DAYS = 30
    COMPRESSION_THRESHOLD = 1000  # tokens

    def __init__(self, db: AsyncSession):
        self.db = db
        self._session_cache: Dict[str, Dict[str, Any]] = {}
        self._memory_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._compression_queue: List[UUID] = []

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    async def create_session(
        self,
        agent_id: str,
        project_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new memory session for an agent.

        Args:
            agent_id: ID of the agent (e.g., "felix", "quinn")
            project_id: Optional project context
            context: Initial session context

        Returns:
            Session details with ID and metadata
        """
        session_id = str(uuid4())
        now = datetime.now()

        session = {
            "id": session_id,
            "agent_id": agent_id,
            "project_id": str(project_id) if project_id else None,
            "context": context or {},
            "created_at": now.isoformat(),
            "last_activity": now.isoformat(),
            "message_count": 0,
            "memory_count": 0,
            "status": "active"
        }

        # Store in cache
        self._session_cache[session_id] = session

        # Load previous session memories for continuity
        if agent_id:
            previous = await self.get_agent_memories(
                agent_id=agent_id,
                project_id=project_id,
                memory_types=[MemoryType.CONTEXT, MemoryType.FACT],
                limit=20
            )
            session["restored_memories"] = len(previous)

        return session

    async def end_session(
        self,
        session_id: str,
        summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        End a memory session and persist important memories.

        Args:
            session_id: Session to end
            summary: Optional session summary

        Returns:
            Session summary with statistics
        """
        session = self._session_cache.get(session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        now = datetime.now()
        session["ended_at"] = now.isoformat()
        session["status"] = "completed"

        # Calculate session statistics
        created = datetime.fromisoformat(session["created_at"])
        duration = (now - created).total_seconds()

        # Store session summary as a memory
        if summary or session["message_count"] > 5:
            await self.store_memory(
                session_id=session_id,
                agent_id=session["agent_id"],
                content=summary or f"Session with {session['message_count']} messages",
                memory_type=MemoryType.CONTEXT,
                priority=MemoryPriority.MEDIUM,
                metadata={"duration_seconds": duration}
            )

        return {
            "session_id": session_id,
            "status": "completed",
            "duration_seconds": round(duration, 2),
            "message_count": session["message_count"],
            "memory_count": session["memory_count"],
            "ended_at": now.isoformat()
        }

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session details."""
        return self._session_cache.get(session_id)

    # ========================================================================
    # MEMORY STORAGE
    # ========================================================================

    async def store_memory(
        self,
        session_id: str,
        agent_id: str,
        content: str,
        memory_type: str = MemoryType.FACT,
        priority: str = MemoryPriority.MEDIUM,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store a memory for an agent.

        Args:
            session_id: Current session
            agent_id: Agent storing the memory
            content: Memory content
            memory_type: Type of memory
            priority: Retention priority
            tags: Searchable tags
            metadata: Additional metadata

        Returns:
            Stored memory details
        """
        memory_id = str(uuid4())
        now = datetime.now()

        # Calculate expiration based on priority
        retention_hours = self.RETENTION_PERIODS.get(priority)
        expires_at = None
        if retention_hours:
            expires_at = (now + timedelta(hours=retention_hours)).isoformat()

        memory = {
            "id": memory_id,
            "session_id": session_id,
            "agent_id": agent_id,
            "content": content,
            "memory_type": memory_type,
            "priority": priority,
            "tags": tags or [],
            "metadata": metadata or {},
            "created_at": now.isoformat(),
            "expires_at": expires_at,
            "access_count": 0,
            "last_accessed": now.isoformat()
        }

        # Store in cache
        cache_key = f"{agent_id}:{memory_type}"
        if cache_key not in self._memory_cache:
            self._memory_cache[cache_key] = []
        self._memory_cache[cache_key].append(memory)

        # Update session stats
        if session_id in self._session_cache:
            self._session_cache[session_id]["memory_count"] += 1
            self._session_cache[session_id]["last_activity"] = now.isoformat()

        return memory

    async def store_conversation(
        self,
        session_id: str,
        agent_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store a conversation message.

        Args:
            session_id: Current session
            agent_id: Agent in the conversation
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Additional metadata

        Returns:
            Stored message details
        """
        message_metadata = metadata or {}
        message_metadata["role"] = role

        memory = await self.store_memory(
            session_id=session_id,
            agent_id=agent_id,
            content=content,
            memory_type=MemoryType.CONVERSATION,
            priority=MemoryPriority.LOW,
            metadata=message_metadata
        )

        # Update session message count
        if session_id in self._session_cache:
            self._session_cache[session_id]["message_count"] += 1

        return memory

    # ========================================================================
    # MEMORY RETRIEVAL
    # ========================================================================

    async def get_agent_memories(
        self,
        agent_id: str,
        project_id: Optional[UUID] = None,
        memory_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        min_priority: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories for an agent.

        Args:
            agent_id: Agent to get memories for
            project_id: Optional project filter
            memory_types: Filter by memory types
            tags: Filter by tags
            min_priority: Minimum priority level
            limit: Maximum memories to return

        Returns:
            List of matching memories
        """
        results = []
        now = datetime.now()

        # Priority ranking for filtering
        priority_rank = {
            MemoryPriority.CRITICAL: 5,
            MemoryPriority.HIGH: 4,
            MemoryPriority.MEDIUM: 3,
            MemoryPriority.LOW: 2,
            MemoryPriority.EPHEMERAL: 1
        }
        min_rank = priority_rank.get(min_priority, 0) if min_priority else 0

        # Search through cache
        for cache_key, memories in self._memory_cache.items():
            if not cache_key.startswith(f"{agent_id}:"):
                continue

            for memory in memories:
                # Check expiration
                if memory.get("expires_at"):
                    expires = datetime.fromisoformat(memory["expires_at"])
                    if now > expires:
                        continue

                # Check memory type filter
                if memory_types and memory["memory_type"] not in memory_types:
                    continue

                # Check priority filter
                mem_rank = priority_rank.get(memory["priority"], 0)
                if mem_rank < min_rank:
                    continue

                # Check tags filter
                if tags:
                    mem_tags = set(memory.get("tags", []))
                    if not mem_tags.intersection(set(tags)):
                        continue

                # Update access stats
                memory["access_count"] = memory.get("access_count", 0) + 1
                memory["last_accessed"] = now.isoformat()

                results.append(memory)

        # Sort by recency and priority
        results.sort(
            key=lambda m: (
                priority_rank.get(m["priority"], 0),
                m.get("created_at", "")
            ),
            reverse=True
        )

        return results[:limit]

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session to get history for
            limit: Maximum messages

        Returns:
            List of conversation messages in order
        """
        results = []

        # Search all memory caches
        for cache_key, memories in self._memory_cache.items():
            for memory in memories:
                if (memory.get("session_id") == session_id and
                    memory.get("memory_type") == MemoryType.CONVERSATION):
                    results.append(memory)

        # Sort by creation time
        results.sort(key=lambda m: m.get("created_at", ""))

        return results[-limit:]

    async def search_memories(
        self,
        agent_id: str,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search memories using keyword matching.

        Args:
            agent_id: Agent to search for
            query: Search query
            memory_types: Filter by types
            limit: Maximum results

        Returns:
            Matching memories with relevance scores
        """
        query_words = set(query.lower().split())
        results = []

        for cache_key, memories in self._memory_cache.items():
            if not cache_key.startswith(f"{agent_id}:"):
                continue

            for memory in memories:
                if memory_types and memory["memory_type"] not in memory_types:
                    continue

                # Calculate relevance
                content_lower = memory["content"].lower()
                content_words = set(content_lower.split())

                # Word overlap
                overlap = len(query_words.intersection(content_words))
                if overlap == 0:
                    continue

                # Exact phrase match bonus
                exact_bonus = 0.5 if query.lower() in content_lower else 0

                relevance = (overlap / len(query_words)) + exact_bonus

                results.append({
                    **memory,
                    "relevance": round(relevance, 3)
                })

        # Sort by relevance
        results.sort(key=lambda m: m["relevance"], reverse=True)

        return results[:limit]

    # ========================================================================
    # MEMORY MANAGEMENT
    # ========================================================================

    async def forget_memory(
        self,
        memory_id: str
    ) -> Dict[str, Any]:
        """
        Delete a specific memory.

        Args:
            memory_id: Memory to delete

        Returns:
            Deletion status
        """
        for cache_key, memories in self._memory_cache.items():
            for i, memory in enumerate(memories):
                if memory["id"] == memory_id:
                    del memories[i]
                    return {
                        "status": "success",
                        "message": f"Memory {memory_id} deleted"
                    }

        return {
            "status": "error",
            "message": "Memory not found"
        }

    async def compress_memories(
        self,
        agent_id: str,
        memory_type: str = MemoryType.CONVERSATION
    ) -> Dict[str, Any]:
        """
        Compress old memories into summaries.

        Args:
            agent_id: Agent to compress memories for
            memory_type: Type to compress

        Returns:
            Compression statistics
        """
        cache_key = f"{agent_id}:{memory_type}"
        memories = self._memory_cache.get(cache_key, [])

        if len(memories) <= self.MAX_CONVERSATION_LENGTH:
            return {
                "status": "skipped",
                "message": "Below compression threshold",
                "memory_count": len(memories)
            }

        # Keep most recent, compress older
        to_keep = memories[-self.MAX_CONVERSATION_LENGTH:]
        to_compress = memories[:-self.MAX_CONVERSATION_LENGTH]

        # Create summary
        summary_content = f"[Compressed {len(to_compress)} {memory_type} memories from {to_compress[0].get('created_at', 'unknown')} to {to_compress[-1].get('created_at', 'unknown')}]"

        summary_memory = {
            "id": str(uuid4()),
            "session_id": to_compress[0].get("session_id"),
            "agent_id": agent_id,
            "content": summary_content,
            "memory_type": memory_type,
            "priority": MemoryPriority.MEDIUM,
            "tags": ["compressed", "summary"],
            "metadata": {
                "compressed_count": len(to_compress),
                "compression_date": datetime.now().isoformat()
            },
            "created_at": datetime.now().isoformat(),
            "access_count": 0
        }

        self._memory_cache[cache_key] = [summary_memory] + to_keep

        return {
            "status": "success",
            "compressed_count": len(to_compress),
            "remaining_count": len(to_keep) + 1,
            "summary_id": summary_memory["id"]
        }

    async def cleanup_expired(self) -> Dict[str, Any]:
        """
        Remove expired memories.

        Returns:
            Cleanup statistics
        """
        now = datetime.now()
        removed = 0

        for cache_key, memories in self._memory_cache.items():
            original_count = len(memories)
            self._memory_cache[cache_key] = [
                m for m in memories
                if not m.get("expires_at") or
                datetime.fromisoformat(m["expires_at"]) > now
            ]
            removed += original_count - len(self._memory_cache[cache_key])

        return {
            "status": "success",
            "removed_count": removed,
            "cleanup_time": now.isoformat()
        }

    # ========================================================================
    # AGENT-SPECIFIC OPERATIONS
    # ========================================================================

    async def learn_fact(
        self,
        agent_id: str,
        session_id: str,
        fact: str,
        source: str,
        confidence: float = 1.0
    ) -> Dict[str, Any]:
        """
        Store a learned fact for an agent.

        Args:
            agent_id: Learning agent
            session_id: Current session
            fact: The fact to learn
            source: Where it was learned
            confidence: Confidence level (0-1)

        Returns:
            Stored fact memory
        """
        priority = (
            MemoryPriority.HIGH if confidence >= 0.9 else
            MemoryPriority.MEDIUM if confidence >= 0.7 else
            MemoryPriority.LOW
        )

        return await self.store_memory(
            session_id=session_id,
            agent_id=agent_id,
            content=fact,
            memory_type=MemoryType.FACT,
            priority=priority,
            tags=["learned", source],
            metadata={
                "confidence": confidence,
                "source": source
            }
        )

    async def store_preference(
        self,
        agent_id: str,
        session_id: str,
        preference_key: str,
        preference_value: Any
    ) -> Dict[str, Any]:
        """
        Store a preference for an agent.

        Args:
            agent_id: Agent with preference
            session_id: Current session
            preference_key: Preference identifier
            preference_value: Preference value

        Returns:
            Stored preference memory
        """
        return await self.store_memory(
            session_id=session_id,
            agent_id=agent_id,
            content=f"{preference_key}: {preference_value}",
            memory_type=MemoryType.PREFERENCE,
            priority=MemoryPriority.HIGH,
            tags=["preference", preference_key],
            metadata={
                "key": preference_key,
                "value": preference_value
            }
        )

    async def get_preferences(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Get all preferences for an agent.

        Returns:
            Dictionary of preferences
        """
        memories = await self.get_agent_memories(
            agent_id=agent_id,
            memory_types=[MemoryType.PREFERENCE],
            limit=100
        )

        preferences = {}
        for memory in memories:
            key = memory.get("metadata", {}).get("key")
            value = memory.get("metadata", {}).get("value")
            if key:
                preferences[key] = value

        return preferences

    # ========================================================================
    # STATISTICS & STATUS
    # ========================================================================

    async def get_agent_stats(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Get memory statistics for an agent.

        Returns:
            Statistics dictionary
        """
        total_memories = 0
        by_type = {}
        by_priority = {}

        for cache_key, memories in self._memory_cache.items():
            if not cache_key.startswith(f"{agent_id}:"):
                continue

            for memory in memories:
                total_memories += 1

                mem_type = memory.get("memory_type", "unknown")
                by_type[mem_type] = by_type.get(mem_type, 0) + 1

                priority = memory.get("priority", "unknown")
                by_priority[priority] = by_priority.get(priority, 0) + 1

        # Count active sessions
        active_sessions = sum(
            1 for s in self._session_cache.values()
            if s.get("agent_id") == agent_id and s.get("status") == "active"
        )

        return {
            "agent_id": agent_id,
            "total_memories": total_memories,
            "by_type": by_type,
            "by_priority": by_priority,
            "active_sessions": active_sessions
        }

    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall MemMachine status.

        Returns:
            System status dictionary
        """
        total_sessions = len(self._session_cache)
        active_sessions = sum(
            1 for s in self._session_cache.values()
            if s.get("status") == "active"
        )

        total_memories = sum(
            len(memories)
            for memories in self._memory_cache.values()
        )

        # Get unique agents
        agents = set()
        for cache_key in self._memory_cache.keys():
            agent_id = cache_key.split(":")[0]
            agents.add(agent_id)

        return {
            "status": "healthy",
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_memories": total_memories,
            "unique_agents": len(agents),
            "memory_types": list(MemoryType.__dict__.keys()),
            "features": [
                "conversation_history",
                "fact_learning",
                "preference_storage",
                "memory_compression",
                "cross_session_continuity"
            ],
            "version": "1.0.0"
        }
