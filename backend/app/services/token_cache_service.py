"""
Token Cache Service - Track and analyze cache metrics

Week 61: Enhanced Observability Integration

Tracks Claude's prompt caching to measure:
- Cache hit rates
- Token savings
- Cost reduction
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.observability import AgentAction


class TokenCacheService:
    """
    Service for tracking and analyzing token cache metrics.

    Claude's prompt caching allows reusing previously computed tokens,
    reducing both latency and cost. This service tracks:
    - cache_creation_input_tokens: New tokens added to cache
    - cache_read_input_tokens: Tokens reused from cache (savings)
    """

    # Cost per million tokens (Claude pricing)
    PRICING = {
        "claude-3-opus": {
            "input": 15.0,
            "output": 75.0,
            "cache_write": 18.75,  # 25% premium for cache creation
            "cache_read": 1.50,    # 90% discount for cache hits
        },
        "claude-3-sonnet": {
            "input": 3.0,
            "output": 15.0,
            "cache_write": 3.75,
            "cache_read": 0.30,
        },
        "claude-3-haiku": {
            "input": 0.25,
            "output": 1.25,
            "cache_write": 0.3125,
            "cache_read": 0.025,
        },
        "default": {
            "input": 3.0,
            "output": 15.0,
            "cache_write": 3.75,
            "cache_read": 0.30,
        }
    }

    def __init__(self, db: Session):
        """Initialize token cache service."""
        self.db = db

    def get_cache_metrics(
        self,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get aggregated cache metrics.

        Args:
            session_id: Filter by session
            agent_name: Filter by agent
            hours: Time window in hours

        Returns:
            Dict with cache statistics
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        query = self.db.query(
            func.sum(AgentAction.input_tokens).label("total_input"),
            func.sum(AgentAction.output_tokens).label("total_output"),
            func.sum(AgentAction.token_cache_creation).label("cache_created"),
            func.sum(AgentAction.token_cache_read).label("cache_read"),
            func.count(AgentAction.id).label("action_count"),
        ).filter(
            AgentAction.created_at >= since
        )

        if session_id:
            query = query.filter(AgentAction.session_id == session_id)
        if agent_name:
            query = query.filter(AgentAction.agent_name == agent_name)

        result = query.first()

        total_input = result.total_input or 0
        total_output = result.total_output or 0
        cache_created = result.cache_created or 0
        cache_read = result.cache_read or 0
        action_count = result.action_count or 0

        # Calculate metrics
        total_tokens = total_input + total_output
        cache_hit_rate = self._calculate_hit_rate(cache_read, total_input)
        potential_input = total_input + cache_read  # What we would have paid without cache

        return {
            "period_hours": hours,
            "action_count": action_count,
            "tokens": {
                "input": total_input,
                "output": total_output,
                "total": total_tokens,
            },
            "cache": {
                "created": cache_created,
                "read": cache_read,
                "hit_rate_percent": cache_hit_rate,
            },
            "savings": {
                "tokens_saved": cache_read,
                "potential_input_tokens": potential_input,
                "savings_percent": round((cache_read / potential_input * 100) if potential_input > 0 else 0, 2),
            }
        }

    def get_cache_metrics_by_agent(
        self,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get cache metrics grouped by agent.

        Args:
            hours: Time window in hours

        Returns:
            List of per-agent cache statistics
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        results = self.db.query(
            AgentAction.agent_name,
            func.sum(AgentAction.input_tokens).label("total_input"),
            func.sum(AgentAction.output_tokens).label("total_output"),
            func.sum(AgentAction.token_cache_creation).label("cache_created"),
            func.sum(AgentAction.token_cache_read).label("cache_read"),
            func.count(AgentAction.id).label("action_count"),
        ).filter(
            AgentAction.created_at >= since
        ).group_by(
            AgentAction.agent_name
        ).all()

        metrics = []
        for row in results:
            total_input = row.total_input or 0
            cache_read = row.cache_read or 0

            metrics.append({
                "agent_name": row.agent_name,
                "action_count": row.action_count or 0,
                "total_input": total_input,
                "total_output": row.total_output or 0,
                "cache_created": row.cache_created or 0,
                "cache_read": cache_read,
                "hit_rate_percent": self._calculate_hit_rate(cache_read, total_input),
            })

        return sorted(metrics, key=lambda x: x["cache_read"], reverse=True)

    def calculate_cost_savings(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cache_created: int,
        cache_read: int
    ) -> Dict[str, float]:
        """
        Calculate cost with and without caching.

        Args:
            model: Model name for pricing
            input_tokens: Regular input tokens
            output_tokens: Output tokens
            cache_created: Tokens written to cache
            cache_read: Tokens read from cache

        Returns:
            Dict with cost breakdown
        """
        pricing = self._get_pricing(model)

        # Cost with caching
        actual_cost = (
            (input_tokens / 1_000_000) * pricing["input"] +
            (output_tokens / 1_000_000) * pricing["output"] +
            (cache_created / 1_000_000) * pricing["cache_write"] +
            (cache_read / 1_000_000) * pricing["cache_read"]
        )

        # Cost without caching (cache_read would have been regular input)
        potential_input = input_tokens + cache_read
        no_cache_cost = (
            (potential_input / 1_000_000) * pricing["input"] +
            (output_tokens / 1_000_000) * pricing["output"]
        )

        savings = no_cache_cost - actual_cost

        return {
            "model": model,
            "actual_cost_usd": round(actual_cost, 6),
            "no_cache_cost_usd": round(no_cache_cost, 6),
            "savings_usd": round(savings, 6),
            "savings_percent": round((savings / no_cache_cost * 100) if no_cache_cost > 0 else 0, 2),
            "breakdown": {
                "input_cost": round((input_tokens / 1_000_000) * pricing["input"], 6),
                "output_cost": round((output_tokens / 1_000_000) * pricing["output"], 6),
                "cache_write_cost": round((cache_created / 1_000_000) * pricing["cache_write"], 6),
                "cache_read_cost": round((cache_read / 1_000_000) * pricing["cache_read"], 6),
            }
        }

    def get_hourly_cache_trend(
        self,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get hourly cache usage trend.

        Args:
            hours: Number of hours to include

        Returns:
            List of hourly cache statistics
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        # Group by hour
        results = self.db.query(
            func.date_trunc('hour', AgentAction.created_at).label("hour"),
            func.sum(AgentAction.input_tokens).label("input"),
            func.sum(AgentAction.token_cache_read).label("cache_read"),
            func.count(AgentAction.id).label("actions"),
        ).filter(
            AgentAction.created_at >= since
        ).group_by(
            func.date_trunc('hour', AgentAction.created_at)
        ).order_by(
            func.date_trunc('hour', AgentAction.created_at)
        ).all()

        trend = []
        for row in results:
            total_input = row.input or 0
            cache_read = row.cache_read or 0

            trend.append({
                "hour": row.hour.isoformat() if row.hour else None,
                "input_tokens": total_input,
                "cache_read_tokens": cache_read,
                "action_count": row.actions or 0,
                "hit_rate_percent": self._calculate_hit_rate(cache_read, total_input),
            })

        return trend

    def record_cache_event(
        self,
        action_id: int,
        cache_created: int,
        cache_read: int
    ) -> Optional[AgentAction]:
        """
        Record cache metrics for an action.

        Args:
            action_id: ID of the AgentAction
            cache_created: Tokens written to cache
            cache_read: Tokens read from cache

        Returns:
            Updated AgentAction or None
        """
        action = self.db.query(AgentAction).filter(
            AgentAction.id == action_id
        ).first()

        if action:
            action.token_cache_creation = cache_created
            action.token_cache_read = cache_read
            self.db.flush()

        return action

    def _get_pricing(self, model: str) -> Dict[str, float]:
        """Get pricing for model."""
        model_lower = model.lower()

        for key in self.PRICING:
            if key in model_lower:
                return self.PRICING[key]

        return self.PRICING["default"]

    def _calculate_hit_rate(self, cache_read: int, total_input: int) -> float:
        """Calculate cache hit rate percentage."""
        potential = total_input + cache_read
        if potential == 0:
            return 0.0
        return round((cache_read / potential) * 100, 2)
