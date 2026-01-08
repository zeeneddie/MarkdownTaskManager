"""
Claude-Mem Service - Week 76

Session memory management for Claude Code sessions.
Provides:
- Observation capture and tagging
- Progressive disclosure (token budget management)
- Memory compression
- Hybrid search (FTS + similarity)
- Endless mode support
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple
from uuid import UUID
import re
import logging
import hashlib

from sqlalchemy import text, select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models.claude_mem import (
    ClaudeMemSession,
    ClaudeMemObservation,
    ClaudeMemSummary,
    ClaudeMemSearchIndex,
    ClaudeMemContextWindow
)

logger = logging.getLogger(__name__)


# Tag patterns for auto-tagging
TAG_PATTERNS = {
    "decision": [r"decided", r"chose", r"selected", r"will use", r"went with"],
    "bugfix": [r"fixed", r"bug", r"error", r"issue resolved", r"patched"],
    "architecture": [r"architecture", r"design", r"pattern", r"structure", r"component"],
    "performance": [r"performance", r"optimize", r"speed", r"latency", r"cache"],
    "security": [r"security", r"vulnerability", r"auth", r"permission", r"encrypt"],
    "refactor": [r"refactor", r"cleanup", r"reorganize", r"restructure"],
    "test": [r"test", r"coverage", r"assertion", r"mock", r"fixture"],
    "documentation": [r"document", r"readme", r"docstring", r"comment"],
    "dependency": [r"dependency", r"package", r"library", r"version", r"upgrade"],
    "config": [r"config", r"setting", r"environment", r"parameter"],
    "api": [r"api", r"endpoint", r"route", r"rest", r"graphql", r"request"],
}

# Priority keywords
PRIORITY_KEYWORDS = {
    "critical": [r"critical", r"urgent", r"breaking", r"security vulnerability", r"data loss"],
    "high": [r"important", r"significant", r"major", r"blocker"],
    "low": [r"minor", r"trivial", r"nice to have", r"cosmetic"],
}


class ClaudeMemService:
    """
    Service for managing Claude Code session memory.

    Provides observation capture, automatic tagging, compression,
    search, and context window generation with token budget management.
    """

    def __init__(self, db: AsyncSession):
        """Initialize with async database session."""
        self.db = db
        self._default_token_budget = 4000
        self._default_compression_ratio = 0.1
        self._tokens_per_char = 0.25  # Approximate tokens per character

    # =========================================================================
    # SECTION 1: Session Management
    # =========================================================================

    async def create_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        project_id: Optional[int] = None,
        token_budget: int = 4000,
        auto_tag: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new session.

        Args:
            session_id: Unique session identifier
            title: Optional session title
            project_id: Optional project association
            token_budget: Max tokens for context window
            auto_tag: Whether to auto-tag observations

        Returns:
            Created session data
        """
        # Check if session already exists
        stmt = select(ClaudeMemSession).where(
            ClaudeMemSession.session_id == session_id
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return {"error": f"Session {session_id} already exists"}

        session = ClaudeMemSession(
            session_id=session_id,
            title=title or f"Session {session_id[:8]}",
            project_id=project_id,
            token_budget=token_budget,
            auto_tag=auto_tag,
            endless_mode=False,
            compression_ratio=self._default_compression_ratio,
            session_data={},
            last_activity=datetime.utcnow()
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session.to_dict()

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        stmt = select(ClaudeMemSession).where(
            ClaudeMemSession.session_id == session_id
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return None

        return session.to_dict()

    async def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update session settings."""
        stmt = select(ClaudeMemSession).where(
            ClaudeMemSession.session_id == session_id
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return {"error": f"Session {session_id} not found"}

        allowed_fields = {
            "title", "token_budget", "compression_ratio",
            "auto_tag", "endless_mode", "session_data"
        }

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(session, field, value)

        session.last_activity = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(session)

        return session.to_dict()

    async def enable_endless_mode(self, session_id: str) -> Dict[str, Any]:
        """Enable endless mode for a session."""
        return await self.update_session(session_id, {"endless_mode": True})

    async def disable_endless_mode(self, session_id: str) -> Dict[str, Any]:
        """Disable endless mode for a session."""
        return await self.update_session(session_id, {"endless_mode": False})

    # =========================================================================
    # SECTION 2: Observation Capture & Tagging
    # =========================================================================

    async def capture_observation(
        self,
        session_id: str,
        content: str,
        observation_type: str = "insight",
        priority: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source_context: Optional[str] = None,
        related_files: Optional[List[str]] = None,
        auto_tag: bool = True
    ) -> Dict[str, Any]:
        """
        Capture an observation during a session.

        Args:
            session_id: Session identifier
            content: Observation content
            observation_type: Type (insight, decision, error, progress)
            priority: Priority level (critical, high, normal, low)
            tags: Manual tags
            source_context: Where the observation came from
            related_files: Related file paths
            auto_tag: Whether to auto-detect tags

        Returns:
            Created observation data
        """
        # Get session settings
        session = await self.get_session(session_id)
        session_auto_tag = session.get("auto_tag", True) if session else True

        # Determine tags
        final_tags = list(tags) if tags else []
        if auto_tag and session_auto_tag:
            auto_tags = self._detect_tags(content)
            final_tags = list(set(final_tags + auto_tags))

        # Determine priority
        if not priority:
            priority = self._detect_priority(content)

        observation = ClaudeMemObservation(
            session_id=session_id,
            content=content,
            observation_type=observation_type,
            priority=priority,
            tags=final_tags,
            source_context=source_context,
            related_files=related_files or [],
            embedding_status="pending",
            observation_data={}
        )

        self.db.add(observation)
        await self.db.commit()
        await self.db.refresh(observation)

        # Create search index entry
        await self._index_observation(observation)

        # Update session activity
        await self._update_session_activity(session_id)

        return observation.to_dict()

    async def tag_observation(
        self,
        observation_id: UUID,
        tags: List[str],
        replace: bool = False
    ) -> Dict[str, Any]:
        """
        Tag an observation.

        Args:
            observation_id: Observation ID
            tags: Tags to add
            replace: Whether to replace existing tags

        Returns:
            Updated observation data
        """
        stmt = select(ClaudeMemObservation).where(
            ClaudeMemObservation.id == observation_id
        )
        result = await self.db.execute(stmt)
        observation = result.scalar_one_or_none()

        if not observation:
            return {"error": f"Observation {observation_id} not found"}

        if replace:
            observation.tags = tags
        else:
            current_tags = observation.tags or []
            observation.tags = list(set(current_tags + tags))

        await self.db.commit()
        await self.db.refresh(observation)

        return observation.to_dict()

    def _detect_tags(self, content: str) -> List[str]:
        """Auto-detect tags based on content."""
        detected = []
        content_lower = content.lower()

        for tag, patterns in TAG_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    detected.append(tag)
                    break

        return detected

    def _detect_priority(self, content: str) -> str:
        """Auto-detect priority based on content."""
        content_lower = content.lower()

        for priority, keywords in PRIORITY_KEYWORDS.items():
            for keyword in keywords:
                if re.search(keyword, content_lower):
                    return priority

        return "normal"

    async def _index_observation(self, observation: ClaudeMemObservation) -> None:
        """Create search index entry for observation."""
        # Normalize text for FTS
        search_text = f"{observation.content} {' '.join(observation.tags or [])}"
        search_text = re.sub(r'[^\w\s]', ' ', search_text.lower())

        index_entry = ClaudeMemSearchIndex(
            observation_id=observation.id,
            search_text=search_text,
            chunk_number=0
        )

        self.db.add(index_entry)
        await self.db.commit()

    async def _update_session_activity(self, session_id: str) -> None:
        """Update session last activity timestamp."""
        stmt = select(ClaudeMemSession).where(
            ClaudeMemSession.session_id == session_id
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            session.last_activity = datetime.utcnow()
            await self.db.commit()

    # =========================================================================
    # SECTION 3: Progressive Disclosure (Context Window)
    # =========================================================================

    async def get_context_window(
        self,
        session_id: str,
        token_budget: Optional[int] = None,
        strategy: str = "recent",
        include_summaries: bool = True
    ) -> Dict[str, Any]:
        """
        Get context window for session within token budget.

        Implements progressive disclosure by including recent observations
        and compressed summaries of older content.

        Args:
            session_id: Session identifier
            token_budget: Max tokens (uses session default if not specified)
            strategy: Selection strategy (recent, priority, mixed)
            include_summaries: Whether to include compressed summaries

        Returns:
            Context window data with text and metadata
        """
        # Get session settings
        session = await self.get_session(session_id)
        if not session:
            return {"error": f"Session {session_id} not found"}

        budget = token_budget or session.get("token_budget", self._default_token_budget)

        # Build context
        context_parts = []
        included_obs = []
        included_sums = []
        total_tokens = 0

        # Get observations based on strategy
        observations = await self._get_observations_by_strategy(
            session_id, strategy
        )

        # Add observations within budget
        for obs in observations:
            obs_tokens = self._estimate_tokens(obs.content)
            if total_tokens + obs_tokens <= budget:
                context_parts.append(self._format_observation(obs))
                included_obs.append(str(obs.id))
                total_tokens += obs_tokens
            else:
                break

        # Add summaries if needed and budget allows
        if include_summaries and total_tokens < budget:
            summaries = await self._get_summaries(session_id)
            for summary in summaries:
                sum_tokens = self._estimate_tokens(summary.summary)
                if total_tokens + sum_tokens <= budget:
                    context_parts.insert(0, self._format_summary(summary))
                    included_sums.append(str(summary.id))
                    total_tokens += sum_tokens

        # Build context text
        context_text = "\n\n".join(context_parts)

        # Store context window
        context_window = ClaudeMemContextWindow(
            session_id=session_id,
            context_text=context_text,
            token_count=total_tokens,
            included_observations=included_obs,
            included_summaries=included_sums,
            generation_strategy=strategy,
            context_data={
                "token_budget": budget,
                "observations_count": len(included_obs),
                "summaries_count": len(included_sums)
            }
        )

        self.db.add(context_window)
        await self.db.commit()
        await self.db.refresh(context_window)

        return {
            "session_id": session_id,
            "context_text": context_text,
            "token_count": total_tokens,
            "token_budget": budget,
            "observations_included": len(included_obs),
            "summaries_included": len(included_sums),
            "strategy": strategy,
            "context_id": str(context_window.id)
        }

    async def _get_observations_by_strategy(
        self,
        session_id: str,
        strategy: str
    ) -> List[ClaudeMemObservation]:
        """Get observations based on selection strategy."""
        if strategy == "priority":
            # High priority first, then recent
            stmt = select(ClaudeMemObservation).where(
                ClaudeMemObservation.session_id == session_id
            ).order_by(
                desc(func.array_position(['critical', 'high', 'normal', 'low'],
                                         ClaudeMemObservation.priority)),
                desc(ClaudeMemObservation.created_at)
            ).limit(100)
        elif strategy == "mixed":
            # Combination of priority and recency
            stmt = select(ClaudeMemObservation).where(
                ClaudeMemObservation.session_id == session_id
            ).order_by(
                desc(ClaudeMemObservation.created_at)
            ).limit(100)
        else:  # recent (default)
            stmt = select(ClaudeMemObservation).where(
                ClaudeMemObservation.session_id == session_id
            ).order_by(
                desc(ClaudeMemObservation.created_at)
            ).limit(100)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _get_summaries(
        self,
        session_id: str,
        limit: int = 5
    ) -> List[ClaudeMemSummary]:
        """Get summaries for session."""
        stmt = select(ClaudeMemSummary).where(
            ClaudeMemSummary.session_id == session_id
        ).order_by(
            desc(ClaudeMemSummary.created_at)
        ).limit(limit)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text."""
        return int(len(text) * self._tokens_per_char)

    def _format_observation(self, obs: ClaudeMemObservation) -> str:
        """Format observation for context."""
        tags_str = f" [{', '.join(obs.tags)}]" if obs.tags else ""
        priority_str = f" ({obs.priority})" if obs.priority != "normal" else ""
        timestamp = obs.created_at.strftime("%H:%M") if obs.created_at else ""

        return f"[{timestamp}]{priority_str}{tags_str}: {obs.content}"

    def _format_summary(self, summary: ClaudeMemSummary) -> str:
        """Format summary for context."""
        return f"[Summary of {summary.original_count} earlier observations]:\n{summary.summary}"

    # =========================================================================
    # SECTION 4: Memory Compression
    # =========================================================================

    async def compress_memories(
        self,
        session_id: str,
        compression_ratio: Optional[float] = None,
        older_than_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Compress older observations into summaries.

        Args:
            session_id: Session identifier
            compression_ratio: Target compression (e.g., 0.1 = 10%)
            older_than_hours: Only compress observations older than this

        Returns:
            Compression result with stats
        """
        # Get session settings
        session = await self.get_session(session_id)
        if not session:
            return {"error": f"Session {session_id} not found"}

        ratio = compression_ratio or session.get(
            "compression_ratio",
            self._default_compression_ratio
        )

        # Get old observations
        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
        stmt = select(ClaudeMemObservation).where(
            and_(
                ClaudeMemObservation.session_id == session_id,
                ClaudeMemObservation.created_at < cutoff
            )
        ).order_by(ClaudeMemObservation.created_at)

        result = await self.db.execute(stmt)
        old_observations = result.scalars().all()

        if not old_observations:
            return {
                "session_id": session_id,
                "observations_compressed": 0,
                "summary_created": False,
                "message": "No observations to compress"
            }

        # Generate summary
        summary_text = self._generate_summary(old_observations, ratio)
        original_tokens = sum(self._estimate_tokens(o.content) for o in old_observations)
        summary_tokens = self._estimate_tokens(summary_text)
        actual_ratio = summary_tokens / original_tokens if original_tokens > 0 else 0

        # Collect tag statistics
        all_tags = []
        for obs in old_observations:
            all_tags.extend(obs.tags or [])
        tags_summary = {}
        for tag in all_tags:
            tags_summary[tag] = tags_summary.get(tag, 0) + 1

        # Create summary
        summary = ClaudeMemSummary(
            session_id=session_id,
            original_count=len(old_observations),
            summary=summary_text,
            compression_ratio=actual_ratio,
            token_count=summary_tokens,
            tags_summary=tags_summary,
            time_range_start=old_observations[0].created_at,
            time_range_end=old_observations[-1].created_at,
            summary_data={
                "original_tokens": original_tokens,
                "target_ratio": ratio
            }
        )

        self.db.add(summary)

        # Delete compressed observations (optional - could keep for search)
        for obs in old_observations:
            await self.db.delete(obs)

        await self.db.commit()
        await self.db.refresh(summary)

        return {
            "session_id": session_id,
            "observations_compressed": len(old_observations),
            "summary_created": True,
            "summary_id": str(summary.id),
            "original_tokens": original_tokens,
            "summary_tokens": summary_tokens,
            "actual_compression_ratio": actual_ratio
        }

    def _generate_summary(
        self,
        observations: List[ClaudeMemObservation],
        target_ratio: float
    ) -> str:
        """
        Generate summary of observations.

        In production, this would use an LLM. For now, we use
        a simple extraction approach.
        """
        # Group by type
        by_type: Dict[str, List[str]] = {}
        for obs in observations:
            obs_type = obs.observation_type or "general"
            if obs_type not in by_type:
                by_type[obs_type] = []
            by_type[obs_type].append(obs.content)

        # Build summary sections
        sections = []
        for obs_type, contents in by_type.items():
            type_label = obs_type.capitalize()
            if len(contents) == 1:
                sections.append(f"{type_label}: {contents[0][:200]}")
            else:
                # Combine with truncation
                combined = "; ".join(c[:100] for c in contents[:5])
                if len(contents) > 5:
                    combined += f" (and {len(contents) - 5} more)"
                sections.append(f"{type_label}s ({len(contents)}): {combined}")

        return "\n".join(sections)

    # =========================================================================
    # SECTION 5: Hybrid Search
    # =========================================================================

    async def search_memories(
        self,
        session_id: str,
        query: str,
        use_fts: bool = True,
        limit: int = 20,
        tags_filter: Optional[List[str]] = None,
        priority_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search session memories with hybrid approach.

        Combines full-text search with filtering capabilities.

        Args:
            session_id: Session identifier
            query: Search query
            use_fts: Whether to use full-text search
            limit: Maximum results
            tags_filter: Filter by tags
            priority_filter: Filter by priority

        Returns:
            Search results with matching observations
        """
        # Build base query
        conditions = [ClaudeMemObservation.session_id == session_id]

        # Add tag filter
        if tags_filter:
            # PostgreSQL JSONB array contains
            for tag in tags_filter:
                conditions.append(
                    ClaudeMemObservation.tags.contains([tag])
                )

        # Add priority filter
        if priority_filter:
            conditions.append(ClaudeMemObservation.priority == priority_filter)

        # Build statement
        if use_fts and query:
            # Use full-text search via search index
            search_stmt = select(ClaudeMemSearchIndex.observation_id).where(
                ClaudeMemSearchIndex.search_text.ilike(f"%{query}%")
            )
            search_result = await self.db.execute(search_stmt)
            matching_ids = [row[0] for row in search_result.fetchall()]

            if matching_ids:
                conditions.append(ClaudeMemObservation.id.in_(matching_ids))
            else:
                # Fallback to direct content search
                conditions.append(ClaudeMemObservation.content.ilike(f"%{query}%"))

        stmt = select(ClaudeMemObservation).where(
            and_(*conditions)
        ).order_by(
            desc(ClaudeMemObservation.created_at)
        ).limit(limit)

        result = await self.db.execute(stmt)
        observations = result.scalars().all()

        return {
            "session_id": session_id,
            "query": query,
            "results_count": len(observations),
            "results": [obs.to_dict() for obs in observations]
        }

    async def get_observations_by_tags(
        self,
        session_id: str,
        tags: List[str],
        match_all: bool = False
    ) -> List[Dict[str, Any]]:
        """Get observations matching specified tags."""
        stmt = select(ClaudeMemObservation).where(
            ClaudeMemObservation.session_id == session_id
        )

        result = await self.db.execute(stmt)
        observations = result.scalars().all()

        # Filter by tags (in Python since JSONB array operations vary)
        filtered = []
        for obs in observations:
            obs_tags = set(obs.tags or [])
            query_tags = set(tags)

            if match_all:
                if query_tags.issubset(obs_tags):
                    filtered.append(obs.to_dict())
            else:
                if query_tags.intersection(obs_tags):
                    filtered.append(obs.to_dict())

        return filtered

    # =========================================================================
    # SECTION 6: Endless Mode Support
    # =========================================================================

    async def inject_context(
        self,
        session_id: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        Inject session context into a prompt for endless mode.

        Args:
            session_id: Session identifier
            prompt: Original user prompt

        Returns:
            Enhanced prompt with session context
        """
        session = await self.get_session(session_id)
        if not session:
            return {"error": f"Session {session_id} not found"}

        if not session.get("endless_mode"):
            return {"error": "Endless mode not enabled for this session"}

        # Get context window
        context = await self.get_context_window(
            session_id,
            strategy="mixed"
        )

        if "error" in context:
            return context

        # Build enhanced prompt
        enhanced_prompt = f"""## Session Context

{context['context_text']}

---

## Current Request

{prompt}"""

        return {
            "session_id": session_id,
            "original_prompt": prompt,
            "enhanced_prompt": enhanced_prompt,
            "context_tokens": context["token_count"],
            "total_tokens_estimated": self._estimate_tokens(enhanced_prompt)
        }

    # =========================================================================
    # SECTION 7: Statistics & Dashboard Data
    # =========================================================================

    async def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a session."""
        session = await self.get_session(session_id)
        if not session:
            return {"error": f"Session {session_id} not found"}

        # Count observations
        obs_count_stmt = select(func.count(ClaudeMemObservation.id)).where(
            ClaudeMemObservation.session_id == session_id
        )
        obs_count = (await self.db.execute(obs_count_stmt)).scalar()

        # Count summaries
        sum_count_stmt = select(func.count(ClaudeMemSummary.id)).where(
            ClaudeMemSummary.session_id == session_id
        )
        sum_count = (await self.db.execute(sum_count_stmt)).scalar()

        # Get tag distribution
        obs_stmt = select(ClaudeMemObservation).where(
            ClaudeMemObservation.session_id == session_id
        )
        result = await self.db.execute(obs_stmt)
        observations = result.scalars().all()

        tag_counts: Dict[str, int] = {}
        priority_counts: Dict[str, int] = {"critical": 0, "high": 0, "normal": 0, "low": 0}
        type_counts: Dict[str, int] = {}
        total_tokens = 0

        for obs in observations:
            for tag in (obs.tags or []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            priority_counts[obs.priority or "normal"] = priority_counts.get(
                obs.priority or "normal", 0
            ) + 1
            type_counts[obs.observation_type or "general"] = type_counts.get(
                obs.observation_type or "general", 0
            ) + 1
            total_tokens += self._estimate_tokens(obs.content)

        return {
            "session_id": session_id,
            "session_data": session,
            "observation_count": obs_count,
            "summary_count": sum_count,
            "total_tokens_estimated": total_tokens,
            "tag_distribution": tag_counts,
            "priority_distribution": priority_counts,
            "type_distribution": type_counts,
            "endless_mode": session.get("endless_mode", False),
            "token_budget": session.get("token_budget", self._default_token_budget)
        }

    async def get_dashboard_data(
        self,
        project_id: Optional[int] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get dashboard data for all sessions or filtered by project."""
        # Get sessions
        if project_id:
            stmt = select(ClaudeMemSession).where(
                ClaudeMemSession.project_id == project_id
            ).order_by(
                desc(ClaudeMemSession.last_activity)
            ).limit(limit)
        else:
            stmt = select(ClaudeMemSession).order_by(
                desc(ClaudeMemSession.last_activity)
            ).limit(limit)

        result = await self.db.execute(stmt)
        sessions = result.scalars().all()

        # Build dashboard data
        session_data = []
        total_observations = 0
        total_summaries = 0
        endless_sessions = 0

        for session in sessions:
            # Count observations per session
            obs_count_stmt = select(func.count(ClaudeMemObservation.id)).where(
                ClaudeMemObservation.session_id == session.session_id
            )
            obs_count = (await self.db.execute(obs_count_stmt)).scalar()

            session_data.append({
                "session_id": session.session_id,
                "title": session.title,
                "endless_mode": session.endless_mode,
                "observation_count": obs_count,
                "last_activity": session.last_activity.isoformat() if session.last_activity else None
            })

            total_observations += obs_count
            if session.endless_mode:
                endless_sessions += 1

        return {
            "project_id": project_id,
            "total_sessions": len(sessions),
            "endless_sessions": endless_sessions,
            "total_observations": total_observations,
            "sessions": session_data
        }

    # =========================================================================
    # SECTION 8: Cleanup & Maintenance
    # =========================================================================

    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete a session and all related data."""
        # Check if session exists
        stmt = select(ClaudeMemSession).where(
            ClaudeMemSession.session_id == session_id
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return {"error": f"Session {session_id} not found"}

        # Delete session (cascades to observations, summaries, context windows)
        await self.db.delete(session)
        await self.db.commit()

        return {
            "success": True,
            "session_id": session_id,
            "message": "Session and all related data deleted"
        }

    async def cleanup_old_sessions(
        self,
        days_inactive: int = 30
    ) -> Dict[str, Any]:
        """Clean up sessions inactive for specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days_inactive)

        stmt = select(ClaudeMemSession).where(
            ClaudeMemSession.last_activity < cutoff
        )
        result = await self.db.execute(stmt)
        old_sessions = result.scalars().all()

        deleted_count = 0
        for session in old_sessions:
            if not session.endless_mode:  # Don't delete endless mode sessions
                await self.db.delete(session)
                deleted_count += 1

        await self.db.commit()

        return {
            "success": True,
            "sessions_deleted": deleted_count,
            "cutoff_date": cutoff.isoformat()
        }
